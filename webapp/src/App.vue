<script setup>
import { ref, onMounted } from 'vue'
import { store, loadData } from './data.js'
import BurnHere from './components/BurnHere.vue'
import CosmicBackdrop from './components/CosmicBackdrop.vue'

// One page. The hash only opens things inside it: #/experiment/PSI-25 , #/compare/PSI-25/PSI-98
const stand = new URLSearchParams(location.search).has('stand')
if (stand) document.documentElement.classList.add('stand-mode')
const route = ref(parse())
function parse() {
  const [, page = '', id = '', id2 = ''] = (location.hash || '#/').slice(1).split('/')
  return { page, id, id2 }
}
window.addEventListener('hashchange', () => { route.value = parse() })
onMounted(loadData)
</script>

<template>
  <CosmicBackdrop :earth="!stand" />
  <header v-if="!stand" class="top">
    <a href="#/" class="brand"><span class="brand-flame" aria-hidden="true"></span>Pale Blue Flame</a>
    <span class="tagline muted small">In space, a flame has nowhere to rise. NASA lit real fires to learn what burns.</span>
  </header>
  <main>
    <p v-if="store.error" class="error">Could not load the data: {{ store.error }}</p>
    <p v-else-if="!store.ready" class="muted">Gathering NASA's fires...</p>
    <BurnHere v-else :stand="stand" :route="route" />
  </main>
  <footer v-if="!stand" class="muted">
    Data: NASA Physical Sciences Informatics, Combustion Science ({{ store.meta.fetched }}). NASA Space Apps 2026, Flame in Freefall.
    <span class="pbd-note">The sky is a tribute to Voyager 1’s Pale Blue Dot photograph: a drawing, not a star map.
      Photos: NASA (Earth, Apollo 17; Moon, Galileo; Mars, Viking; the Station from Atlantis, STS-135; the McCandless spacewalk, STS-41B;
      the Lunar Electric Rover prototype; an Apollo 14 lunar module standing in for a Moon base, which nobody has built yet).</span>
  </footer>
</template>
