<script setup>
// Everything below the first screen, behind one row of tabs: one idea on screen at a time.
// The tabs follow the material and place chosen above.
import { ref, reactive, computed, watch, nextTick } from 'vue'
import { store, experimentByName } from '../data.js'
import GapMap from './GapMap.vue'
import FireReplay from './FireReplay.vue'
import ExperimentDetail from './ExperimentDetail.vue'

const props = defineProps({ route: Object, material: String, place: Object, mine: Array, region: Object,
  inside: Boolean, closest: Object, ranked: Array, sources: Array, materials: Array })
const emit = defineEmits(['place', 'material', 'interact'])

const TABS = [['gap', 'The gap'], ['experiments', 'Experiments'], ['fire', 'A real fire'], ['earth', 'Back on Earth'], ['data', 'The data']]
const tab = ref('gap')
const placeName = computed(() => props.place.name.replace(/ \(.*\)/, ''))
const link = name => `#/experiment/${experimentByName(name)?.id}`

// --- the gap
const o2All = computed(() => store.tests.filter(t => t.oxygen_pct != null).map(t => t.oxygen_pct))
const o2Span = computed(() => `${Math.min(...o2All.value)}–${Math.max(...o2All.value)}%`)

// --- experiments: three rows (prevent, detect, suppress), the most relevant few in each, the rest one click away
const PILLARS = [
  { id: 'prevent', name: 'Prevent', text: 'How things catch fire and how fast a flame spreads.' },
  { id: 'detect', name: 'Detect', text: 'The smoke and dust a fire leaves in the air.' },
  { id: 'suppress', name: 'Suppress', text: 'What makes a flame die.' },
]
const PER = 3
const offset = reactive({ prevent: 0, detect: 0, suppress: 0 })
const rows = computed(() => PILLARS.map(p => {
  const all = props.ranked.filter(r => r.pillar === p.id)
  const start = all.length > PER ? offset[p.id] % all.length : 0
  const cards = all.length > PER ? Array.from({ length: PER }, (_, i) => all[(start + i) % all.length]) : all
  return { ...p, all, cards }
}))
watch(() => [props.material, props.place?.id], () => { offset.prevent = offset.detect = offset.suppress = 0 })   // new ranking: best first again

// the hash opens an investigation in place: #/experiment/PSI-98 , #/compare/PSI-98/PSI-25
const openId = computed(() => ['experiment', 'compare'].includes(props.route.page) ? props.route.id : null)
const compareId = computed(() => props.route.page === 'compare' ? props.route.id2 : null)
const openRow = computed(() => openId.value && rows.value.find(r => r.all.some(x => x.e.id === openId.value))?.id)
watch(openId, async id => {
  if (!id) return
  tab.value = 'experiments'
  await nextTick()
  document.getElementById('exp-detail')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}, { immediate: true })

// --- back on Earth
const earthNotes = computed(() => store.experiments
  .map(e => ({ e, text: store.summaries?.[e.id]?.earth }))
  .filter(x => x.text && x.e.kind.startsWith('flight')).slice(0, 4))
const totalTests = computed(() => store.experiments.reduce((s, e) => s + e.test_table_rows, 0))

