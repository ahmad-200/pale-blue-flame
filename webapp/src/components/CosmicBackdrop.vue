<script setup>
// The sky behind the page: a spiral galaxy in the pale blue of a flame in microgravity.
// One still picture (drawn by scripts/make-galaxy.py, not a photograph or a star map) that drifts a few pixels
// over a minute. The drift moves the whole layer on the GPU, so nothing is redrawn while it moves.
import { onMounted, onBeforeUnmount, ref } from 'vue'

// pause the drift when the tab is hidden (nothing to render for nobody)
const hidden = ref(false)
const onVis = () => { hidden.value = document.hidden }
onMounted(() => document.addEventListener('visibilitychange', onVis))
onBeforeUnmount(() => document.removeEventListener('visibilitychange', onVis))
</script>

<template>
  <div class="cosmos" aria-hidden="true">
    <div class="sky" :class="{ paused: hidden }"></div>
    <div class="veil"></div>
  </div>
</template>

<style scoped>
.cosmos { position: fixed; inset: 0; z-index: -1; pointer-events: none; overflow: hidden; background: #05070B; }
/* 12px larger than the screen on every side, so the drift never shows an edge */
.sky { position: absolute; inset: -12px; background: #05070B url('/img/galaxy.webp') center / cover no-repeat;
  will-change: transform; animation: drift 56s ease-in-out infinite alternate; }
.sky.paused { animation-play-state: paused; }
/* a soft shade behind the reading column, so text over the bright arms stays easy to read */
.veil { position: absolute; inset: 0;
  background: linear-gradient(90deg, rgba(5, 7, 11, 0) 0%, rgba(5, 7, 11, .38) 22%, rgba(5, 7, 11, .38) 78%, rgba(5, 7, 11, 0) 100%); }
@keyframes drift { from { transform: translate(0, 0) } to { transform: translate(-6px, 3px) } }
@media (prefers-reduced-motion: reduce) { .sky { animation: none; } }
/* phones: the galaxy's centre stays on screen */
@media (max-width: 700px) { .sky { background-position: 66% center; } .veil { background: rgba(5, 7, 11, .3); } }
</style>
