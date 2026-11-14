<script setup>
import { computed } from 'vue'
import { store, experimentById } from '../data.js'
import FireReplay from './FireReplay.vue'
import GapMap from './GapMap.vue'

const props = defineProps({ id: String })
const e = computed(() => experimentById(props.id))
const tests = computed(() => e.value ? store.tests.filter(t => t.experiment === e.value.name) : [])
const materials = computed(() => [...new Set(tests.value.map(t => t.material))].join(', '))
const firstMaterial = computed(() => tests.value.find(t => t.oxygen_pct != null)?.material)
const station = computed(() => store.places.find(p => p.id === 'iss'))
const sum = computed(() => store.summaries?.[props.id])
const SRC = { objective: 'NASA record: goal', approach: 'NASA record: method', hypothesis: 'NASA record: hypothesis',
  earth_benefits: 'NASA record: impacts', our_table: 'our test table' }
const srcLabel = s => SRC[s] || (s.startsWith('paper:') ? 'paper title' : s)

// how the tests differed and what stayed the same, worked out from our table (no AI)
const range = (vals, unit) => { const v = vals.filter(x => x != null); if (!v.length) return null
  const lo = Math.min(...v), hi = Math.max(...v); return lo === hi ? `${lo} ${unit}` : `${lo}–${hi} ${unit}` }
const differ = computed(() => {
  const t = tests.value; if (!t.length) return null
  const uniq = k => [...new Set(t.map(x => x[k]).filter(Boolean))]
  return [
    ['Materials', uniq('material').join(', ')],
    ['Shapes', uniq('shape').join(', ') || 'not recorded'],
    ['Thickness or diameter', range(t.map(x => x.size_mm), 'mm') || 'not recorded'],
    ['Oxygen', range(t.map(x => x.oxygen_pct), '%') || 'not recorded'],
    ['Airflow at the start', range(t.map(x => x.airflow_start_cm_s), 'cm/s') || 'not recorded'],
    ['Flow direction', uniq('flow_direction').join(', ') || 'not recorded'],
    ['Pressure', 'about 1 atm in every test (cabin air; assumed where not recorded)'],
  ]
})

// compare with another investigation
const others = computed(() => store.experiments.filter(x => x.id !== props.id))
function compareWith(ev) { if (ev.target.value) location.hash = `#/compare/${props.id}/${ev.target.value}` }

const sections = [['objective', 'What they wanted to know'], ['approach', 'How they did it'], ['hypothesis', 'What they expected'], ['earth_benefits', 'Why it matters down here']]
</script>

<template>
  <p v-if="!e">No experiment called {{ id }}. <a href="#/">Back home</a></p>
  <article v-else class="experiment">
    <a href="#/" class="muted small">&larr; back to all experiments</a>
    <h1>{{ e.name || e.id }}</h1>
    <p class="subtitle">{{ e.title }}</p>
    <dl class="meta">
      <div><dt>Group</dt><dd><span class="pill" :class="e.pillar">{{ e.pillar }}</span></dd></div>
      <div><dt>Kind</dt><dd>{{ e.kind }}</dd></div>
      <div v-if="e.where"><dt>Where</dt><dd>{{ e.where }}</dd></div>
      <div v-if="e.start"><dt>Dates in NASA's record</dt><dd>{{ e.start }} to {{ e.end }}</dd></div>
      <div v-if="e.nasa_center"><dt>NASA center</dt><dd>{{ e.nasa_center }}</dd></div>
    </dl>
    <img :src="e.image" :alt="e.title" class="photo" @error="$event.target.style.display = 'none'" />

    <section class="found">
      <h2>In short</h2>
      <template v-if="sum">
        <ul class="sourced">
          <li v-for="(l, i) in sum.summary" :key="i">{{ l.text }} <span class="src">{{ srcLabel(l.source) }}</span></li>
        </ul>
        <h3>What they found</h3>
        <ul v-if="sum.findings.length" class="sourced findings">
          <li v-for="(l, i) in sum.findings" :key="i">{{ l.text }} <span class="src">{{ srcLabel(l.source) }}</span></li>
        </ul>
        <p v-else class="muted">NASA's record for this investigation does not state its results; they are in the papers below.</p>
        <p v-if="sum.safety"><b>For fire safety:</b> {{ sum.safety }}</p>
        <p v-if="sum.earth"><b>Back on Earth:</b> {{ sum.earth }}</p>
        <p class="muted small">Drafted by AI only from NASA's record for this investigation; each line names the part of the record it
          comes from, and lines without a real source were removed.</p>
      </template>
      <p v-else class="muted">No summary yet.</p>
    </section>

    <section v-if="differ">
      <h2>How the {{ tests.length }} tests differed</h2>
      <dl class="differ">
        <div v-for="[k, v] in differ" :key="k"><dt>{{ k }}</dt><dd>{{ v }}</dd></div>
      </dl>
      <p class="muted small">From our cleaned copy of NASA's test table. Results are recorded for only some tests.</p>
    </section>

    <section v-if="e.table_columns?.length || e.hardware">
      <h2>What was measured</h2>
      <p v-if="e.hardware"><b>Hardware:</b> {{ e.hardware }}</p>
      <p v-if="e.table_columns?.length"><b>Recorded for each test in NASA's table:</b> {{ e.table_columns.join(', ') }}.</p>
      <p v-else class="muted">NASA's record has no test table for this investigation.</p>
    </section>

    <section>
      <h2>Compare with another investigation</h2>
      <select class="compare-pick" @change="compareWith">
        <option value="">Choose one…</option>
        <option v-for="o in others" :key="o.id" :value="o.id">{{ o.name || o.id }}: {{ o.title }}</option>
      </select>
    </section>

    <section v-if="e.id === 'PSI-98' && store.saffire">
      <h2>The fire, as its heat sensors saw it</h2>
      <FireReplay :data="store.saffire" />
    </section>

    <section v-if="firstMaterial">
      <h2>Every test, by oxygen and air pressure</h2>
      <GapMap :tests="store.tests" :material="firstMaterial" :places="store.places" :place="station" :region="null" />
      <p class="muted small">Blue: {{ firstMaterial }} fires from NASA's tables (test pressure assumed 1 atm). Diamonds: places people live.
        The dashed amber line is a calculated burning-rate limit for 8.2 psi air, from one study under its own assumptions,
        not a safe/unsafe border (<a :href="store.warning?.source" target="_blank">source</a>).</p>
    </section>

    <section v-for="[k, label] in sections" :key="k" v-show="e[k]">
      <h2>{{ label }}</h2>
      <p class="prose">{{ e[k] }}</p>
    </section>

    <section v-if="e.papers.length">
      <h2>Read more ({{ e.papers.length }} papers)</h2>
      <ul class="papers">
        <li v-for="p in e.papers" :key="p.title">
          <a v-if="p.doi" :href="`https://doi.org/${p.doi}`" target="_blank">{{ p.title }}</a><span v-else>{{ p.title }}</span>
          <small class="muted"> {{ p.authors }}</small>
        </li>
      </ul>
    </section>

    <p class="actions">
      <a :href="e.link" target="_blank" class="cta">See it in NASA's database</a>
      <span class="muted small">Behind it: {{ e.raw_files }} raw files, {{ e.raw_size_gb }} GB of video and sensor data.</span>
    </p>
  </article>
</template>
