<script setup lang="ts">
import { computed } from 'vue'
import { Plus, Minus } from 'lucide-vue-next'

const props = defineProps<{ rows: string[][]; label?: string }>()
const emit = defineEmits<{ addRow: []; removeRow: [number]; addCol: []; removeCol: [number] }>()

const columns = computed(() => props.rows[0]?.length ?? 0)
</script>

<template>
  <div class="grid-editor">
    <div class="grid-tools">
      <span class="grid-hint">直接修改数值。可动态添加或删除行/列。</span>
      <div class="grid-actions">
        <button class="grid-btn" title="添加一行" @click="emit('addRow')"><Plus :size="13" /> 行</button>
        <button class="grid-btn" title="添加一列" @click="emit('addCol')"><Plus :size="13" /> 列</button>
      </div>
    </div>
    <div class="grid-scroll">
      <table class="grid-table">
        <thead>
          <tr>
            <th class="grid-corner">{{ label ?? '矩阵' }}</th>
            <th v-for="(_, c) in columns" :key="c">
              列 {{ c + 1 }}
              <button class="th-del" title="删除此列" @click="emit('removeCol', c)"><Minus :size="10" /></button>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, r) in rows" :key="r">
            <th class="grid-index">
              行 {{ r + 1 }}
              <button class="th-del" title="删除此行" @click="emit('removeRow', r)"><Minus :size="10" /></button>
            </th>
            <td v-for="(cell, c) in row" :key="c"><input v-model="rows[r][c]" spellcheck="false" /></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
