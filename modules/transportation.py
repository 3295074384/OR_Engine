# fmt: off
# =============================================================================
# Author:      王梓轩
# Project:     运筹学算法推演引擎
# Description: 运输问题模块（Transportation Problem）。
#              使用 Vogel 逼近法求初始基可行解，
#              位势法（MODI/U-V Method）检验最优性，
#              闭回路法（Stepping Stone）进行迭代改进。
#              全程 fractions.Fraction 精确计算，无浮点误差。
# =============================================================================
# fmt: on

from __future__ import annotations
from fractions import Fraction
from copy import deepcopy

from base_module import (
    BaseModule, STATUS_OPTIMAL, STATUS_ERROR,
    fmt, to_fraction
)


class TransportationModule(BaseModule):
    """运输问题求解模块：Vogel 初始解 + MODI 最优性检验 + 闭回路调整。"""

    PROBLEM_TYPE = "TP"

    # ─────────────────────────────────────────────────────────────────────────
    # 主入口
    # ─────────────────────────────────────────────────────────────────────────

    def solve(self, payload: dict, options: dict) -> dict:
        self._init_steps()
        step_no = [0]   # 用列表传递，方便嵌套方法递增

        # ── 1. 解析输入 ──────────────────────────────────────────────────────
        supply = [to_fraction(v) for v in payload["supply"]]
        demand = [to_fraction(v) for v in payload["demand"]]
        cost   = [[to_fraction(v) for v in row] for row in payload["cost"]]
        m, n   = len(supply), len(demand)

        total_s = sum(supply)
        total_d = sum(demand)

        # ── 2. 产销平衡检测与预处理（Step 0） ──────────────────────────────
        if total_s != total_d:
            diff = abs(total_s - total_d)
            calcs = [
                f"总产量 = {fmt(total_s)},  总销量 = {fmt(total_d)}",
                f"差额 = {fmt(diff)}",
            ]
            if total_s > total_d:
                demand.append(diff)
                for row in cost:
                    row.append(Fraction(0))
                n += 1
                calcs.append(f"添加虚拟销地 d{n}（列 {n}），运价全置为 0，需求量 = {fmt(diff)}")
                action0 = (f"产销不平衡：总产量({fmt(total_s)}) > 总销量({fmt(total_d)})，"
                           f"新增虚拟销地列 {n}，运价 = 0")
            else:
                supply.append(diff)
                cost.append([Fraction(0)] * n)
                m += 1
                calcs.append(f"添加虚拟产地 s{m}（行 {m}），运价全置为 0，供给量 = {fmt(diff)}")
                action0 = (f"产销不平衡：总销量({fmt(total_d)}) > 总产量({fmt(total_s)})，"
                           f"新增虚拟产地行 {m}，运价 = 0")

            self._add_step(self.snapshot(
                step=step_no[0],
                state_matrix=self._cost_snapshot(cost, supply, demand, m, n, None),
                action=action0,
                calculation=calcs,
            ))
            step_no[0] += 1

        # ── 3. Vogel 逼近法（初始基可行解） ─────────────────────────────────
        allocation = [[None] * n for _ in range(m)]
        basis: set[tuple[int, int]] = set()
        rem_s = list(supply)
        rem_d = list(demand)

        self._vogel(cost, allocation, basis, rem_s, rem_d, m, n, step_no)

        # ── 4. MODI 位势法迭代至最优 ─────────────────────────────────────────
        iteration = 0
        while True:
            u, v = self._potentials(cost, allocation, basis, m, n)
            sigma = self._check_numbers(cost, u, v, basis, m, n)

            # 寻找最小（最负）检验数
            min_val = Fraction(0)
            enter_r, enter_c = -1, -1
            for i in range(m):
                for j in range(n):
                    if (i, j) not in basis and sigma[i][j] < min_val:
                        min_val = sigma[i][j]
                        enter_r, enter_c = i, j

            # 记录 MODI 检验表快照
            iteration += 1
            step_no[0] += 1
            u_fmt = [fmt(u[i]) for i in range(m)]
            v_fmt = [fmt(v[j]) for j in range(n)]

            modi_calcs = [f"令 u[1]=0，通过 c_ij=u_i+v_j 解出所有位势"]
            for i in range(m):
                modi_calcs.append(f"  u[{i+1}] = {fmt(u[i])}")
            for j in range(n):
                modi_calcs.append(f"  v[{j+1}] = {fmt(v[j])}")
            modi_calcs.append("计算非基变量检验数 σ_ij = c_ij - u_i - v_j：")
            for i in range(m):
                for j in range(n):
                    if (i, j) not in basis:
                        modi_calcs.append(
                            f"  σ({i+1},{j+1}) = {fmt(cost[i][j])} - ({fmt(u[i])}) - ({fmt(v[j])}) = {fmt(sigma[i][j])}"
                        )

            if enter_r == -1:
                # 所有检验数 >= 0，已最优
                self._add_step(self.snapshot(
                    step=step_no[0],
                    state_matrix=self._alloc_snapshot(cost, allocation, sigma, u, v, basis, m, n, []),
                    action="所有检验数 σ_ij ≥ 0，当前方案已最优",
                    calculation=modi_calcs + ["结论：所有 σ_ij ≥ 0，最优！"],
                    u=u_fmt, v=v_fmt,
                ))
                break

            # 有负检验数，找闭回路进行调整
            modi_calcs.append(f"最小检验数 σ({enter_r+1},{enter_c+1}) = {fmt(min_val)} < 0，"
                              f"格 ({enter_r+1},{enter_c+1}) 入基")

            loop = self._find_loop(enter_r, enter_c, basis, m, n)
            if loop is None:
                return self.build_output(
                    STATUS_ERROR,
                    final_result={},
                    error_message=f"无法找到从格({enter_r+1},{enter_c+1})出发的闭回路，数据可能退化"
                )

            # theta = 负号顶点处的最小运量
            minus_cells = [loop[k] for k in range(1, len(loop), 2)]
            theta = min(allocation[r][c] for (r, c) in minus_cells)

            loop_path_str = " → ".join(
                f"({'+'if k%2==0 else '-'})({r+1},{c+1})"
                for k, (r, c) in enumerate(loop)
            )

            stone_calcs = modi_calcs + [
                f"闭回路路径：{loop_path_str}",
                f"调整量 θ = min({', '.join(fmt(allocation[r][c]) for r,c in minus_cells)}) = {fmt(theta)}",
            ]
            for k, (r, c) in enumerate(loop):
                sign = "+" if k % 2 == 0 else "-"
                old_val = allocation[r][c] if allocation[r][c] is not None else Fraction(0)
                new_val = old_val + theta if k % 2 == 0 else old_val - theta
                stone_calcs.append(f"  格({r+1},{c+1}): {fmt(old_val)} {sign} {fmt(theta)} = {fmt(new_val)}")

            # 记录调整前快照（含入基格高亮信息）
            self._add_step(self.snapshot(
                step=step_no[0],
                state_matrix=self._alloc_snapshot(cost, allocation, sigma, u, v, basis, m, n, loop),
                action=(f"MODI 第 {iteration} 轮：入基格({enter_r+1},{enter_c+1}) "
                        f"σ={fmt(min_val)}，θ={fmt(theta)}，"
                        f"出基格({minus_cells[minus_cells.index(min((minus_cells), key=lambda rc: allocation[rc[0]][rc[1]]))][0]+1},"
                        f"{minus_cells[minus_cells.index(min((minus_cells), key=lambda rc: allocation[rc[0]][rc[1]]))][1]+1})"),
                calculation=stone_calcs,
                loop=[(r+1, c+1) for r, c in loop],
                theta=fmt(theta),
                u=u_fmt, v=v_fmt,
            ))

            # 执行运量调整
            # 在入基格 (enter_r, enter_c) 写入 0（初始化），再统一 ± theta
            allocation[enter_r][enter_c] = Fraction(0)
            basis.add((enter_r, enter_c))

            leaving_cell = None
            for k, (r, c) in enumerate(loop):
                if k % 2 == 0:
                    allocation[r][c] += theta
                else:
                    allocation[r][c] -= theta
                    if allocation[r][c] == Fraction(0) and leaving_cell is None:
                        leaving_cell = (r, c)

            # 出基：移除调整后为零的格（取第一个遇到的）
            if leaving_cell:
                basis.discard(leaving_cell)
                allocation[leaving_cell[0]][leaving_cell[1]] = None

        # ── 5. 计算最优目标值 ─────────────────────────────────────────────────
        total_cost = Fraction(0)
        allocation_result: dict[str, str] = {}
        for i in range(m):
            for j in range(n):
                if allocation[i][j] is not None and allocation[i][j] > 0:
                    total_cost += cost[i][j] * allocation[i][j]
                    allocation_result[f"x({i+1},{j+1})"] = fmt(allocation[i][j])

        final_result = {
            "total_cost":  fmt(total_cost),
            "allocation":  allocation_result,
            "basis_cells": [(r+1, c+1) for (r, c) in sorted(basis)],
        }
        return self.build_output(STATUS_OPTIMAL, final_result)

    # ─────────────────────────────────────────────────────────────────────────
    # Vogel 逼近法
    # ─────────────────────────────────────────────────────────────────────────

    def _vogel(self, cost, allocation, basis, rem_s, rem_d, m, n, step_no):
        """Vogel 逼近法求初始基可行解，每步记录快照。"""
        row_done = [False] * m
        col_done = [False] * n

        vam_iter = 0
        while True:
            active_rows = [i for i in range(m) if not row_done[i]]
            active_cols = [j for j in range(n) if not col_done[j]]
            if not active_rows or not active_cols:
                break

            # 计算各行罚数
            row_pen: list[tuple[Fraction | None, int, int]] = []
            for i in active_rows:
                costs_i = sorted([(cost[i][j], j) for j in active_cols])
                if len(costs_i) == 1:
                    pen, best_j = Fraction(0), costs_i[0][1]
                else:
                    pen  = costs_i[1][0] - costs_i[0][0]
                    best_j = costs_i[0][1]
                row_pen.append((pen, i, best_j))

            # 计算各列罚数
            col_pen: list[tuple[Fraction | None, int, int]] = []
            for j in active_cols:
                costs_j = sorted([(cost[i][j], i) for i in active_rows])
                if len(costs_j) == 1:
                    pen, best_i = Fraction(0), costs_j[0][1]
                else:
                    pen  = costs_j[1][0] - costs_j[0][0]
                    best_i = costs_j[0][1]
                col_pen.append((pen, j, best_i))

            # 找最大罚数
            all_candidates = (
                [(p, "行", idx, best) for p, idx, best in row_pen] +
                [(p, "列", idx, best) for p, idx, best in col_pen]
            )
            all_candidates.sort(key=lambda x: -x[0])
            max_pen, kind, idx, best = all_candidates[0]

            if kind == "行":
                alloc_r, alloc_c = idx, best
            else:
                alloc_r, alloc_c = best, idx

            amount = min(rem_s[alloc_r], rem_d[alloc_c])
            allocation[alloc_r][alloc_c] = amount
            basis.add((alloc_r, alloc_c))
            rem_s[alloc_r] -= amount
            rem_d[alloc_c] -= amount

            vam_iter += 1
            step_no[0] += 1

            row_pen_fmt = {i: fmt(p) for p, i, _ in row_pen}
            col_pen_fmt = {j: fmt(p) for p, j, _ in col_pen}

            calcs = [
                f"各行罚数: { {i+1: row_pen_fmt[i] for i in row_pen_fmt} }",
                f"各列罚数: { {j+1: col_pen_fmt[j] for j in col_pen_fmt} }",
                f"最大罚数 = {fmt(max_pen)}（{kind} {idx+1}）",
                f"该{kind}中最小运价格: ({alloc_r+1},{alloc_c+1})，运价 = {fmt(cost[alloc_r][alloc_c])}",
                f"填入运量 = min({fmt(rem_s[alloc_r]+amount)}, {fmt(rem_d[alloc_c]+amount)}) = {fmt(amount)}",
            ]

            if rem_s[alloc_r] == 0:
                row_done[alloc_r] = True
                calcs.append(f"行 {alloc_r+1} 产量耗尽，划去该行")
            if rem_d[alloc_c] == 0:
                col_done[alloc_c] = True
                calcs.append(f"列 {alloc_c+1} 销量满足，划去该列")

            self._add_step(self.snapshot(
                step=step_no[0],
                state_matrix=self._cost_snapshot(cost, rem_s, rem_d, m, n, allocation),
                action=(f"Vogel 第 {vam_iter} 步：选{kind} {idx+1}（罚数={fmt(max_pen)}），"
                        f"在格({alloc_r+1},{alloc_c+1})填入 {fmt(amount)}"),
                calculation=calcs,
                row_penalties=[fmt(p) for p, _, _ in row_pen],
                col_penalties=[fmt(p) for p, _, _ in col_pen],
                basis=[(r+1, c+1) for r, c in sorted(basis)],
            ))

    # ─────────────────────────────────────────────────────────────────────────
    # 位势法（MODI）
    # ─────────────────────────────────────────────────────────────────────────

    def _potentials(self, cost, allocation, basis, m, n):
        """解出所有 u_i, v_j 位势，令 u[0] = 0。"""
        u: list[Fraction | None] = [None] * m
        v: list[Fraction | None] = [None] * n
        u[0] = Fraction(0)

        changed = True
        while changed:
            changed = False
            for (i, j) in basis:
                if u[i] is not None and v[j] is None:
                    v[j] = cost[i][j] - u[i]
                    changed = True
                elif v[j] is not None and u[i] is None:
                    u[i] = cost[i][j] - v[j]
                    changed = True

        # 对孤立节点赋 0（退化情况兜底）
        for i in range(m):
            if u[i] is None:
                u[i] = Fraction(0)
        for j in range(n):
            if v[j] is None:
                v[j] = Fraction(0)

        return u, v

    def _check_numbers(self, cost, u, v, basis, m, n):
        """计算所有非基变量的检验数 σ_ij = c_ij - u_i - v_j。"""
        sigma = [[Fraction(0)] * n for _ in range(m)]
        for i in range(m):
            for j in range(n):
                if (i, j) not in basis:
                    sigma[i][j] = cost[i][j] - u[i] - v[j]
        return sigma

    # ─────────────────────────────────────────────────────────────────────────
    # 闭回路寻找（DFS）
    # ─────────────────────────────────────────────────────────────────────────

    def _find_loop(self, er, ec, basis, m, n) -> list[tuple[int, int]] | None:
        """
        从入基格 (er, ec) 出发，用 DFS 寻找闭回路。
        返回有序格子列表（不含重复的起点），奇数下标为负号顶点。
        """
        start = (er, ec)

        def dfs(path: list, horiz: bool) -> list | None:
            r, c = path[-1]
            if horiz:
                # 在第 r 行寻找不同列的基变量格
                candidates = [(r, cj) for (ri, cj) in basis if ri == r and cj != c and (ri, cj) not in path]
                for cell in candidates:
                    nr, nc = cell
                    new_path = path + [cell]
                    # 闭合条件：下一步垂直可回到起点 → nc == ec 且 len >= 3
                    if nc == ec and len(new_path) >= 3:
                        return new_path
                    res = dfs(new_path, False)
                    if res:
                        return res
            else:
                # 在第 c 列寻找不同行的基变量格
                candidates = [(ri, c) for (ri, cj) in basis if cj == c and ri != r and (ri, c) not in path]
                for cell in candidates:
                    nr, nc = cell
                    new_path = path + [cell]
                    # 闭合条件：下一步水平可回到起点 → nr == er 且 len >= 3
                    if nr == er and len(new_path) >= 3:
                        return new_path
                    res = dfs(new_path, True)
                    if res:
                        return res
            return None

        # 先尝试从水平方向出发，再尝试垂直
        for first_horiz in (True, False):
            res = dfs([start], first_horiz)
            if res:
                return res
        return None

    # ─────────────────────────────────────────────────────────────────────────
    # 快照构建工具
    # ─────────────────────────────────────────────────────────────────────────

    def _cost_snapshot(self, cost, supply, demand, m, n, allocation):
        """构建运价/分配表快照（用于 VAM 阶段）。"""
        rows = []
        for i in range(m):
            cells = []
            for j in range(n):
                alloc_val = allocation[i][j] if allocation else None
                cells.append({
                    "cost":       fmt(cost[i][j]),
                    "allocation": fmt(alloc_val) if alloc_val is not None else None,
                })
            rows.append({
                "supply": fmt(supply[i]),
                "cells":  cells,
            })
        return {
            "type":    "transport_cost_table",
            "headers": [f"d{j+1}" for j in range(n)],
            "rows":    rows,
            "demand":  [fmt(demand[j]) for j in range(n)],
        }

    def _alloc_snapshot(self, cost, allocation, sigma, u, v, basis, m, n, loop):
        """构建含检验数和位势的完整分配表快照（MODI 阶段）。"""
        loop_set = set(loop)
        loop_idx = {cell: k for k, cell in enumerate(loop)}

        rows = []
        for i in range(m):
            cells = []
            for j in range(n):
                in_loop = (i, j) in loop_set
                sign = None
                if in_loop:
                    k = loop_idx[(i, j)]
                    sign = "+" if k % 2 == 0 else "-"
                if (i, j) in basis:
                    cells.append({
                        "type": "basic",
                        "cost": fmt(cost[i][j]),
                        "allocation": fmt(allocation[i][j]),
                        "loop_sign": sign,
                    })
                else:
                    cells.append({
                        "type": "non_basic",
                        "cost": fmt(cost[i][j]),
                        "sigma": fmt(sigma[i][j]),
                        "loop_sign": sign,
                    })
            rows.append({
                "u":     fmt(u[i]),
                "cells": cells,
            })
        return {
            "type":    "transport_alloc_table",
            "headers": [f"d{j+1}" for j in range(n)],
            "rows":    rows,
            "v":       [fmt(v[j]) for j in range(n)],
        }
