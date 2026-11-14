<script setup>
// Two number lines that explain each slide: where NASA's fires were (dots) and where this place is (marker),
// for oxygen and for air pressure. D3 does the scales and the dot layout; CSS animates the moves.
import { computed, ref, watch, onBeforeUnmount } from 'vue'
import { scaleLinear } from 'd3-scale'
import { forceSimulation, forceX, forceY, forceCollide } from 'd3-force'
import { experimentByName } from '../data.js'
const open = t => { const e = experimentByName(t.experiment); if (e) location.hash = `#/experiment/${e.id}` }

const props = defineProps({ tests: Array, place: Object, material: String, warning: Number, asked: String, compact: Boolean })
const W = 900, L = 150, R = 30
const ox = scaleLinear().domain([10, 40]).range([L, W - R])
const px = scaleLinear().domain([0.4, 1.1]).range([L, W - R])
const ROW_O = 46, ROW_P = 146

// one dot per fire, spread up and down a little so none overlap (same layout every time)
const dots = computed(() => {
  const n = props.tests.map((t, i) => ({ t, x: ox(t.oxygen_pct), y: ROW_O + ((i * 7) % 9) - 4 }))
  forceSimulation(n).force('x', forceX(d => ox(d.t.oxygen_pct)).strength(1)).force('y', forceY(ROW_O).strength(0.08))
    .force('c', forceCollide(3.4)).stop().tick(120)
  return n
})
const range = computed(() => props.tests.length
  ? [Math.min(...props.tests.map(t => t.oxygen_pct)), Math.max(...props.tests.map(t => t.oxygen_pct))] : null)
// the untested stretch between the tested range and this place
const gapO = computed(() => {
  if (!range.value) return null
  const p = props.place.oxygen_pct, [lo, hi] = range.value
  if (p > hi + 1) return { a: hi, b: p }
  if (p < lo - 1) return { a: p, b: lo }
  return null
})
const gapP = computed(() => Math.abs(props.place.pressure_atm - 1) > 0.1 ? { a: props.place.pressure_atm, b: 1 } : null)
const oTicks = [10, 15, 20, 25, 30, 35, 40], pTicks = [0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1]
// where the tested fires sit, for the "closest NASA material" arrow
// the chart explains itself one step at a time: 1 where NASA's fires were, 2 where this place is, 3 the stretch nobody tested.
// Each arrow blinks while it is the newest, then holds still. A new material, place or question starts again.
const step = ref(0); let timers = []
function explain() {
  timers.forEach(clearTimeout); step.value = 0
  if (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) { step.value = 3; return }
  timers = [1, 2, 3].map(n => setTimeout(() => { step.value = n }, 400 + (n - 1) * 1300))
}
watch(() => [props.material, props.place?.id, props.asked], explain, { immediate: true })
onBeforeUnmount(() => timers.forEach(clearTimeout))
const placeName = computed(() => props.place.name.replace(/ \(.*\)/, ''))
// keep the two labels inside the chart, whatever they point at
const fit = (px, text) => { const half = text.length * 3.6 + 6; return Math.max(half, Math.min(px, W - half)) - px }
const nasaText = computed(() => props.asked ? `closest NASA material: ${props.material}` : `NASA's ${props.tests.length} ${props.tests.length === 1 ? 'fire' : 'fires'} burned here`)
const youText = computed(() => props.asked ? `your ${props.asked} would be here` : `${placeName.value} air is here`)

// hover, as on a trading chart: a guide line follows the pointer and snaps to the nearest fire
const svg = ref(null), guide = ref(null)
function move(ev) {
  const m = svg.value.getScreenCTM(); if (!m) return
  const px = (ev.clientX - m.e) / m.a, py = (ev.clientY - m.f) / m.d
  if (px < L || px > W - R || py < ROW_O - 30 || py > ROW_O + 40) { guide.value = null; return }
  let best = null, bd = 12
  for (const d of dots.value) { const k = Math.hypot(d.x - px, d.y - py); if (k < bd) { bd = k; best = d } }
  guide.value = best ? { x: best.x, dot: best, text: `${best.t.experiment} ${best.t.test}: ${best.t.oxygen_pct}% oxygen` }
                     : { x: px, text: `${ox.invert(px).toFixed(1)}% oxygen` }
}
const middle = computed(() => range.value ? ox((range.value[0] + range.value[1]) / 2) : null)
</script>

