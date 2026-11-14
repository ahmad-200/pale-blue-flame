<script setup>
import { ref, onMounted } from 'vue'
import { store, loadData } from './data.js'
import HomeView from './components/HomeView.vue'
import BurnHere from './components/BurnHere.vue'
import ExperimentCard from './components/ExperimentCard.vue'
import CosmicBackdrop from './components/CosmicBackdrop.vue'

// Tiny hash router: #/ , #/burn , #/experiment/PSI-25
const stand = new URLSearchParams(location.search).has('stand')
if (stand) document.documentElement.classList.add('stand-mode')
const route = ref(parse())
function parse() {
  const [, page = '', id = ''] = (location.hash || '#/').slice(1).split('/')
  return { page, id }
}
window.addEventListener('hashchange', () => { route.value = parse(); window.scrollTo(0, 0) })
onMounted(loadData)
</script>

<template>
  <CosmicBackdrop :earth="route.page === '' && !stand" />
  <header v-if="!stand" class="top">
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
      <BurnHere v-if="route.page === 'burn' || stand" :stand="stand" />
      <ExperimentCard v-else-if="route.page === 'experiment'" :id="route.id" />
      <HomeView v-else />
    </template>
  </main>
  <footer v-if="!stand" class="muted">
    Data: NASA Physical Sciences Informatics, Combustion Science ({{ store.meta.fetched }}). NASA Space Apps 2026, Flame in Freefall.
    <span class="pbd-note">The sky is a tribute to Voyager 1’s Pale Blue Dot (14 February 1990, about 6 billion km away): Earth less than a pixel across,
      inside a ray of sunlight scattered in the camera. An artistic interpretation, not a star map.
      Every fire on this site was lit to keep people safe a long way from it.</span>
  </footer>
</template>
