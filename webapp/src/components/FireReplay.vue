<script setup>
// Replays a real NASA fire from its heat-sensor log (Saffire-I). D3 does the maths (scales, smooth lines,
// the timer); Vue draws the SVG. Ten seconds of animation stand for about sixteen minutes of the real fire.
import { ref, computed, onBeforeUnmount } from 'vue'
import { scaleLinear } from 'd3-scale'
import { line, curveMonotoneX } from 'd3-shape'
import { timer } from 'd3-timer'
import { max, range } from 'd3-array'

const props = defineProps({ data: Object })
const W = 640, H = 220, L = 40, R = 16, T = 16, B = 34
const pts = computed(() => props.data.points)
const T_END = computed(() => pts.value[pts.value.length - 1].t)
const x = computed(() => scaleLinear().domain([0, T_END.value]).range([L, W - R]))
const y = computed(() => scaleLinear().domain([-20, max(pts.value, p => Math.max(p.s1, p.s2, p.s3, p.s4)) * 1.1]).range([H - B, T]))
const SENSORS = [{ k: 's2', c: '#F2A65A' }, { k: 's3', c: '#E8C07A' }, { k: 's1', c: '#9FD3FF' }, { k: 's4', c: '#5E9BE0' }]

const now = ref(T_END.value)          // the moment shown; starts on the full picture
const playing = ref(false)
let t = null
function play() {
  t?.stop(); playing.value = true; now.value = 0
  t = timer(ms => { now.value = Math.min(T_END.value, ms / 10000 * T_END.value); if (now.value >= T_END.value) { t.stop(); playing.value = false } })
}
onBeforeUnmount(() => t?.stop())

const shown = computed(() => pts.value.filter(p => p.t <= now.value))
const path = k => line().x(p => x.value(p.t)).y(p => y.value(p[k])).curve(curveMonotoneX)(shown.value) || ''
// how hot each sensor is right now, 0..1, for the glowing dots
const heat = k => {
  const p = shown.value[shown.value.length - 1]; if (!p) return 0
  return Math.max(0, Math.min(1, (p[k] + 15) / 150))
}
const minutes = computed(() => `${Math.floor(now.value / 60)}:${String(Math.floor(now.value % 60)).padStart(2, '0')}`)
const ticks = computed(() => range(0, T_END.value + 1, 120))   // a mark every 2 minutes
</script>

<template>
  <div class="replay">
    <div class="sensors">
      <div v-for="(s, i) in SENSORS" :key="s.k" class="sensor" :style="{ '--c': s.c, '--h': heat(s.k) }">
        <span class="bulb"></span><small>sensor {{ s.k.slice(1) }}</small>
      </div>
      <button class="cta" @click="play" :disabled="playing">{{ playing ? `Burning… ${minutes}` : 'Replay the fire' }}</button>
    </div>
    <svg :viewBox="`0 0 ${W} ${H}`" class="replay-chart" role="img" aria-label="Heat sensor readings during a real NASA fire">
      <g v-for="v in ticks" :key="v">
        <line :x1="x(v)" :x2="x(v)" :y1="T" :y2="H - B" class="grid" />
        <text :x="x(v)" :y="H - B + 16" class="tick" text-anchor="middle">{{ Math.round(v / 60) }} min</text>
      </g>
      <path v-for="s in SENSORS" :key="s.k" :d="path(s.k)" :stroke="s.c" class="trace" />
      <line v-if="playing" :x1="x(now)" :x2="x(now)" :y1="T" :y2="H - B" class="cursor" />
      <text :x="L" :y="T + 4" class="tick">heat at the sensor</text>
    </svg>
  </div>
</template>
