<script setup>
import { ref, computed } from 'vue'
import { store } from '../data.js'

const PILLARS = [
  { id: 'prevent', name: 'Prevent', text: 'How materials catch fire and how flames spread' },
  { id: 'detect', name: 'Detect', text: 'Smoke and dust: how a fire can be noticed' },
  { id: 'suppress', name: 'Suppress', text: 'How flames go out' },
]
const pillar = ref(null)
const count = id => store.experiments.filter(e => e.pillar === id).length
const shown = computed(() => store.experiments.filter(e => !pillar.value || e.pillar === pillar.value))
const totalTests = computed(() => store.experiments.reduce((s, e) => s + e.test_table_rows, 0))
</script>

<template>
  <section class="hero">
    <h1>Fire behaves differently in space.</h1>
    <p>
      On Earth, hot gas rises and pulls fresh air into a flame. Without gravity nothing rises, so a flame
      lives on whatever air drifts past it. NASA has recorded {{ totalTests.toLocaleString() }} tests in
      {{ store.experiments.length }} investigations to learn how. Fires have cost lives before: Apollo 1
      on the launch pad, and the 1997 fire aboard Mir.
    </p>
    <a href="#/burn" class="cta">Will it burn here? &rarr;</a>
  </section>

  <section>
    <h2>The experiments, by what they protect against</h2>
    <div class="pillars">
      <button v-for="p in PILLARS" :key="p.id" class="pillar" :class="[p.id, { on: pillar === p.id }]"
              @click="pillar = pillar === p.id ? null : p.id">
        <strong>{{ p.name }}</strong>
        <span>{{ count(p.id) }} studies</span>
        <small>{{ p.text }}</small>
      </button>
    </div>
    <p class="muted small">{{ store.meta.pillar_rule }}</p>

    <div class="grid">
      <a v-for="e in shown" :key="e.id" :href="`#/experiment/${e.id}`" class="card-link">
        <span class="tag" :class="e.pillar">{{ e.pillar }}</span>
        <strong>{{ e.name || e.id }}</strong>
        <span>{{ e.title }}</span>
        <small class="muted">{{ e.kind }}<template v-if="e.test_table_rows"> · {{ e.test_table_rows }} test rows</template></small>
      </a>
    </div>
  </section>
</template>