<template>
  <svg :viewBox="`0 -52 ${W} ${52 + (compact ? 134 : 200)}`" class="airlines" role="img" ref="svg"
       @pointermove="move" @pointerleave="guide = null"
       :aria-label="`Oxygen and air pressure of NASA's ${material} fires compared with ${place.name}`">
    <!-- oxygen -->
    <text x="0" :y="ROW_O + 4" class="row-label">Oxygen</text>
    <line :x1="L" :x2="W - R" :y1="ROW_O + 18" :y2="ROW_O + 18" class="axis" />
    <g v-for="v in oTicks" :key="'o' + v"><text :x="ox(v)" :y="ROW_O + 34" class="tick" text-anchor="middle">{{ v }}%</text></g>
    <line :x1="ox(21)" :x2="ox(21)" :y1="ROW_O + 18" :y2="ROW_O + 24" class="earth-line" />
    <g v-if="warning">
      <line :x1="ox(warning)" :x2="ox(warning)" :y1="ROW_O - 22" :y2="ROW_O + 18" class="warn-line" />
      <text :x="ox(warning) + 4" :y="ROW_O - 26" class="note warn">{{ warning }}%: a calculated limit, see the source</text>
    </g>
    <rect v-if="gapO && step >= 3" :x="ox(gapO.a)" :y="ROW_O - 14" :width="ox(gapO.b) - ox(gapO.a)" height="28" class="gap" />
    <text v-if="gapO && step >= 3" :x="(ox(gapO.a) + ox(gapO.b)) / 2" :y="ROW_O + 4" class="gap-text" text-anchor="middle">{{ ox(gapO.b) - ox(gapO.a) < 130 ? 'untested' : 'no matching test' }}</text>
    <circle v-for="d in dots" :key="material + d.t.experiment + d.t.test" :cx="d.x" :cy="d.y" r="3" class="fire" @click="open(d.t)" />
    <g class="marker" :style="{ transform: `translateX(${ox(place.oxygen_pct)}px)` }">
      <path :d="`M 0 ${ROW_O - 12} l 7 12 l -7 12 l -7 -12 z`" />
      <text v-if="!guide" :y="ROW_O + 52" text-anchor="middle">{{ place.oxygen_pct }}%</text>
    </g>

    <g v-if="guide" class="guide">
      <line :x1="guide.x" :x2="guide.x" :y1="ROW_O - 20" :y2="ROW_O + 18" />
      <circle v-if="guide.dot" :cx="guide.dot.x" :cy="guide.dot.y" r="5" />
      <text :x="Math.max(L + 90, Math.min(guide.x, W - R - 90))" :y="ROW_O + 52" text-anchor="middle">{{ guide.text }}</text>
    </g>

    <!-- the arrows: first NASA's fires, then this place; each blinks while it is the newest -->
    <g v-if="tests.length" class="callouts" :class="{ quiet: guide }">
      <g v-if="middle && step >= 1" class="callout nasa" :class="{ now: step === 1 }" :style="{ transform: `translateX(${middle}px)` }">
        <text :x="fit(middle, nasaText)" y="-36" text-anchor="middle">{{ nasaText }}</text>
        <path d="M 0 -28 L 0 22 M -6 14 L 0 22 L 6 14" />
      </g>
      <g v-if="step >= 2" class="callout you" :class="{ now: step >= 2 }" :style="{ transform: `translateX(${ox(place.oxygen_pct)}px)` }">
        <text :x="fit(ox(place.oxygen_pct), youText)" y="-14" text-anchor="middle">{{ youText }}</text>
        <path d="M 0 -6 L 0 22 M -6 14 L 0 22 L 6 14" />
      </g>
    </g>

    <!-- compact: pressure as two values -->
    <text v-if="compact" x="0" :y="ROW_O + 76" class="row-label">Air pressure</text>
    <text v-if="compact" :x="L" :y="ROW_O + 76" class="pressure-pair">
      NASA's tests: 1 atm<tspan class="sep" dx="18">|</tspan><tspan dx="18" :class="{ off: Math.abs(place.pressure_atm - 1) > 0.1 }">{{ placeName }}: {{ place.pressure_atm }} atm</tspan>
    </text>

    <g v-if="!compact">
    <!-- air pressure -->
    <text x="0" :y="ROW_P + 4" class="row-label">Air pressure</text>
    <line :x1="L" :x2="W - R" :y1="ROW_P + 18" :y2="ROW_P + 18" class="axis" />
    <g v-for="v in pTicks" :key="'p' + v"><text :x="px(v)" :y="ROW_P + 34" class="tick" text-anchor="middle">{{ v }} atm</text></g>
    <rect v-if="gapP" :x="px(gapP.a)" :y="ROW_P - 14" :width="px(gapP.b) - px(gapP.a)" height="28" class="gap" />
    <text v-if="gapP" :x="(px(gapP.a) + px(gapP.b)) / 2" :y="ROW_P + 4" class="gap-text" text-anchor="middle">no matching test</text>
    <circle v-if="tests.length" :cx="px(1)" :cy="ROW_P" r="9" class="fire-group" />
    <text v-if="tests.length" :x="px(1)" :y="ROW_P - 24" class="note" text-anchor="end">all {{ tests.length }} fires (normal pressure, assumed)</text>
    <g class="marker" :style="{ transform: `translateX(${px(place.pressure_atm)}px)` }">
      <path :d="`M 0 ${ROW_P - 12} l 7 12 l -7 12 l -7 -12 z`" />
      <text :y="ROW_P + 52" text-anchor="middle">{{ place.pressure_atm }} atm</text>
    </g>
    </g>
  </svg>
</template>
