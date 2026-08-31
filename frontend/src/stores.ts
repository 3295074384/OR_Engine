/// <reference types="vite/client" />
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

export type Panel = 'lp_graphical' | 'lp_simplex' | 'ip' | 'tp' | 'ap' | 'gt'
export type ProblemType = 'LP' | 'IP' | 'TP' | 'AP' | 'GT'
export type LpMethod = 'graphical' | 'simplex'
export type IpMethod = 'branch_and_bound' | 'cutting_plane'
export type ThemeBackground = 'cyber' | 'deep_ocean' | 'aurora' | 'pure_dark'

export interface RationalNumber {
  display: string
  numerator: number
  denominator: number
  decimal: number
}

export interface SolverResponse {
  status: string
  problem_type?: string
  sub_type?: string
  objective?: {
    sense?: string
    value?: RationalNumber | string | number
  }
  solution?: Record<string, unknown>
  iterations?: Iteration[]
  diagnostics?: {
    elapsed_ms?: number
    total_steps?: number
    error_message?: string | null
  }
  final_result?: Record<string, any>
  sensitivity?: Record<string, any>
  error_message?: string | null
}

export interface Iteration {
  step?: number
  action?: string
  calculation?: string | string[]
  state_matrix?: Record<string, any>
  loop?: number[][]
  theta?: RationalNumber | string
  phase?: number
  description?: string
  node_id?: number
  parent_id?: number
  z_lp?: string
  branch_var?: string
  branch_val?: string
  branch_floor?: string
  branch_ceil?: string
  integer_solution?: boolean
  incumbent_z?: string
  pruned?: boolean
  prune_reason?: string
  gomory_cut?: string
}

export interface ConstraintRow {
  coeffs: string[]
  sign: string
  rhs: string
}

export interface ModelForm {
  nVars: number
  c: string[]
  integer: boolean[]
  constraints: ConstraintRow[]
  supply: string[]
  demand: string[]
  cost: string[][]
  cost_matrix: string[][]
  payoff_matrix: string[][]
}

function makeRows(nVars: number, count: number): ConstraintRow[] {
  return Array.from({ length: count }, () => ({
    coeffs: Array.from({ length: nVars }, () => '1'),
    sign: '<=',
    rhs: '10'
  }))
}

function makeMatrix(rows: number, cols: number): string[][] {
  return Array.from({ length: rows }, () => Array.from({ length: cols }, () => '1'))
}

function linearModel(nVars: number): ModelForm {
  return {
    nVars,
    c: Array.from({ length: nVars }, (_, i) => String(i === 0 ? 3 : 5)),
    integer: Array.from({ length: nVars }, () => true),
    constraints: makeRows(nVars, 2),
    supply: ['30', '40', '50'],
    demand: ['25', '35', '40', '20'],
    cost: makeMatrix(3, 4),
    cost_matrix: makeMatrix(4, 4),
    payoff_matrix: makeMatrix(2, 2),
  }
}

interface PanelConfig {
  problemType: ProblemType
  lpMethod?: LpMethod
  model: ModelForm
  title: string
}

const PANELS: Record<Panel, PanelConfig> = {
  lp_graphical: { problemType: 'LP', lpMethod: 'graphical', model: linearModel(2), title: '线性规划（图解法）' },
  lp_simplex: { problemType: 'LP', lpMethod: 'simplex', model: linearModel(2), title: '线性规划（单纯形法）' },
  ip: { problemType: 'IP', model: linearModel(2), title: '整数规划（IP）' },
  tp: { problemType: 'TP', model: linearModel(3), title: '运输问题（产销平衡）' },
  ap: { problemType: 'AP', model: linearModel(4), title: '指派问题（匈牙利法）' },
  gt: { problemType: 'GT', model: linearModel(2), title: '矩阵博弈论' },
}

