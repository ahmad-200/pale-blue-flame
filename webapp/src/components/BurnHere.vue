<script setup>
import { ref, computed } from 'vue'
import { store, experimentByName } from '../data.js'
import GapMap from './GapMap.vue'
import JourneyStrip from './JourneyStrip.vue'

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
const fmt = (v, unit, digits) => `${v > 0 ? '+' : v < 0 ? '−' : '±'}${Math.abs(v).toFixed(digits)} ${unit}`
const nearest = computed(() => withOxygen.value.map(t => {
  const dO = place.value.oxygen_pct - t.oxygen_pct, dP = place.value.pressure_atm - t.pressure_atm
  return { ...t, dist: Math.abs(dO) / 10 + Math.abs(dP) / 0.5,
           gap: `this place: ${fmt(dO, 'pts oxygen', 1)}, ${fmt(dP, 'atm', 2)}` }
}).sort((a, b) => a.dist - b.dist).slice(0, 5))
const closest = computed(() => nearest.value[0])
const link = name => `#/experiment/${experimentByName(name)?.id}`
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
    <label class="inline-select"><span class="sr">Place</span>
      <select v-model="placeId">
        <option v-for="p in store.places" :key="p.id" :value="p.id">{{ p.name }}</option>
      </select>
    </label>?
  </h1>
  <p class="intro">Pick a place where people live in space, and something that could catch fire there.
    We will show you every fire NASA has lit with it, and whether any of them happened in that kind of air.</p>

  <section class="journey-section">
    <JourneyStrip :places="store.places" :place-id="placeId" :status="statusOf" :material="material" :tests="withOxygen" @pick="id => placeId = id" />
    <p class="muted small">Every blue dot is a real fire NASA lit with {{ material }}; higher dots had more oxygen. A dashed flame means nobody has lit it there yet.
      Tap a place to choose it.</p>
  </section>

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

  <div class="facts">
    <section>
      <h2>The air there</h2>
      <p class="air">{{ place.oxygen_pct }}% oxygen, {{ place.pressure_psia }} psi ({{ place.pressure_atm }} atm)</p>
      <p class="muted">{{ place.note }} <a :href="place.source" target="_blank">Source</a></p>
      <p class="muted small">PMMA is acrylic, the clear plastic in Plexiglas. SIBAL is a cotton and fiberglass fabric.
        Nomex is the flame-resistant fabric in firefighter suits.</p>
    </section>

    <section>
      <h2>The closest NASA got</h2>
      <p class="muted small">The fires whose air was most like this place, and how far off they were. These are distances, not danger scores.</p>
      <ol class="nearest">
        <li v-for="t in nearest" :key="t.experiment + t.test">
          <a :href="link(t.experiment)">{{ t.experiment }} {{ t.test }}</a>
          <span class="gap-text">{{ t.gap }}</span>
          <small class="muted">{{ t.oxygen_pct }}% oxygen<template v-if="t.airflow_start_cm_s != null">, {{ t.airflow_start_cm_s }} cm/s airflow</template>,
            {{ t.material_text }}<template v-if="t.result">. {{ t.result }}</template></small>
        </li>
        <li v-if="!nearest.length" class="muted">None yet: no fire with this material has its oxygen written down.</li>
      </ol>
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
