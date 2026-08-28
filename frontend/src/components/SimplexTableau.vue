<script setup lang="ts">
import { computed } from 'vue'
const props = defineProps<{ tableau: Record<string, any> }>()
const names = computed(() => props.tableau.var_names ?? props.tableau.c_j?.map((_: unknown, i: number) => `x${i + 1}`) ?? [])
const basisNames = computed(() => props.tableau.basis_var_names ?? props.tableau.x_b ?? [])
const values = (key: string) => props.tableau[key] ?? []
const pivot = computed(() => props.tableau.pivot ?? null)
const enteringCol = computed(() => pivot.value?.entering_col ?? pivot.value?.pivot_position?.[1] ?? null)
const leavingRow = computed(() => pivot.value?.leaving_row ?? pivot.value?.pivot_position?.[0] ?? null)
const isPivot = (row: number, col: number) => leavingRow.value === row && enteringCol.value === col
function display(value: unknown) { if (value === null || value === undefined || value === '') return '—'; if (typeof value === 'object' && value && 'display' in value) return String((value as any).display); return String(value) }
</script>

<template>
  <section class="tableau-wrap">
    <div class="tableau-meta">
      <span>第 {{ display(tableau.phase) }} 阶段</span>
      <span>z = {{ display(tableau.current_z) }}</span>
      <span v-if="pivot">进基：{{ display(names[enteringCol ?? -1]) }}</span>
    </div>
    <div class="table-scroll">
      <table class="tableau">
        <thead>
          <tr>
            <th class="corner">cᵦ / xᵦ</th>
            <th v-for="(name, index) in names" :key="name" :class="{ entering: enteringCol === index }">
              {{ name }}<small>cⱼ {{ display(values('c_j')[index]) }}</small>
            </th>
            <th class="rhs">b</th>
            <th class="theta">θ</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, rowIndex) in values('matrix_a')" :key="rowIndex" :class="{ leaving: leavingRow === rowIndex }">
            <th class="basis">
              <b>{{ display(values('c_b')[rowIndex]) }}</b>
              <span>{{ display(basisNames[rowIndex]) }}</span>
            </th>
            <td v-for="(value, colIndex) in row" :key="colIndex" :class="{ pivot: isPivot(rowIndex, colIndex), entering: enteringCol === colIndex }">
              {{ display(value) }}
            </td>
            <td class="rhs">{{ display(values('b')[rowIndex]) }}</td>
            <td class="theta">{{ display(values('theta')[rowIndex]) }}</td>
          </tr>
          <tr class="sigma">
            <th>σⱼ</th>
            <td v-for="(value, index) in values('sigma')" :key="index" :class="{ entering: enteringCol === index }">{{ display(value) }}</td>
            <td class="rhs">—</td>
            <td class="theta">—</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