function cloneForm(m: ModelForm): ModelForm {
  return {
    nVars: m.nVars,
    c: [...m.c],
    integer: [...m.integer],
    constraints: m.constraints.map((r) => ({ coeffs: [...r.coeffs], sign: r.sign, rhs: r.rhs })),
    supply: [...m.supply],
    demand: [...m.demand],
    cost: m.cost.map((r) => [...r]),
    cost_matrix: m.cost_matrix.map((r) => [...r]),
    payoff_matrix: m.payoff_matrix.map((r) => [...r]),
  }
}

function toNumber(token: string): number {
  const t = token.trim()
  const fraction = /^-?\d+\/\d+$/.test(t)
  if (fraction) {
    const [n, d] = t.split('/').map(Number)
    return d === 0 ? NaN : n / d
  }
  return Number(t)
}

function validList(tokens: string[]): boolean {
  return tokens.length > 0 && tokens.every((token) => Number.isFinite(toNumber(token)))
}

const apiBase = import.meta.env.VITE_API_BASE ?? ''

export const useSolverStore = defineStore('solver', () => {
  const panel = ref<Panel>('lp_simplex')
  const config = computed(() => PANELS[panel.value])
  const problemType = computed<ProblemType>(() => config.value.problemType)
  const objective = ref<'max' | 'min'>('max')
  const ipMethod = ref<IpMethod>('branch_and_bound')
  const form = ref<ModelForm>(cloneForm(PANELS.lp_simplex.model))

  const currentTheme = ref<ThemeBackground>('aurora')
  const enableGlassBlur = ref(true)

  const loading = ref(false)
  const error = ref('')
  const result = ref<SolverResponse | null>(null)
  const selectedStep = ref(0)
  const iterations = computed(() => result.value?.iterations ?? [])

  function selectPanel(next: Panel) {
    panel.value = next
    form.value = cloneForm(PANELS[next].model)
    objective.value = PANELS[next].problemType === 'AP' ? 'min' : 'max'
    error.value = ''
    loading.value = false
    result.value = null
    selectedStep.value = 0
  }

  function resetForm() {
    form.value = cloneForm(PANELS[panel.value].model)
  }

  function setNVars(n: number) {
    const count = Math.max(2, Math.min(20, Math.floor(n) || 2))
    form.value.nVars = count
    form.value.c = Array.from({ length: count }, (_, i) => form.value.c[i] ?? '1')
    form.value.integer = Array.from({ length: count }, (_, i) => form.value.integer[i] ?? true)
    form.value.constraints.forEach((row) => {
      row.coeffs = Array.from({ length: count }, (_, i) => row.coeffs[i] ?? '1')
    })
  }

  function addConstraint() {
    form.value.constraints.push({
      coeffs: Array.from({ length: form.value.nVars }, () => '1'),
      sign: '<=',
      rhs: '10'
    })
  }

  function removeConstraint(i: number) {
    if (form.value.constraints.length > 1) {
      form.value.constraints.splice(i, 1)
    }
  }

  function addRow(key: 'cost' | 'cost_matrix' | 'payoff_matrix') {
    const cols = form.value[key][0]?.length ?? form.value[key].length
    form.value[key].push(Array.from({ length: cols }, () => '1'))
  }

  function removeRow(key: 'cost' | 'cost_matrix' | 'payoff_matrix', i: number) {
    if (form.value[key].length > 1) form.value[key].splice(i, 1)
  }

  function addCol(key: 'cost' | 'cost_matrix' | 'payoff_matrix') {
    form.value[key].forEach((row) => row.push('1'))
  }

  function removeCol(key: 'cost' | 'cost_matrix' | 'payoff_matrix', i: number) {
    if ((form.value[key][0]?.length ?? 0) > 1) {
      form.value[key].forEach((row) => row.splice(i, 1))
    }
  }

  function parseList(tokens: string[], field: string): string[] {
    if (!validList(tokens)) throw new Error(`${field} 包含无效数值`)
    return tokens.map((t) => t.trim())
  }

  function parseMatrix(rows: string[][], field: string): string[][] {
    const width = rows[0]?.length ?? 0
    if (!width || rows.some((row) => row.length !== width)) throw new Error(`${field} 各行列数必须一致`)
    if (rows.some((row) => row.some((cell) => !Number.isFinite(toNumber(cell))))) throw new Error(`${field} 包含无效数值`)
    return rows.map((row) => row.map((cell) => cell.trim()))
  }

  function buildPayload(): Record<string, unknown> {
    const pt = problemType.value
    if (pt === 'LP' || pt === 'IP') {
      const c = parseList(form.value.c, 'c')
      const b = form.value.constraints.map((row) => parseList([row.rhs], 'b')[0])
      const constraint_types = form.value.constraints.map((row) => row.sign)
      const A = form.value.constraints.map((row) => parseList(row.coeffs, '约束矩阵'))
      if (c.length !== A[0].length || constraint_types.some((x) => !['<=', '>=', '='].includes(x))) {
        throw new Error('c、A、b 和约束符号的维度必须匹配')
      }
      const payload: Record<string, unknown> = {
        objective: objective.value,
        c,
        A,
        b,
        constraint_types,
        signs: constraint_types,
        variable_names: form.value.c.map((_, i) => `x${i + 1}`),
      }
      if (pt === 'IP') {
        const integer_indices = form.value.integer.map((flag, i) => (flag ? i : -1)).filter((i) => i >= 0)
        if (integer_indices.length === 0) throw new Error('整数规划至少需要勾选一个整数变量')
        payload.integer_vars = integer_indices
        payload.integer_indices = integer_indices
      }
      return payload
    }
    if (pt === 'TP') {
      return {
        supply: parseList(form.value.supply, '产量'),
        demand: parseList(form.value.demand, '销量'),
        cost: parseMatrix(form.value.cost, '运价矩阵'),
      }
    }
    if (pt === 'AP') {
      return {
        objective: objective.value,
        cost_matrix: parseMatrix(form.value.cost_matrix, '成本矩阵')
      }
    }
    return {
      payoff_matrix: parseMatrix(form.value.payoff_matrix, '收益矩阵')
    }
  }

  async function solve() {
    loading.value = true
    error.value = ''
    result.value = null
    selectedStep.value = 0
    try {
      const payload = buildPayload()
      const options: Record<string, unknown> = {}

      const request: Record<string, unknown> = {
        problem_type: problemType.value,
        payload,
        options
      }

      if (problemType.value === 'IP') {
        const method = ipMethod.value === 'cutting_plane' ? 'cutting_plane' : 'branch_bound'
        options.integer_method = method
      } else if (problemType.value === 'LP') {
        request.sub_type = config.value.lpMethod ?? 'simplex'
      }

      const response = await fetch(`${apiBase}/api/solve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request)
      })
      const body = await response.text()
      let data: SolverResponse & { detail?: Array<{ msg?: string }> }
      try {
        data = body ? JSON.parse(body) : ({} as SolverResponse)
      } catch {
        throw new Error('服务器返回了非法的 JSON 响应')
      }
      if (!response.ok) {
        throw new Error(data.detail?.[0]?.msg ?? data.error_message ?? '求解请求失败')
      }
      result.value = data
      if (data.iterations?.length) {
        selectedStep.value = data.iterations.length - 1
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '网络请求失败，请检查 API 服务'
    } finally {
      loading.value = false
    }
  }

  return {
    panel,
    selectPanel,
    problemType,
    config,
    objective,
    ipMethod,
    form,
    currentTheme,
    enableGlassBlur,
    loading,
    error,
    result,
    iterations,
    selectedStep,
    resetForm,
    setNVars,
    addConstraint,
    removeConstraint,
    addRow,
    removeRow,
    addCol,
    removeCol,
    solve
  }
})