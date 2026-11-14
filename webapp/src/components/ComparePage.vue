<script setup>
// Two NASA investigations side by side: what they studied, how, in what air, what they recorded.
import { computed } from 'vue'
import { store, experimentById } from '../data.js'

const props = defineProps({ a: String, b: String })
const pair = computed(() => [props.a, props.b].map(id => experimentById(id)).filter(Boolean))
const rng = (v, u) => { v = v.filter(x => x != null); if (!v.length) return '–'
  const lo = Math.min(...v), hi = Math.max(...v); return lo === hi ? `${lo} ${u}` : `${lo}–${hi} ${u}` }
const row = e => {
  const t = store.tests.filter(x => x.experiment === e.name)
  const s = store.summaries?.[e.id]
  return {
    'Group': e.pillar, 'Kind': e.kind, 'Where': e.where || '–', 'Dates in record': e.start ? `${e.start} to ${e.end}` : '–',
    'In short': s?.summary?.[0]?.text || '–',
    'Findings stated in NASA record': s?.findings?.length ? s.findings.map(f => f.text).join(' ') : 'none stated (see papers)',
    'Material tests in our table': t.length || '–',
    'Materials': [...new Set(t.map(x => x.material))].join(', ') || '–',
    'Oxygen tested': rng(t.map(x => x.oxygen_pct), '%'), 'Airflow tested': rng(t.map(x => x.airflow_start_cm_s), 'cm/s'),
    'Recorded per test': e.table_columns?.length ? e.table_columns.join(', ') : '–',
    'Hardware': e.hardware || '–', 'Papers': e.papers.length,
  }
}
const rows = computed(() => pair.value.map(row))
const keys = computed(() => rows.value.length ? Object.keys(rows.value[0]) : [])
</script>

<template>
  <article class="compare">
    <a href="#/" class="muted small">&larr; back to all experiments</a>
    <h1>Compare two investigations</h1>
    <p v-if="pair.length < 2">Pick two experiments from an experiment page.</p>
    <div v-else class="table-wrap">
      <table>
        <thead><tr><th></th><th v-for="e in pair" :key="e.id"><a :href="`#/experiment/${e.id}`">{{ e.name || e.id }}</a><br /><small class="muted">{{ e.title }}</small></th></tr></thead>
        <tbody>
          <tr v-for="k in keys" :key="k"><th>{{ k }}</th><td v-for="(r, i) in rows" :key="i">{{ r[k] }}</td></tr>
        </tbody>
      </table>
    </div>
    <p class="muted small">Summaries drafted by AI from NASA's records; numbers from our cleaned copy of NASA's test tables.</p>
  </article>
</template>
