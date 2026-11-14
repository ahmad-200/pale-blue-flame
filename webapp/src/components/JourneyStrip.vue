<script setup>
// Earth -> Space Station -> airlock -> Moon base -> rover, drawn as a strip.
// Each place shows whether NASA has ever burned the chosen material in its air.
const props = defineProps({ places: Array, placeId: String, status: Function, material: String })
const emit = defineEmits(['pick'])

// where each place sits on the strip (x across, y down), and how it is drawn
const SPOTS = {
  iss: { x: 300, y: 120, icon: 'station' },
  airlock: { x: 470, y: 120, icon: 'airlock' },
  moon: { x: 700, y: 175, icon: 'base' },
  rover: { x: 860, y: 205, icon: 'rover' },
}
const stops = () => props.places.filter(p => SPOTS[p.id]).map(p => ({ ...p, ...SPOTS[p.id], st: props.status(p) }))
const flame = (x, y, s = 1) => `M ${x} ${y - 26 * s} C ${x + 14 * s} ${y - 8 * s}, ${x + 12 * s} ${y + 10 * s}, ${x} ${y + 12 * s}
  C ${x - 12 * s} ${y + 10 * s}, ${x - 14 * s} ${y - 8 * s}, ${x} ${y - 26 * s} Z`
// a few dots around a tested place: one per fire, at most 40, placed in a ring
const dots = (s) => Array.from({ length: Math.min(s.st.count, 40) }, (_, i) => {
  const a = i * 2.4, r = 44 + (i % 5) * 5
  return { cx: s.x + Math.cos(a) * r, cy: s.y - 10 + Math.sin(a) * r * 0.55 }
})
</script>

<template>
  <svg viewBox="0 0 960 300" class="journey" role="img" aria-label="Earth, the Space Station, the Moon: where fires were tested">
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

    <g v-for="s in stops()" :key="s.id" class="stop" :class="{ on: s.id === placeId }" @click="emit('pick', s.id)">
      <circle v-for="(d, i) in (s.st.tested ? dots(s) : [])" :key="i" :cx="d.cx" :cy="d.cy" r="3" class="fire-dot" />
      <circle :cx="s.x" :cy="s.y" r="34" class="halo" />
      <!-- the place itself -->
      <g v-if="s.icon === 'station'">
        <rect :x="s.x - 30" :y="s.y + 18" width="60" height="6" class="body" />
        <rect :x="s.x - 44" :y="s.y + 12" width="12" height="18" class="panel-wing" />
        <rect :x="s.x + 32" :y="s.y + 12" width="12" height="18" class="panel-wing" />
      </g>
      <rect v-else-if="s.icon === 'airlock'" :x="s.x - 14" :y="s.y + 14" width="28" height="14" rx="4" class="body" />
      <path v-else-if="s.icon === 'base'" :d="`M ${s.x - 30} ${s.y + 28} a 30 22 0 0 1 60 0 Z`" class="body" />
      <g v-else>
        <rect :x="s.x - 22" :y="s.y + 12" width="44" height="14" rx="5" class="body" />
        <circle :cx="s.x - 13" :cy="s.y + 28" r="5" class="wheel" /><circle :cx="s.x + 13" :cy="s.y + 28" r="5" class="wheel" />
      </g>
      <!-- the fire: solid if tested, a dashed question if not -->
      <path :d="flame(s.x, s.y - 4)" :class="s.st.tested ? 'flame' : 'flame unknown'" />
      <text v-if="!s.st.tested" :x="s.x" :y="s.y + 2" class="q" text-anchor="middle">?</text>
      <text :x="s.x" :y="s.y - 46" class="label" text-anchor="middle">{{ s.name.replace(/ \(.*\)/, '') }}</text>
      <text :x="s.x" :y="s.y + 52" class="small" :class="s.st.tested ? 'yes' : 'no'" text-anchor="middle">
        {{ s.st.tested ? `${s.st.count} fires tested` : 'Never tested' }}
      </text>
    </g>
  </svg>
</template>
