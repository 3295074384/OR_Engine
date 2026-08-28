<script setup lang="ts">
import { Plus, Minus } from 'lucide-vue-next'
import type { ModelForm } from '../stores'

const props = defineProps<{ model: ModelForm; isIP: boolean }>()
const emit = defineEmits<{ setN: [number]; addConstraint: []; removeConstraint: [number] }>()

function clampN(value: string) { emit('setN', Number(value) || 2) }
</script>

<template>
  <div class="lp-editor">
    <div class="field-label">决策变量数量 <span>N</span></div>
    <div class="nvar-stepper">
      <button class="step-btn" @click="emit('setN', model.nVars - 1)"><Minus :size="14" /></button>
      <input :value="model.nVars" type="number" min="2" @change="clampN(($event.target as HTMLInputElement).value)" />
      <button class="step-btn" @click="emit('setN', model.nVars + 1)"><Plus :size="14" /></button>
    </div>

    <div class="block-label">1. 目标函数系数（c 向量）</div>
    <div class="grid-scroll">
      <table class="grid-table">
        <thead>
          <tr><th class="grid-corner">cⱼ</th><th v-for="(_, i) in model.nVars" :key="i">x{{ i + 1 }}</th></tr>
        </thead>
        <tbody>
          <tr>
            <th class="grid-index">系数</th>
            <td v-for="(_, i) in model.nVars" :key="i"><input v-model="model.c[i]" spellcheck="false" /></td>
          </tr>
        </tbody>
      </table>
    </div>

    <template v-if="isIP">
      <div class="block-label">整数变量</div>
      <div class="grid-scroll">
        <table class="grid-table">
          <thead>
            <tr><th class="grid-corner">取整</th><th v-for="(_, i) in model.nVars" :key="i">x{{ i + 1 }}</th></tr>
          </thead>
          <tbody>
            <tr>
              <th class="grid-index">整数</th>
              <td v-for="(_, i) in model.nVars" :key="i" class="check-cell"><input type="checkbox" v-model="model.integer[i]" /></td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <div class="block-label">2. 约束条件组</div>
    <div class="grid-scroll">
      <table class="grid-table">
        <thead>
          <tr>
            <th class="grid-corner">约束</th>
            <th v-for="(_, i) in model.nVars" :key="i">x{{ i + 1 }}</th>
            <th class="grid-sign">符号</th>
            <th class="grid-rhs">rhs</th>
            <th class="grid-del"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, r) in model.constraints" :key="r">
            <th class="grid-index">C{{ r + 1 }}</th>
            <td v-for="(_, c) in model.nVars" :key="c"><input v-model="row.coeffs[c]" spellcheck="false" /></td>
            <td class="sign-cell">
              <select v-model="row.sign">
                <option value="<=">&lt;=</option>
                <option value=">=">&gt;=</option>
                <option value="=">=</option>
              </select>
            </td>
            <td class="rhs-cell"><input v-model="row.rhs" spellcheck="false" /></td>
            <td class="grid-del"><button class="th-del" title="删除此约束" @click="emit('removeConstraint', r)"><Minus :size="11" /></button></td>
          </tr>
        </tbody>
      </table>
    </div>
    <button class="add-row-btn" @click="emit('addConstraint')"><Plus :size="13" /> 添加约束</button>
  </div>
</template>
