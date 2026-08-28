/// <reference types="vite/client" />
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

export type Panel = 'lp_graphical' | 'lp_simplex' | 'ip' | 'tp' | 'ap' | 'gt'
export type ProblemType = 'LP' | 'IP' | 'TP' | 'AP' | 'GT'
export type LpMethod = 'graphical' | 'simplex'

export interface SolverResponse { status: string; problem_type?: string; sub_type?: string; objective?: { sense?: string; value?: { display?: string; decimal?: number } | string | number }; solution?: Record<string, unknown>; iterations?: Iteration[]; diagnostics?: { elapsed_ms?: number; total_steps?: number; error_message?: string | null }; final_result?: Record<string, any>; error_message?: string | null }
export interface Iteration { step?: number; action?: string; calculation?: string | string[]; state_matrix?: Record<string, any> }

interface FormState { c: string; A: string; b: string; constraint_types: string; integer_vars: string; variable_names: string; supply: string; demand: string; cost: string; cost_matrix: string; payoff_matrix: string }

const BASE_LP: Partial<FormState> = { c: '3, 5', A: '1, 0\n0, 1\n3, 2', b: '4, 3, 12', constraint_types: '<=, <=, <=', variable_names: 'x1, x2' }
const BASE_IP: Partial<FormState> = { c: '3, 5', A: '1, 0\n0, 1\n3, 2', b: '4, 3, 12', constraint_types: '<=, <=, <=', variable_names: 'x1, x2', integer_vars: 'x1, x2' }
const BASE_TP: Partial<FormState> = { supply: '30, 40, 50', demand: '25, 35, 40, 20', cost: '2, 3, 11, 7\n1, 0, 6, 1\n5, 8, 15, 9' }
const BASE_AP: Partial<FormState> = { cost_matrix: '9, 2, 7, 8\n6, 4, 3, 7\n5, 8, 1, 8\n7, 6, 9, 4' }
const BASE_GT: Partial<FormState> = { payoff_matrix: '3, -1\n-2, 4' }

interface PanelConfig { problemType: ProblemType; lpMethod?: LpMethod; defaults: Partial<FormState>; title: string }
const PANELS: Record<Panel, PanelConfig> = {
  lp_graphical: { problemType: 'LP', lpMethod: 'graphical', defaults: BASE_LP, title: '线性规划（图解法）' },
  lp_simplex: { problemType: 'LP', lpMethod: 'simplex', defaults: BASE_LP, title: '线性规划（单纯形法）' },
  ip: { problemType: 'IP', defaults: BASE_IP, title: '整数规划' },
  tp: { problemType: 'TP', defaults: BASE_TP, title: '运输问题' },
  ap: { problemType: 'AP', defaults: BASE_AP, title: '指派问题' },
  gt: { problemType: 'GT', defaults: BASE_GT, title: '博弈论' },
}

const EMAIL_EMPTY = { c: '', A: '', b: '', constraint_types: '', integer_vars: '', variable_names: '', supply: '', demand: '', cost: '', cost_matrix: '', payoff_matrix: '' }

function toNumber(token: string): number {
  const t = token.trim()
  const fraction = /^-?\d+\/\d+$/.test(t)
  if (fraction) { const [n, d] = t.split('/').map(Number); return d === 0 ? NaN : n / d }
  return Number(t)
}

