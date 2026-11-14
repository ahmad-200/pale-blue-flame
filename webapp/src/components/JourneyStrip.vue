<script setup>
// Earth -> Space Station -> airlock -> Moon base -> rover, drawn as a strip.
// Each place shows whether NASA has ever burned the chosen material in its air.
import { beeswarm } from './useBeeswarm.js'
const props = defineProps({ places: Array, placeId: String, status: Function, material: String, tests: Array, closest: Object, twoStop: Boolean })
const emit = defineEmits(['pick'])

// where each place sits on the strip (x across, y down), and how it is drawn
const SPOTS = {
  iss: { x: 300, y: 120, icon: 'station' },
  airlock: { x: 470, y: 120, icon: 'airlock' },
  moon: { x: 700, y: 175, icon: 'base' },
  rover: { x: 860, y: 205, icon: 'rover' },
  mars: { x: 925, y: 95, icon: 'mars' },
}
// on a phone: only the Station (where NASA tested) and the chosen place, side by side
const TWO = { iss: { x: 300, y: 140 }, other: { x: 700, y: 175 } }
const stops = () => props.places.filter(p => SPOTS[p.id] && (!props.twoStop || p.id === 'iss' || p.id === props.placeId))
  .map(p => ({ ...p, ...SPOTS[p.id], ...(props.twoStop ? TWO[p.id === 'iss' ? 'iss' : 'other'] : {}), st: props.status(p) }))
const flame = (x, y, s = 1) => `M ${x} ${y - 26 * s} C ${x + 14 * s} ${y - 8 * s}, ${x + 12 * s} ${y + 10 * s}, ${x} ${y + 12 * s}
  C ${x - 12 * s} ${y + 10 * s}, ${x - 14 * s} ${y - 8 * s}, ${x} ${y - 26 * s} Z`
// one dot per real fire beside a tested place, higher = more oxygen (D3 force layout, no overlaps)
const dotR = () => ((props.tests || []).length > 50 ? 2.2 : 3.2)   // many fires: smaller dots, same space
const dots = (s) => beeswarm(props.tests || [], s.x - 80, s.y - 6, 90, dotR()).map(n => ({ cx: n.x, cy: n.y, t: n.t }))

// the closest NASA got: a line from that real fire's dot at the Station to the untested place you chose
const bridge = () => {
  const target = stops().find(s => s.id === props.placeId)
  const home = stops().find(s => s.st.tested)
  if (!props.closest || !target || target.st.tested || !home) return null
  const d = dots(home).find(d => d.t.experiment === props.closest.experiment && d.t.test === props.closest.test)
  if (!d) return null
  // bend the line underneath the stops, so it never crosses their names; the label sits on the curve's lowest point
  const tx = target.x, ty = target.y + 8, mx = (d.cx + tx) / 2, my = Math.max(d.cy, ty) + 130
  const midY = 0.25 * d.cy + 0.5 * my + 0.25 * ty
  return { d: `M ${d.cx} ${d.cy} Q ${mx} ${my} ${tx} ${ty}`, x: d.cx, y: d.cy, lx: mx, ly: midY + 18,
           label: `closest NASA got: ${props.closest.oxygen_pct}% oxygen` }
}
</script>

