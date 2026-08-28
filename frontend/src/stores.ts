/// <reference types="vite/client" />
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

export type ProblemType = 'LP' | 'IP' | 'TP' | 'AP' | 'GT'
export interface SolverResponse { status: string; problem_type?: string; sub_type?: string; objective?: { sense?: string; value?: { display?: string; decimal?: number } | string | number }; solution?: Record<string, unknown>; iterations?: Iteration[]; diagnostics?: { elapsed_ms?: number; total_steps?: number; error_message?: string | null }; final_result?: Record<string, unknown>; error_message?: string | null }
export interface Iteration { step?: number; action?: string; calculation?: string; state_matrix?: Record<string, any> }

const defaults = { c: '3, 5', A: '1, 0\n0, 1\n3, 2', b: '4, 3, 12', constraint_types: '<=, <=, <=', integer_vars: 'x1, x2' }
export const useSolverStore = defineStore('solver', () => {
  const problemType = ref<ProblemType>('LP'); const objective = ref<'max' | 'min'>('max'); const form = ref({ ...defaults }); const loading = ref(false); const error = ref(''); const result = ref<SolverResponse | null>(null); const selectedStep = ref(0)
  const iterations = computed(() => result.value?.iterations ?? [])
  function reset() { form.value = { ...defaults }; result.value = null; error.value = '' }
  function parseList(value: string, field: string) {
    const tokens = value.split(',').map((x) => x.trim())
    if (tokens.some((token) => !token || !Number.isFinite(Number(token)))) throw new Error(`${field} 包含无效数值`)
    return tokens.map(Number)
  }
  function parseMatrix(value: string) {
    const rows = value.split('\n').map((line) => parseList(line, '约束矩阵'))
    const width = rows[0]?.length ?? 0
    if (!width || rows.some((row) => row.length !== width)) throw new Error('约束矩阵各行列数必须一致')
    return rows
  }
  async function solve() {
    loading.value = true; error.value = ''; result.value = null; selectedStep.value = 0
    try {
      const A = parseMatrix(form.value.A); const c = parseList(form.value.c, 'c'); const b = parseList(form.value.b, 'b'); const constraint_types = form.value.constraint_types.split(',').map((x) => x.trim())
      if (c.length !== A[0].length || b.length !== A.length || constraint_types.length !== A.length || constraint_types.some((x) => !['<=', '>=', '='].includes(x))) throw new Error('c、A、b 和约束符号的维度必须匹配')
      const payload: Record<string, unknown> = { objective: objective.value, c, A, b, constraint_types }
      if (problemType.value === 'IP') {
        const integer_vars = form.value.integer_vars.split(',').map((x) => x.trim()).filter(Boolean).map((x) => {
          const match = /^x(\d+)$/i.exec(x)
          if (!match) throw new Error('整数变量必须使用 x1、x2 等名称')
          return Number(match[1]) - 1
        })
        if (integer_vars.some((index) => index < 0 || index >= c.length)) throw new Error('整数变量超出变量范围')
        payload.integer_vars = integer_vars
      }
      const response = await fetch(`${import.meta.env.VITE_API_BASE ?? ''}/api/solve`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ problem_type: problemType.value, payload }) })
      const body = await response.text()
      let data: SolverResponse & { detail?: Array<{ msg?: string }> }
      try { data = body ? JSON.parse(body) : {} as SolverResponse } catch { throw new Error('服务器返回了无效响应') }
      if (!response.ok) throw new Error(data.detail?.[0]?.msg ?? data.error_message ?? '求解请求失败')
      result.value = data
    } catch (err) { error.value = err instanceof Error ? err.message : '网络请求失败，请检查 API 服务' }
    finally { loading.value = false }
  }
  return { problemType, objective, form, loading, error, result, iterations, selectedStep, reset, solve }
})
