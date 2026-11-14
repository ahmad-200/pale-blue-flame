<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { store } from '../data.js'
import JourneyStrip from './JourneyStrip.vue'
import MaterialIcon from './MaterialIcon.vue'
import AirLines from './AirLines.vue'
import LookCloser from './LookCloser.vue'

const props = defineProps({ stand: Boolean, route: Object })   // ?stand=1: the full-screen exhibition view
const placeId = ref('moon')
const material = ref('SIBAL (cotton-fiberglass)')
const place = computed(() => store.places.find(p => p.id === placeId.value))
const short = name => name.replace(/ \(.*\)/, '')   // "Spacewalk prep (airlock 'campout')" -> "Spacewalk prep"

const materials = computed(() => {
  const n = {}
  for (const t of store.tests) if (t.material !== 'not stated') n[t.material] = (n[t.material] || 0) + 1
  return Object.entries(n).sort((a, b) => b[1] - a[1])
})
const mine = computed(() => store.tests.filter(t => t.material === material.value))
const withOxygen = computed(() => mine.value.filter(t => t.oxygen_pct != null))

// the air this material was actually tested in
const region = computed(() => {
  if (!withOxygen.value.length) return null
  const o = withOxygen.value.map(t => t.oxygen_pct)
  return { min: Math.min(...o), max: Math.max(...o) }
})
// is a place's air inside the air this material was tested in? (pressure about 1 atm, oxygen within the tested range)
const statusOf = p => {
  const tested = !!region.value && Math.abs(p.pressure_atm - 1) <= 0.1
    && p.oxygen_pct >= region.value.min - 1 && p.oxygen_pct <= region.value.max + 1
  return { tested, count: tested ? withOxygen.value.length : 0 }
}
const inside = computed(() => statusOf(place.value).tested)
const nothing = () => ({ tested: false, count: 0 })   // no material matched the question: no fires to show anywhere

// nearest = smallest gap in oxygen (10 points) and pressure (0.5 atm) weighted alike; shown as plain differences
// plain words for the difference: "the same air as here", or what this place has more or less of
const gapWords = (dO, dP) => {
  const parts = []
  if (Math.abs(dO) >= 0.5) parts.push(`${Math.abs(dO).toFixed(1)} points ${dO > 0 ? 'more' : 'less'} oxygen here`)
  if (Math.abs(dP) >= 0.05) parts.push(dP < 0 ? `air ${Math.abs(dP).toFixed(2)} atm thinner here` : `air ${dP.toFixed(2)} atm denser here`)
  return parts.length ? parts.join(', ') : 'the same air as here'
}
const nearest = computed(() => withOxygen.value.map(t => {
  const dO = place.value.oxygen_pct - t.oxygen_pct, dP = place.value.pressure_atm - t.pressure_atm
  return { ...t, dist: Math.abs(dO) / 10 + Math.abs(dP) / 0.5,
           gap: gapWords(dO, dP) }
}).sort((a, b) => a.dist - b.dist).slice(0, 5))
const closest = computed(() => nearest.value[0])

// what each material is, in everyday words (SIBAL from NASA's Saffire-I record)
const WHAT = {
  'SIBAL (cotton-fiberglass)': 'A fabric of cotton on a fiberglass backing. It burns like cotton but keeps its shape.',
  'PMMA (acrylic)': 'Clear, hard plastic: the stuff of Plexiglas windows. NASA burned it as sheets, rods and spheres.',
  'PMMA (assumed)': 'Probably acrylic: NASA’s table only says “sphere”.',
  'PMMA + Nomex': 'Acrylic and Nomex fabric in one sample.',
  'Nomex': 'A flame-resistant fabric, the kind used in firefighter suits.',
  'silicone': 'A soft, rubbery material, used in seals and cable coverings.',
  'candle wax': 'Ordinary candle wax.',
  'Ultem': 'A tough, amber-coloured plastic.',
}
const what = computed(() => WHAT[material.value] || 'NASA’s table does not say what this sample was.')

