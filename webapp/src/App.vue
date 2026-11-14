<script setup>
import { ref, onMounted } from 'vue'
import { store, loadData } from './data.js'
import HomeView from './components/HomeView.vue'
import BurnHere from './components/BurnHere.vue'
import ExperimentCard from './components/ExperimentCard.vue'

// Tiny hash router: #/ , #/burn , #/experiment/PSI-25
const route = ref(parse())
function parse() {
  const [, page = '', id = ''] = (location.hash || '#/').slice(1).split('/')
  return { page, id }
}
window.addEventListener('hashchange', () => { route.value = parse(); window.scrollTo(0, 0) })
onMounted(loadData)
</script>

<template>
  <header class="top">
    <a href="#/" class="brand"><span class="brand-flame" aria-hidden="true"></span>Pale Blue Flame</a>
    <nav>
      <a href="#/" :class="{ on: route.page === '' }">Home</a>
      <a href="#/burn" :class="{ on: route.page === 'burn' }">Will it burn here?</a>
    </nav>
  </header>
  <main>
    <p v-if="store.error" class="error">Could not load the data: {{ store.error }}</p>
    <p v-else-if="!store.ready" class="muted">Gathering NASA's fires...</p>
    <template v-else>
      <BurnHere v-if="route.page === 'burn'" />
      <ExperimentCard v-else-if="route.page === 'experiment'" :id="route.id" />
      <HomeView v-else />
    </template>
  </main>
  <footer class="muted">
    Data: NASA Physical Sciences Informatics, Combustion Science ({{ store.meta.fetched }}). NASA Space Apps 2026, Flame in Freefall.
  </footer>
</template>
