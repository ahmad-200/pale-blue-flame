<script setup>
// Earth -> Space Station -> airlock -> Moon base -> rover, drawn as a strip.
// Each place shows whether NASA has ever burned the chosen material in its air.
import { beeswarm } from './useBeeswarm.js'
const props = defineProps({ places: Array, placeId: String, status: Function, material: String, tests: Array, closest: Object, twoStop: Boolean })
const emit = defineEmits(['pick'])

// where each place sits on the strip (x across, y down), and how it is drawn
// Every picture is a real NASA photograph. Distances are real numbers, but the strip is not to scale:
// at this size, with the Moon where it is, Mars would be about half a kilometre off the right edge of the screen.
const SPOTS = {
  iss: { x: 262, y: 130, icon: 'station', size: 78, dist: '400 km up' },
  airlock: { x: 404, y: 130, icon: 'astronaut', size: 78, dist: '400 km up' },
  moon: { x: 570, y: 96, icon: 'moonbase', size: 78, dist: '384,400 km' },
  rover: { x: 688, y: 96, icon: 'rover', size: 78, dist: '384,400 km' },
  mars: { x: 900, y: 150, icon: 'mars', size: 60, dist: 'about 225 million km' },
}
// on a phone: only the Station (where NASA tested) and the chosen place, side by side
const TWO = { iss: { x: 300, y: 130 }, other: { x: 640, y: 96 } }
const stops = () => props.places.filter(p => SPOTS[p.id] && (!props.twoStop || p.id === 'iss' || p.id === props.placeId))
  .map(p => ({ ...p, ...SPOTS[p.id], ...(props.twoStop ? TWO[p.id === 'iss' ? 'iss' : 'other'] : {}), st: props.status(p) }))
const flame = (x, y, s = 1) => `M ${x} ${y - 26 * s} C ${x + 14 * s} ${y - 8 * s}, ${x + 12 * s} ${y + 10 * s}, ${x} ${y + 12 * s}
  C ${x - 12 * s} ${y + 10 * s}, ${x - 14 * s} ${y - 8 * s}, ${x} ${y - 26 * s} Z`
// one dot per real fire beside a tested place, higher = more oxygen (D3 force layout, no overlaps)
const dotR = () => ((props.tests || []).length > 50 ? 2.2 : 3.2)   // many fires: smaller dots, same space
const dots = (s) => beeswarm(props.tests || [], s.x - 86, s.y - 6, 90, dotR()).map(n => ({ cx: n.x, cy: n.y, t: n.t }))

// the closest NASA got: an animated line from that real fire's dot at the Station to the untested place you chose.
// It tries a set of arcs (over the top first, then underneath) and keeps the first one that crosses no name, icon or caption.
const short = n => n.replace(/ \(.*\)/, '')
const bridge = () => {
  const all = stops()
  const target = all.find(s => s.id === props.placeId), home = all.find(s => s.st.tested)
  if (!props.closest || !target || target.st.tested || !home) return null
  const d = dots(home).find(d => d.t.experiment === props.closest.experiment && d.t.test === props.closest.test)
  if (!d) return null
  // everything the line must not touch: [x1, y1, x2, y2]
  const boxes = [[home.x - 116, home.y - 72, home.x - 56, home.y - 56],
    [22, 206, 138, 340], [584, 232, 674, 340]]   // "more O2", "less"
  for (const s of all) {
    const name = short(s.name).length * 4.4 + 4, cap = (s.st.tested ? `${s.st.count} fires tested` : 'No matching test').length * 3.3 + 4
    boxes.push([s.x - name, s.y - 60, s.x + name, s.y - 40], [s.x - cap, s.y + s.size + 10, s.x + cap, s.y + s.size + 40])
    boxes.push(s !== target ? [s.x - s.size / 2 - 2, s.y - 30, s.x + s.size / 2 + 2, s.y + s.size + 8] : [s.x - s.size / 2 + 8, s.y + 14, s.x + s.size / 2, s.y + s.size + 8])
  }
  const h = target.size / 2
  const ends = [[target.x - 25, target.y - 6], [target.x - h - 3, target.y + 6 + h], [target.x - h, target.y + 14], [target.x - 16, target.y - 24], [target.x - h, target.y + h * 2]]
  const mx = (d.cx + target.x) / 2
  let best = null
  search: for (const cy of [-40, -80, -10, -130, 20, -190, 45, 420, 460, 500, 380, 340]) for (const dx of [0, 80, -80, 160, 240, -160, 320]) for (const [ex, ey] of ends) {
    const cx = mx + dx, pts = []
    for (let i = 2; i <= 38; i++) { const t = i / 40, u = 1 - t
      pts.push([u * u * d.cx + 2 * u * t * cx + t * t * ex, u * u * d.cy + 2 * u * t * cy + t * t * ey]) }
    const hits = pts.filter(([px, py]) => py < 10 || py > 334 || boxes.some(b => px > b[0] && px < b[2] && py > b[1] && py < b[3])).length
    if (!best || hits < best.hits) best = { hits, cx, cy, ex, ey, mid: pts[cy < 100 ? 9 : 18] }   // the label: a quarter of the way along an arc over the top, or at the bottom of a dip
    if (!hits) break search
  }
  const over = best.cy < d.cy
  return { d: `M ${d.cx} ${d.cy} Q ${best.cx} ${best.cy} ${best.ex} ${best.ey}`, x: d.cx, y: d.cy,
           lx: Math.max(120, Math.min(best.mid[0] + (over ? 30 : 0), 840)), ly: Math.max(14, Math.min(332, best.mid[1] + (over ? -10 : 18))),
           label: `closest NASA got: ${props.closest.oxygen_pct}% oxygen` }
}
</script>

