<script setup>
import { ref, computed } from 'vue'
import { store } from '../data.js'
import FireReplay from './FireReplay.vue'

const PILLARS = [
  { id: 'prevent', name: 'Prevent', text: 'Stop it starting: how things catch fire, and how fast a flame spreads.' },
  { id: 'detect', name: 'Detect', text: 'Notice it early: the smoke and dust a fire leaves in the air.' },
  { id: 'suppress', name: 'Suppress', text: 'Put it out: what makes a flame die.' },
]
const pillar = ref(null)
const count = id => store.experiments.filter(e => e.pillar === id).length
const shown = computed(() => store.experiments.filter(e => !pillar.value || e.pillar === pillar.value))
// investigations whose own record (summarized) says what they mean back on Earth
const earthNotes = computed(() => store.experiments
  .map(e => ({ e, text: store.summaries?.[e.id]?.earth }))
  .filter(x => x.text && ['prevent', 'detect', 'suppress'].includes(x.e.pillar) && x.e.kind.startsWith('flight'))
  .slice(0, 4))
const totalTests = computed(() => store.experiments.reduce((s, e) => s + e.test_table_rows, 0))
</script>

<template>
  <section class="hero">
    <div class="hero-text">
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
      <a href="#/burn" class="cta">Will it burn here?</a>
    </div>
    <div class="hero-flame" aria-hidden="true"><span></span></div>
  </section>

  <section class="replay-section">
    <h2>Watch a real fire</h2>
    <p class="lede">This is not an animation we made up. A sheet of cotton and fiberglass fabric, almost a metre long, was set alight
      on a cargo ship after it left the Space Station, with a gentle 20 cm/s breeze. Four heat sensors recorded it.
      Press play: two sensors warm up first, then the other two, about two minutes later. That is the flame moving.</p>
    <FireReplay :data="store.saffire" auto />
    <p class="muted small">Saffire-I, NASA. Raw sensor values, about one reading every 30 seconds.
      <a href="#/experiment/PSI-98">About this experiment</a></p>
  </section>

  <section class="earth-section">
    <h2>Back on Earth</h2>
    <p class="lede">Fire safety in space has a habit of coming home.</p>
    <ul class="spinoffs">
      <li><b>Water-mist fire extinguishers.</b> Fine-water-mist extinguishers developed for the Space Station have uses on Earth too.
        <span class="muted small">(named in the Space Apps challenge)</span></li>
      <li><b>Smoke detectors.</b> A 1970s detector built for the shuttle could tell smoke from dust.
        <a href="https://spinoff.nasa.gov/node/9407" target="_blank">NASA Spinoff</a></li>
      <li><b>Firefighters' air tanks.</b> Spacesuit technology made firefighters' breathing gear lighter.
        <a href="https://spinoff.nasa.gov/node/9582" target="_blank">NASA Spinoff</a></li>
      <li><b>Protective clothing.</b> Spacesuit materials found their way into firefighters' gear.
        <a href="https://spinoff.nasa.gov/node/9918" target="_blank">NASA Spinoff</a></li>
    </ul>
    <template v-if="earthNotes.length">
      <h3>What the experiments themselves say</h3>
      <ul class="sourced">
        <li v-for="n in earthNotes" :key="n.e.id"><a :href="`#/experiment/${n.e.id}`">{{ n.e.name }}</a>: {{ n.text }}</li>
      </ul>
      <p class="muted small">Drafted by AI from each investigation's NASA record.</p>
    </template>
  </section>

  <section>
    <h2>Three ways to stay alive near a fire</h2>
    <div class="pillars" role="group" aria-label="Filter experiments">
      <button v-for="p in PILLARS" :key="p.id" class="pillar" :class="[p.id, { on: pillar === p.id }]"
              :aria-pressed="pillar === p.id" @click="pillar = pillar === p.id ? null : p.id">
        <strong>{{ p.name }}</strong>
        <span class="count">{{ count(p.id) }} studies</span>
        <span class="muted">{{ p.text }}</span>
      </button>
    </div>
    <p class="muted small">We sorted NASA's experiments this way ourselves (NASA files them differently). Tap one to see only its experiments.</p>

    <ul class="exp-list">
      <li v-for="e in shown" :key="e.id">
        <a :href="`#/experiment/${e.id}`">
          <span class="exp-name">{{ e.name || e.id }}</span>
          <span class="exp-title">{{ e.title }}</span>
          <span class="exp-meta"><span class="pill" :class="e.pillar">{{ e.pillar }}</span><template v-if="e.test_table_rows">{{ e.test_table_rows }} tests</template></span>
        </a>
      </li>
    </ul>
  </section>
</template>
