<script setup lang="ts">
import { computed } from 'vue'
import { RotateCcw, Play, LoaderCircle, Zap, Activity, CheckCircle2, AlertTriangle, ChevronRight } from 'lucide-vue-next'
import SimplexTableau from './components/SimplexTableau.vue'
import { useSolverStore } from './stores'
const store = useSolverStore()
const current = computed(() => store.iterations[store.selectedStep])
function valueText(value: any) { if (value === null || value === undefined) return '—'; if (typeof value === 'object' && value.display) return value.display; return String(value) }
function solutionEntries() { return Object.entries(store.result?.solution ?? {}) }
</script>

<template>
  <main class="shell">
    <header class="topbar"><div class="brand"><div class="brand-mark"><Zap :size="18" /></div><div><strong>OR / ENGINE</strong><span>运筹学推演工作台</span></div></div><div class="header-status"><i></i> API 正常 <span>v0.1</span></div></header>
    <div class="workspace">
      <aside class="sidebar"><div class="eyebrow">模型定义 <span>01</span></div><h1>构建你的<br /><em>优化问题。</em></h1><p class="lede">配置精确的优化模型，跟随引擎回放每一步计算。</p>
        <div class="field-label">问题类型</div><div class="segmented"><button :class="{ active: store.problemType === 'LP' }" @click="store.problemType = 'LP'">线性规划 <b>LP</b></button><button :class="{ active: store.problemType === 'IP' }" @click="store.problemType = 'IP'">整数规划 <b>IP</b></button></div>
        <div class="field-label objective-label">目标函数 <span>方向</span></div><div class="objective"><button :class="{ selected: store.objective === 'max' }" @click="store.objective = 'max'">最大化</button><button :class="{ selected: store.objective === 'min' }" @click="store.objective = 'min'">最小化</button></div>
        <label class="field-label">目标系数 <span>c</span><input v-model="store.form.c" spellcheck="false" /></label><label class="field-label">约束矩阵 <span>A · 每行一组</span><textarea v-model="store.form.A" rows="4" spellcheck="false" /></label><label class="field-label">右端项 <span>b</span><input v-model="store.form.b" spellcheck="false" /></label><label class="field-label">约束符号 <span>逗号分隔</span><input v-model="store.form.constraint_types" spellcheck="false" /></label><label v-if="store.problemType === 'IP'" class="field-label">整数变量 <span>x1, x2</span><input v-model="store.form.integer_vars" spellcheck="false" /></label>
        <div class="actions"><button class="run" :disabled="store.loading" @click="store.solve"><LoaderCircle v-if="store.loading" class="spin" :size="17" /><Play v-else :size="17" /> {{ store.loading ? '求解中' : '开始求解' }}</button><button class="reset" title="重置模型" @click="store.reset"><RotateCcw :size="17" /></button></div><p v-if="store.error" class="error"><AlertTriangle :size="15" /> {{ store.error }}</p>
      </aside>
      <section class="results"><div class="result-head"><div><div class="eyebrow">计算轨迹 <span>02</span></div><h2>{{ store.result ? '求解完成' : '等待模型输入' }}</h2></div><div v-if="store.result" class="status-pill" :class="store.result.status === 'OPTIMAL' ? 'good' : 'warn'"><CheckCircle2 :size="15" /> {{ store.result.status }}</div></div>
        <div v-if="!store.result" class="empty"><div class="empty-grid"></div><Activity :size="42" stroke-width="1.2" /><strong>准备就绪</strong><span>在左侧输入模型，开始查看计算轨迹。</span></div>
        <template v-else><div class="metrics"><div><span>目标函数值</span><strong>{{ valueText(store.result.objective?.value) }}</strong><small>{{ store.objective === 'max' ? '最大化目标' : '最小化目标' }}</small></div><div><span>迭代次数</span><strong>{{ store.result.diagnostics?.total_steps ?? store.iterations.length }}</strong><small>计算耗时 {{ store.result.diagnostics?.elapsed_ms ?? 0 }} 毫秒</small></div><div><span>变量数量</span><strong>{{ solutionEntries().length || '—' }}</strong><small>决策变量</small></div><div><span>求解方法</span><strong class="subtype">{{ store.result.sub_type ?? '—' }}</strong><small>算法路径</small></div></div><div class="solution-bar"><span>最终解</span><div v-for="([key, val], index) in solutionEntries()" :key="key" class="solution-chip"><b>{{ key }}</b> {{ valueText(val) }}</div></div><div class="trace-layout"><nav class="steps"><div class="trace-title">迭代记录 <span>{{ store.iterations.length }} 步</span></div><button v-for="(step, index) in store.iterations" :key="index" :class="{ current: store.selectedStep === index }" @click="store.selectedStep = index"><span>{{ String(index + 1).padStart(2, '0') }}</span><div><b>{{ step.action || `Tableau ${index + 1}` }}</b><small>{{ step.state_matrix?.type === 'simplex_tableau' ? `第 ${step.state_matrix.phase} 阶段` : '状态快照' }}</small></div><ChevronRight :size="15" /></button></nav><article class="trace-view"><div class="trace-view-head"><div><span>第 {{ String(store.selectedStep + 1).padStart(2, '0') }} 步</span><h3>{{ current?.action || '状态快照' }}</h3></div><span class="type-tag">类型：{{ current?.state_matrix?.type ?? '迭代' }}</span></div><SimplexTableau v-if="current?.state_matrix?.type === 'simplex_tableau'" :tableau="current.state_matrix" /><pre v-else class="raw-state">{{ JSON.stringify(current?.state_matrix, null, 2) }}</pre><p v-if="current?.calculation" class="calculation">{{ current.calculation }}</p></article></div></template>
      </section>
    </div>
  </main>
</template>
