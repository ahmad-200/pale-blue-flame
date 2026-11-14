<script setup>
import { ref, computed } from 'vue'
import { store, experimentByName } from '../data.js'
import GapMap from './GapMap.vue'

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
const inside = computed(() => region.value && Math.abs(place.value.pressure_atm - 1) <= 0.1
  && place.value.oxygen_pct >= region.value.min - 1 && place.value.oxygen_pct <= region.value.max + 1)

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
  <h1>Will it burn here?</h1>
  <div class="burn">
    <aside class="panel">
      <h3>You choose</h3>
      <label>Place
        <select v-model="placeId">
          <option v-for="p in store.places" :key="p.id" :value="p.id">{{ p.name }}</option>
        </select>
      </label>
      <p class="air">{{ place.oxygen_pct }}% oxygen · {{ place.pressure_psia }} psi ({{ place.pressure_atm }} atm)</p>
      <p class="muted small">{{ place.note }} <a :href="place.source" target="_blank">Source</a></p>
      <label>Material
        <select v-model="material">
          <option v-for="[m, n] in materials" :key="m" :value="m">{{ m }} ({{ n }} tests)</option>
        </select>
      </label>
    </aside>

    <section class="panel map">
      <h3>Gap map: where fire was tested</h3>
      <GapMap :tests="store.tests" :material="material" :places="store.places" :place="place" :region="region" />
      <p class="muted small">Dots are NASA test fires (yours in colour). Test pressure is assumed 1 atm: the tables do not record it.</p>
    </section>
  </div>

  <div class="burn-bottom">
    <section class="panel" :class="inside ? 'ok' : 'gap'">
      <h3>The honest answer</h3>
      <template v-if="!withOxygen.length">
        <p>NASA burned {{ mine.length }} samples of <b>{{ material }}</b>, but their tables do not record the oxygen.
           We cannot place them on the map yet.</p>
      </template>
      <template v-else-if="inside">
        <p><b>Tested.</b> {{ withOxygen.length }} tests burned {{ material }} in air like this
           ({{ region.min }}–{{ region.max }}% oxygen, about 1 atm).</p>
      </template>
      <template v-else>
        <p><b>Nobody has burned {{ material }} in this air.</b></p>
        <p>The nearest test: {{ closest.oxygen_pct }}% oxygen at {{ closest.pressure_atm }} atm
           ({{ closest.experiment }} {{ closest.test }}). This place has {{ place.oxygen_pct }}% at {{ place.pressure_atm }} atm.</p>
        <p class="muted small">"Not tested" does not mean safe.</p>
      </template>
      <p v-if="place.oxygen_pct > 31.4 && place.pressure_atm < 0.6" class="warn small">
        {{ store.warning.text }} <a :href="store.warning.source" target="_blank">Source</a>
      </p>
    </section>

    <section class="panel">
      <h3>Nearest tests</h3>
      <p class="muted small">The tests whose air was closest to this place, and how far off they are.</p>
      <ol class="nearest">
        <li v-for="t in nearest" :key="t.experiment + t.test">
          <a :href="link(t.experiment)">{{ t.experiment }} {{ t.test }}</a>
          <span>{{ t.gap }}</span>
          <small class="muted">{{ t.oxygen_pct }}% O2<template v-if="t.airflow_start_cm_s != null"> · {{ t.airflow_start_cm_s }} cm/s</template>
            · {{ t.material_text }}<template v-if="t.result"> · {{ t.result }}</template></small>
        </li>
        <li v-if="!nearest.length" class="muted">No test with recorded oxygen for this material.</li>
      </ol>
    </section>
  </div>
</template>
