/// <reference types="vite/client" />
import { defineStore } from 'pinia';
import { computed, ref } from 'vue';
const defaults = { c: '3, 5', A: '1, 0\n0, 1\n3, 2', b: '4, 3, 12', constraint_types: '<=, <=, <=' };
export const useSolverStore = defineStore('solver', () => {
    const problemType = ref('LP');
    const objective = ref('max');
    const form = ref({ ...defaults });
    const loading = ref(false);
    const error = ref('');
    const result = ref(null);
    const selectedStep = ref(0);
    const iterations = computed(() => result.value?.iterations ?? []);
    function reset() { form.value = { ...defaults }; result.value = null; error.value = ''; }
    function parseList(value) { return value.split(',').map((x) => Number(x.trim())).filter((x) => Number.isFinite(x)); }
    function parseMatrix(value) { return value.split('\n').map((row) => row.split(',').map((x) => Number(x.trim())).filter((x) => Number.isFinite(x))).filter((row) => row.length); }
    async function solve() {
        loading.value = true;
        error.value = '';
        result.value = null;
        selectedStep.value = 0;
        try {
            const A = parseMatrix(form.value.A);
            const c = parseList(form.value.c);
            const b = parseList(form.value.b);
            const constraint_types = form.value.constraint_types.split(',').map((x) => x.trim()).filter(Boolean);
            const response = await fetch(`${import.meta.env.VITE_API_BASE ?? ''}/api/solve`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ problem_type: problemType.value, payload: { objective: objective.value, c, A, b, constraint_types } }) });
            const data = await response.json();
            if (!response.ok)
                throw new Error(data.detail?.[0]?.msg ?? data.error_message ?? '求解请求失败');
            result.value = data;
        }
        catch (err) {
            error.value = err instanceof Error ? err.message : '网络请求失败，请检查 API 服务';
        }
        finally {
            loading.value = false;
        }
    }
    return { problemType, objective, form, loading, error, result, iterations, selectedStep, reset, solve };
});
