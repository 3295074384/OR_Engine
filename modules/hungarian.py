# fmt: off
# =============================================================================
# Author:      王梓轩
# Project:     运筹学算法推演引擎
# Description: 指派问题模块（Assignment Problem）— 匈牙利法（Hungarian Method）。
#              支持 min/max、非方阵自动补虚拟行/列，严格记录每步行列化简、
#              画线覆盖、矩阵调整的推演细节。全程 fractions.Fraction 精确计算。
# =============================================================================
# fmt: on

from __future__ import annotations
from fractions import Fraction
from copy import deepcopy

from base_module import (
    BaseModule, STATUS_OPTIMAL, STATUS_ERROR,
    fmt, to_fraction
)


class HungarianModule(BaseModule):
    """匈牙利法求解指派问题。"""

    PROBLEM_TYPE = "AP"

    # ─────────────────────────────────────────────────────────────────────────
    # 主入口
    # ─────────────────────────────────────────────────────────────────────────

    def solve(self, payload: dict, options: dict) -> dict:
        self._init_steps()
        step = [0]

        objective = payload.get("objective", "min")
        raw_cost  = payload["cost_matrix"]
        m_raw     = len(raw_cost)
        n_raw     = len(raw_cost[0])

        # 所有数值转 Fraction
        cost = [[to_fraction(raw_cost[i][j]) for j in range(n_raw)]
                for i in range(m_raw)]

        # ── 1. max → min 转化 ────────────────────────────────────────────────
        max_val = None
        if objective == "max":
            max_val = max(cost[i][j] for i in range(m_raw) for j in range(n_raw))
            cost    = [[max_val - cost[i][j] for j in range(n_raw)]
                       for i in range(m_raw)]

        # ── 2. 补虚拟行/列（非方阵） ─────────────────────────────────────────
        n = max(m_raw, n_raw)
        is_dummy_row = [False] * n
        is_dummy_col = [False] * n
        pad_action   = None
        pad_calcs    = []

        if m_raw < n:
            # 补虚拟行
            for i in range(m_raw, n):
                cost.append([Fraction(0)] * n_raw)
                is_dummy_row[i] = True
            pad_action = (f"行数({m_raw}) < 列数({n_raw})，添加 {n-m_raw} 个虚拟行"
                          f"（行 {m_raw+1}..{n}），代价填 0")
            pad_calcs  = [f"虚拟行 {i+1}：代价 = [0, 0, ..., 0]"
                          for i in range(m_raw, n)]

        if n_raw < n:
            # 补虚拟列
            for i in range(m_raw if m_raw >= n else n):
                for _ in range(n_raw, n):
                    cost[i].append(Fraction(0))
                    is_dummy_col[n_raw] = True  # mark once
            for j in range(n_raw, n):
                is_dummy_col[j] = True
            pad_action = (f"列数({n_raw}) < 行数({m_raw})，添加 {n-n_raw} 个虚拟列"
                          f"（列 {n_raw+1}..{n}），代价填 0")
            pad_calcs  = [f"虚拟列 {j+1}：代价 = [0, 0, ..., 0]"
                          for j in range(n_raw, n)]

        if objective == "max":
            prefix = f"max 问题转 min：所有元素 = {fmt(max_val)} - 原值；"
            if pad_action:
                pad_action = prefix + pad_action
                pad_calcs  = [f"矩阵最大值 = {fmt(max_val)}，取反后再补虚拟"
                              ] + pad_calcs
            else:
                pad_action = prefix.rstrip("；")
                pad_calcs  = [f"矩阵最大值 = {fmt(max_val)}，各元素取反"]

        if pad_action or objective == "max":
            self._add_step(self.snapshot(
                step=step[0],
                state_matrix=self._mat_snap(cost, n, [], []),
                action=pad_action or "max→min 转化（方阵，无需补虚拟）",
                calculation=pad_calcs or [f"最大值 = {fmt(max_val)}，全部元素 = max - 原值"],
            ))
            step[0] += 1

        # ── 3. 行化简 ───────────────────────────────────────────────────────
        row_calcs = []
        for i in range(n):
            row_min = min(cost[i])
            if row_min != 0:
                cost[i] = [cost[i][j] - row_min for j in range(n)]
                row_calcs.append(f"第 {i+1} 行减去最小值 {fmt(row_min)}")
            else:
                row_calcs.append(f"第 {i+1} 行最小值 = 0，无需化简")

        self._add_step(self.snapshot(
            step=step[0],
            state_matrix=self._mat_snap(cost, n, [], []),
            action="步骤 1A：行化简（每行减去本行最小值）",
            calculation=row_calcs,
        ))
        step[0] += 1

        # ── 4. 列化简 ───────────────────────────────────────────────────────
        col_calcs = []
        for j in range(n):
            col_min = min(cost[i][j] for i in range(n))
            if col_min != 0:
                for i in range(n):
                    cost[i][j] -= col_min
                col_calcs.append(f"第 {j+1} 列减去最小值 {fmt(col_min)}")
            else:
                col_calcs.append(f"第 {j+1} 列最小值 = 0，无需化简")

        self._add_step(self.snapshot(
            step=step[0],
            state_matrix=self._mat_snap(cost, n, [], []),
            action="步骤 1B：列化简（每列减去本列最小值）",
            calculation=col_calcs,
        ))
        step[0] += 1

        # ── 5. 主循环：画线 → 判断 → 调整 → 重复 ──────────────────────────
        MAX_ITER = n * 4 + 10
        for outer in range(MAX_ITER):
            covered_rows, covered_cols, match_r, match_c = \
                self._min_line_cover(cost, n)

            line_count = len(covered_rows) + len(covered_cols)
            cover_calcs = [
                f"最大匹配数（独立 0 元素数）= {line_count}",
                f"覆盖行：{ {i+1 for i in covered_rows} if covered_rows else '无'} "
                f"（{len(covered_rows)} 条）",
                f"覆盖列：{ {j+1 for j in covered_cols} if covered_cols else '无'} "
                f"（{len(covered_cols)} 条）",
                f"共 {line_count} 条直线，矩阵阶数 N = {n}",
            ]

            if line_count >= n:
                # 最优！提取指派方案
                cover_calcs.append(f"直线数 {line_count} = N = {n}，指派方案最优！")
                self._add_step(self.snapshot(
                    step=step[0],
                    state_matrix=self._mat_snap(cost, n, list(covered_rows), list(covered_cols)),
                    action=f"步骤 2：{line_count} 条直线覆盖所有 0 且等于 N={n}，最优指派已确定",
                    calculation=cover_calcs,
                    covered_rows=[i+1 for i in covered_rows],
                    covered_cols=[j+1 for j in covered_cols],
                ))
                step[0] += 1

                # 提取指派：从最大匹配中读出指派对
                assignment = []
                for i in range(n):
                    if match_r[i] != -1 and not is_dummy_row[i] and not is_dummy_col[match_r[i]]:
                        assignment.append((i, match_r[i]))
                    elif match_r[i] != -1 and not is_dummy_row[i]:
                        assignment.append((i, match_r[i]))  # dummy col: include for completeness

                # 计算原始成本（非虚拟部分）
                orig_cost = [[to_fraction(raw_cost[i][j]) for j in range(n_raw)]
                             for i in range(m_raw)]
                total_cost = Fraction(0)
                assign_result = []
                for (i, j) in sorted(assignment):
                    if i < m_raw and j < n_raw:
                        c = orig_cost[i][j]
                        total_cost += c
                        assign_result.append({
                            "worker": i + 1,
                            "task":   j + 1,
                            "cost":   fmt(c),
                        })
                    elif i < m_raw:
                        assign_result.append({
                            "worker": i + 1,
                            "task":   f"虚拟{j+1}",
                            "cost":   "0（不指派）",
                        })

                final_result = {
                    "total_cost":  fmt(total_cost if objective == "min" else -total_cost + max_val * m_raw),
                    "assignment":  assign_result,
                }
                if objective == "max":
                    # 重新算原始最大值总收益
                    orig_total = sum(to_fraction(raw_cost[i][j])
                                     for (i, j) in assignment if i < m_raw and j < n_raw)
                    final_result["total_cost"] = fmt(orig_total)

                return self.build_output(STATUS_OPTIMAL, final_result)

            # 画线但未到 N：记录并进行矩阵调整
            cover_calcs.append(f"直线数 {line_count} < N = {n}，需进行矩阵调整")
            self._add_step(self.snapshot(
                step=step[0],
                state_matrix=self._mat_snap(cost, n, list(covered_rows), list(covered_cols)),
                action=(f"步骤 2：{line_count} 条直线（行 {sorted(i+1 for i in covered_rows)}，"
                        f"列 {sorted(j+1 for j in covered_cols)}）覆盖所有 0，但 {line_count} < N={n}"),
                calculation=cover_calcs,
                covered_rows=[i+1 for i in covered_rows],
                covered_cols=[j+1 for j in covered_cols],
            ))
            step[0] += 1

            # 矩阵调整：找未覆盖最小值 θ
            theta = None
            for i in range(n):
                for j in range(n):
                    if i not in covered_rows and j not in covered_cols:
                        if theta is None or cost[i][j] < theta:
                            theta = cost[i][j]

            if theta is None or theta == 0:
                return self.build_output(STATUS_ERROR, final_result={},
                                         error_message="矩阵调整中θ=0或无未覆盖元素，算法异常")

            adj_calcs = [
                f"未覆盖元素中的最小值 θ = {fmt(theta)}",
                f"操作：未覆盖元素（行 ∉ {{{','.join(str(i+1) for i in sorted(covered_rows))} }}，"
                f"列 ∉ {{{','.join(str(j+1) for j in sorted(covered_cols))}}}）减去 θ",
                f"操作：行列交叉处元素加上 θ",
                f"操作：仅覆盖行/覆盖列但非交叉处元素不变",
            ]

            new_cost = [list(row) for row in cost]
            for i in range(n):
                for j in range(n):
                    if i in covered_rows and j in covered_cols:
                        new_cost[i][j] = cost[i][j] + theta   # 交叉处 +θ
                    elif i not in covered_rows and j not in covered_cols:
                        new_cost[i][j] = cost[i][j] - theta   # 未覆盖 -θ
                    # 单行/单列覆盖处不变

            cost = new_cost

            self._add_step(self.snapshot(
                step=step[0],
                state_matrix=self._mat_snap(cost, n, [], []),
                action=f"步骤 3：矩阵调整，θ = {fmt(theta)}（未覆盖 -θ，交叉 +θ）",
                calculation=adj_calcs,
                theta=fmt(theta),
            ))
            step[0] += 1

        return self.build_output(STATUS_ERROR, final_result={},
                                 error_message=f"超过最大迭代次数 {MAX_ITER}，算法未收敛")

    # ─────────────────────────────────────────────────────────────────────────
    # 最小线覆盖（König 定理 + 最大二部图匹配）
    # ─────────────────────────────────────────────────────────────────────────

    def _min_line_cover(self, cost, n):
        """
        返回 (covered_rows_set, covered_cols_set, match_r, match_c)。
        match_r[i] = j  ↔  行 i 指派到列 j（-1 表示未匹配）。
        使用增广路径求最大匹配，通过 König 定理得最小覆盖。
        """
        match_r = [-1] * n
        match_c = [-1] * n

        # 最大匹配
        for i in range(n):
            visited = [False] * n
            self._augment(i, match_r, match_c, visited, cost, n)

        # König 定理：从未匹配行出发做交替可达标记
        unmatched_rows = set(i for i in range(n) if match_r[i] == -1)
        marked_rows = set(unmatched_rows)
        marked_cols: set[int] = set()

        changed = True
        while changed:
            changed = False
            # 标记：在已标记行中含 0 的列
            for i in list(marked_rows):
                for j in range(n):
                    if cost[i][j] == 0 and j not in marked_cols:
                        marked_cols.add(j)
                        changed = True
            # 标记：已标记列中匹配行
            for j in list(marked_cols):
                r = match_c[j]
                if r != -1 and r not in marked_rows:
                    marked_rows.add(r)
                    changed = True

        # 覆盖线 = 未被标记的行 ∪ 被标记的列
        covered_rows = set(i for i in range(n) if i not in marked_rows)
        covered_cols = marked_cols
        return covered_rows, covered_cols, match_r, match_c

    def _augment(self, row, match_r, match_c, visited, cost, n) -> bool:
        """增广路径算法（用于最大二部图匹配）。"""
        for j in range(n):
            if cost[row][j] == 0 and not visited[j]:
                visited[j] = True
                if match_c[j] == -1 or self._augment(match_c[j], match_r, match_c, visited, cost, n):
                    match_r[row] = j
                    match_c[j]   = row
                    return True
        return False

    # ─────────────────────────────────────────────────────────────────────────
    # 快照构建
    # ─────────────────────────────────────────────────────────────────────────

    def _mat_snap(self, cost, n, covered_rows, covered_cols):
        """构建矩阵快照（所有数值转字符串）。"""
        cr_set = set(covered_rows)
        cc_set = set(covered_cols)
        rows = []
        for i in range(n):
            cells = []
            for j in range(n):
                is_zero = (cost[i][j] == 0)
                in_row  = (i in cr_set)
                in_col  = (j in cc_set)
                cells.append({
                    "value":        fmt(cost[i][j]),
                    "is_zero":      is_zero,
                    "covered":      in_row or in_col,
                    "crossed":      in_row and in_col,
                    "row_covered":  in_row,
                    "col_covered":  in_col,
                })
            rows.append({"row": i + 1, "cells": cells})
        return {
            "type":          "assignment_matrix",
            "size":          n,
            "rows":          rows,
            "covered_rows":  [i+1 for i in covered_rows],
            "covered_cols":  [j+1 for j in covered_cols],
        }
