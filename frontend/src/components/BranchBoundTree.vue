<template>
  <div class="p-6 rounded-2xl border border-white/10 bg-slate-900/40 backdrop-blur-xl shadow-2xl space-y-4">
    <div class="flex items-center justify-between border-b border-white/10 pb-4">
      <div class="flex items-center space-x-2">
        <span class="w-3 h-3 rounded-full bg-indigo-400 animate-pulse"></span>
        <h3 class="font-bold text-sm text-slate-100">分支定界层次拓扑树 (Branch & Bound Tree)</h3>
      </div>
      <div class="flex items-center space-x-4 text-xs font-mono">
        <span class="flex items-center space-x-1.5"><span class="w-2.5 h-2.5 rounded bg-emerald-500"></span><span class="text-slate-300">整数解</span></span>
        <span class="flex items-center space-x-1.5"><span class="w-2.5 h-2.5 rounded bg-indigo-500"></span><span class="text-slate-300">继续分支</span></span>
        <span class="flex items-center space-x-1.5"><span class="w-2.5 h-2.5 rounded bg-rose-500"></span><span class="text-slate-300">剪枝 / 无解</span></span>
      </div>
    </div>

    <div class="w-full overflow-x-auto bg-slate-950/80 rounded-xl border border-white/5 p-4 flex justify-center">
      <svg :width="treeLayout.width" :height="treeLayout.height" class="select-none font-mono">
        <defs>
          <filter id="node-glow" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#000" flood-opacity="0.5"/>
          </filter>
        </defs>

        <g v-for="edge in treeLayout.edges" :key="'edge-' + edge.from + '-' + edge.to">
          <path 
            :d="edge.path" 
            fill="none" 
            stroke="#475569" 
            stroke-width="1.8" 
            stroke-dasharray="3 3"
          />
          <g :transform="`translate(${edge.midX}, ${edge.midY})`">
            <rect 
              :x="-edge.label.length * 3.8 - 6" 
              y="-10" 
              :width="edge.label.length * 7.6 + 12" 
              height="20" 
              rx="5" 
              fill="#0f172a" 
              stroke="#334155" 
              stroke-width="1"
            />
            <text 
              x="0" 
              y="3.5" 
              fill="#38bdf8" 
              font-size="10" 
              font-weight="bold" 
              text-anchor="middle"
            >
              {{ edge.label }}
            </text>
          </g>
        </g>

        <g 
          v-for="node in treeLayout.nodes" 
          :key="'node-' + node.id"
          :transform="`translate(${node.x - nodeWidth / 2}, ${node.y})`"
          filter="url(#node-glow)"
          class="transition-all duration-300"
        >
          <rect 
            :width="nodeWidth" 
            :height="nodeHeight" 
            rx="8" 
            :fill="node.bgColor" 
            :stroke="node.borderColor" 
            stroke-width="1.8"
          />

          <rect :width="nodeWidth" height="24" rx="8" :fill="node.headerBg" />
          <text 
            :x="nodeWidth / 2" 
            y="16" 
            fill="#fff" 
            font-size="11" 
            font-weight="bold" 
            text-anchor="middle"
          >
            {{ node.name }}
          </text>

          <template v-if="node.isInfeasible">
            <text :x="nodeWidth / 2" y="48" fill="#f43f5e" font-size="11" font-weight="bold" text-anchor="middle">
              无可行解
            </text>
            <text :x="nodeWidth / 2" y="66" fill="#94a3b8" font-size="9" text-anchor="middle">
              (剪枝)
            </text>
          </template>

          <template v-else>
            <text :x="10" y="44" fill="#cbd5e1" font-size="10">
              {{ node.solutionStr }}
            </text>
            <text :x="10" y="62" fill="#34d399" font-size="10" font-weight="bold">
              Z = {{ node.zVal }}
            </text>
            <text :x="nodeWidth - 10" y="62" :fill="node.statusColor" font-size="9" font-weight="bold" text-anchor="end">
              {{ node.statusBadge }}
            </text>
          </template>
        </g>
      </svg>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  iterations: any[]
}>()

const nodeWidth = 148
const nodeHeight = 76
const levelGapY = 110
const siblingGapX = 26

interface TreeNode {
  id: number
  parentId: number
  name: string
  branchLabel: string
  zVal: string
  solutionStr: string
  isInfeasible: boolean
  isInteger: boolean
  isPruned: boolean
  bgColor: string
  borderColor: string
  headerBg: string
  statusColor: string
  statusBadge: string
  x: number
  y: number
  level: number
  children: TreeNode[]
}

