<script setup>
// Replays a real NASA fire from its heat-sensor log (Saffire-I). D3 does the maths (scales, smooth lines,
// the timer); Vue draws the SVG. Ten seconds of animation stand for about sixteen minutes of the real fire.
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { scaleLinear } from 'd3-scale'
import { line, curveMonotoneX } from 'd3-shape'
import { timer } from 'd3-timer'
import { max, range } from 'd3-array'

const props = defineProps({ data: Object, auto: Boolean })
const W = 640, H = 220, L = 40, R = 16, T = 16, B = 34
const pts = computed(() => props.data.points)
const T_END = computed(() => pts.value[pts.value.length - 1].t)
const x = computed(() => scaleLinear().domain([0, T_END.value]).range([L, W - R]))
const y = computed(() => scaleLinear().domain([-20, max(pts.value, p => Math.max(p.s1, p.s2, p.s3, p.s4)) * 1.1]).range([H - B, T]))
const SENSORS = [{ k: 's2', c: '#F2A65A' }, { k: 's3', c: '#E8C07A' }, { k: 's1', c: '#9FD3FF' }, { k: 's4', c: '#5E9BE0' }]

const now = ref(T_END.value)          // the moment shown; starts on the full picture
const playing = ref(false)
const chart = ref(null), hover = ref(null)
let t = null
let again = null
let lastFrame = -1
// the auto loop runs only while the chart is on screen and the tab is visible: an endless loop nobody sees
// kept the CPU busy re-drawing four curves 60 times a second
const root = ref(null)
const onScreen = ref(false)
const canLoop = () => props.auto && onScreen.value && !document.hidden && !hover.value   // never restart under a reader's pointer
function play() {
  t?.stop(); clearTimeout(again); playing.value = true; now.value = 0; lastFrame = -1; hover.value = null
  t = timer(ms => {
    const f = Math.floor(ms / 40)            // 25 updates a second is smooth for a line chart
    if (f === lastFrame) return
    lastFrame = f
    now.value = Math.min(T_END.value, ms / 10000 * T_END.value)
    if (now.value >= T_END.value) {
      t.stop(); playing.value = false
      if (canLoop()) again = setTimeout(play, 4000)   // hold the finished chart, then burn again
    }
  })
}
function halt() { t?.stop(); clearTimeout(again); playing.value = false; now.value = T_END.value }
function onVisibility() { if (document.hidden) { if (props.auto) halt() } else if (canLoop() && !playing.value) play() }
let io = null
onMounted(() => {
  if (!props.auto) return
  io = new IntersectionObserver(([e]) => {
    onScreen.value = e.isIntersecting
    if (canLoop() && !playing.value) play()
    else if (!e.isIntersecting) halt()
  })
  io.observe(root.value)
  document.addEventListener('visibilitychange', onVisibility)
})
onBeforeUnmount(() => { t?.stop(); clearTimeout(again); io?.disconnect(); document.removeEventListener('visibilitychange', onVisibility) })

const shown = computed(() => pts.value.filter(p => p.t <= now.value))
// hover, as on a trading chart: a crosshair snaps to the nearest reading and shows all four sensors
function move(ev) {
  const m = chart.value.getScreenCTM(); if (!m || !shown.value.length) return
  const px = (ev.clientX - m.e) / m.a
  if (px < L - 6 || px > W - R + 6) { hover.value = null; return }
  const t = x.value.invert(px)
  hover.value = shown.value.reduce((a, p) => Math.abs(p.t - t) < Math.abs(a.t - t) ? p : a)
}
function leave() { hover.value = null; if (canLoop() && !playing.value) { clearTimeout(again); again = setTimeout(play, 4000) } }
const clock = t => `${Math.floor(t / 60)}:${String(Math.floor(t % 60)).padStart(2, '0')}`
const tipX = computed(() => { const hx = x.value(hover.value.t); return hx > W - R - 150 ? hx - 138 : hx + 10 })
const path = k => line().x(p => x.value(p.t)).y(p => y.value(p[k])).curve(curveMonotoneX)(shown.value) || ''
// how hot each sensor is right now, 0..1, for the glowing dots
const heat = k => {
  const p = hover.value || shown.value[shown.value.length - 1]; if (!p) return 0
  return Math.max(0, Math.min(1, (p[k] + 15) / 150))
}
const minutes = computed(() => `${Math.floor(now.value / 60)}:${String(Math.floor(now.value % 60)).padStart(2, '0')}`)
const ticks = computed(() => range(0, T_END.value + 1, 120))   // a mark every 2 minutes
</script>

<template>
  <div class="replay" ref="root">
    <div class="sensors">
      <div v-for="(s, i) in SENSORS" :key="s.k" class="sensor" :style="{ '--c': s.c, '--h': heat(s.k) }">
        <span class="bulb"></span><small>sensor {{ s.k.slice(1) }}</small>
      </div>
      <button class="cta" @click="play" :disabled="playing">{{ playing ? `Burning… ${minutes}` : 'Replay the fire' }}</button>
    </div>
    <svg :viewBox="`0 0 ${W} ${H}`" class="replay-chart" role="img" aria-label="Heat sensor readings during a real NASA fire"
         ref="chart" @pointermove="move" @pointerleave="leave">
      <g v-for="v in ticks" :key="v">
        <line :x1="x(v)" :x2="x(v)" :y1="T" :y2="H - B" class="grid" />
        <text :x="x(v)" :y="H - B + 16" class="tick" text-anchor="middle">{{ Math.round(v / 60) }} min</text>
      </g>
      <path v-for="s in SENSORS" :key="s.k" :d="path(s.k)" :stroke="s.c" class="trace" />
      <line v-if="playing" :x1="x(now)" :x2="x(now)" :y1="T" :y2="H - B" class="cursor" />
      <text :x="L" :y="T + 4" class="tick">heat at the sensor</text>
      <g v-if="hover && hover.t <= now" class="cross">
        <line :x1="x(hover.t)" :x2="x(hover.t)" :y1="T" :y2="H - B" />
        <circle v-for="s in SENSORS" :key="s.k" :cx="x(hover.t)" :cy="y(hover[s.k])" r="4" :fill="s.c" />
        <rect :x="tipX" :y="T + 10" width="128" height="88" rx="6" />
        <text :x="tipX + 10" :y="T + 27" class="when">{{ clock(hover.t) }} into the burn</text>
        <g v-for="(s, i) in SENSORS" :key="s.k">
          <circle :cx="tipX + 14" :cy="T + 40 + i * 14" r="3.5" :fill="s.c" />
          <text :x="tipX + 24" :y="T + 44 + i * 14">sensor {{ s.k.slice(1) }}</text>
          <text :x="tipX + 118" :y="T + 44 + i * 14" text-anchor="end" class="val">{{ hover[s.k].toFixed(1) }}</text>
        </g>
      </g>
    </svg>
  </div>
</template>
