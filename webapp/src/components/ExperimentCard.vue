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
    <dl class="meta">
      <div><dt>Group</dt><dd><span class="pill" :class="e.pillar">{{ e.pillar }}</span></dd></div>
      <div><dt>Kind</dt><dd>{{ e.kind }}</dd></div>
      <div v-if="e.where"><dt>Where</dt><dd>{{ e.where }}</dd></div>
      <div v-if="e.start"><dt>Dates in NASA's record</dt><dd>{{ e.start }} to {{ e.end }}</dd></div>
      <div v-if="e.nasa_center"><dt>NASA center</dt><dd>{{ e.nasa_center }}</dd></div>
    </dl>
    <img :src="e.image" :alt="e.title" class="photo" @error="$event.target.style.display = 'none'" />

    <section class="found">
      <h2>What they found</h2>
      <p class="muted">We haven't written this part yet. Truth is, the results live mostly in the papers below, not in
        NASA's tables, and we want to read them before we sum them up.</p>
      <p v-if="tests.length">What we do have: <b>{{ tests.length }}</b> fires from this experiment in our table ({{ materials }}).</p>
    </section>

    <section v-if="e.id === 'PSI-98' && store.saffire">
      <h2>The fire, as its heat sensors saw it</h2>
      <FireReplay :data="store.saffire" />
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
