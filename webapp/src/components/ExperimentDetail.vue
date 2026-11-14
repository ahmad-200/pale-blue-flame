<script setup>
// One investigation, opened in place. The short answer first; the long record stays folded until asked for.
import { computed } from 'vue'
import { store, experimentById } from '../data.js'
import ComparePage from './ComparePage.vue'

const props = defineProps({ id: String, compare: String })
const e = computed(() => experimentById(props.id))
const tests = computed(() => e.value ? store.tests.filter(t => t.experiment === e.value.name) : [])
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
const facts = computed(() => [e.value.kind, e.value.where, e.value.start && `${e.value.start} to ${e.value.end}`, e.value.nasa_center].filter(Boolean))
const others = computed(() => store.experiments.filter(x => x.id !== props.id))
function compareWith(ev) { location.hash = ev.target.value ? `#/compare/${props.id}/${ev.target.value}` : `#/experiment/${props.id}` }
const sections = [['objective', 'What they wanted to know'], ['approach', 'How they did it'], ['hypothesis', 'What they expected'], ['earth_benefits', 'Why it matters down here']]
</script>

<template>
  <article v-if="e" id="exp-detail" class="detail">
    <header>
      <div>
        <h3>{{ e.name || e.id }} <span class="pill" :class="e.pillar">{{ e.pillar }}</span></h3>
        <p class="muted">{{ e.title }}</p>
        <p class="muted small">{{ facts.join(' · ') }}</p>
      </div>
      <a href="#/" class="close" aria-label="Close this investigation">Close</a>
    </header>

    <template v-if="sum">
      <ul class="sourced">
        <li v-for="(l, i) in sum.summary.slice(0, 3)" :key="i">{{ l.text }} <span class="src">{{ srcLabel(l.source) }}</span></li>
      </ul>
      <p v-if="sum.findings.length"><b>What they found:</b>
        <template v-for="(l, i) in sum.findings" :key="i"> {{ l.text }} <span class="src">{{ srcLabel(l.source) }}</span></template></p>
      <p v-else class="muted"><b>What they found:</b> NASA's record does not state its results; they are in the papers.</p>
      <p v-if="sum.safety"><b>For fire safety:</b> {{ sum.safety }}</p>
      <p class="muted small">Drafted by AI only from NASA's record; each line names the part it comes from.</p>
    </template>
    <p v-else class="muted">No summary yet.</p>

    <div class="folds">
      <details v-if="differ">
        <summary>How the {{ tests.length }} tests differed</summary>
        <dl class="differ"><div v-for="[k, v] in differ" :key="k"><dt>{{ k }}</dt><dd>{{ v }}</dd></div></dl>
      </details>
      <details v-if="e.table_columns?.length || e.hardware">
        <summary>What was measured</summary>
        <p v-if="e.hardware"><b>Hardware:</b> {{ e.hardware }}</p>
        <p v-if="e.table_columns?.length"><b>Recorded for each test:</b> {{ e.table_columns.join(', ') }}.</p>
      </details>
      <details>
        <summary>NASA's record, in its own words</summary>
        <template v-for="[k, label] in sections" :key="k">
          <template v-if="e[k]"><h4>{{ label }}</h4><p class="prose">{{ e[k] }}</p></template>
        </template>
        <p v-if="sum?.earth"><b>Back on Earth:</b> {{ sum.earth }}</p>
      </details>
      <details v-if="e.papers.length">
        <summary>Papers ({{ e.papers.length }})</summary>
        <ul class="papers">
          <li v-for="p in e.papers" :key="p.title">
            <a v-if="p.doi" :href="`https://doi.org/${p.doi}`" target="_blank">{{ p.title }}</a><span v-else>{{ p.title }}</span>
            <small class="muted"> {{ p.authors }}</small>
          </li>
        </ul>
      </details>
    </div>

    <p class="detail-foot">
      <a :href="e.link" target="_blank">See it in NASA's database</a>
      <span class="muted small">{{ e.raw_files }} raw files, {{ e.raw_size_gb }} GB</span>
      <label class="muted small">Compare with
        <select class="compare-pick" :value="compare || ''" @change="compareWith">
          <option value="">choose one…</option>
          <option v-for="o in others" :key="o.id" :value="o.id">{{ o.name || o.id }}</option>
        </select>
      </label>
    </p>
    <ComparePage v-if="compare" :a="id" :b="compare" />
  </article>
</template>
