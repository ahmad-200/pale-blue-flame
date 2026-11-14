<script setup>
// Oxygen (up) against cabin pressure (across). Every material test is a dot; places are diamonds.
// Tap a dot to see which fire it is; tap a diamond to choose that place.
import { computed, ref, watch } from 'vue'
import { scaleLinear } from 'd3-scale'
import { forceSimulation, forceX, forceY, forceCollide } from 'd3-force'
import { experimentByName } from '../data.js'

const props = defineProps({ tests: Array, material: String, places: Array, place: Object, region: Object })
const emit = defineEmits(['pick'])
const W = 640, H = 400, L = 52, R = 24, T = 26, B = 46
const P0 = 0.4, P1 = 1.1, O0 = 10, O1 = 40
const x = scaleLinear().domain([P0, P1]).range([L, W - R])
const y = scaleLinear().domain([O0, O1]).range([H - B, T])
const picked = ref(null)   // the dot someone tapped (works on phones, unlike a hover tooltip)
watch(() => [props.material, props.place?.id], () => { picked.value = null })

// every test sits at about 1 atm: pack the dots side by side at their true oxygen, so none hides another.
// The layout depends only on the tests, so it is computed once and never jumps when the material changes.
const layout = computed(() => {
  const n = props.tests.filter(t => t.oxygen_pct != null).map((t, i) => ({ t, x: x(t.pressure_atm) + ((i * 37) % 21) - 10, y: y(t.oxygen_pct) }))
  forceSimulation(n).force('x', forceX(d => x(d.t.pressure_atm)).strength(0.06)).force('y', forceY(d => y(d.t.oxygen_pct)).strength(1))
    .force('c', forceCollide(4.3)).stop().tick(160)
  return n
})
// the chosen material is drawn last, on top
const dots = computed(() => layout.value.map(d => ({ ...d, mine: d.t.material === props.material })).sort((a, b) => a.mine - b.mine))
const count = computed(() => dots.value.filter(d => d.mine).length)
// places with the same air (Moon base, rover, Mars) share one marker and one label
const groups = computed(() => {
  const m = new Map()
  for (const p of props.places) {
    const k = `${p.pressure_atm}|${p.oxygen_pct}`
    if (!m.has(k)) m.set(k, { key: k, p: p.pressure_atm, o: p.oxygen_pct, names: [], ids: [] })
    m.get(k).names.push(p.name.replace(/ \(.*\)/, '')); m.get(k).ids.push(p.id)
  }
  return [...m.values()].map(g => ({ ...g, on: g.ids.includes(props.place.id), atDots: g.p > 0.9 }))
})
// hover, as on a trading chart: a crosshair follows the pointer, reads both axes, and snaps to the nearest fire or place
const svg = ref(null), cross = ref(null), hover = ref(null)
function locate(ev) {
  const m = svg.value.getScreenCTM(); if (!m) return null
  const px = (ev.clientX - m.e) / m.a, py = (ev.clientY - m.f) / m.d
  if (px < L || px > W - R || py < T || py > H - B) return null
  let dot = null, bd = 12
  for (const d of dots.value) { const k = Math.hypot(d.x - px, d.y - py); if (k < bd || (k === bd && d.mine)) { bd = k; dot = d } }
  const g = dot ? null : groups.value.find(g => Math.hypot(x(g.p) - px, y(g.o) - py) < 16)
  return { px, py, dot, g }
}
function move(ev) {
  const at = locate(ev)
  if (!at) { cross.value = hover.value = null; return }
  hover.value = at.dot
  cross.value = at.dot ? { x: at.dot.x, y: at.dot.y, o: at.dot.t.oxygen_pct, p: at.dot.t.pressure_atm, snap: true }
    : at.g ? { x: x(at.g.p), y: y(at.g.o), o: at.g.o, p: at.g.p, snap: true }
    : { x: at.px, y: at.py, o: y.invert(at.py), p: x.invert(at.px) }
}
function tap(ev) { const at = locate(ev); picked.value = at?.dot && at.dot !== picked.value ? at.dot : null }
const shownDot = computed(() => hover.value || picked.value)
const tipX = computed(() => Math.max(L + 4, Math.min(shownDot.value.x - 115, W - R - 234)))
const tipY = computed(() => shownDot.value.y < T + 64 ? shownDot.value.y + 14 : shownDot.value.y - 56)
const expId = computed(() => experimentByName(shownDot.value?.t.experiment)?.id)
// the gap, said at the chosen place: a short arrow under its diamond (only when that place is untested).
// It points straight up from clear space, so it never crosses another marker.
const gapArrow = computed(() => {
  const r = props.region, p = props.place
  if (!r || !p || (Math.abs(p.pressure_atm - 1) <= 0.1 && p.oxygen_pct >= r.min - 1 && p.oxygen_pct <= r.max + 1)) return null
  const o = Math.max(r.min, Math.min(r.max, p.oxygen_pct)), dO = p.oxygen_pct - o, dP = p.pressure_atm - 1
  const parts = []
  if (Math.abs(dO) >= 0.5) parts.push(`${Math.abs(dO).toFixed(1)} points ${dO > 0 ? 'more' : 'less'} oxygen`)
  if (Math.abs(dP) >= 0.05) parts.push(`${Math.abs(dP).toFixed(2)} atm ${dP < 0 ? 'thinner' : 'denser'}`)
  const text = `untested: ${parts.join(', ')} than any fire`
  const px = x(p.pressure_atm), py = y(p.oxygen_pct), half = text.length * 3.3
  return { d: `M ${px} ${py + 40} L ${px} ${py + 14} M ${px - 6} ${py + 22} L ${px} ${py + 14} L ${px + 6} ${py + 22}`,
           lx: Math.max(L + 6 + half, Math.min(px, W - R - 6 - half)), ly: py + 56, text }
})
const xTicks = [0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1, 1.1]
const yTicks = [10, 15, 20, 25, 30, 35, 40]
</script>

