<script setup>
import { ref, computed } from 'vue'
import { store } from '../data.js'

const PILLARS = [
  { id: 'prevent', name: 'Prevent', text: 'Stop it starting: how things catch fire, and how fast a flame spreads.' },
  { id: 'detect', name: 'Detect', text: 'Notice it early: the smoke and dust a fire leaves in the air.' },
  { id: 'suppress', name: 'Suppress', text: 'Put it out: what makes a flame die.' },
]
const pillar = ref(null)
const count = id => store.experiments.filter(e => e.pillar === id).length
const shown = computed(() => store.experiments.filter(e => !pillar.value || e.pillar === pillar.value))
const totalTests = computed(() => store.experiments.reduce((s, e) => s + e.test_table_rows, 0))
</script>

<template>
  <section class="hero">
    <h1>In space, a flame has nowhere to rise.</h1>
    <p>
      On Earth, a flame breathes through gravity: hot air goes up, and fresh air rushes in underneath.
      Take gravity away and nothing goes up. The flame becomes a small, dim ball that lives on whatever
      air drifts past it. Turn on a fan, and it keeps going.
    </p>
    <p>
      NASA has spent years studying this, one small fire at a time: {{ totalTests.toLocaleString() }} recorded
      tests across {{ store.experiments.length }} investigations. Fires have cost lives before (Apollo 1 on the
      launch pad, Mir in 1997), so this is not an academic question.
    </p>
    <p>We built one question on top of all of it.</p>
    <a href="#/burn" class="cta">Will it burn here? &rarr;</a>
  </section>

  <section>
    <h2>Three ways to stay alive near a fire</h2>
    <div class="pillars">
      <button v-for="p in PILLARS" :key="p.id" class="pillar" :class="[p.id, { on: pillar === p.id }]"
              @click="pillar = pillar === p.id ? null : p.id">
        <strong>{{ p.name }}</strong>
        <span>{{ count(p.id) }} studies</span>
        <small>{{ p.text }}</small>
      </button>
    </div>
    <p class="muted small">We sorted NASA's experiments this way ourselves (NASA files them differently). Tap one to see only its experiments.</p>

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
