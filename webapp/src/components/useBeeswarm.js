// D3 force layout: one dot per fire, pulled up or down by its oxygen %, pushed apart so none overlap.
import { forceSimulation, forceX, forceY, forceCollide } from 'd3-force'
import { scaleLinear } from 'd3-scale'

export function beeswarm(tests, cx, cy, height = 90, r = 3.2) {
  if (!tests.length) return []
  const y = scaleLinear().domain([14, 23]).range([cy + height / 2, cy - height / 2]).clamp(true)
  const nodes = tests.map((t, i) => ({ t, x: cx + ((i * 37) % 21) - 10, y: y(t.oxygen_pct) }))   // fixed start: same picture every time
  forceSimulation(nodes)
    .force('x', forceX(cx).strength(0.05))
    .force('y', forceY(d => y(d.t.oxygen_pct)).strength(0.9))
    .force('c', forceCollide(r + 0.6))
    .stop().tick(160)
  return nodes
}
