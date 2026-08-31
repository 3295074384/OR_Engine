<template>
  <div class="space-y-4">
    <!-- 步骤控制栏：3 按钮极简切换与动效 -->
    <div class="p-4 rounded-2xl border border-white/10 bg-slate-900/40 backdrop-blur-xl flex flex-wrap items-center justify-between gap-4 shadow-xl">
      <div class="flex items-center space-x-3">
        <span class="text-xs text-slate-400 font-semibold">推演进度:</span>
        <div class="flex items-center space-x-1.5">
          <span class="font-mono font-black text-indigo-400 text-sm">Step {{ currentStepIndex + 1 }}</span>
          <span class="text-slate-500 text-xs font-mono">/ {{ iterations.length }}</span>
        </div>
        <span v-if="parsedStep.phase" class="text-[10px] px-2.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 font-mono font-bold">
          Phase {{ parsedStep.phase }}
        </span>
      </div>

      <!-- 核心 3 按钮控制器 -->
      <div class="flex items-center space-x-2">
        <button
          @click="currentStepIndex = Math.max(0, currentStepIndex - 1)"
          :disabled="currentStepIndex === 0"
          class="px-3.5 py-1.5 rounded-xl bg-white/5 hover:bg-white/10 disabled:opacity-30 text-xs text-slate-200 font-semibold transition active:scale-95 flex items-center space-x-1 border border-white/5"
        >
          <span>←</span>
          <span>上一步</span>
        </button>

        <button
          @click="currentStepIndex = Math.min(iterations.length - 1, currentStepIndex + 1)"
          :disabled="currentStepIndex === iterations.length - 1"
          class="px-4 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-30 text-xs text-white font-bold transition active:scale-95 shadow-md shadow-indigo-600/20 flex items-center space-x-1"
        >
          <span>下一步</span>
          <span>→</span>
        </button>

        <button
          @click="currentStepIndex = iterations.length - 1"
          :disabled="currentStepIndex === iterations.length - 1"
          class="px-3.5 py-1.5 rounded-xl bg-emerald-600/20 hover:bg-emerald-600/30 border border-emerald-500/40 text-emerald-300 text-xs font-bold transition active:scale-95 flex items-center space-x-1 disabled:opacity-30"
        >
          <span>⏩ 最终表 (Final)</span>
        </button>
      </div>

      <!-- 步骤动作说明 -->
      <div class="text-xs text-slate-300 max-w-sm truncate font-medium bg-black/20 px-3 py-1 rounded-lg border border-white/5" :title="parsedStep.description">
        {{ parsedStep.description }}
      </div>
    </div>

    <!-- 运筹学经典四分格单纯形表 (带入出基动画) -->
    <div class="overflow-x-auto rounded-2xl border border-white/10 bg-slate-950/60 backdrop-blur-2xl shadow-2xl">
      <table class="w-full text-center border-collapse font-mono text-xs">
        <!-- 顶栏：c_j 价值系数 -->
        <thead>
          <tr class="bg-slate-950/80 border-b border-white/10 text-slate-400">
            <th colspan="3" class="py-3 px-3 border-r border-white/10 text-slate-500 text-right font-bold">c_j →</th>
            <th
              v-for="(cj, colIdx) in parsedStep.c_j"
              :key="'cj-' + colIdx"
              class="py-3 px-3 border-r border-white/5 transition-all duration-300"
              :class="{'bg-emerald-500/20 text-emerald-300 font-extrabold shadow-inner': parsedStep.pivotCol === colIdx}"
            >
              {{ cj }}
            </th>
            <th class="py-3 px-3 text-slate-500 font-bold">θ (步长比)</th>
          </tr>

          <!-- 表头：c_B, x_B, b, 变量名列表 -->
          <tr class="bg-slate-900/60 border-b border-white/10 text-slate-300">
            <th class="py-2.5 px-3 border-r border-white/10 w-16 text-slate-400 font-semibold">c_B</th>
            <th class="py-2.5 px-3 border-r border-white/10 w-16 text-slate-400 font-semibold">x_B</th>
            <th class="py-2.5 px-3 border-r border-white/10 w-20 text-indigo-300 font-bold">b</th>
            <th
              v-for="(varName, colIdx) in parsedStep.var_names"
              :key="'var-' + colIdx"
              class="py-2.5 px-3 border-r border-white/5 transition-all duration-300"
              :class="{'bg-emerald-500/20 text-emerald-300 font-bold': parsedStep.pivotCol === colIdx}"
            >
              <div class="flex items-center justify-center space-x-1">
                <span>{{ varName }}</span>
                <span v-if="parsedStep.pivotCol === colIdx" class="text-emerald-400 font-black animate-bounce">↑</span>
              </div>
            </th>
            <th class="py-2.5 px-3 text-slate-400">比值 test</th>
          </tr>
        </thead>

        <!-- 主体：基变量行与初等行变换技术系数矩阵 A -->
        <tbody>
          <tr
            v-for="(row, rowIdx) in parsedStep.matrix_a"
            :key="'row-' + rowIdx"
            class="border-b border-white/5 hover:bg-white/5 transition-colors duration-200"
            :class="{'bg-rose-500/10': parsedStep.pivotRow === rowIdx}"
          >
            <!-- c_B -->
            <td class="py-3 px-3 border-r border-white/10 text-slate-400">
              {{ parsedStep.c_b[rowIdx] ?? '0' }}
            </td>
            <!-- x_B -->
            <td class="py-3 px-3 border-r border-white/10 font-bold text-slate-200">
              <div class="flex items-center justify-center space-x-1">
                <span>{{ parsedStep.basis_names[rowIdx] ?? ('x' + (rowIdx + 1)) }}</span>
                <span v-if="parsedStep.pivotRow === rowIdx" class="text-rose-400 font-black animate-bounce">↓</span>
              </div>
            </td>
            <!-- b (右端常数项) -->
            <td class="py-3 px-3 border-r border-white/10 font-black text-indigo-300">
              {{ parsedStep.b[rowIdx] ?? '0' }}
            </td>

            <!-- A 矩阵技术系数单元格 -->
            <td
              v-for="(cell, colIdx) in row"
              :key="'cell-' + rowIdx + '-' + colIdx"
              class="py-3 px-3 border-r border-white/5 transition-all duration-300"
              :class="{
                'bg-emerald-500/10 text-emerald-200': parsedStep.pivotCol === colIdx && parsedStep.pivotRow !== rowIdx,
                'ring-2 ring-indigo-400 bg-indigo-600/40 text-white font-black shadow-lg rounded-md transform scale-105': parsedStep.pivotCol === colIdx && parsedStep.pivotRow === rowIdx
              }"
            >
              {{ cell }}
            </td>

            <!-- θ 步长比例列 -->
            <td class="py-3 px-3 text-slate-400 font-mono" :class="{'text-rose-400 font-bold': parsedStep.pivotRow === rowIdx}">
              {{ parsedStep.theta[rowIdx] ?? '-' }}
            </td>
          </tr>
        </tbody>

        <!-- 底栏：检验数 σ_j 与当前目标值 z -->
        <tfoot>
          <tr class="bg-slate-950/90 font-bold border-t border-white/10 text-slate-200">
            <td colspan="2" class="py-3 px-3 border-r border-white/10 text-slate-400 text-right">检验数 σ_j</td>
            <!-- 当前目标值 -->
            <td class="py-3 px-3 border-r border-white/10 text-emerald-400 font-black">
              {{ parsedStep.current_z }}
            </td>
            <!-- 检验数各列 -->
            <td
              v-for="(sigma, colIdx) in parsedStep.sigma"
              :key="'sigma-' + colIdx"
              class="py-3 px-3 border-r border-white/5 transition-all duration-300"
              :class="{
                'text-emerald-400 font-black': isPositive(sigma),
                'text-slate-500': isZero(sigma),
                'text-slate-400': !isPositive(sigma) && !isZero(sigma),
                'bg-emerald-500/20': parsedStep.pivotCol === colIdx
              }"
            >
              {{ sigma }}
            </td>
            <td class="py-3 px-3 text-slate-600">-</td>
          </tr>
        </tfoot>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Iteration } from '../stores'