// --- carousel: nobody at a stand clicks, so the page walks through examples by itself.
// Each tested case at the Station is followed by the same material somewhere nobody has tried.
const SLIDES = [
  ['SIBAL (cotton-fiberglass)', 'iss'], ['SIBAL (cotton-fiberglass)', 'moon'],
  ['PMMA (acrylic)', 'iss'], ['PMMA (acrylic)', 'rover'],
  ['Nomex', 'iss'], ['Nomex', 'airlock'],
  ['silicone', 'iss'], ['silicone', 'moon'],
]
const STEP_MS = 6000, IDLE_MS = 20000   // six seconds: the verdict plus one number
const slide = ref(0), auto = ref(true), asked = ref(false)
let tick = null, idle = null
function show(i) {
  noMatch.value = false
  if (asked.value) { asked.value = false; reading.value = null }
  slide.value = (i + SLIDES.length) % SLIDES.length
  ;[material.value, placeId.value] = SLIDES[slide.value]
}
function start() { clearInterval(tick); auto.value = true; tick = setInterval(() => show(slide.value + 1), STEP_MS) }
function stop() { clearInterval(tick); auto.value = false }
// someone touched it: pause, and come back to the tour after a quiet spell
function touched() { stop(); clearTimeout(idle); if (!asked.value) idle = setTimeout(start, IDLE_MS) }   // after a question: wait for Play
// a change that does not match the current slide came from a person (Vue runs this after the change, so compare, don't flag)
let fromAsk = null   // the material and place the question box just set: not a person's click
watch([material, placeId], ([m, p]) => {
  if (fromAsk && m === fromAsk[0] && p === fromAsk[1]) return
  const [sm, sp] = SLIDES[slide.value]
  if (m !== sm || p !== sp) { noMatch.value = false; touched() }
})
// a person chose an example (a dot or an arrow): go there and pause the tour until they press Play
function pick(i) { show(i); stop(); clearTimeout(idle) }
const step = d => pick(slide.value + d)
// the keyboard arrows do the same, unless the person is typing or choosing in a menu
function onKey(e) {
  if (e.altKey || e.ctrlKey || e.metaKey || !['ArrowLeft', 'ArrowRight'].includes(e.key)) return
  if (e.target.closest?.('input, textarea, select, [contenteditable], .closer')) return
  e.preventDefault(); step(e.key === 'ArrowLeft' ? -1 : 1)
}
// reading the tabs below: stop the tour for good (Play starts it again), so the page does not change under the reader
function holdTour() { stop(); clearTimeout(idle) }
function toCloser() { holdTour(); document.getElementById('closer')?.scrollIntoView({ behavior: 'smooth', block: 'start' }) }
function toggle() { clearTimeout(idle); if (auto.value) stop(); else backToTour() }
function backToTour() { asked.value = false; reading.value = null; noMatch.value = false; question.value = ''; show(slide.value); start() }
onMounted(() => { show(0); start(); window.addEventListener('keydown', onKey) })

// --- the question box: an AI reads the visitor's words and picks one of OUR materials and places.
// The answer itself still comes from NASA's data. The key lives on the server (/api/ask), never here.
const ASK_URL = import.meta.env.VITE_ASK_URL || '/api/ask'
const question = ref(''), asking = ref(false), reading = ref(null)
// example questions: one click asks it, so a visitor sees a real answer arrive
const PROMPTS = ['Would my running shoe burn in a Moon rover?', 'Would my cotton shirt burn on the Station?',
  'Would a candle burn on Mars?', 'Would a metal spoon burn on the Moon?']
function askThis(q) { if (asking.value) return; question.value = q; ask() }
// seconds since the question was sent, shown beside the spinner
const waited = ref(0); let waitTimer = null
const noMatch = ref(false)   // the AI found no material we have: say so, never show a leftover one

