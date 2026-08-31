<template>
  <div class="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-2xl space-y-4">
    <div class="flex items-center justify-between border-b border-slate-800 pb-3">
      <div class="flex items-center space-x-2">
        <span class="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
        <h3 class="text-sm font-bold text-slate-200">二维可行域与最优顶点</h3>
      </div>
      <div v-if="optimalPoint" class="text-xs font-mono text-emerald-400">
        Optimal: ({{ optimalPoint.rawX }}, {{ optimalPoint.rawY }}) | z* = {{ finalResult.objective_value }}
      </div>
    </div>

    <!-- SVG 画布区域 -->
    <div class="relative w-full aspect-[4/3] max-h-[460px] bg-slate-950 rounded-lg border border-slate-800/80 overflow-hidden flex items-center justify-center">
      <svg :viewBox="`0 0 ${width} ${height}`" class="w-full h-full select-none">
        <!-- 栅格背景 -->
        <defs>
          <pattern id="grid" width="30" height="30" patternUnits="userSpaceOnUse">
            <path d="M 30 0 L 0 0 0 30" fill="none" stroke="rgba(51, 65, 85, 0.3)" stroke-width="1" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" />

        <!-- 坐标轴 -->
        <line :x1="pad" :y1="height - pad" :x2="width - pad" :y2="height - pad" stroke="#64748b" stroke-width="1.5" />
        <line :x1="pad" :y1="height - pad" :x2="pad" :y2="pad" stroke="#64748b" stroke-width="1.5" />
        <text :x="width - pad" :y="height - pad + 20" fill="#94a3b8" font-size="11" font-family="monospace">x1</text>
        <text :x="pad - 20" :y="pad" fill="#94a3b8" font-size="11" font-family="monospace">x2</text>

        <!-- 可行域多边形 (凸包填充) -->
        <polygon 
          v-if="polygonPointsStr" 
          :points="polygonPointsStr" 
          fill="rgba(16, 185, 129, 0.18)" 
          stroke="#10b981" 
          stroke-width="2" 
          stroke-dasharray="4 2"
        />

        <!-- 边界线 -->
        <g v-for="(line, idx) in finalResult.boundary_lines" :key="'line-' + idx">
          <line 
            v-if="calcLineCoords(line)" 
            :x1="calcLineCoords(line)!.x1" 
            :y1="calcLineCoords(line)!.y1" 
            :x2="calcLineCoords(line)!.x2" 
            :y2="calcLineCoords(line)!.y2" 
            stroke="#475569" 
            stroke-width="1"
            stroke-dasharray="2 2"
          />
        </g>

        <!-- 极点散点与最优解高亮 -->
        <g v-for="(pt, idx) in parsedVertices" :key="'pt-' + idx">
          <circle 
            :cx="mapX(pt.x)" 
            :cy="mapY(pt.y)" 
            :r="pt.isOptimal ? 6 : 3.5" 
            :fill="pt.isOptimal ? '#f59e0b' : '#38bdf8'" 
            :stroke="pt.isOptimal ? '#fff' : '#0284c7'" 
            stroke-width="1.5"
          />
          <text 
            :x="mapX(pt.x) + 8" 
            :y="mapY(pt.y) - 6" 
            fill="#cbd5e1" 
            font-size="10" 
            font-family="monospace"
          >
            ({{ pt.rawX }}, {{ pt.rawY }})
          </text>
        </g>
      </svg>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  finalResult: {
    objective_value: string
    solution: Record<string, string>
    feasible_vertices: Array<{ x1: string; x2: string; z: string }>
    boundary_lines: Array<{ a1: string; a2: string; d: string; type: string }>
  }
}>()

const width = 560
const height = 400
const pad = 45

function parseFrac(val: string): number {
  if (!val) return 0
  if (val.includes('/')) {
    const [n, d] = val.split('/').map(Number)
    return d !== 0 ? n / d : 0
  }
  return Number(val)
}

const parsedVertices = computed(() => {
  const list = props.finalResult.feasible_vertices || []
  const sol = props.finalResult.solution || {}
  const optX = parseFrac(sol.x1)
  const optY = parseFrac(sol.x2)

  return list.map((v) => {
    const x = parseFrac(v.x1)
    const y = parseFrac(v.x2)
    const isOptimal = Math.abs(x - optX) < 1e-4 && Math.abs(y - optY) < 1e-4
    return { x, y, rawX: v.x1, rawY: v.x2, z: v.z, isOptimal }
  })
})

const bounds = computed(() => {
  const xs = parsedVertices.value.map((p) => p.x)
  const ys = parsedVertices.value.map((p) => p.y)
  const maxX = Math.max(...xs, 5) * 1.2
  const maxY = Math.max(...ys, 5) * 1.2
  return { maxX, maxY }
})

function mapX(x: number) { return pad + (x / bounds.value.maxX) * (width - 2 * pad) }
function mapY(y: number) { return height - pad - (y / bounds.value.maxY) * (height - 2 * pad) }

const polygonPointsStr = computed(() => {
  const pts = [...parsedVertices.value]
  if (pts.length < 3) return ''
  const cx = pts.reduce((acc, p) => acc + p.x, 0) / pts.length
  const cy = pts.reduce((acc, p) => acc + p.y, 0) / pts.length
  pts.sort((a, b) => Math.atan2(a.y - cy, a.x - cx) - Math.atan2(b.y - cy, b.x - cx))
  return pts.map((p) => `${mapX(p.x)},${mapY(p.y)}`).join(' ')
})

const optimalPoint = computed(() => parsedVertices.value.find((p) => p.isOptimal))

function calcLineCoords(l: { a1: string; a2: string; d: string }) {
  const a1 = parseFrac(l.a1)
  const a2 = parseFrac(l.a2)
  const d = parseFrac(l.d)
  if (a1 === 0 && a2 === 0) return null
  if (a1 === 0) {
    const y = d / a2
    return { x1: mapX(0), y1: mapY(y), x2: mapX(bounds.value.maxX), y2: mapY(y) }
  }
  if (a2 === 0) {
    const x = d / a1
    return { x1: mapX(x), y1: mapY(0), x2: mapX(x), y2: mapY(bounds.value.maxY) }
  }
  const yAt0 = d / a2
  const xAt0 = d / a1
  return { x1: mapX(0), y1: mapY(yAt0), x2: mapX(xAt0), y2: mapY(0) }
}
</script>