const props = defineProps<{
  iterations: Iteration[]
}>()

const currentStepIndex = ref(0)

function formatVal(v: any): string {
  if (v === null || v === undefined) return '-'
  if (typeof v === 'object' && 'display' in v) return String(v.display)
  return String(v)
}

function isPositive(v: string): boolean {
  if (v.includes('/')) {
    const [n, d] = v.split('/').map(Number)
    return n / d > 0
  }
  return Number(v) > 0
}

function isZero(v: string): boolean {
  return v === '0' || Number(v) === 0
}

const parsedStep = computed(() => {
  const step = props.iterations[currentStepIndex.value] || {}
  const sm = step.state_matrix || {}

  const phase = step.phase || sm.phase || (step.action?.includes('Phase') ? (step.action.includes('Phase 1') ? 1 : 2) : undefined)
  const description = step.action || step.description || `Iteration Step ${currentStepIndex.value + 1}`

  const var_names: string[] = (sm.var_names || sm.variable_names || []).map(formatVal)
  const c_j: string[] = (sm.c_j || sm.cj || []).map(formatVal)
  const c_b: string[] = (sm.c_b || sm.cb || []).map(formatVal)
  const basis_names: string[] = (sm.basis_var_names || sm.basis_names || sm.basis || []).map(formatVal)
  const b: string[] = (sm.b || sm.rhs || []).map(formatVal)

  const matrix_a: string[][] = (sm.matrix_a || sm.matrix || sm.A || []).map((row: any[]) => row.map(formatVal))
  const sigma: string[] = (sm.sigma || sm.reduced_costs || []).map(formatVal)
  const current_z = formatVal(sm.current_z ?? sm.objective_value ?? '0')
  const theta: (string | null)[] = (sm.theta || []).map((t: any) => t ? formatVal(t) : null)

  const pivot = sm.pivot || {}
  const pivotCol = pivot.entering_col ?? pivot.col ?? null
  const pivotRow = pivot.leaving_row ?? pivot.row ?? null

  return {
    phase,
    description,
    var_names,
    c_j,
    c_b,
    basis_names,
    b,
    matrix_a,
    sigma,
    current_z,
    theta,
    pivotCol,
    pivotRow
  }
})
</script>