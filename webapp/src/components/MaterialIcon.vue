<script setup>
// A small drawn picture of each material, so people can imagine what burned. Illustrations, not photos of NASA's samples.
defineProps({ material: String })
</script>

<template>
  <svg viewBox="0 0 64 64" class="material-icon" role="img" :aria-label="`Illustration of ${material}`">
    <!-- SIBAL: cotton woven on fiberglass, a fabric swatch -->
    <g v-if="material.startsWith('SIBAL')">
      <path d="M8 14 L56 10 L54 52 L10 54 Z" fill="#E9DFC9" />
      <g stroke="#C9BB9C" stroke-width="2">
        <path v-for="i in 7" :key="'h' + i" :d="`M9 ${14 + i * 5.5} L55 ${10 + i * 5.5}`" />
        <path v-for="i in 7" :key="'v' + i" :d="`M${9 + i * 6} 14 L${10 + i * 6} 54`" />
      </g>
      <path d="M54 52 l-8 2 l6 -9 z" fill="#F7F1E3" />
    </g>
    <!-- acrylic: a clear rod and a clear sheet -->
    <g v-else-if="material.startsWith('PMMA (acrylic)') || material === 'PMMA (assumed)'">
      <rect x="10" y="12" width="30" height="40" rx="2" fill="rgba(200,230,255,.25)" stroke="#BFE3FF" stroke-width="2" />
      <path d="M14 16 L22 16 L14 30 Z" fill="rgba(255,255,255,.55)" />
      <rect x="44" y="8" width="10" height="48" rx="5" fill="rgba(200,230,255,.3)" stroke="#BFE3FF" stroke-width="2" />
      <rect x="47" y="12" width="2.5" height="38" rx="1.2" fill="rgba(255,255,255,.6)" />
    </g>
    <!-- acrylic and Nomex together -->
    <g v-else-if="material === 'PMMA + Nomex'">
      <path d="M6 18 L40 14 L38 54 L8 56 Z" fill="#D9B95B" />
      <rect x="30" y="8" width="26" height="36" rx="2" fill="rgba(200,230,255,.3)" stroke="#BFE3FF" stroke-width="2" />
    </g>
    <!-- Nomex: firefighter-suit fabric, folded, with a stitch line -->
    <g v-else-if="material === 'Nomex'">
      <path d="M8 16 L52 12 L56 50 L12 54 Z" fill="#D9B95B" />
      <path d="M8 16 L52 12 L46 24 L10 28 Z" fill="#C4A24A" />
      <path d="M14 44 L50 40" stroke="#8A6F2C" stroke-width="1.5" stroke-dasharray="3 2" />
    </g>
    <!-- silicone: a soft, bendy rubber strip -->
    <g v-else-if="material === 'silicone'">
      <path d="M6 40 C 18 20, 30 52, 42 30 S 58 22, 58 22 L 58 32 C 52 32, 50 42, 42 42 C 30 62, 18 30, 6 50 Z" fill="#E36F5C" />
      <path d="M10 41 C 20 26, 30 54, 41 34" stroke="rgba(255,255,255,.35)" stroke-width="2" fill="none" />
    </g>
    <!-- candle wax -->
    <g v-else-if="material === 'candle wax'">
      <rect x="22" y="24" width="20" height="32" rx="3" fill="#F3EBD8" />
      <path d="M22 28 q 4 6 0 10" fill="#E3D8BF" />
      <path d="M32 24 L32 18" stroke="#3A3A3A" stroke-width="2" />
      <path d="M32 6 C 37 12, 36 18, 32 19 C 28 18, 27 12, 32 6 Z" fill="#9FD3FF" />
    </g>
    <!-- Ultem: a tough amber plastic sheet -->
    <g v-else-if="material === 'Ultem'">
      <rect x="10" y="12" width="44" height="40" rx="3" fill="rgba(214,138,40,.55)" stroke="#D68A28" stroke-width="2" />
      <path d="M14 16 L26 16 L14 32 Z" fill="rgba(255,255,255,.35)" />
    </g>
    <!-- unknown -->
    <g v-else>
      <rect x="12" y="12" width="40" height="40" rx="6" fill="none" stroke="#8C95A8" stroke-width="2" stroke-dasharray="4 3" />
      <text x="32" y="40" text-anchor="middle" font-size="22" fill="#8C95A8">?</text>
    </g>
  </svg>
</template>