const treeLayout = computed(() => {
  const steps = props.iterations || []
  if (steps.length === 0) return { width: 500, height: 200, nodes: [], edges: [] }

  const nodeMap = new Map<number, TreeNode>()
  const rawList: TreeNode[] = []

  steps.forEach((step, idx) => {
    const sm = step.state_matrix || {}
    const id = step.node_id ?? sm.node_id ?? idx
    const parentId = step.parent_id ?? sm.parent_id ?? -1
    
    const isInfeasible = step.prune_reason?.includes('不可行') || sm.lp_status === 'INFEASIBLE'
    const isInteger = !!(step.integer_solution || sm.integer_solution)
    const isPruned = !!(step.pruned || sm.pruned)

    let zVal = step.z_lp || sm.z_lp || '-'
    let solutionStr = ''

    if (sm.x) {
      solutionStr = Object.entries(sm.x).map(([k, v]) => `${k}=${v}`).join(', ')
    } else if (step.branch_var) {
      solutionStr = `${step.branch_var}=${step.branch_val ?? '-'}`
    } else {
      solutionStr = 'LP 松弛解'
    }

    let branchLabel = ''
    if (step.branch_floor && step.branch_var) {
      branchLabel = `${step.branch_var} ≤ ${step.branch_floor}`
    } else if (step.branch_ceil && step.branch_var) {
      branchLabel = `${step.branch_var} ≥ ${step.branch_ceil}`
    } else if (step.action?.includes('≤') || step.action?.includes('≥')) {
      const match = step.action.match(/x\d+\s*[≤≥]\s*[-+]?\d+(\/\d+)?/)
      if (match) branchLabel = match[0]
    }

    let bgColor = '#0f172a'
    let borderColor = '#3b82f6'
    let headerBg = '#1e293b'
    let statusColor = '#38bdf8'
    let statusBadge = '分支中'

    if (isInfeasible) {
      borderColor = '#f43f5e'
      headerBg = '#4c0519'
      statusColor = '#fb7185'
      statusBadge = '无可行解'
    } else if (isInteger) {
      borderColor = '#10b981'
      headerBg = '#064e3b'
      statusColor = '#34d399'
      statusBadge = '⭐ 整数解'
    } else if (isPruned) {
      borderColor = '#f59e0b'
      headerBg = '#451a03'
      statusColor = '#fbbf24'
      statusBadge = '界剪枝'
    }

    const treeNode: TreeNode = {
      id,
      parentId,
      name: id === 0 ? 'LP (Root)' : `LP${id}`,
      branchLabel,
      zVal,
      solutionStr: solutionStr.length > 20 ? solutionStr.slice(0, 19) + '…' : solutionStr,
      isInfeasible,
      isInteger,
      isPruned,
      bgColor,
      borderColor,
      headerBg,
      statusColor,
      statusBadge,
      x: 0,
      y: 0,
      level: 0,
      children: []
    }

    nodeMap.set(id, treeNode)
    rawList.push(treeNode)
  })

  let root: TreeNode | null = null
  rawList.forEach((node) => {
    if (node.parentId === -1 || !nodeMap.has(node.parentId)) {
      root = node
    } else {
      const p = nodeMap.get(node.parentId)
      if (p) p.children.push(node)
    }
  })

  if (!root) root = rawList[0]

  let currentLeafX = 40

  function layoutSubtree(node: TreeNode, depth: number) {
    node.level = depth
    node.y = 30 + depth * levelGapY

    if (node.children.length === 0) {
      node.x = currentLeafX + nodeWidth / 2
      currentLeafX += nodeWidth + siblingGapX
    } else {
      node.children.forEach((c) => layoutSubtree(c, depth + 1))
      const firstX = node.children[0].x
      const lastX = node.children[node.children.length - 1].x
      node.x = (firstX + lastX) / 2
    }
  }

  layoutSubtree(root, 0)

  const edges: any[] = []
  rawList.forEach((node) => {
    if (node.parentId !== -1 && nodeMap.has(node.parentId)) {
      const parent = nodeMap.get(node.parentId)!
      const startX = parent.x
      const startY = parent.y + nodeHeight
      const endX = node.x
      const endY = node.y

      const midX = (startX + endX) / 2
      const midY = (startY + endY) / 2

      const path = `M ${startX} ${startY} C ${startX} ${startY + 30}, ${endX} ${endY - 30}, ${endX} ${endY}`

      edges.push({
        from: parent.id,
        to: node.id,
        path,
        midX,
        midY,
        label: node.branchLabel || (node.x < parent.x ? '左分支' : '右分支')
      })
    }
  })

  const maxLevel = Math.max(...rawList.map((n) => n.level), 1)
  const totalWidth = Math.max(currentLeafX + 40, 720)
  const totalHeight = (maxLevel + 1) * levelGapY + 80

  return {
    width: totalWidth,
    height: totalHeight,
    nodes: rawList,
    edges
  }
})
</script>