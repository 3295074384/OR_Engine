<template>
  <div
    class="min-h-screen text-slate-100 flex flex-col relative overflow-x-hidden font-sans transition-all duration-700 select-none"
    :class="bgThemeClasses"
  >
    <div class="fixed inset-0 overflow-hidden pointer-events-none z-0">
      <div class="absolute -top-32 -left-32 w-96 h-96 bg-indigo-600/20 rounded-full blur-3xl animate-pulse"></div>
      <div class="absolute top-1/3 -right-32 w-96 h-96 bg-emerald-600/15 rounded-full blur-3xl animate-pulse" style="animation-delay: 2s;"></div>
      <div class="absolute -bottom-32 left-1/3 w-96 h-96 bg-violet-600/20 rounded-full blur-3xl animate-pulse" style="animation-delay: 4s;"></div>
    </div>

    <header class="h-16 border-b border-white/10 bg-slate-950/40 backdrop-blur-xl px-6 flex items-center justify-between sticky top-0 z-30 transition-all">
      <div class="flex items-center space-x-3">
        <div class="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center font-black text-xs text-white shadow-lg shadow-indigo-500/30 transform hover:scale-105 transition">OR</div>
        <div>
          <div class="flex items-center space-x-2">
            <span class="font-extrabold tracking-wide text-white text-base">OR Engine 2.0</span>
            <span class="text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 font-mono">
              {{ store.config.title }}
            </span>
          </div>
        </div>
      </div>

      <div class="flex items-center space-x-3">
        <div class="flex items-center bg-black/40 backdrop-blur border border-white/10 rounded-lg p-1 space-x-1">
          <button
            v-for="th in themes"
            :key="th.key"
            @click="store.currentTheme = th.key"
            :title="th.label"
            class="w-5 h-5 rounded-md transition-all transform hover:scale-110 flex items-center justify-center"
            :class="[th.color, store.currentTheme === th.key ? 'ring-2 ring-white shadow-md' : 'opacity-40 hover:opacity-100']"
          ></button>
        </div>

        <button
          @click="store.enableGlassBlur = !store.enableGlassBlur"
          class="px-2.5 py-1.5 rounded-lg border text-xs font-mono transition backdrop-blur-sm"
          :class="store.enableGlassBlur ? 'bg-white/10 border-white/20 text-indigo-300' : 'bg-black/30 border-white/5 text-slate-500'"
          title="切换高斯模糊与毛玻璃透明度"
        >
          {{ store.enableGlassBlur ? '✨ 极光毛玻璃' : '🌑 高对比暗色' }}
        </button>

        <button
          @click="isDrawerOpen = !isDrawerOpen"
          class="flex items-center space-x-2 px-4 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 active:scale-95 transition-all text-xs font-bold text-white shadow-lg shadow-indigo-600/30"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 transition-transform duration-300" :class="{'rotate-180': isDrawerOpen}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
          </svg>
          <span>{{ isDrawerOpen ? '收起配置' : '配置参数 / 模型' }}</span>
        </button>
      </div>
    </header>

    <main class="flex-1 p-4 md:p-8 max-w-7xl mx-auto w-full space-y-6 relative z-10">
      <Transition enter-active-class="transition duration-300 ease-out" enter-from-class="transform -translate-y-4 opacity-0" enter-to-class="transform translate-y-0 opacity-100">
        <div v-if="store.error" class="bg-rose-950/60 backdrop-blur-xl border border-rose-500/40 rounded-2xl p-4 flex items-center justify-between text-rose-200 text-xs shadow-2xl">
          <div class="flex items-center space-x-2">
            <span class="p-1 rounded bg-rose-500/20 text-rose-400 font-bold">⚠ 求解异常</span>
            <span>{{ store.error }}</span>
          </div>
          <button @click="store.error = ''" class="text-rose-400 hover:text-white font-bold px-2">✕</button>
        </div>
      </Transition>

      <Transition enter-active-class="transition duration-500 ease-out" enter-from-class="transform scale-95 opacity-0" enter-to-class="transform scale-100 opacity-100">
        <div
          v-if="store.result"
          class="border rounded-2xl p-5 flex flex-wrap items-center justify-between gap-4 shadow-2xl transition-all duration-300"
          :class="glassCardClasses"
        >
          <div class="flex items-center space-x-3">
            <div class="w-3 h-3 rounded-full animate-ping" :class="store.result.status === 'OPTIMAL' ? 'bg-emerald-400' : 'bg-amber-400'"></div>
            <span class="text-xs text-slate-300">求解状态:</span>
            <span class="text-xs px-3 py-1 rounded-lg font-mono font-black tracking-wide"
              :class="{
                'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40': store.result.status === 'OPTIMAL',
                'bg-rose-500/20 text-rose-300 border border-rose-500/40': ['INFEASIBLE', 'UNBOUNDED', 'ERROR'].includes(store.result.status),
                'bg-amber-500/20 text-amber-300 border border-amber-500/40': store.result.status === 'MAX_ITER_REACHED'
              }"
            >
              {{ store.result.status }}
            </span>
            <span v-if="store.result.sub_type" class="text-[11px] text-indigo-300 font-mono">({{ store.result.sub_type }})</span>
          </div>

          <div class="flex items-center space-x-6 text-sm">
            <div v-if="store.result.objective?.value" class="flex items-center space-x-2">
              <span class="text-slate-300 text-xs font-semibold">最优值 / 目标值:</span>
              <span class="font-mono font-black text-emerald-400 text-lg">
                {{ typeof store.result.objective.value === 'object' ? store.result.objective.value.display : store.result.objective.value }}
              </span>
            </div>
            <div v-if="store.result.diagnostics" class="text-slate-300 text-xs flex items-center space-x-4">
              <span>计算耗时: <strong class="text-white font-mono">{{ store.result.diagnostics.elapsed_ms ?? 0 }}ms</strong></span>
              <span>推演迭代: <strong class="text-white font-mono">{{ store.result.diagnostics.total_steps ?? store.iterations.length }} 步</strong></span>
            </div>
          </div>
        </div>
      </Transition>

      <GraphicalCanvas
        v-if="store.problemType === 'LP' && store.config.lpMethod === 'graphical' && graphicalResult"
        :final-result="graphicalResult"
        :class="glassCardClasses"
      />

      <SimplexTableau
        v-else-if="store.iterations?.length && (store.problemType === 'LP' || (store.problemType === 'IP' && store.ipMethod === 'cutting_plane'))"
        :iterations="store.iterations"
        :class="glassCardClasses"
      />

      <BranchBoundTree
        v-else-if="store.problemType === 'IP' && store.ipMethod === 'branch_and_bound' && store.iterations?.length"
        :iterations="store.iterations"
        :class="glassCardClasses"
      />

      <TransportationView
        v-else-if="store.problemType === 'TP' && store.iterations?.length"
        :iterations="store.iterations"
        :class="glassCardClasses"
      />

      <AssignmentView
        v-else-if="store.problemType === 'AP' && store.result"
        :result="store.result"
        :class="glassCardClasses"
      />

      <GameTheoryView
        v-else-if="store.problemType === 'GT' && store.result"
        :result="store.result"
        :class="glassCardClasses"
      />

      <div v-else :class="glassCardClasses" class="h-[55vh] flex flex-col items-center justify-center text-center space-y-4 border rounded-3xl p-8">
        <div class="w-16 h-16 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 animate-bounce">
          <svg xmlns="http://www.w3.org/2000/svg" class="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.6" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </div>
        <div>
          <div class="text-white text-base font-bold">工作区就绪</div>
          <p class="text-slate-400 text-xs mt-1 max-w-md leading-relaxed">
            点击右上角「配置参数 / 模型」呼出推拉抽屉，输入运筹学模型矩阵并启动两阶段与全链路推演！
          </p>
        </div>
      </div>
    </main>

    <Teleport to="body">
      <Transition
        enter-active-class="transition-opacity ease-out duration-300"
        enter-from-class="opacity-0"
        enter-to-class="opacity-100"
        leave-active-class="transition-opacity ease-in duration-200"
        leave-from-class="opacity-100"
        leave-to-class="opacity-0"
      >
        <div
          v-if="isDrawerOpen"
          @click="isDrawerOpen = false"
          class="fixed inset-0 bg-black/70 backdrop-blur-md z-40"
        ></div>
      </Transition>

      <Transition
        enter-active-class="transform transition cubic-bezier(0.16, 1, 0.3, 1) duration-300"
        enter-from-class="translate-x-full"
        enter-to-class="translate-x-0"
        leave-active-class="transform transition cubic-bezier(0.7, 0, 0.84, 0) duration-200"
        leave-from-class="translate-x-0"
        leave-to-class="translate-x-full"
      >
        <aside
          v-if="isDrawerOpen"
          class="fixed top-0 right-0 h-full w-full max-w-xl bg-slate-950/90 backdrop-blur-2xl border-l border-white/10 shadow-2xl z-50 flex flex-col"
        >
          <div class="p-5 border-b border-white/10 flex items-center justify-between bg-slate-900/40">
            <div>
              <h2 class="font-bold text-sm text-white flex items-center space-x-2">
                <span>参数与模型配置</span>
              </h2>
              <p class="text-xs text-slate-400 mt-0.5">选择算法类型并配置约束技术系数</p>
            </div>
            <button
              @click="isDrawerOpen = false"
              class="w-8 h-8 rounded-xl bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white flex items-center justify-center text-xs transition active:scale-95"
            >
              ✕
            </button>
          </div>

          <div class="flex-1 overflow-y-auto p-5 space-y-6">
            <div class="space-y-2">
              <label class="text-xs font-semibold text-slate-300">问题类型</label>
              <div class="grid grid-cols-3 gap-2">
                <button
                  v-for="p in panels"
                  :key="p.key"
                  @click="store.selectPanel(p.key)"
                  class="py-2 px-2.5 text-xs font-medium rounded-xl border transition-all text-left flex flex-col justify-center"
                  :class="store.panel === p.key ? 'bg-indigo-600/30 border-indigo-500 text-white shadow-lg shadow-indigo-600/20' : 'bg-white/5 border-white/5 text-slate-400 hover:bg-white/10'"
                >
                  <span class="font-bold font-mono text-indigo-300">{{ p.label }}</span>
                  <span class="text-[10px] opacity-70 truncate">{{ p.desc }}</span>
                </button>
              </div>
            </div>

            <div v-if="store.problemType === 'IP'" class="flex items-center justify-between bg-white/5 p-3 rounded-xl border border-white/10 backdrop-blur">
              <span class="text-xs text-slate-300 font-medium">整数规划算法</span>
              <div class="flex items-center space-x-2">
                <button
                  @click="store.ipMethod = 'branch_and_bound'"
                  class="px-3 py-1 text-xs rounded-lg transition font-medium"
                  :class="store.ipMethod === 'branch_and_bound' ? 'bg-indigo-600 text-white shadow-md' : 'bg-white/5 text-slate-400 hover:text-white'"
                >
                  分支定界 (B&B)
                </button>
                <button
                  @click="store.ipMethod = 'cutting_plane'"
                  class="px-3 py-1 text-xs rounded-lg transition font-medium"
                  :class="store.ipMethod === 'cutting_plane' ? 'bg-indigo-600 text-white shadow-md' : 'bg-white/5 text-slate-400 hover:text-white'"
                >
                  Gomory 割平面
                </button>
              </div>
            </div>

            <div v-if="['LP', 'IP', 'AP'].includes(store.problemType)" class="flex items-center justify-between bg-white/5 p-3 rounded-xl border border-white/10 backdrop-blur">
              <span class="text-xs text-slate-300 font-medium">优化目标方向</span>
              <div class="flex items-center space-x-2">
                <button
                  @click="store.objective = 'max'"
                  class="px-3.5 py-1 text-xs rounded-lg font-mono font-bold transition"
                  :class="store.objective === 'max' ? 'bg-indigo-600 text-white shadow-md' : 'bg-white/5 text-slate-400 hover:text-white'"
                >
                  max (极大化)
                </button>
                <button
                  @click="store.objective = 'min'"
                  class="px-3.5 py-1 text-xs rounded-lg font-mono font-bold transition"
                  :class="store.objective === 'min' ? 'bg-indigo-600 text-white shadow-md' : 'bg-white/5 text-slate-400 hover:text-white'"
                >
                  min (极小化)
                </button>
              </div>
            </div>

            <div v-if="store.problemType === 'LP' || store.problemType === 'IP'">
              <LpEditor
                :model="store.form"
                :is-i-p="store.problemType === 'IP'"
                @set-n="store.setNVars"
                @add-constraint="store.addConstraint"
                @remove-constraint="store.removeConstraint"
              />
            </div>

            <div v-else-if="store.problemType === 'TP'" class="space-y-4">
              <div>
                <span class="text-xs text-slate-400 block mb-1">产地供应量 (Supply)</span>
                <div class="flex gap-2">
                  <input v-for="(_, i) in store.form.supply" :key="'s-'+i" v-model="store.form.supply[i]" class="w-16 bg-slate-900 border border-white/10 rounded-lg p-1.5 text-xs text-center font-mono focus:border-indigo-500 outline-none" />
                </div>
              </div>
              <div>
                <span class="text-xs text-slate-400 block mb-1">销地需求量 (Demand)</span>
                <div class="flex gap-2">
                  <input v-for="(_, i) in store.form.demand" :key="'d-'+i" v-model="store.form.demand[i]" class="w-16 bg-slate-900 border border-white/10 rounded-lg p-1.5 text-xs text-center font-mono focus:border-indigo-500 outline-none" />
                </div>
              </div>
              <MatrixEditor
                :rows="store.form.cost"
                label="运价表"
                @add-row="store.addRow('cost')"
                @remove-row="(i) => store.removeRow('cost', i)"
                @add-col="store.addCol('cost')"
                @remove-col="(i) => store.removeCol('cost', i)"
              />
            </div>

            <div v-else-if="store.problemType === 'AP'">
              <MatrixEditor
                :rows="store.form.cost_matrix"
                label="指派成本"
                @add-row="store.addRow('cost_matrix')"
                @remove-row="(i) => store.removeRow('cost_matrix', i)"
                @add-col="store.addCol('cost_matrix')"
                @remove-col="(i) => store.removeCol('cost_matrix', i)"
              />
            </div>

            <div v-else-if="store.problemType === 'GT'">
              <MatrixEditor
                :rows="store.form.payoff_matrix"
                label="收益矩阵"
                @add-row="store.addRow('payoff_matrix')"
                @remove-row="(i) => store.removeRow('payoff_matrix', i)"
                @add-col="store.addCol('payoff_matrix')"
                @remove-col="(i) => store.removeCol('payoff_matrix', i)"
              />
            </div>
          </div>

          <div class="p-5 border-t border-white/10 bg-slate-950/80 backdrop-blur flex items-center justify-between gap-3">
            <button
              @click="store.resetForm()"
              class="px-4 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-slate-300 text-xs font-medium transition active:scale-95"
            >
              重置参数
            </button>
            <button
              @click="handleSolve"
              :disabled="store.loading"
              class="flex-1 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 active:scale-98 text-white font-bold text-xs tracking-wide shadow-lg shadow-indigo-600/30 flex items-center justify-center space-x-2 transition disabled:opacity-50"
            >
              <span v-if="store.loading" class="animate-spin text-sm">↻</span>
              <span>{{ store.loading ? '算法求解推演中...' : '开始求解 (Solve)' }}</span>
            </button>
          </div>
        </aside>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useSolverStore, type Panel, type ThemeBackground } from './stores'