// --- the data: the tests behind the current view, and a CSV of them
const allRows = ref(false)
watch(() => props.material, () => { allRows.value = false })
const COLS = ['experiment', 'test', 'date', 'material', 'shape', 'size_mm', 'oxygen_pct', 'airflow_start_cm_s', 'airflow_min_cm_s', 'flow_direction', 'pressure_atm', 'pressure_assumed', 'result', 'material_text', 'source']
function downloadCsv() {
  const cell = v => v == null ? '' : /[",\n]/.test(String(v)) ? `"${String(v).replace(/"/g, '""')}"` : String(v)
  const text = [COLS.join(','), ...props.mine.map(r => COLS.map(c => cell(r[c])).join(','))].join('\n')
  const a = document.createElement('a')
  a.href = URL.createObjectURL(new Blob([text], { type: 'text/csv' }))
  a.download = `nasa-${props.material.replace(/[^a-z0-9]+/gi, '-').replace(/-$/, '').toLowerCase()}-tests.csv`; a.click()
  setTimeout(() => URL.revokeObjectURL(a.href), 1000)
}
</script>

<template>
  <section class="closer" id="closer" @click="emit('interact')">
    <p class="tabs-label">Look closer:</p>
    <div class="tabs" role="tablist" aria-label="Look closer">
      <button v-for="[id, name] in TABS" :key="id" role="tab" :aria-selected="tab === id" :class="{ on: tab === id }" @click="tab = id">{{ name }}</button>
    </div>

    <!-- THE GAP: every fire against every place, in one picture -->
    <div v-if="tab === 'gap'" class="pane split">
      <div>
        <p class="take">{{ inside ? `NASA burned ${material} in air like the ${placeName}'s.` : `No fire in NASA's data burned in air like the ${placeName}'s.` }}</p>
        <p>Each dot is one real fire. All {{ o2All.length }} burned at about 1 atm, in {{ o2Span }} oxygen.
          The diamonds are where people plan to live.</p>
        <p v-if="closest && !inside"><b>The closest NASA got:</b>{{ ' ' }}
          <a :href="link(closest.experiment)">{{ closest.experiment }} {{ closest.test }}</a>, {{ closest.oxygen_pct }}% oxygen at 1 atm.
          Compared with the {{ placeName }}: {{ closest.gap }}.</p>
        <p class="muted small">Bright dots: {{ material }}. Grey dots: every other material. The dashed amber line is a calculated
          burning-rate limit from one study, not a safe/unsafe border (<a :href="store.warning?.source" target="_blank">source</a>).</p>
      </div>
      <div>
        <GapMap :tests="store.tests" :material="material" :places="store.places" :place="place" :region="region" @pick="id => emit('place', id)" />
        <p class="muted small chart-hint">Move over the chart to read it. Tap a diamond to choose that place.</p>
      </div>
    </div>

    <!-- EXPERIMENTS: ranked for this place, three at a time -->
    <div v-else-if="tab === 'experiments'" class="pane">
      <p class="muted small pane-note">{{ store.experiments.length }} NASA investigations, the most relevant for the {{ placeName }} first:
        what each studied, whether it burned {{ material }}, how close its air came. Our ranking, not NASA's.</p>
      <template v-for="r in rows" :key="r.id">
        <div class="topic">
          <div class="topic-head">
            <h3>{{ r.name }}</h3>
            <p class="muted small">{{ r.all.length }} {{ r.all.length === 1 ? 'study' : 'studies' }}</p>
            <div class="waffle" :class="r.id">
              <a v-for="x in r.all" :key="x.e.id" :href="`#/experiment/${x.e.id}`" :title="x.e.name || x.e.id"
                 :class="{ shown: r.cards.includes(x), open: x.e.id === openId }" :aria-label="x.e.name || x.e.id"></a>
            </div>
            <p class="muted small">{{ r.text }}</p>
          </div>
          <a v-for="x in r.cards" :key="x.e.id" :href="`#/experiment/${x.e.id}`" class="card" :class="{ open: x.e.id === openId }">
            <b>{{ x.e.name || x.e.id }}</b>
            <span class="card-title">{{ x.e.title }}</span>
            <span class="card-why">{{ x.why.slice(0, 2).join('; ') }}.</span>
            <span class="more">Read more</span>
          </a>
          <button v-if="r.all.length > PER" class="next" :aria-label="`Next ${r.name} studies`" title="Show the next three"
                  @click="offset[r.id] += PER">
            <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><path d="M20 12a8 8 0 1 1-2.6-5.9M20 4v5h-5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" /></svg>
          </button>
        </div>
        <ExperimentDetail v-if="openRow === r.id" :id="openId" :compare="compareId" :key="openId" />
      </template>
    </div>

    <!-- A REAL FIRE -->
    <div v-else-if="tab === 'fire'" class="pane">
      <div class="split fire-top">
        <div>
          <p class="take">In space, a flame has nowhere to rise.</p>
          <p>On Earth, hot air goes up and fresh air rushes in underneath. Without gravity nothing goes up: the flame becomes
            a small, dim ball that lives on whatever air drifts past it. NASA has studied this in
            {{ totalTests.toLocaleString() }} recorded tests across {{ store.experiments.length }} investigations.</p>
          <p>Below is one of them, as its four heat sensors saw it: almost a metre of cotton-fiberglass fabric, burning on a cargo ship.
            Two sensors warm first, the other two about two minutes later. That is the flame moving.</p>
        </div>
        <div class="hero-flame" aria-hidden="true"><span></span></div>
      </div>
      <FireReplay :data="store.saffire" auto />
      <p class="muted small">Saffire-I, NASA. Raw sensor values, about one reading every 30 seconds. Ten seconds here stand for sixteen minutes.
        <a href="#/experiment/PSI-98">About this experiment</a></p>
    </div>

    <!-- BACK ON EARTH -->
    <div v-else-if="tab === 'earth'" class="pane">
      <p class="take">Fire safety in space has a habit of coming home.</p>
      <ul class="spinoffs">
        <li><b>Water-mist extinguishers</b><span>Developed for the Space Station, used on Earth too.</span>
          <span class="muted small">Named in the Space Apps challenge</span></li>
        <li><b>Smoke detectors</b><span>A 1970s shuttle detector could tell smoke from dust.</span>
          <a href="https://spinoff.nasa.gov/node/9407" target="_blank">NASA Spinoff</a></li>
        <li><b>Firefighters' air tanks</b><span>Spacesuit technology made breathing gear lighter.</span>
          <a href="https://spinoff.nasa.gov/node/9582" target="_blank">NASA Spinoff</a></li>
        <li><b>Protective clothing</b><span>Spacesuit materials went into firefighters' gear.</span>
          <a href="https://spinoff.nasa.gov/node/9918" target="_blank">NASA Spinoff</a></li>
      </ul>
      <details v-if="earthNotes.length">
        <summary>What the experiments themselves say</summary>
        <ul class="sourced">
          <li v-for="n in earthNotes" :key="n.e.id"><a :href="`#/experiment/${n.e.id}`">{{ n.e.name }}</a>: {{ n.text }}</li>
        </ul>
        <p class="muted small">Drafted by AI from each investigation's NASA record.</p>
      </details>
    </div>

    <!-- THE DATA -->
    <div v-else class="pane modellers">
      <p class="take">What NASA burned</p>
      <div class="bars" role="group" aria-label="Choose a material">
        <button v-for="[m, n] in materials" :key="m" :class="{ on: m === material }" :aria-pressed="m === material" @click="emit('material', m)">
          <span class="bar-name">{{ m }}</span>
          <span class="bar-track"><span class="bar-fill" :style="{ width: `${n / materials[0][1] * 100}%` }"></span></span>
          <span class="bar-n">{{ n }}</span>
        </button>
      </div>
      <p class="muted small">Tests per material in NASA's tables. Choose one to see its tests below, and its verdict above.</p>
      <h3 class="table-title">The {{ mine.length }} {{ material }} tests</h3>
      <p class="muted small">One row per test from NASA's tables, cleaned into the same columns.
        <button class="link" @click="downloadCsv">Download these as CSV</button>
        or <a href="./data/material_tests.csv" download>all {{ store.tests.length }} material tests</a>.</p>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Experiment</th><th>Test</th><th>Shape</th><th>Size (mm)</th><th>Oxygen %</th><th>Airflow cm/s</th><th>Flow</th><th>Result in table</th></tr></thead>
          <tbody>
            <tr v-for="t in (allRows ? mine : mine.slice(0, 6))" :key="t.experiment + t.test">
              <td><a :href="link(t.experiment)">{{ t.experiment }}</a></td><td>{{ t.test }}</td><td>{{ t.shape || '–' }}</td>
              <td>{{ t.size_mm ?? '–' }}</td><td>{{ t.oxygen_pct ?? '–' }}</td>
              <td>{{ t.airflow_start_cm_s ?? '–' }}<template v-if="t.airflow_min_cm_s != null && t.airflow_min_cm_s !== t.airflow_start_cm_s"> → {{ t.airflow_min_cm_s }}</template></td>
              <td>{{ t.flow_direction || '–' }}</td><td>{{ t.result || '–' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <button v-if="mine.length > 6" class="show-more" @click="allRows = !allRows">{{ allRows ? 'Show fewer' : `Show all ${mine.length}` }}</button>
      <details>
        <summary>Sources and limits</summary>
        <ul class="limits">
          <li v-if="sources.length">These fires come from {{ sources.join(', ') }} (NASA Physical Sciences Informatics).</li>
          <li>NASA's tables do not record the pressure of the material tests. We use cabin pressure, about 1 atm, and mark it as assumed.</li>
          <li>“No matching test” applies only to the data we used, not to every fire test ever run.</li>
          <li>{{ placeName }} air is a NASA {{ place.id === 'iss' ? 'cabin value' : 'proposed design atmosphere' }}
            (<a :href="place.source" target="_blank">source</a>). Real missions can differ.</li>
          <li>The drawings are illustrations, not to scale.</li>
        </ul>
      </details>
    </div>
  </section>
</template>
