<script setup>
// Oxygen (up) against cabin pressure (across). Every material test is a dot; places are diamonds.
import { computed } from 'vue'

const props = defineProps({ tests: Array, material: String, places: Array, place: Object, region: Object })
const W = 640, H = 380, L = 56, R = 20, T = 20, B = 48
const P0 = 0.4, P1 = 1.1, O0 = 10, O1 = 40
const x = p => L + (p - P0) / (P1 - P0) * (W - L - R)
const y = o => T + (O1 - o) / (O1 - O0) * (H - T - B)

// all tests sit at ~1 atm: spread them a little sideways so they do not hide each other
const dots = computed(() => props.tests.filter(t => t.oxygen_pct != null).map((t, i) => ({
  cx: x(t.pressure_atm) - 30 + ((i * 37) % 60), cy: y(t.oxygen_pct), mine: t.material === props.material, t,
})))
// places with the same air (Moon base and rover) share one marker and one label
const groups = computed(() => {
  const m = new Map()
  for (const p of props.places) {
    const k = `${p.pressure_atm}|${p.oxygen_pct}`
    if (!m.has(k)) m.set(k, { key: k, p: p.pressure_atm, o: p.oxygen_pct, names: [], ids: [] })
    m.get(k).names.push(p.name); m.get(k).ids.push(p.id)
  }
  return [...m.values()]
})
const xTicks = [0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1]
const yTicks = [10, 15, 20, 25, 30, 35, 40]
</script>

<template>
  <svg :viewBox="`0 0 ${W} ${H}`" class="gapmap" role="img" aria-label="Gap map: oxygen against pressure">
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
    <text :x="14" :y="(T + H - B) / 2" class="axis" text-anchor="middle" :transform="`rotate(-90 14 ${(T + H - B) / 2})`">oxygen</text>

    <line :x1="L" :x2="W - R" :y1="y(31.4)" :y2="y(31.4)" class="limit" />
    <text :x="L + 6" :y="y(31.4) - 6" class="limit-text">NASA: above 31.4% burns faster at 8.2 psi</text>

    <rect v-if="region" :x="x(0.9)" :y="y(region.max + 1)" :width="x(1.1) - x(0.9)"
          :height="y(region.min - 1) - y(region.max + 1)" class="region" />

    <circle v-for="(d, i) in dots" :key="i" :cx="d.cx" :cy="d.cy" :r="d.mine ? 5 : 3.5"
            :class="d.mine ? 'dot mine' : 'dot other'">
      <title>{{ d.t.experiment }} {{ d.t.test }}: {{ d.t.material }}, {{ d.t.oxygen_pct }}% oxygen</title>
    </circle>

    <g v-for="g in groups" :key="g.key" :class="g.ids.includes(place.id) ? 'place on' : 'place'">
      <rect :x="x(g.p) - 7" :y="y(g.o) - 7" width="14" height="14" :transform="`rotate(45 ${x(g.p)} ${y(g.o)})`" />
      <text :x="x(g.p) + 12" :y="y(g.o) - 8">{{ g.names.join(' / ') }}</text>
    </g>
  </svg>
</template>
