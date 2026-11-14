<script setup>
// Two number lines that explain each slide: where NASA's fires were (dots) and where this place is (marker),
// for oxygen and for air pressure. D3 does the scales and the dot layout; CSS animates the moves.
import { computed } from 'vue'
import { scaleLinear } from 'd3-scale'
import { forceSimulation, forceX, forceY, forceCollide } from 'd3-force'

const props = defineProps({ tests: Array, place: Object, material: String, warning: Number, asked: String })
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
const middle = computed(() => range.value ? ox((range.value[0] + range.value[1]) / 2) : null)
</script>

<template>
  <svg :viewBox="`0 ${asked ? -88 : 0} ${W} ${asked ? 288 : 200}`" class="airlines" role="img"
       :aria-label="`Oxygen and air pressure of NASA's ${material} fires compared with ${place.name}`">
    <!-- oxygen -->
    <text x="0" :y="ROW_O + 4" class="row-label">Oxygen</text>
    <line :x1="L" :x2="W - R" :y1="ROW_O + 18" :y2="ROW_O + 18" class="axis" />
    <g v-for="v in oTicks" :key="'o' + v"><text :x="ox(v)" :y="ROW_O + 34" class="tick" text-anchor="middle">{{ v }}%</text></g>
    <line :x1="ox(21)" :x2="ox(21)" :y1="ROW_O - 22" :y2="ROW_O + 18" class="earth-line" />
    <text :x="ox(21)" :y="ROW_O - 26" class="note" text-anchor="middle">Earth air</text>
    <line :x1="ox(warning)" :x2="ox(warning)" :y1="ROW_O - 22" :y2="ROW_O + 18" class="warn-line" />
    <text :x="ox(warning) + 4" :y="ROW_O - 26" class="note warn">burns faster above here (NASA, at 8.2 psi)</text>
    <rect v-if="gapO" :x="ox(gapO.a)" :y="ROW_O - 14" :width="ox(gapO.b) - ox(gapO.a)" height="28" class="gap" />
    <text v-if="gapO" :x="(ox(gapO.a) + ox(gapO.b)) / 2" :y="ROW_O + 4" class="gap-text" text-anchor="middle">never tested</text>
    <circle v-for="d in dots" :key="material + d.t.experiment + d.t.test" :cx="d.x" :cy="d.y" r="3" class="fire">
      <title>{{ d.t.experiment }} {{ d.t.test }}: {{ d.t.oxygen_pct }}% oxygen</title>
    </circle>
    <g class="marker" :style="{ transform: `translateX(${ox(place.oxygen_pct)}px)` }">
      <path :d="`M 0 ${ROW_O - 12} l 7 12 l -7 12 l -7 -12 z`" />
      <text :y="ROW_O + 52" text-anchor="middle">{{ place.oxygen_pct }}%</text>
    </g>

    <!-- what the visitor asked about: their thing would be at the diamond; the nearest NASA material is the dots -->
    <g v-if="asked" class="callouts">
      <g :style="{ transform: `translateX(${ox(place.oxygen_pct)}px)` }" class="callout you">
        <text y="-42" text-anchor="middle">your {{ asked }} would be here</text>
        <path d="M 0 -34 L 0 22 M -6 14 L 0 22 L 6 14" />
      </g>
      <g v-if="middle" class="callout nasa" :style="{ transform: `translateX(${middle}px)` }">
        <text y="-62" text-anchor="middle">closest NASA material: {{ material }}</text>
        <path d="M 0 -34 L 0 22 M -6 14 L 0 22 L 6 14" />
      </g>
    </g>

    <!-- air pressure -->
    <text x="0" :y="ROW_P + 4" class="row-label">Air pressure</text>
    <line :x1="L" :x2="W - R" :y1="ROW_P + 18" :y2="ROW_P + 18" class="axis" />
    <g v-for="v in pTicks" :key="'p' + v"><text :x="px(v)" :y="ROW_P + 34" class="tick" text-anchor="middle">{{ v }} atm</text></g>
    <rect v-if="gapP" :x="px(gapP.a)" :y="ROW_P - 14" :width="px(gapP.b) - px(gapP.a)" height="28" class="gap" />
    <text v-if="gapP" :x="(px(gapP.a) + px(gapP.b)) / 2" :y="ROW_P + 4" class="gap-text" text-anchor="middle">never tested</text>
    <circle v-if="tests.length" :cx="px(1)" :cy="ROW_P" r="9" class="fire-group" />
    <text v-if="tests.length" :x="px(1)" :y="ROW_P - 24" class="note" text-anchor="end">all {{ tests.length }} fires (normal pressure, assumed)</text>
    <g class="marker" :style="{ transform: `translateX(${px(place.pressure_atm)}px)` }">
      <path :d="`M 0 ${ROW_P - 12} l 7 12 l -7 12 l -7 -12 z`" />
      <text :y="ROW_P + 52" text-anchor="middle">{{ place.pressure_atm }} atm</text>
    </g>
  </svg>
</template>
