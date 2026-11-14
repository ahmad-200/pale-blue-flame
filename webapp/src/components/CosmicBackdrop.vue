<script setup>
// The sky behind every page: a tribute to Voyager 1's Pale Blue Dot, not a star catalog.
// Three layers: the void (near black), a sparse fixed starfield, and one soft band of scattered sunlight
// (in the photo, sunlight scattered inside the camera optics). Positions come from a seeded random
// function, so refreshes, routes and carousel slides never regenerate the sky.
import { onMounted, onBeforeUnmount, ref } from 'vue'

const props = defineProps({ earth: Boolean })   // the tiny pale blue point, on Home only
const W = 1920, H = 1080

function mulberry32(seed) {                      // small deterministic PRNG
  return () => {
    seed |= 0; seed = (seed + 0x6D2B79F5) | 0
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

// the content column (text, charts) sits roughly here at 1920 wide: fewer and fainter stars behind it
const inContent = (x, y) => x > 380 && x < 1540 && y > 90 && y < 1000

const stars = (() => {
  const rnd = mulberry32(1990)                   // the year of the photograph
  const out = []
  // a few loose groupings with empty space around them, plus a thin scatter everywhere
  const groups = Array.from({ length: 6 }, () => ({ x: rnd() * W, y: rnd() * H, r: 90 + rnd() * 160 }))
  let tries = 0
  while (out.length < 150 && tries++ < 4000) {
    let x, y
    if (rnd() < 0.45) {
      const g = groups[Math.floor(rnd() * groups.length)], a = rnd() * Math.PI * 2, d = Math.sqrt(rnd()) * g.r
      x = g.x + Math.cos(a) * d; y = g.y + Math.sin(a) * d
    } else { x = rnd() * W; y = rnd() * H }
    if (x < 0 || x > W || y < 0 || y > H) continue
    const behind = inContent(x, y)
    if (behind && rnd() < 0.55) continue          // fewer behind the content
    const bright = rnd() < 0.07
    out.push({
      x: +x.toFixed(1), y: +y.toFixed(1),
      r: bright ? 1.3 + rnd() * 0.7 : 0.45 + rnd() * 0.55,
      o: (bright ? 0.75 : 0.25 + rnd() * 0.4) * (behind ? 0.6 : 1),
      blue: rnd() < 0.35,                         // white or a desaturated blue-white, never amber
      halo: bright && rnd() < 0.5,
      phone: rnd() < 0.28,                         // about 40 of them stay on a phone
    })
  }
  return out
})()

// pause the slow drift when the tab is hidden (nothing to render for nobody)
const hidden = ref(false)
const onVis = () => { hidden.value = document.hidden }
onMounted(() => document.addEventListener('visibilitychange', onVis))
onBeforeUnmount(() => document.removeEventListener('visibilitychange', onVis))
</script>

<template>
  <div class="cosmos" :class="{ paused: hidden }" aria-hidden="true">
    <svg :viewBox="`0 0 ${W} ${H}`" preserveAspectRatio="xMidYMid slice">
      <defs>
        <!-- the void: almost black, with a trace of depth, not a colored wash -->
        <radialGradient id="void" cx="62%" cy="38%" r="85%">
          <stop offset="0" stop-color="#0A0E16" />
          <stop offset="0.55" stop-color="#06080D" />
          <stop offset="1" stop-color="#040508" />
        </radialGradient>
        <!-- scattered sunlight: soft across its width, fading along its length -->
        <linearGradient id="band-across" x1="0" x2="1" y1="0" y2="0">
          <stop offset="0" stop-color="#CFE3FF" stop-opacity="0" />
          <stop offset="0.5" stop-color="#F2F6FF" stop-opacity="1" />
          <stop offset="1" stop-color="#CFE3FF" stop-opacity="0" />
        </linearGradient>
        <linearGradient id="band-along" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0" stop-color="#fff" stop-opacity="0.12" />
          <stop offset="0.55" stop-color="#fff" stop-opacity="0.6" />
          <stop offset="1" stop-color="#fff" stop-opacity="1" />
        </linearGradient>
        <mask id="band-fade"><rect x="-200" y="-300" width="2400" height="1700" fill="url(#band-along)" /></mask>
        <radialGradient id="halo">
          <stop offset="0" stop-color="#E8F1FF" stop-opacity="0.5" />
          <stop offset="1" stop-color="#E8F1FF" stop-opacity="0" />
        </radialGradient>
        <radialGradient id="earth">
          <stop offset="0" stop-color="#DDF0FF" />
          <stop offset="0.5" stop-color="#9FD3FF" />
          <stop offset="1" stop-color="#9FD3FF" stop-opacity="0" />
        </radialGradient>
      </defs>

      <rect :width="W" :height="H" fill="url(#void)" />

      <g class="drift">
        <!-- the Voyager light: one broad, faint, slightly tilted band, and an even fainter one -->
        <g class="light" mask="url(#band-fade)">
          <rect x="1180" y="-300" width="300" height="1700" fill="url(#band-across)" opacity="0.055"
                transform="rotate(14 1330 540)" />
          <rect x="560" y="-300" width="180" height="1700" fill="url(#band-across)" opacity="0.025"
                transform="rotate(14 650 540)" />
        </g>

        <!-- the stars: fixed relative to one another -->
        <g>
          <template v-for="(s, i) in stars" :key="i">
            <circle v-if="s.halo" :cx="s.x" :cy="s.y" :r="s.r * 5" fill="url(#halo)" :class="{ phone: s.phone }" />
            <circle :cx="s.x" :cy="s.y" :r="s.r" :fill="s.blue ? '#DCE8FF' : '#FFFFFF'" :opacity="s.o" :class="{ phone: s.phone }" />
          </template>
        </g>

        <!-- distant Earth: a tiny pale blue point inside the main band (Home only) -->
        <g v-if="earth">
          <circle cx="1428" cy="150" r="5" fill="url(#earth)" opacity="0.55" />
          <circle cx="1428" cy="150" r="1.6" fill="#CFE8FF" />
        </g>
      </g>
    </svg>
  </div>
</template>

<style scoped>
.cosmos { position: fixed; inset: 0; z-index: -1; pointer-events: none; overflow: hidden; background: #05070B; }
.cosmos svg { width: 100%; height: 100%; display: block; }
/* almost still: the whole sky drifts a few pixels over a minute, and the light breathes very slightly */
.drift { animation: drift 56s ease-in-out infinite alternate; }
.light { animation: breathe 48s ease-in-out infinite alternate; }
.paused .drift, .paused .light { animation-play-state: paused; }
@keyframes drift { from { transform: translate(0, 0) } to { transform: translate(-6px, 3px) } }
@keyframes breathe { from { opacity: 0.85 } to { opacity: 1 } }
@media (max-width: 700px) { circle:not(.phone) { display: none; } }
@media (prefers-reduced-motion: reduce) { .drift, .light { animation: none; } }
</style>
