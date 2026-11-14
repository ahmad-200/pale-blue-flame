// Loads our own data files once (copied into public/data by scripts/sync-data.mjs).
import { reactive } from 'vue'

export const store = reactive({ ready: false, error: null, experiments: [], meta: {}, places: [], warning: null, tests: [], saffire: null, summaries: {} })

export async function loadData() {
  try {
    const get = f => fetch(`./data/${f}`).then(r => { if (!r.ok) throw new Error(`${f}: ${r.status}`); return r.json() })
    const [exp, places, tests, saffire, sums] = await Promise.all([get('experiments.json'), get('places.json'), get('material_tests.json'), get('saffire1_sensors.json'), get('summaries.json')])
    Object.assign(store, { experiments: exp.experiments, meta: exp.meta, places: places.places, warning: places.warning, tests, saffire, summaries: sums.summaries, summariesMeta: sums.meta, ready: true })
  } catch (e) {
    store.error = String(e)
  }
}

export const experimentById = id => store.experiments.find(e => e.id === id)
export const experimentByName = name => store.experiments.find(e => e.name === name)
