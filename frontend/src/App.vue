<script setup lang="ts">
import { computed, ref } from 'vue'
import { RotateCcw, Play, LoaderCircle, Zap, Activity, CheckCircle2, AlertTriangle, ChevronRight, ChevronDown } from 'lucide-vue-next'
import SimplexTableau from './components/SimplexTableau.vue'
import LpEditor from './components/LpEditor.vue'
import MatrixEditor from './components/MatrixEditor.vue'
import { useSolverStore, type Panel } from './stores'

const store = useSolverStore()
const current = computed(() => store.iterations[store.selectedStep])
const drawerOpen = ref(true)
const activePanelLabel = computed(() => store.config?.title ?? '')

const panels: Array<{ key: Panel; label: string }> = [
  { key: 'lp_graphical', label: '线性规划（图解法）' },
  { key: 'lp_simplex', label: '线性规划（单纯形法）' },
  { key: 'ip', label: '整数规划' },
  { key: 'tp', label: '运输问题' },
  { key: 'ap', label: '指派问题' },
  { key: 'gt', label: '博弈论' },
]

const isLP = computed(() => store.problemType === 'LP')
const isIP = computed(() => store.problemType === 'IP')
const isTP = computed(() => store.problemType === 'TP')
const isAP = computed(() => store.problemType === 'AP')
const isGT = computed(() => store.problemType === 'GT')

function valueText(value: any) { if (value === null || value === undefined) return '—'; if (typeof value === 'object' && value.display) return value.display; return String(value) }

function finalEntries() { return Object.entries(store.result?.final_result ?? {}) }

function solutionEntries() { return Object.entries(store.result?.solution ?? {}) }

function allocationEntries() {
  const alloc = (store.result?.final_result as any)?.allocation
  if (!alloc || typeof alloc !== 'object') return []
  return Object.entries(alloc).map(([key, val]) => ({ key, val: valueText(val) }))
}

function assignmentList() {
  return (store.result?.final_result as any)?.assignment ?? []
}

function allocationCells() {
  const basis = (store.result?.final_result as any)?.basis_cells ?? []
  const alloc = (store.result?.final_result as any)?.allocation ?? {}
  return basis.map(([r, c]: [number, number]) => ({ row: r, col: c, val: valueText(alloc[`x(${r},${c})`]) }))
}

function strategyRows() {
  const fr = store.result?.final_result as any
  if (!fr) return []
  const p1 = fr.player1_strategy
  const p2 = fr.player2_strategy
  const keys = new Set<string>()
  if (p1 && typeof p1 === 'object') Object.keys(p1).forEach((k) => keys.add(k))
  if (p2 && typeof p2 === 'object') Object.keys(p2).forEach((k) => keys.add(k))
  const rows = [...keys].map((key) => ({ key, p1: typeof p1 === 'object' && p1[key] != null ? valueText(p1[key]) : '—', p2: typeof p2 === 'object' && p2[key] != null ? valueText(p2[key]) : '—' }))
  const labels = [...keys].sort((a, b) => (a.match(/\d+/) ? Number(a.match(/\d+/)![0]) : 0) - (b.match(/\d+/) ? Number(b.match(/\d+/)![0]) : 0) || 0)
  return rows.sort((a, b) => labels.indexOf(a.key) - labels.indexOf(b.key))
}

function calculationLines() {
  const calc = current.value?.calculation
  if (Array.isArray(calc)) return calc
  if (typeof calc === 'string' && calc) return [calc]
  return []
}

const resultMetricCount = computed(() => {
  if (isTP.value) return allocationEntries().length
  if (isAP.value) return assignmentList().length
  if (isGT.value) return strategyRows().length
  return solutionEntries().length
})
</script>