// the place for the story's footer: which NASA experiments the dots come from
const sources = computed(() => [...new Set(withOxygen.value.map(t => t.experiment))])
// --- rank NASA's investigations for the chosen place: our rule, explained in words (no AI)
// what it studied (material flammability > detection, suppression > gas flames > models), whether it burned this
// material, and how close its tested oxygen came to this place's air
const ROLE = {
  'BASS': ['prevent', 3, 'burned solid materials in moving air'], 'BASS-II': ['prevent', 3, 'burned solid materials in moving air'],
  'SAFFIRE-I': ['prevent', 3, 'large fabric fire on a cargo ship'], 'SAFFIRE-II': ['prevent', 3, 'material fires on a cargo ship'],
  'SAFFIRE-III': ['prevent', 3, 'large fabric fire on a cargo ship'], 'ACME BRE': ['prevent', 2.5, 'emulated burning materials in still air, including elevated oxygen'],
  'SAME': ['detect', 2.5, 'measured smoke from heated materials'], 'SAME-R': ['detect', 2.5, 'measured smoke from heated materials'],
  'DAFT / DAFT-2': ['detect', 2, 'tested a smoke-detector instrument on dust'],
  'FLEX': ['suppress', 2.5, 'put out flames with CO2 and helium'], 'FLEX-2': ['suppress', 2.5, 'put out fuel-droplet flames'],
}
const ranked = computed(() => store.experiments.map(e => {
  const role = ROLE[e.name] || (e.kind.startsWith('flight') ? [e.pillar, 1, 'studied gas or droplet flames'] : [e.pillar, 0.5, 'models or ground data'])
  const rows = store.tests.filter(t => t.experiment === e.name)
  const sameMaterial = rows.some(t => t.material === material.value)
  const o2 = rows.filter(t => t.oxygen_pct != null).map(t => t.oxygen_pct)
  const gap = o2.length ? Math.min(...o2.map(v => Math.abs(v - place.value.oxygen_pct))) : null
  const why = [role[2]]
  if (sameMaterial) why.push(`burned ${material.value}`)
  if (gap != null) why.push(gap < 1 ? `tested at ${place.value.name}'s oxygen level` : `closest test ${gap.toFixed(1)} points of oxygen away`)
  if (e.name === 'ACME BRE') why.push('its record reports burning in elevated oxygen without airflow')
  const score = role[1] + (sameMaterial ? 1 : 0) + (gap != null ? Math.max(0, 1 - gap / 20) : 0) + (e.name === 'ACME BRE' && place.value.oxygen_pct > 25 ? 1 : 0)
  return { e, pillar: role[0], score, why }
}).sort((a, b) => b.score - a.score))   // best first; the tabs below show the top few of each kind

const isNarrow = ref(false)
const mq = typeof window !== 'undefined' ? window.matchMedia('(max-width: 700px)') : null
if (mq) { isNarrow.value = mq.matches; mq.addEventListener('change', e => { isNarrow.value = e.matches }) }

