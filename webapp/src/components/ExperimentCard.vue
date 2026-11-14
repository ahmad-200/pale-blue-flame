<script setup>
import { computed } from 'vue'
import { store, experimentById } from '../data.js'
import FireReplay from './FireReplay.vue'

const props = defineProps({ id: String })
const e = computed(() => experimentById(props.id))
const tests = computed(() => e.value ? store.tests.filter(t => t.experiment === e.value.name) : [])
const materials = computed(() => [...new Set(tests.value.map(t => t.material))].join(', '))
const sections = [['objective', 'What they wanted to know'], ['approach', 'How they did it'], ['hypothesis', 'What they expected'], ['earth_benefits', 'Why it matters down here']]
</script>

<template>
  <p v-if="!e">No experiment called {{ id }}. <a href="#/">Back home</a></p>
  <article v-else class="experiment">
    <a href="#/" class="muted small">&larr; back to all experiments</a>
    <h1>{{ e.name || e.id }}</h1>
    <p class="subtitle">{{ e.title }}</p>
    <p class="facts">
      <span class="tag" :class="e.pillar">{{ e.pillar }}</span>
      {{ e.kind }}<template v-if="e.where"> · {{ e.where }}</template>
      <template v-if="e.start"> · {{ e.start }} to {{ e.end }}</template>
      <template v-if="e.nasa_center"> · {{ e.nasa_center }}</template>
    </p>
    <img :src="e.image" :alt="e.title" class="photo" @error="$event.target.style.display = 'none'" />

    <section class="panel found">
      <h3>What they found</h3>
      <p class="muted">We haven't written this part yet. Truth is, the results live mostly in the papers below, not in
        NASA's tables, and we want to read them before we sum them up.</p>
      <p v-if="tests.length">What we do have: <b>{{ tests.length }}</b> fires from this experiment in our table ({{ materials }}).</p>
    </section>

    <section v-if="e.id === 'PSI-98' && store.saffire" class="panel">
      <h3>The fire, as its heat sensors saw it</h3>
      <FireReplay :data="store.saffire" />
    </section>

    <section v-for="[k, label] in sections" :key="k" v-show="e[k]">
      <h3>{{ label }}</h3>
      <p class="prose">{{ e[k] }}</p>
    </section>

    <section v-if="e.papers.length">
      <h3>Read more ({{ e.papers.length }} papers)</h3>
      <ul class="papers">
        <li v-for="p in e.papers" :key="p.title">
          <a v-if="p.doi" :href="`https://doi.org/${p.doi}`" target="_blank">{{ p.title }}</a><span v-else>{{ p.title }}</span>
          <small class="muted"> {{ p.authors }}</small>
        </li>
      </ul>
    </section>

    <p class="actions">
      <a :href="e.link" target="_blank" class="cta small">See it in NASA's database</a>
      <span class="muted small">Behind it: {{ e.raw_files }} raw files, {{ e.raw_size_gb }} GB of video and sensor data.</span>
    </p>
  </article>
</template>