<template>
  <main class="shell">
    <header class="topbar">
      <div class="brand"><div class="brand-mark"><Zap :size="18" /></div><div><strong>OR / ENGINE</strong><span>运筹学推演工作台</span></div></div>
      <div class="header-status"><i></i> API 正常 <span>v0.1</span></div>
    </header>
    <div class="workspace" :class="{ 'drawer-open': drawerOpen, 'drawer-collapsed': !drawerOpen }">
      <div class="input-drawer">
        <button class="drawer-handle" @click="drawerOpen = !drawerOpen">
          <div class="drawer-handle-left">
            <div class="eyebrow">模型定义 <span>01</span></div>
            <span class="drawer-title">{{ activePanelLabel }}</span>
          </div>
          <div class="drawer-handle-right"><ChevronDown :size="18" class="drawer-caret" /><span class="drawer-hint">{{ drawerOpen ? '收起配置' : '展开配置' }}</span></div>
        </button>
        <div v-show="drawerOpen" class="drawer-body">
          <p class="lede">配置精确的优化模型，跟随引擎回放每一步计算。</p>

          <div class="field-label">问题类型</div>
          <div class="panel-nav">
            <button v-for="p in panels" :key="p.key" :class="{ active: store.panel === p.key }" @click="store.selectPanel(p.key)">{{ p.label }}</button>
          </div>

          <template v-if="isLP || isIP">
            <div class="field-label objective-label">目标函数 <span>方向</span></div>
            <div class="objective"><button :class="{ selected: store.objective === 'max' }" @click="store.objective = 'max'">最大化</button><button :class="{ selected: store.objective === 'min' }" @click="store.objective = 'min'">最小化</button></div>
            <LpEditor :model="store.form" :isIP="isIP" @set-n="store.setNVars" @add-constraint="store.addConstraint" @remove-constraint="store.removeConstraint" />
          </template>

          <template v-else-if="isTP">
            <div class="block-label">产量（supply）</div>
            <div class="list-editor"><input v-for="(v, i) in store.form.supply" :key="i" v-model="store.form.supply[i]" spellcheck="false" /></div>
            <div class="block-label">销量（demand）</div>
            <div class="list-editor"><input v-for="(v, i) in store.form.demand" :key="i" v-model="store.form.demand[i]" spellcheck="false" /></div>
            <div class="block-label">运价矩阵（cost）</div>
            <MatrixEditor :rows="store.form.cost" label="cost" @add-row="store.addRow('cost')" @remove-row="store.removeRow('cost', $event)" @add-col="store.addCol('cost')" @remove-col="store.removeCol('cost', $event)" />
          </template>

          <template v-else-if="isAP">
            <div class="field-label objective-label">目标函数 <span>方向</span></div>
            <div class="objective"><button :class="{ selected: store.objective === 'min' }" @click="store.objective = 'min'">最小化</button><button :class="{ selected: store.objective === 'max' }" @click="store.objective = 'max'">最大化</button></div>
            <div class="block-label">成本/收益矩阵</div>
            <MatrixEditor :rows="store.form.cost_matrix" label="矩阵" @add-row="store.addRow('cost_matrix')" @remove-row="store.removeRow('cost_matrix', $event)" @add-col="store.addCol('cost_matrix')" @remove-col="store.removeCol('cost_matrix', $event)" />
          </template>

          <template v-else-if="isGT">
            <div class="block-label">行玩家收益矩阵</div>
            <MatrixEditor :rows="store.form.payoff_matrix" label="payoff" @add-row="store.addRow('payoff_matrix')" @remove-row="store.removeRow('payoff_matrix', $event)" @add-col="store.addCol('payoff_matrix')" @remove-col="store.removeCol('payoff_matrix', $event)" />
          </template>

          <div class="actions">
            <button class="run" :disabled="store.loading" @click="store.solve"><LoaderCircle v-if="store.loading" class="spin" :size="17" /><Play v-else :size="17" /> {{ store.loading ? '求解中' : '开始求解' }}</button>
            <button class="reset" title="重置" @click="store.reset"><RotateCcw :size="17" /></button>
          </div>
          <p v-if="store.error" class="error"><AlertTriangle :size="15" /> {{ store.error }}</p>
        </div>
      </div>

      <section class="results">
        <div class="result-head">
          <div><div class="eyebrow">计算轨迹 <span>02</span></div><h2>{{ store.result ? '求解完成' : '等待模型输入' }}</h2></div>
          <div v-if="store.result" class="status-pill" :class="store.result.status === 'OPTIMAL' ? 'good' : 'warn'"><CheckCircle2 :size="15" /> {{ store.result.status }}</div>
        </div>

        <div v-if="!store.result" class="empty"><div class="empty-grid"></div><Activity :size="42" stroke-width="1.2" /><strong>准备就绪</strong><span>在左侧输入模型，开始查看计算轨迹。</span></div>

        <template v-else>
          <div class="metrics">
            <div><span>目标函数值</span><strong>{{ valueText(store.result.objective?.value) }}</strong><small>{{ store.objective === 'max' ? '最大化目标' : '最小化目标' }}</small></div>
            <div><span>迭代次数</span><strong>{{ store.result.diagnostics?.total_steps ?? store.iterations.length }}</strong><small>计算耗时 {{ store.result.diagnostics?.elapsed_ms ?? 0 }} 毫秒</small></div>
            <div><span>方案数量</span><strong class="metrics-count">{{ resultMetricCount }}</strong><small>决策条目</small></div>
            <div><span>求解方法</span><strong class="subtype">{{ store.result.sub_type ?? '—' }}</strong><small>算法路径</small></div>
          </div>

          <!-- 运输问题：分配方案 -->
          <div v-if="isTP" class="solution-panel">
            <div class="solution-bar"><span>运输分配方案</span><div class="solution-chip" v-for="item in allocationEntries()" :key="item.key"><b>{{ item.key }}</b> {{ item.val }}</div></div>
          </div>

          <!-- 指派问题：指派结果 -->
          <div v-else-if="isAP" class="solution-panel">
            <div class="solution-bar"><span>最优指派</span><div class="solution-chip" v-for="item in assignmentList()" :key="item.worker"><b>行{{ item.worker }} → 列{{ item.task }}</b> 成本 {{ valueText(item.cost) }}</div></div>
          </div>

          <!-- 博弈论：策略分布 -->
          <div v-else-if="isGT" class="solution-panel">
            <div class="solution-bar"><span>对策信息</span><div class="solution-chip" v-for="entry in finalEntries()" :key="entry[0]"><b>{{ entry[0] }}</b> {{ valueText(entry[1]) }}</div></div>
          </div>

          <!-- LP/IP：变量解 -->
          <div v-else class="solution-bar"><span>最终解</span><div v-for="([key, val], index) in solutionEntries()" :key="key" class="solution-chip"><b>{{ key }}</b> {{ valueText(val) }}</div></div>

          <div class="trace-layout">
            <nav class="steps">
              <div class="trace-title">迭代记录 <span>{{ store.iterations.length }} 步</span></div>
              <button v-for="(step, index) in store.iterations" :key="index" :class="{ current: store.selectedStep === index }" @click="store.selectedStep = index">
                <span>{{ String(index + 1).padStart(2, '0') }}</span>
                <div><b>{{ step.action || `步骤 ${index + 1}` }}</b><small>{{ step.state_matrix?.type === 'simplex_tableau' ? `第 ${step.state_matrix.phase} 阶段` : (step.state_matrix?.type ?? '状态快照') }}</small></div>
                <ChevronRight :size="15" />
              </button>
            </nav>
            <article class="trace-view">
              <div class="trace-view-head">
                <div><span>第 {{ String(store.selectedStep + 1).padStart(2, '0') }} 步</span><h3>{{ current?.action || '状态快照' }}</h3></div>
                <span class="type-tag">类型：{{ current?.state_matrix?.type ?? '迭代' }}</span>
              </div>
              <SimplexTableau v-if="current?.state_matrix?.type === 'simplex_tableau'" :tableau="current.state_matrix" />
              <pre v-else-if="current?.state_matrix && Object.keys(current.state_matrix).length" class="raw-state">{{ JSON.stringify(current.state_matrix, null, 2) }}</pre>
              <div v-if="calculationLines().length" class="calculation"><p v-for="(line, i) in calculationLines()" :key="i">{{ line }}</p></div>
            </article>
          </div>
        </template>
      </section>
    </div>
  </main>
</template>
