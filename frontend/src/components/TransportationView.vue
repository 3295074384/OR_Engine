<template>
  <div class="space-y-4">
    <!-- 步骤与闭回路提示 -->
    <div class="bg-slate-900/90 border border-slate-800 rounded-xl p-4 flex items-center justify-between shadow-lg">
      <div class="flex items-center space-x-3">
        <span class="text-xs text-slate-400">运输推演步骤:</span>
        <span class="font-mono font-bold text-indigo-400 text-sm">Step {{ stepIndex + 1 }} / {{ iterations.length }}</span>
        <span class="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
          {{ currentSnapshot.type === 'transport_cost_table' ? 'Vogel 初始分配' : 'MODI 位势检验' }}
        </span>
      </div>

      <div class="flex items-center space-x-2">
        <button @click="stepIndex = Math.max(0, stepIndex - 1)" :disabled="stepIndex === 0" class="w-7 h-7 rounded bg-slate-800 text-xs disabled:opacity-30 flex items-center justify-center">←</button>
        <button @click="stepIndex = Math.min(iterations.length - 1, stepIndex + 1)" :disabled="stepIndex === iterations.length - 1" class="w-7 h-7 rounded bg-slate-800 text-xs disabled:opacity-30 flex items-center justify-center">→</button>
      </div>
    </div>

    <!-- 产销平衡运输表 -->
    <div class="overflow-x-auto bg-slate-900/90 border border-slate-800 rounded-xl shadow-xl">
      <table class="w-full text-center border-collapse font-mono text-xs">
        <thead>
          <tr class="bg-slate-950 border-b border-slate-800 text-slate-400">
            <th class="py-2.5 px-3 border-r border-slate-800">产地 \ 销地</th>
            <th v-for="(h, j) in currentSnapshot.headers" :key="j" class="py-2.5 px-3 border-r border-slate-800/60">
              {{ h }}
              <div v-if="currentSnapshot.v" class="text-[10px] text-indigo-400 font-normal mt-0.5">v_{{ j + 1 }} = {{ currentSnapshot.v[j] }}</div>
            </th>
            <th class="py-2.5 px-3 border-r border-slate-800 text-indigo-300">产量 (a_i)</th>
            <th v-if="currentSnapshot.rows?.[0]?.u !== undefined" class="py-2.5 px-3 text-emerald-400">位势 u_i</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, i) in currentSnapshot.rows" :key="'r-' + i" class="border-b border-slate-800/80">
            <th class="py-3 px-3 border-r border-slate-800 bg-slate-950/40 text-slate-300">S{{ i + 1 }}</th>
            
            <!-- 单元格：运价 + 调运量 / 检验数 -->
            <td 
              v-for="(cell, j) in row.cells" 
              :key="'c-' + i + '-' + j" 
              class="py-2 px-2 border-r border-slate-800/60 relative transition-all"
              :class="{
                'bg-indigo-950/30': cell.type === 'basic',
                'ring-2 ring-amber-400 bg-amber-950/30': isLoopCell(i + 1, j + 1)
              }"
            >
              <div class="flex items-center justify-between text-[10px] text-slate-500 mb-1">
                <span class="px-1 rounded bg-slate-800 text-slate-300 font-semibold">{{ cell.cost }}</span>
                <span v-if="cell.loop_sign" class="text-amber-400 font-bold">{{ cell.loop_sign }}</span>
              </div>
              <div class="font-bold text-sm" :class="cell.type === 'basic' ? 'text-emerald-400' : 'text-slate-500'">
                {{ cell.allocation ?? (cell.sigma ? `σ=${cell.sigma}` : '-') }}
              </div>
            </td>

            <td class="py-3 px-3 border-r border-slate-800 font-bold text-slate-300">{{ row.supply ?? '-' }}</td>
            <td v-if="row.u !== undefined" class="py-3 px-3 text-emerald-400 font-bold">{{ row.u }}</td>
          </tr>
        </tbody>
        <tfoot v-if="currentSnapshot.demand">
          <tr class="bg-slate-950 font-bold border-t-2 border-slate-700 text-slate-300">
            <td class="py-2.5 px-3 border-r border-slate-800">销量 (b_j)</td>
            <td v-for="(d, j) in currentSnapshot.demand" :key="'d-' + j" class="py-2.5 px-3 border-r border-slate-800/60">{{ d }}</td>
            <td colspan="2">-</td>
          </tr>
        </tfoot>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{ iterations: any[] }>()
const stepIndex = ref(0)
const currentSnapshot = computed(() => props.iterations[stepIndex.value]?.state_matrix || {})

function isLoopCell(row: number, col: number): boolean {
  const loop: number[][] = props.iterations[stepIndex.value]?.loop || []
  return loop.some(([r, c]) => r === row && c === col)
}
</script>