import SimplexTableau from './components/SimplexTableau.vue'
import GraphicalCanvas from './components/GraphicalCanvas.vue'
import BranchBoundTree from './components/BranchBoundTree.vue'
import TransportationView from './components/TransportationView.vue'
import AssignmentView from './components/AssignmentView.vue'
import GameTheoryView from './components/GameTheoryView.vue'
import LpEditor from './components/LpEditor.vue'
import MatrixEditor from './components/MatrixEditor.vue'

const store = useSolverStore()
const isDrawerOpen = ref(false)

const themes: { key: ThemeBackground; label: string; color: string }[] = [
  { key: 'aurora', label: '极光渐变 (Aurora)', color: 'bg-emerald-500' },
  { key: 'cyber', label: '赛博霓虹 (Cyber)', color: 'bg-indigo-500' },
  { key: 'deep_ocean', label: '深海湛蓝 (Deep Ocean)', color: 'bg-blue-600' },
  { key: 'pure_dark', label: '极夜暗黑 (Pure Dark)', color: 'bg-slate-800' },
]

const bgThemeClasses = computed(() => {
  switch (store.currentTheme) {
    case 'cyber':
      return 'bg-gradient-to-br from-slate-950 via-indigo-950/40 to-slate-950'
    case 'deep_ocean':
      return 'bg-gradient-to-br from-slate-950 via-blue-950/40 to-slate-900'
    case 'aurora':
      return 'bg-gradient-to-br from-slate-950 via-emerald-950/30 to-slate-950'
    case 'pure_dark':
    default:
      return 'bg-slate-950'
  }
})