<template>
  <svg :viewBox="`0 0 ${W} ${H}`" class="gapmap" role="img" aria-label="Every NASA material fire by oxygen and cabin pressure, with the places people plan to live"
       ref="svg" @click="tap" @pointermove="move" @pointerleave="cross = hover = null">
    <rect :x="L" :y="T" :width="W - L - R" :height="H - T - B" class="plot" />
    <g v-for="v in xTicks" :key="'x' + v">
      <line :x1="x(v)" :x2="x(v)" :y1="T" :y2="H - B" class="grid" />
      <text :x="x(v)" :y="H - B + 16" class="tick" text-anchor="middle">{{ v }}</text>
    </g>
    <g v-for="v in yTicks" :key="'y' + v">
      <line :x1="L" :x2="W - R" :y1="y(v)" :y2="y(v)" class="grid" />
      <text :x="L - 8" :y="y(v) + 4" class="tick" text-anchor="end">{{ v }}%</text>
    </g>
    <text :x="(L + W - R) / 2" :y="H - 8" class="axis" text-anchor="middle">cabin pressure (atm)</text>
    <text :x="L" :y="T - 10" class="axis">oxygen</text>

    <line :x1="L" :x2="W - R" :y1="y(31.4)" :y2="y(31.4)" class="limit" />
    <text :x="W - R - 6" :y="y(31.4) + 14" class="limit-text" text-anchor="end">31.4%: a calculated limit, one study</text>

    <rect v-if="region" :x="x(1) - 62" :y="y(region.max) - 8" width="124" :height="y(region.min) - y(region.max) + 16" rx="6" class="region" />
    <text v-if="region" :x="x(1) - 68" :y="y((region.min + region.max) / 2) + 4" class="region-text" text-anchor="end">{{ count }} {{ material }} fires</text>

    <circle v-for="d in dots" :key="d.t.experiment + d.t.test" :cx="d.x" :cy="d.y" :r="d.mine ? 4 : 3.2"
            :class="['dot', d.mine ? 'mine' : 'other', { picked: shownDot === d }]" />

    <g v-for="g in groups" :key="g.key" :class="['place', { on: g.on }]" role="button" tabindex="0"
       :aria-label="`Choose ${g.names.join(' or ')}`"
       @click.stop="emit('pick', g.on ? place.id : g.ids[0])" @keydown.enter="emit('pick', g.on ? place.id : g.ids[0])">
      <rect :x="x(g.p) - 16" :y="y(g.o) - 16" width="32" height="32" class="hit" />
      <rect :x="x(g.p) - 7" :y="y(g.o) - 7" width="14" height="14" :transform="`rotate(45 ${x(g.p)} ${y(g.o)})`" class="diamond" />
      <!-- the Station sits among the dots: its name goes above them -->
      <text v-if="g.atDots" :x="x(g.p)" :y="y(23.6)" text-anchor="middle">{{ g.names.join(' / ') }}</text>
      <text v-else :x="x(g.p) + 14" :y="y(g.o) + 4">{{ g.names.join(' / ') }}</text>
    </g>

    <g v-if="gapArrow" class="gap-arrow" :key="material + place.id">
      <path :d="gapArrow.d" />
      <text :x="gapArrow.lx" :y="gapArrow.ly" text-anchor="middle">{{ gapArrow.text }}</text>
    </g>

    <!-- the crosshair and its read-outs on both axes -->
    <g v-if="cross" class="cross" :class="{ snap: cross.snap }">
      <line :x1="L" :x2="W - R" :y1="cross.y" :y2="cross.y" /><line :x1="cross.x" :x2="cross.x" :y1="T" :y2="H - B" />
      <rect :x="L - 48" :y="cross.y - 9" width="46" height="18" rx="3" />
      <text :x="L - 6" :y="cross.y + 4" text-anchor="end">{{ cross.o.toFixed(1) }}%</text>
      <rect :x="cross.x - 30" :y="H - B + 4" width="60" height="18" rx="3" />
      <text :x="cross.x" :y="H - B + 17" text-anchor="middle">{{ cross.p.toFixed(2) }} atm</text>
    </g>

    <g v-if="shownDot" class="pick" @click.stop>
      <rect :x="tipX" :y="tipY" width="230" height="42" rx="6" />
      <text :x="tipX + 10" :y="tipY + 17">{{ shownDot.t.experiment }} {{ shownDot.t.test }}: {{ shownDot.t.oxygen_pct }}% oxygen</text>
      <text :x="tipX + 10" :y="tipY + 33" class="sub">{{ shownDot.t.material }}<template v-if="expId"> · </template>
        <a v-if="expId" :href="`#/experiment/${expId}`">open experiment</a></text>
    </g>
  </svg>
</template>
