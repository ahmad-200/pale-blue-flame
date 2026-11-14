<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { store, experimentByName } from '../data.js'
import GapMap from './GapMap.vue'
import JourneyStrip from './JourneyStrip.vue'
import MaterialIcon from './MaterialIcon.vue'

const placeId = ref('moon')
const material = ref('SIBAL (cotton-fiberglass)')
const place = computed(() => store.places.find(p => p.id === placeId.value))

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
const link = name => `#/experiment/${experimentByName(name)?.id}`

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
const STEP_MS = 3000, IDLE_MS = 20000
const slide = ref(0), auto = ref(true)
let tick = null, idle = null
function show(i) {
  slide.value = (i + SLIDES.length) % SLIDES.length
  ;[material.value, placeId.value] = SLIDES[slide.value]
}
function start() { clearInterval(tick); auto.value = true; tick = setInterval(() => show(slide.value + 1), STEP_MS) }
function stop() { clearInterval(tick); auto.value = false }
// someone touched it: pause, and come back to the tour after a quiet spell
function touched() { stop(); clearTimeout(idle); idle = setTimeout(start, IDLE_MS) }
// a change that does not match the current slide came from a person (Vue runs this after the change, so compare, don't flag)
watch([material, placeId], ([m, p]) => { const [sm, sp] = SLIDES[slide.value]; if (m !== sm || p !== sp) touched() })
function pick(i) { show(i); touched() }
function toggle() { clearTimeout(idle); auto.value ? stop() : start() }
onMounted(() => { show(0); start() })
onBeforeUnmount(() => { clearInterval(tick); clearTimeout(idle) })
</script>

<template>
  <h1 class="burn-q">
    Would
    <label class="inline-select"><span class="sr">Material</span>
      <select v-model="material">
        <option v-for="[m, n] in materials" :key="m" :value="m">{{ m }}</option>
      </select>
    </label>
    burn in
    <span class="nowrap"><label class="inline-select"><span class="sr">Place</span>
      <select v-model="placeId">
        <option v-for="p in store.places" :key="p.id" :value="p.id">{{ p.name }}</option>
      </select>
    </label>?</span>
  </h1>
  <Transition name="swap" mode="out-in">
    <div class="material-line" :key="material">
      <MaterialIcon :material="material" />
      <p><b>{{ material }}</b><br />{{ what }} <span class="muted small">(illustration)</span></p>
    </div>
  </Transition>

  <div class="tour" :class="{ paused: !auto }">
    <button class="tour-toggle" @click="toggle" :aria-label="auto ? 'Pause the tour' : 'Play the tour'">{{ auto ? 'Pause' : 'Play' }}</button>
    <div class="tour-dots" role="tablist" aria-label="Examples">
      <button v-for="(s, i) in SLIDES" :key="i" role="tab" :aria-selected="i === slide" :class="{ on: i === slide }"
              :aria-label="`${s[0]} in ${store.places.find(p => p.id === s[1])?.name}`" @click="pick(i)"></button>
    </div>
    <div class="tour-bar"><span :key="slide + String(auto)" :style="{ animationDuration: STEP_MS + 'ms' }"></span></div>
  </div>
  <p class="intro">Pick a place where people live in space, and something that could catch fire there.
    We will show you every fire NASA has lit with it, and whether any of them happened in that kind of air.</p>

  <section class="journey-section">
    <JourneyStrip :places="store.places" :place-id="placeId" :status="statusOf" :material="material" :tests="withOxygen" :closest="inside ? null : closest" @pick="id => placeId = id" />
    <p class="muted small">Every blue dot is a real fire NASA lit with {{ material }}; higher dots had more oxygen. A dashed flame means nobody has lit it there yet.
      Tap a place to choose it.</p>
  </section>

  <div class="answer-row">
  <section class="answer" :class="inside ? 'ok' : 'gap'" aria-live="polite">
    <Transition name="swap" mode="out-in">
      <div :key="placeId + material">
        <template v-if="!withOxygen.length">
          <p class="verdict">We can't place these fires yet.</p>
          <p>NASA burned {{ mine.length }} samples of <b>{{ material }}</b>, but never wrote down the oxygen in those tests.
             So we can't put them on the map yet, which is a bit frustrating.</p>
        </template>
        <template v-else-if="inside">
          <p class="verdict">Yes, NASA has tested this.</p>
          <p>{{ withOxygen.length }} fires burned {{ material }} in air like this ({{ region.min }}–{{ region.max }}% oxygen,
             at normal pressure). What happened in them is on each experiment's page.</p>
        </template>
        <template v-else>
          <p class="verdict">We don't know, because nobody has tried.</p>
          <p>NASA has never burned {{ material }} in air like this. The closest they came was {{ closest.oxygen_pct }}% oxygen
             at normal pressure ({{ closest.experiment }} {{ closest.test }}). This place has {{ place.oxygen_pct }}% oxygen, in thinner air.</p>
          <p class="muted">Not tested is not the same as safe. It only means we are guessing.</p>
        </template>
        <p v-if="place.oxygen_pct > 31.4 && place.pressure_atm < 0.6" class="warn">
          {{ store.warning.text }} <a :href="store.warning.source" target="_blank">Source</a>
        </p>
      </div>
    </Transition>
  </section>

  <section class="closest" aria-live="polite">
    <h2>The closest NASA got</h2>
    <Transition name="swap" mode="out-in">
      <ol class="nearest" :key="placeId + material">
        <li v-for="t in nearest.slice(0, 3)" :key="t.experiment + t.test">
          <a :href="link(t.experiment)">{{ t.experiment }} {{ t.test }}</a>
          <span class="gap-text">{{ t.gap }}</span>
          <small class="muted">{{ t.oxygen_pct }}% oxygen<template v-if="t.airflow_start_cm_s != null">, {{ t.airflow_start_cm_s }} cm/s airflow</template></small>
        </li>
        <li v-if="!nearest.length" class="muted">None yet: no fire with this material has its oxygen written down.</li>
      </ol>
    </Transition>
    <p class="muted small">Distances, not danger scores.</p>
  </section>
  </div>

  <div class="facts">
    <section>
      <h2>The air there</h2>
      <p class="air">{{ place.oxygen_pct }}% oxygen, {{ place.pressure_psia }} psi ({{ place.pressure_atm }} atm)</p>
      <p class="muted">{{ place.note }} <a :href="place.source" target="_blank">Source</a></p>
    </section>


  </div>

  <details class="map">
    <summary>Show the detailed chart (oxygen and air pressure)</summary>
    <GapMap :tests="store.tests" :material="material" :places="store.places" :place="place" :region="region" />
    <p class="muted small">Each dot is one fire NASA lit (yours are blue). The diamonds are places people live.
      Higher up means more oxygen; further left means thinner air. The empty space is what nobody has tested yet.
      (We assume the tests ran at normal cabin pressure, because NASA's tables don't say.)</p>
  </details>
</template>