const glassCardClasses = computed(() => {
  if (store.enableGlassBlur) {
    return 'bg-slate-900/40 backdrop-blur-2xl border-white/10 shadow-[0_8px_32px_0_rgba(0,0,0,0.37)]'
  }
  return 'bg-slate-900 border-slate-800 shadow-xl'
})

const graphicalResult = computed<{
  objective_value: string
  solution: Record<string, string>
  feasible_vertices: Array<{ x1: string; x2: string; z: string }>
  boundary_lines: Array<{ a1: string; a2: string; d: string; type: string }>
} | null>(() => {
  const fr = store.result?.final_result as any
  if (!fr) return null
  return fr
})

const panels: { key: Panel; label: string; desc: string }[] = [
  { key: 'lp_simplex', label: 'LP Simplex', desc: '单纯形法' },
  { key: 'lp_graphical', label: 'LP Graphical', desc: '图解法' },
  { key: 'ip', label: 'Integer IP', desc: '分支定界/割平面' },
  { key: 'tp', label: 'Transport TP', desc: '产销平衡' },
  { key: 'ap', label: 'Assign AP', desc: '匈牙利法' },
  { key: 'gt', label: 'Game GT', desc: '零和博弈' },
]

async function handleSolve() {
  await store.solve()
  if (store.result && !store.error) {
    isDrawerOpen.value = false
  }
}
</script>