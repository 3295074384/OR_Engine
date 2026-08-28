import { computed } from 'vue';
const props = defineProps();
const names = computed(() => props.tableau.var_names ?? props.tableau.c_j?.map((_, i) => `x${i + 1}`) ?? []);
const basisNames = computed(() => props.tableau.basis_var_names ?? props.tableau.x_b ?? []);
const values = (key) => props.tableau[key] ?? [];
const pivot = computed(() => props.tableau.pivot ?? null);
const enteringCol = computed(() => pivot.value?.entering_col ?? pivot.value?.pivot_position?.[1] ?? null);
const leavingRow = computed(() => pivot.value?.leaving_row ?? pivot.value?.pivot_position?.[0] ?? null);
const isPivot = (row, col) => leavingRow.value === row && enteringCol.value === col;
function display(value) { if (value === null || value === undefined || value === '')
    return '—'; if (typeof value === 'object' && value && 'display' in value)
    return String(value.display); return String(value); }
debugger; /* PartiallyEnd: #3632/scriptSetup.vue */
const __VLS_ctx = {};
let __VLS_components;
let __VLS_directives;
__VLS_asFunctionalElement(__VLS_intrinsicElements.section, __VLS_intrinsicElements.section)({
    ...{ class: "tableau-wrap" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "tableau-meta" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
(__VLS_ctx.display(__VLS_ctx.tableau.phase));
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
(__VLS_ctx.display(__VLS_ctx.tableau.current_z));
if (__VLS_ctx.pivot) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    (__VLS_ctx.display(__VLS_ctx.names[__VLS_ctx.enteringCol ?? -1]));
}
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "table-scroll" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.table, __VLS_intrinsicElements.table)({
    ...{ class: "tableau" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.thead, __VLS_intrinsicElements.thead)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.tr, __VLS_intrinsicElements.tr)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({
    ...{ class: "corner" },
});
for (const [name, index] of __VLS_getVForSourceType((__VLS_ctx.names))) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({
        key: (name),
        ...{ class: ({ entering: __VLS_ctx.enteringCol === index }) },
    });
    (name);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.small, __VLS_intrinsicElements.small)({});
    (__VLS_ctx.display(__VLS_ctx.values('c_j')[index]));
}
__VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({
    ...{ class: "rhs" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({
    ...{ class: "theta" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.tbody, __VLS_intrinsicElements.tbody)({});
for (const [row, rowIndex] of __VLS_getVForSourceType((__VLS_ctx.values('matrix_a')))) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.tr, __VLS_intrinsicElements.tr)({
        key: (rowIndex),
        ...{ class: ({ leaving: __VLS_ctx.leavingRow === rowIndex }) },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({
        ...{ class: "basis" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.b, __VLS_intrinsicElements.b)({});
    (__VLS_ctx.display(__VLS_ctx.values('c_b')[rowIndex]));
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    (__VLS_ctx.display(__VLS_ctx.basisNames[rowIndex]));
    for (const [value, colIndex] of __VLS_getVForSourceType((row))) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({
            key: (colIndex),
            ...{ class: ({ pivot: __VLS_ctx.isPivot(rowIndex, colIndex), entering: __VLS_ctx.enteringCol === colIndex }) },
        });
        (__VLS_ctx.display(value));
    }
    __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({
        ...{ class: "rhs" },
    });
    (__VLS_ctx.display(__VLS_ctx.values('b')[rowIndex]));
    __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({
        ...{ class: "theta" },
    });
    (__VLS_ctx.display(__VLS_ctx.values('theta')[rowIndex]));
}
__VLS_asFunctionalElement(__VLS_intrinsicElements.tr, __VLS_intrinsicElements.tr)({
    ...{ class: "sigma" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
for (const [value, index] of __VLS_getVForSourceType((__VLS_ctx.values('sigma')))) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({
        key: (index),
        ...{ class: ({ entering: __VLS_ctx.enteringCol === index }) },
    });
    (__VLS_ctx.display(value));
}
__VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({
    ...{ class: "rhs" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({
    ...{ class: "theta" },
});
/** @type {__VLS_StyleScopedClasses['tableau-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['tableau-meta']} */ ;
/** @type {__VLS_StyleScopedClasses['table-scroll']} */ ;
/** @type {__VLS_StyleScopedClasses['tableau']} */ ;
/** @type {__VLS_StyleScopedClasses['corner']} */ ;
/** @type {__VLS_StyleScopedClasses['rhs']} */ ;
/** @type {__VLS_StyleScopedClasses['theta']} */ ;
/** @type {__VLS_StyleScopedClasses['basis']} */ ;
/** @type {__VLS_StyleScopedClasses['rhs']} */ ;
/** @type {__VLS_StyleScopedClasses['theta']} */ ;
/** @type {__VLS_StyleScopedClasses['sigma']} */ ;
/** @type {__VLS_StyleScopedClasses['rhs']} */ ;
/** @type {__VLS_StyleScopedClasses['theta']} */ ;
var __VLS_dollars;
const __VLS_self = (await import('vue')).defineComponent({
    setup() {
        return {
            names: names,
            basisNames: basisNames,
            values: values,
            pivot: pivot,
            enteringCol: enteringCol,
            leavingRow: leavingRow,
            isPivot: isPivot,
            display: display,
        };
    },
    __typeProps: {},
});
export default (await import('vue')).defineComponent({
    setup() {
        return {};
    },
    __typeProps: {},
});
; /* PartiallyEnd: #4569/main.vue */