<template>
  <svg viewBox="0 40 960 260" class="journey" role="img" aria-label="Earth, the Space Station, the Moon: where fires were tested">
    <defs>
      <radialGradient id="pale-blue-flame" cx="50%" cy="55%" r="55%">
        <stop offset="0%" stop-color="#ffffff" stop-opacity=".95" />
        <stop offset="35%" stop-color="#cfe6ff" stop-opacity=".9" />
        <stop offset="70%" stop-color="#6fa8ff" stop-opacity=".55" />
        <stop offset="100%" stop-color="#2f6bff" stop-opacity="0" />
      </radialGradient>
    </defs>
    <!-- Earth, a reference only -->
    <circle cx="60" cy="290" r="150" class="earth" />
    <path d="M 0 230 q 40 -30 80 -10 q 30 15 60 -5" class="land" />
    <text x="40" y="70" class="label">Earth</text>
    <text x="40" y="88" class="small">Fires here rise:</text>
    <text x="40" y="104" class="small">hot air goes up</text>

    <!-- the Moon -->
    <circle cx="790" cy="420" r="230" class="moon" />
    <circle cx="700" cy="270" r="14" class="crater" /><circle cx="900" cy="250" r="10" class="crater" />

    <!-- the route -->
    <path d="M 150 150 Q 230 90 300 120 T 470 120 Q 600 110 700 175 T 860 205" class="route" />

    <g v-if="bridge()" class="bridge" :key="placeId + material">
      <path :d="bridge().d" pathLength="1" />
      <circle :cx="bridge().x" :cy="bridge().y" r="6" />
      <text :x="bridge().lx" :y="bridge().ly" text-anchor="middle">{{ bridge().label }}</text>
    </g>

    <g v-for="s in stops()" :key="s.id" class="stop" :class="{ on: s.id === placeId }" @click="emit('pick', s.id)">
      <circle v-for="(d, i) in (s.st.tested ? dots(s) : [])" :key="material + d.t.experiment + d.t.test" :cx="d.cx" :cy="d.cy" :r="dotR()"
              class="fire-dot" :style="{ '--dx': `${s.x - d.cx}px`, '--dy': `${s.y - 6 - d.cy}px`, animationDelay: `${i * 25}ms` }">
        <title>{{ d.t.experiment }} {{ d.t.test }}: {{ d.t.oxygen_pct }}% oxygen</title>
      </circle>
      <g v-if="s.st.tested && tests && tests.length" class="small">
        <text :x="s.x - 80" :y="s.y - 60" class="small" text-anchor="middle">↑ more O₂</text>
        <text :x="s.x - 80" :y="s.y + 56" class="small" text-anchor="middle">less</text>
      </g>
      <!-- the place itself -->
      <g v-if="s.icon === 'station'">
        <rect :x="s.x - 30" :y="s.y + 18" width="60" height="6" class="body" />
        <rect :x="s.x - 44" :y="s.y + 12" width="12" height="18" class="panel-wing" />
        <rect :x="s.x + 32" :y="s.y + 12" width="12" height="18" class="panel-wing" />
      </g>
      <rect v-else-if="s.icon === 'airlock'" :x="s.x - 14" :y="s.y + 14" width="28" height="14" rx="4" class="body" />
      <g v-else-if="s.icon === 'mars'">
        <circle :cx="s.x" :cy="s.y + 22" r="13" class="mars" />
        <path :d="`M ${s.x - 9} ${s.y + 31} a 13 6 0 0 0 18 -2`" class="mars-shade" />
      </g>
      <path v-else-if="s.icon === 'base'" :d="`M ${s.x - 30} ${s.y + 28} a 30 22 0 0 1 60 0 Z`" class="body" />
      <g v-else>
        <rect :x="s.x - 22" :y="s.y + 12" width="44" height="14" rx="5" class="body" />
        <circle :cx="s.x - 13" :cy="s.y + 28" r="5" class="wheel" /><circle :cx="s.x + 13" :cy="s.y + 28" r="5" class="wheel" />
      </g>
      <!-- the fire: solid if tested, a dashed question if not -->
      <circle v-if="s.st.tested" :cx="s.x" :cy="s.y - 6" r="22" class="flame" fill="url(#pale-blue-flame)"
              :style="{ transformOrigin: `${s.x}px ${s.y - 6}px` }" />
      <path v-else :d="flame(s.x, s.y - 4)" class="flame unknown" />
      <text v-if="!s.st.tested" :x="s.x" :y="s.y + 2" class="q" text-anchor="middle">?</text>
      <text :x="s.x" :y="s.y - 46" class="label" text-anchor="middle">{{ s.name.replace(/ \(.*\)/, '') }}</text>
      <text :x="s.x" :y="s.y + 52" class="small" :class="s.st.tested ? 'yes' : 'no'" text-anchor="middle">
        {{ s.st.tested ? `${s.st.count} fires tested` : 'No matching test' }}
      </text>
    </g>
  </svg>
</template>