async function ask() {
  if (!question.value.trim() || asking.value) return
  asking.value = true; reading.value = null; touched()
  waited.value = 0; clearInterval(waitTimer); waitTimer = setInterval(() => waited.value++, 1000)
  try {
    const r = await fetch(ASK_URL, { method: 'POST', headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({ question: question.value }) })
    const out = await r.json()
    if (out.error) { reading.value = { error: out.error }; return }
    if (out.place) placeId.value = out.place
    if (out.material) material.value = out.material
    fromAsk = [material.value, placeId.value]
    noMatch.value = !out.material
    reading.value = out
  } catch {
    reading.value = { error: 'Custom questions need an internet connection. The NASA experiment tour still works offline.' }
  } finally {
    asking.value = false; clearInterval(waitTimer); stop(); clearTimeout(idle)
    if (reading.value && !reading.value.error) {
      asked.value = true
      await nextTick(); window.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }
}
onBeforeUnmount(() => { clearInterval(tick); clearTimeout(idle); clearInterval(waitTimer); window.removeEventListener('keydown', onKey) })
</script>

<template>
  <div class="burn" :class="{ stand, answering: asked, thinking: asking }">
    <section class="stage">
      <!-- 1. the question and the verdict, first -->
      <header class="qv">
        <p v-if="asking" class="thinking-line" role="status" aria-live="polite">
          <span class="spinner" aria-hidden="true"></span>
          <span>Reading <b>“{{ question }}”</b>, then looking up the closest materials NASA tested… <span class="muted">{{ waited }} s</span></span>
        </p>
        <p v-if="asked && reading && reading.object && !noMatch" class="asked-line">
          NASA never burned a {{ reading.object }}. The closest material NASA tested is <b>{{ material }}</b>{{ " " }}
          <span class="muted">(a stand-in, not the object itself)</span>
          <br v-if="reading.made_of" /><span v-if="reading.made_of" class="muted small">Usually made of: {{ reading.made_of }}.</span>
        </p>
        <h1 v-if="noMatch" class="burn-q">Would your <span class="asked">{{ reading?.object || question }}</span> burn?</h1>
        <h1 v-else-if="asked && reading && reading.object" class="burn-q">
          Would your <span class="pick">{{ reading.object }}</span> burn in
          <span class="nowrap"><label class="inline-select"><span class="sr">Place</span>
            <select v-model="placeId">
              <option v-for="p in store.places" :key="p.id" :value="p.id">{{ short(p.name) }}</option>
            </select>
          </label>?</span>
        </h1>
        <h1 v-else-if="stand" class="burn-q">Would <span class="pick">{{ material }}</span> burn in <span class="pick">{{ place.name }}</span>?</h1>
        <h1 v-else class="burn-q">
          Would
          <label class="inline-select"><span class="sr">Material</span>
            <select v-model="material">
              <option v-for="[m] in materials" :key="m" :value="m">{{ m }}</option>
            </select>
          </label>
          burn in
          <span class="nowrap"><label class="inline-select"><span class="sr">Place</span>
            <select v-model="placeId">
              <option v-for="p in store.places" :key="p.id" :value="p.id">{{ short(p.name) }}</option>
            </select>
          </label>?</span>
        </h1>

        <Transition name="swap" mode="out-in">
          <div class="verdict-block" :class="inside ? 'ok' : 'gap'" :key="placeId + material + noMatch" aria-live="polite">
            <template v-if="noMatch">
              <p class="verdict">NASA's data can't answer this.</p>
              <p class="why">{{ reading?.answer }}</p>
            </template>
            <template v-else-if="!withOxygen.length">
              <p class="verdict">We can't place these fires.</p>
              <p class="why">NASA burned {{ mine.length }} samples of {{ material }}, but its tables don't record the oxygen.</p>
            </template>
            <template v-else-if="inside">
              <p class="verdict">NASA tested this.</p>
              <p class="why">{{ withOxygen.length }} real fires in air like this. Tested is not the same as safe.</p>
            </template>
            <template v-else>
              <p class="verdict">We don't know. No matching test.</p>
              <p class="why">NASA burned it only in {{ region.min === region.max ? region.min : `${region.min}–${region.max}` }}% oxygen at 1 atm.
                Not tested here does not mean safe.</p>
            </template>
          </div>
        </Transition>

        <Transition name="swap" mode="out-in">
          <p v-if="stand && !noMatch && !asked" class="material-line" :key="material">
            <MaterialIcon :material="material" /><span><b>{{ material }}:</b> {{ what }} <span class="muted small">(illustration)</span></span>
          </p>
        </Transition>

        <div v-if="!stand && reading && reading.candidates && reading.candidates.length > 1" class="standins">
          <span class="muted small">Other close materials NASA tested:</span>
          <button v-for="c in reading.candidates" :key="c.material" class="standin" :title="c.why" :class="{ on: c.material === material }"
                  @click="material = c.material; fromAsk = [c.material, placeId]; touched()">
            <MaterialIcon :material="c.material" /><span><b>{{ c.material }}</b> <small>{{ c.why }}</small></span>
          </button>
        </div>
        <p v-if="reading && reading.error" class="reading error">{{ reading.error }}</p>
      </header>

      <!-- 2. the journey: where NASA tested, where nobody has -->
      <div class="journey-wrap">
        <JourneyStrip :places="store.places" :place-id="placeId" :status="noMatch ? nothing : statusOf" :material="material" :tests="noMatch ? [] : withOxygen"
                      :closest="inside || noMatch ? null : closest" :two-stop="isNarrow" @pick="id => placeId = id" />
      </div>

      <!-- 3. the evidence, compact -->
      <div v-if="!noMatch" class="evidence">
        <AirLines :tests="withOxygen" :place="place" :material="material" compact
                  :asked="asked && reading && reading.object ? reading.object : ''" />
      </div>

      <button v-if="!stand" type="button" class="more-below" @click="toCloser">Look closer: the gap, the experiments, a real fire, back on Earth, the data</button>

      <!-- 4. the tour controls (top right on a wide screen) -->
      <div class="stage-foot">
        <div class="tour" :class="{ paused: !auto }">
          <button v-if="!stand && asked" class="tour-toggle" @click="backToTour">Back to the tour</button>
          <button v-else-if="!stand" class="tour-toggle" @click="toggle" :aria-label="auto ? 'Pause the tour' : 'Play the tour'">{{ auto ? 'Pause' : 'Play' }}</button>
          <button class="tour-step" type="button" aria-label="Previous example" title="Previous (←)" @click="step(-1)">
            <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path d="M15 5l-7 7 7 7" /></svg>
          </button>
          <span class="muted small tour-count">Story {{ slide + 1 }} of {{ SLIDES.length }}</span>
          <button class="tour-step" type="button" aria-label="Next example" title="Next (→)" @click="step(1)">
            <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path d="M9 5l7 7-7 7" /></svg>
          </button>
          <div class="tour-dots" role="tablist" aria-label="Examples">
            <button v-for="(s, i) in SLIDES" :key="i" role="tab" :aria-selected="i === slide" :class="{ on: i === slide && !asked }"
                    :aria-label="`${s[0]} in ${store.places.find(p => p.id === s[1])?.name}`" @click="pick(i)"></button>
          </div>
          <div class="tour-bar"><span :key="slide + String(auto)" :style="{ animationDuration: STEP_MS + 'ms' }"></span></div>
        </div>
      </div>
    </section>

    <!-- after a question: background from the AI, kept apart from NASA's data -->
    <section v-if="!stand && asked && reading && reading.more" class="more-ai">
      <h2>More about your {{ reading.object }}</h2>
      <p>{{ reading.more }}</p>
      <p class="muted small">General background written by AI. It is not a NASA test result; the verdict above comes only from NASA's data.</p>
    </section>

    <p v-if="!stand && noMatch" class="muted small leftover">The tabs below still show NASA's data for {{ material }}, the last material on screen.
      They are not about your {{ reading?.object || 'object' }}.</p>

    <!-- everything else, one tab at a time -->
    <LookCloser v-if="!stand" :route="route" :material="material" :place="place" :mine="mine" :region="region" :inside="inside"
                :closest="closest" :ranked="ranked" :sources="sources" :materials="materials"
                @place="id => placeId = id" @material="m => material = m" @interact="holdTour" />

    <!-- the ask bar, docked at the bottom (not on the unattended stand) -->
    <form v-if="!stand" class="ask-bar" @submit.prevent="ask">
      <div class="prompts" aria-label="Try a question">
        <span class="muted small">Try:</span>
        <button v-for="p in PROMPTS" :key="p" type="button" class="prompt" :disabled="asking"
                :class="{ on: asking && question === p }" @click="askThis(p)">{{ p }}</button>
      </div>
      <label class="sr" for="ask-input">Ask about something you own</label>
      <input id="ask-input" v-model="question" maxlength="300" autocomplete="off"
             placeholder="Ask about something you own, e.g. would my running shoe burn in a Moon rover?" />
      <button class="cta ask-btn" :disabled="asking || !question.trim()" :aria-busy="asking">
        <span v-if="asking" class="spinner dark" aria-hidden="true"></span>{{ asking ? 'Reading…' : 'Ask' }}</button>
      <span class="muted small ask-note">AI maps your words; NASA supplies the data.</span>
    </form>
  </div>
</template>
