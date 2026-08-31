<template>
  <div class="p-6 rounded-2xl border border-white/10 bg-slate-900/40 backdrop-blur-xl shadow-2xl space-y-6">
    <div class="flex items-center justify-between border-b border-white/10 pb-4">
      <div class="flex items-center space-x-2">
        <span class="w-3 h-3 rounded-full bg-violet-400 animate-pulse"></span>
        <h3 class="font-bold text-sm text-slate-100">博弈论均衡策略决策 (Nash Equilibrium)</h3>
      </div>
      <div class="text-xs font-mono font-bold text-violet-300">
        博弈值 Value (v) = {{ result.final_result?.game_value ?? result.objective?.value?.display ?? '-' }}
      </div>
    </div>

    <div v-if="result.final_result?.type === 'pure_strategy'" class="p-4 rounded-xl bg-slate-950/60 border border-white/10 space-y-2">
      <div class="text-xs font-bold text-amber-400">🎯 存在纯策略鞍点 (Saddle Point)</div>
      <div class="text-xs text-slate-300">
        局中人 1 策略：<strong class="text-indigo-400">{{ result.final_result.player1_strategy }}</strong>
      </div>
      <div class="text-xs text-slate-300">
        局中人 2 策略：<strong class="text-emerald-400">{{ result.final_result.player2_strategy }}</strong>
      </div>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div class="p-4 rounded-xl bg-slate-950/60 border border-white/10 space-y-3">
        <div class="text-xs font-bold text-indigo-300 flex items-center justify-between">
          <span>局中人 1 最优混合策略 (P)</span>
        </div>
        <div v-for="(prob, name) in formatStrategy(result.final_result?.player1_strategy)" :key="name" class="space-y-1">
          <div class="flex items-center justify-between text-xs text-slate-300">
            <span>{{ name }}</span>
            <span class="font-mono font-bold text-indigo-400">{{ prob }}</span>
          </div>
          <div class="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
            <div class="h-full bg-indigo-500 rounded-full transition-all duration-500" :style="{ width: calcPercent(prob) }"></div>
          </div>
        </div>
      </div>

      <div class="p-4 rounded-xl bg-slate-950/60 border border-white/10 space-y-3">
        <div class="text-xs font-bold text-emerald-300 flex items-center justify-between">
          <span>局中人 2 最优混合策略 (Q)</span>
        </div>
        <div v-for="(prob, name) in formatStrategy(result.final_result?.player2_strategy)" :key="name" class="space-y-1">
          <div class="flex items-center justify-between text-xs text-slate-300">
            <span>{{ name }}</span>
            <span class="font-mono font-bold text-emerald-400">{{ prob }}</span>
          </div>
          <div class="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
            <div class="h-full bg-emerald-500 rounded-full transition-all duration-500" :style="{ width: calcPercent(prob) }"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{ result: any }>()

function formatStrategy(strat: any): Record<string, string> {
  if (!strat) return {}
  if (typeof strat === 'string') return { '策略': strat }
  return strat
}

function calcPercent(probStr: string): string {
  if (!probStr) return '0%'
  if (probStr.includes('/')) {
    const [n, d] = probStr.split('/').map(Number)
    return `${Math.round((n / d) * 100)}%`
  }
  return `${Math.round(Number(probStr) * 100)}%`
}
</script>