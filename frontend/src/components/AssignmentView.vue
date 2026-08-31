<template>
  <div class="space-y-6">
    <div v-if="iterations.length > 0" class="p-4 rounded-2xl border border-white/10 bg-slate-900/40 backdrop-blur-xl flex flex-wrap items-center justify-between gap-4 shadow-xl">
      <div class="flex items-center space-x-3">
        <span class="text-xs text-slate-400 font-semibold">化简与覆盖步骤:</span>
        <div class="flex items-center space-x-1.5">
          <span class="font-mono font-black text-indigo-400 text-sm">Step {{ stepIndex + 1 }}</span>
          <span class="text-slate-500 text-xs font-mono">/ {{ iterations.length }}</span>
        </div>
        <span class="text-[10px] px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-mono font-bold">
          Hungarian Method
        </span>
      </div>

      <div class="flex items-center space-x-2">
        <button 
          @click="stepIndex = Math.max(0, stepIndex - 1)" 
          :disabled="stepIndex === 0"
          class="px-3.5 py-1.5 rounded-xl bg-white/5 hover:bg-white/10 disabled:opacity-30 text-xs text-slate-200 font-semibold transition active:scale-95 flex items-center space-x-1 border border-white/5"
        >
          <span>←</span>
          <span>上一步</span>
        </button>

        <button 
          @click="stepIndex = Math.min(iterations.length - 1, stepIndex + 1)" 
          :disabled="stepIndex === iterations.length - 1"
          class="px-4 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-30 text-xs text-white font-bold transition active:scale-95 shadow-md shadow-indigo-600/20 flex items-center space-x-1"
        >
          <span>下一步</span>
          <span>→</span>
        </button>

        <button 
          @click="stepIndex = iterations.length - 1" 
          :disabled="stepIndex === iterations.length - 1"
          class="px-3.5 py-1.5 rounded-xl bg-emerald-600/20 hover:bg-emerald-600/30 border border-emerald-500/40 text-emerald-300 text-xs font-bold transition active:scale-95 flex items-center space-x-1 disabled:opacity-30"
        >
          <span>⏩ 最终匹配</span>
        </button>
      </div>

      <div class="text-xs text-slate-300 max-w-sm truncate font-medium bg-black/20 px-3 py-1 rounded-lg border border-white/5" :title="currentStep.action">
        {{ currentStep.action || '匈牙利法行列化简推演' }}
      </div>
    </div>

    <div v-if="matrixSnap.rows?.length" class="overflow-x-auto rounded-2xl border border-white/10 bg-slate-950/60 backdrop-blur-2xl shadow-2xl p-4">
      <table class="w-full text-center border-collapse font-mono text-xs">
        <thead>
          <tr class="bg-slate-900/60 border-b border-white/10 text-slate-400">
            <th class="py-2.5 px-3 border-r border-white/10 w-20 text-slate-400 font-bold">人员 \ 任务</th>
            <th 
              v-for="c in matrixSnap.size" 
              :key="'th-' + c"
              class="py-2.5 px-3 border-r border-white/5 transition-all"
              :class="{'bg-rose-500/20 text-rose-300 font-black': isColCovered(c)}"
            >
              <div class="flex items-center justify-center space-x-1">
                <span>任务 {{ c }}</span>
                <span v-if="isColCovered(c)" class="text-rose-400 text-xs" title="该列被直线覆盖">│</span>
              </div>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr 
            v-for="(row, rIdx) in matrixSnap.rows" 
            :key="'row-' + rIdx"
            class="border-b border-white/5 hover:bg-white/5 transition-colors"
            :class="{'bg-rose-500/10': isRowCovered(row.row)}"
          >
            <th class="py-3 px-3 border-r border-white/10 font-bold text-slate-300">
              <div class="flex items-center justify-center space-x-1">
                <span>人员 {{ row.row }}</span>
                <span v-if="isRowCovered(row.row)" class="text-rose-400 text-xs" title="该行被直线覆盖">─</span>
              </div>
            </th>

            <td 
              v-for="(cell, cIdx) in row.cells" 
              :key="'cell-' + rIdx + '-' + cIdx"
              class="py-3 px-3 border-r border-white/5 transition-all duration-300 relative"
              :class="{
                'bg-amber-500/20 ring-1 ring-amber-400 font-extrabold text-amber-200': cell.crossed,
                'bg-emerald-500/20 text-emerald-300 font-black': cell.is_zero && !cell.covered,
                'text-slate-500 opacity-60': cell.covered && !cell.crossed
              }"
            >
              <span class="text-sm">{{ cell.value }}</span>
              <span v-if="cell.crossed" class="absolute top-1 right-1 text-[9px] text-amber-400 font-bold" title="行列交叉点 (需 +θ)">+θ</span>
              <span v-else-if="cell.is_zero" class="absolute top-1 right-1 text-[9px] text-emerald-400 font-bold">⓪</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="p-6 rounded-2xl border border-white/10 bg-slate-900/40 backdrop-blur-xl shadow-2xl space-y-6">
      <div class="flex items-center justify-between border-b border-white/10 pb-4">
        <div class="flex items-center space-x-2">
          <span class="w-3 h-3 rounded-full bg-emerald-400 animate-pulse"></span>
          <h3 class="font-bold text-sm text-slate-100">匈牙利法最佳指派方案 (Assignment Solution)</h3>
        </div>
        <div class="text-xs font-mono font-bold text-emerald-400">
          最优总成本 / 收益 = {{ result.final_result?.total_cost ?? result.objective?.value?.display ?? '-' }}
        </div>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
        <div 
          v-for="(item, idx) in assignments" 
          :key="idx"
          class="p-4 rounded-xl bg-slate-950/60 border border-white/10 backdrop-blur hover:border-indigo-500/50 transition-all duration-300 transform hover:-translate-y-1 shadow-lg space-y-2"
        >
          <div class="flex items-center justify-between text-xs">
            <span class="px-2.5 py-1 rounded-lg bg-indigo-500/20 text-indigo-300 font-bold">人员 {{ item.worker }}</span>
            <span class="text-slate-500 font-mono">分配至 →</span>
            <span class="px-2.5 py-1 rounded-lg bg-emerald-500/20 text-emerald-300 font-bold">任务 {{ item.task }}</span>
          </div>
          <div class="pt-2 border-t border-white/5 flex items-center justify-between text-xs font-mono">
            <span class="text-slate-400">单项代价:</span>
            <span class="font-bold text-indigo-400">{{ item.cost }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{ result: any }>()

const stepIndex = ref(0)
const iterations = computed(() => props.result?.iterations || [])
const currentStep = computed(() => iterations.value[stepIndex.value] || {})
const matrixSnap = computed(() => currentStep.value.state_matrix || {})

const assignments = computed(() => {
  const fr = props.result?.final_result || {}
  return fr.assignment || []
})

function isRowCovered(rowNum: number): boolean {
  const covered = matrixSnap.value.covered_rows || []
  return covered.includes(rowNum)
}

function isColCovered(colNum: number): boolean {
  const covered = matrixSnap.value.covered_cols || []
  return covered.includes(colNum)
}
</script>