<template>
  <svg viewBox="0 0 960 340" class="journey" role="img" aria-label="Earth, the Space Station, the Moon: where fires were tested">
    <defs>
      <radialGradient id="pale-blue-flame" cx="50%" cy="55%" r="55%">
        <stop offset="0%" stop-color="#ffffff" stop-opacity=".95" />
        <stop offset="35%" stop-color="#cfe6ff" stop-opacity=".9" />
        <stop offset="70%" stop-color="#6fa8ff" stop-opacity=".55" />
        <stop offset="100%" stop-color="#2f6bff" stop-opacity="0" />
      </radialGradient>
      <clipPath id="earth-clip"><circle cx="80" cy="266" r="68" /></clipPath>
      <clipPath id="moon-clip"><circle cx="629" cy="278" r="58" /></clipPath>
      <radialGradient id="unknown-flame" cx="50%" cy="55%" r="55%">
        <stop offset="0%" stop-color="#F2A65A" stop-opacity=".5" />
        <stop offset="55%" stop-color="#F2A65A" stop-opacity=".22" />
        <stop offset="100%" stop-color="#F2A65A" stop-opacity="0" />
      </radialGradient>
    </defs>
    <!-- Earth, a reference only -->
    <circle cx="80" cy="266" r="68" class="earth" />
    <image :href="'./img/earth.jpg'" x="12" y="198" width="136" height="136" clip-path="url(#earth-clip)" class="photo-earth" />
    <circle cx="80" cy="266" r="68" class="air" />
    <text x="14" y="140" class="label">Earth</text>
    <text x="14" y="156" class="small">Fires here rise:</text>
    <text x="14" y="172" class="small">hot air goes up</text>

    <!-- the Moon -->
    <circle cx="629" cy="278" r="58" class="moon" />
    <image :href="'./img/moon.jpg'" x="569" y="218" width="120" height="120" clip-path="url(#moon-clip)" class="photo-moon" />

    <!-- the route: Earth to the Station, on to the Moon, then the long way to Mars (the line is broken: it is not to scale) -->
    <path d="M 128 214 Q 150 178 172 176 M 306 168 Q 334 176 360 168 M 448 166 Q 496 166 526 144" class="route" />
    <template v-if="!twoStop">
      <path d="M 734 188 L 796 184 M 816 183 L 864 180" class="route" />
      <path d="M 800 175 l -6 18 M 810 174 l -6 18" class="route-break" />
      <text x="804" y="210" class="small" text-anchor="middle">not to scale</text>
    </template>

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
        <text :x="s.x - 86" :y="s.y - 60" class="small" text-anchor="middle">↑ more O₂</text>
      </g>
      <!-- the place itself -->
      <image :href="`./img/${s.icon}.png`" :x="s.x - s.size / 2" :y="s.y + 6" :width="s.size" :height="s.size" />
      <!-- the fire: solid if tested, a dashed question if not -->
      <circle v-if="s.st.tested" :cx="s.x" :cy="s.y - 6" r="22" class="flame" fill="url(#pale-blue-flame)"
              :style="{ transformOrigin: `${s.x}px ${s.y - 6}px` }" />
      <template v-else>
        <circle :cx="s.x" :cy="s.y - 6" r="22" class="flame" fill="url(#unknown-flame)" :style="{ transformOrigin: `${s.x}px ${s.y - 6}px` }" />
        <circle :cx="s.x" :cy="s.y - 6" r="11" class="ring" />
        <text :x="s.x" :y="s.y" class="q" text-anchor="middle">?</text>
      </template>
      <text :x="s.x" :y="s.y - 46" class="label" text-anchor="middle">{{ s.name.replace(/ \(.*\)/, '') }}</text>
      <text :x="s.x" :y="s.y + s.size + 22" class="small" :class="s.st.tested ? 'yes' : 'no'" text-anchor="middle">
        {{ s.st.tested ? `${s.st.count} fires tested` : 'No matching test' }}
      </text>
      <text :x="s.x" :y="s.y + s.size + 36" class="small dist" text-anchor="middle">{{ s.dist }}</text>
    </g>
  </svg>
</template>
