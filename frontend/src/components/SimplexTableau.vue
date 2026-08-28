<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ tableau: Record<string, any> }>()
const names = computed(() => props.tableau.var_names ?? [])
const basisNames = computed(() => props.tableau.x_b ?? props.tableau.basis_var_names ?? [])
const values = (key: string) => props.tableau[key] ?? []
const pivot = computed(() => props.tableau.pivot ?? null)
const enteringCol = computed(() => pivot.value?.entering_col ?? pivot.value?.pivot_position?.[1] ?? null)
const leavingRow = computed(() => pivot.value?.leaving_row ?? pivot.value?.pivot_position?.[0] ?? null)
const isPivot = (row: number, col: number) => props.tableau.snapshot_stage === 'before_pivot' && leavingRow.value === row && enteringCol.value === col
function display(value: unknown) {
  if (value === null || value === undefined || value === '') return '—'
  if (typeof value === 'object' && value && 'display' in value) return String((value as any).display)
  return String(value)
}
</script>

<template>
  <section class="tableau-wrap">
    <div class="tableau-meta">
      <span>第 {{ display(tableau.phase) }} 阶段</span>
      <span>当前 Z = {{ display(tableau.current_z ?? tableau.z) }}</span>
      <span v-if="pivot">下一步：{{ display(names[enteringCol ?? -1]) }} 进基</span>
      <span v-if="tableau.is_optimal">已达到最优</span>
      <span v-else-if="tableau.is_unbounded">目标无界</span>
    </div>
    <div class="table-scroll">
      <table class="tableau">
        <thead>
          <tr>
            <th class="cb">cᵦ</th>
            <th class="xb">xᵦ</th>
            <th v-for="(name, index) in names" :key="name" :class="{ entering: enteringCol === index }">
              {{ name }}<small>cⱼ = {{ display(values('c_j')[index]) }}</small>
            </th>
            <th class="rhs">b</th>
            <th class="theta">θ</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, rowIndex) in values('matrix_a')" :key="rowIndex" :class="{ leaving: leavingRow === rowIndex }">
            <td class="cb">{{ display(values('c_b')[rowIndex]) }}</td>
            <th class="xb">{{ display(basisNames[rowIndex]) }}</th>
            <td v-for="(value, colIndex) in row" :key="colIndex" :class="{ pivot: isPivot(rowIndex, colIndex), entering: enteringCol === colIndex }">
              {{ display(value) }}
            </td>
            <td class="rhs">{{ display(values('b')[rowIndex]) }}</td>
            <td class="theta">{{ display(values('theta')[rowIndex]) }}</td>
          </tr>
          <tr class="z-row">
            <th colspan="2">Zⱼ</th>
            <td v-for="(value, index) in values('z_j')" :key="index" :class="{ entering: enteringCol === index }">{{ display(value) }}</td>
            <td class="rhs">Z = {{ display(tableau.current_z ?? tableau.z) }}</td>
            <td class="theta">—</td>
          </tr>
          <tr class="sigma">
            <th colspan="2">σⱼ = cⱼ − Zⱼ</th>
            <td v-for="(value, index) in values('sigma')" :key="index" :class="{ entering: enteringCol === index }">{{ display(value) }}</td>
            <td class="rhs">—</td>
            <td class="theta">—</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