export const useSolverStore = defineStore('solver', () => {
  const panel = ref<Panel>('lp_simplex')
  const config = computed(() => PANELS[panel.value])
  const problemType = computed<ProblemType>(() => config.value.problemType)
  const objective = ref<'max' | 'min'>('max')
  const form = ref<FormState>({ ...EMAIL_EMPTY, ...PANELS.lp_simplex.defaults })
  const loading = ref(false)
  const error = ref('')
  const result = ref<SolverResponse | null>(null)
  const selectedStep = ref(0)
  const iterations = computed(() => result.value?.iterations ?? [])

  function selectPanel(next: Panel) {
    panel.value = next
    form.value = { ...EMAIL_EMPTY, ...PANELS[next].defaults }
    objective.value = PANELS[next].problemType === 'AP' ? 'min' : 'max'
    error.value = ''
    loading.value = false
  }

  function reset() {
    error.value = ''
    loading.value = false
    const keep = result.value && selectedStep.value
    if (!keep) result.value = null
  }

  function parseList(value: string, field: string): string[] {
    const tokens = value.split(',').map((x) => x.trim()).filter(Boolean)
    if (!tokens.length || tokens.some((token) => !Number.isFinite(toNumber(token)))) throw new Error(`${field} 包含无效数值`)
    return tokens
  }

  function parseMatrix(value: string, field: string): string[][] {
    const rows = value.split('\n').map((line) => line.split(',').map((x) => x.trim()).filter(Boolean)).filter((row) => row.length)
    const width = rows[0]?.length ?? 0
    if (!width || rows.some((row) => row.length !== width)) throw new Error(`${field} 各行列数必须一致`)
    if (rows.some((row) => row.some((cell) => !Number.isFinite(toNumber(cell))))) throw new Error(`${field} 包含无效数值`)
    return rows
  }

  function parseVariableNames(value: string, count: number): string[] | undefined {
    const tokens = value.split(',').map((x) => x.trim()).filter(Boolean)
    if (!tokens.length) return undefined
    if (tokens.length !== count) throw new Error('变量名数量必须与 c 一致')
    return tokens
  }

  function buildPayload(): Record<string, unknown> {
    const pt = problemType.value
    if (pt === 'LP' || pt === 'IP') {
      const c = parseList(form.value.c, 'c')
      const A = parseMatrix(form.value.A, '约束矩阵')
      const b = parseList(form.value.b, 'b')
      const constraint_types = parseList(form.value.constraint_types, '约束符号')
      if (c.length !== A[0].length || b.length !== A.length || constraint_types.length !== A.length) throw new Error('c、A、b 和约束符号的维度必须匹配')
      if (constraint_types.some((x) => !['<=', '>=', '='].includes(x))) throw new Error('约束符号必须为 <=、>= 或 =')
      const payload: Record<string, unknown> = { objective: objective.value, c, A, b, constraint_types }
      const vn = parseVariableNames(form.value.variable_names, c.length)
      if (vn) payload.variable_names = vn
      if (pt === 'IP') {
        const integer_vars = parseList(form.value.integer_vars.replace(/,/g, ' '), '整数变量').map((x) => {
          const match = /^x(\d+)$/i.exec(x)
          if (!match) throw new Error('整数变量必须使用 x1、x2 等名称')
          return Number(match[1]) - 1
        })
        if (integer_vars.some((index) => index < 0 || index >= c.length)) throw new Error('整数变量超出变量范围')
        payload.integer_vars = integer_vars
      }
      return payload
    }
    if (pt === 'TP') {
      return { supply: parseList(form.value.supply, '产量'), demand: parseList(form.value.demand, '销量'), cost: parseMatrix(form.value.cost, '运价矩阵') }
    }
    if (pt === 'AP') {
      return { objective: objective.value, cost_matrix: parseMatrix(form.value.cost_matrix, '成本矩阵') }
    }
    return { payoff_matrix: parseMatrix(form.value.payoff_matrix, '收益矩阵') }
  }

  async function solve() {
    loading.value = true; error.value = ''; result.value = null; selectedStep.value = 0
    try {
      const payload = buildPayload()
      const request: Record<string, unknown> = { problem_type: problemType.value, payload }
      if (problemType.value === 'LP') request.sub_type = config.value.lpMethod ?? 'simplex'
      const response = await fetch(`${import.meta.env.VITE_API_BASE ?? ''}/api/solve`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(request) })
      const body = await response.text()
      let data: SolverResponse & { detail?: Array<{ msg?: string }> }
      try { data = body ? JSON.parse(body) : {} as SolverResponse } catch { throw new Error('服务器返回了无效响应') }
      if (!response.ok) throw new Error(data.detail?.[0]?.msg ?? data.error_message ?? '求解请求失败')
      result.value = data
    } catch (err) { error.value = err instanceof Error ? err.message : '网络请求失败，请检查 API 服务' }
    finally { loading.value = false }
  }

  return { panel, selectPanel, problemType, config, objective, form, loading, error, result, iterations, selectedStep, reset, solve }
})
