# fmt: off
# =============================================================================
# Author:      王梓轩
# Project:     运筹学算法推演引擎
# Description: 博弈论模块（Game Theory）— 二人零和博弈。
#              阶段一：纯策略鞍点检验（Maximin / Minimax）。
#              阶段二：混合策略转化为线性规划，内部调用 SimplexModule 求解，
#              精确还原概率分布 p_i / q_j 及对策值 V（全 Fraction 推演）。
# =============================================================================
# fmt: on

from __future__ import annotations
from fractions import Fraction

from base_module import (
    BaseModule, STATUS_OPTIMAL, STATUS_ERROR,
    fmt, to_fraction
)


class GameTheoryModule(BaseModule):
    """二人零和博弈求解模块。"""

    PROBLEM_TYPE = "GT"

    # ─────────────────────────────────────────────────────────────────────────
    # 主入口
    # ─────────────────────────────────────────────────────────────────────────

    def solve(self, payload: dict, options: dict) -> dict:
        self._init_steps()

        raw = payload["payoff_matrix"]
        m   = len(raw)          # 行数（甲方策略数）
        n   = len(raw[0])       # 列数（乙方策略数）
        A   = [[to_fraction(raw[i][j]) for j in range(n)] for i in range(m)]

        # ── 阶段一：纯策略鞍点检验 ────────────────────────────────────────────
        row_mins = [min(A[i]) for i in range(m)]
        col_maxs = [max(A[i][j] for i in range(m)) for j in range(n)]
        alpha    = max(row_mins)   # Maximin（甲方下限）
        beta     = min(col_maxs)   # Minimax（乙方上限）

        phase1_calcs = ["── 纯策略鞍点检验 ──"]
        for i, rm in enumerate(row_mins):
            phase1_calcs.append(f"  行 {i+1} 最小值 = {fmt(rm)}")
        phase1_calcs.append(f"  α (Maximin) = max{{{', '.join(fmt(v) for v in row_mins)}}} = {fmt(alpha)}")
        for j, cm in enumerate(col_maxs):
            phase1_calcs.append(f"  列 {j+1} 最大值 = {fmt(cm)}")
        phase1_calcs.append(f"  β (Minimax) = min{{{', '.join(fmt(v) for v in col_maxs)}}} = {fmt(beta)}")
        phase1_calcs.append(f"  {'α = β = ' + fmt(alpha) + '，存在纯策略鞍点' if alpha == beta else 'α ≠ β，无纯策略鞍点，需使用混合策略'}")

        if alpha == beta:
            # 找鞍点坐标
            saddle_pts = [(i+1, j+1) for i in range(m) for j in range(n)
                          if A[i][j] == alpha and A[i][j] == row_mins[i] and A[i][j] == col_maxs[j]]
            self._add_step(self.snapshot(
                step=0,
                state_matrix=self._payoff_snap(A, m, n, saddle_pts),
                action=f"阶段一：发现纯策略鞍点 {saddle_pts}，对策值 V = {fmt(alpha)}",
                calculation=phase1_calcs,
                alpha=fmt(alpha), beta=fmt(beta), saddle_points=saddle_pts,
            ))
            # 纯策略：鞍点所在行/列确定最优策略
            si, sj = saddle_pts[0]
            final_result = {
                "type":          "pure_strategy",
                "game_value":    fmt(alpha),
                "player1_strategy": f"行 {si}（纯策略）",
                "player2_strategy": f"列 {sj}（纯策略）",
                "saddle_points": saddle_pts,
            }
            return self.build_output(STATUS_OPTIMAL, final_result)

        # α ≠ β，进入混合策略
        self._add_step(self.snapshot(
            step=0,
            state_matrix=self._payoff_snap(A, m, n, []),
            action=f"阶段一：α={fmt(alpha)} ≠ β={fmt(beta)}，无纯策略鞍点，转入混合策略 LP",
            calculation=phase1_calcs,
            alpha=fmt(alpha), beta=fmt(beta),
        ))

        # ── 阶段二：构造 LP 求混合策略 ────────────────────────────────────────
        # 步骤 2.1：若矩阵含 ≤ 0 元素，平移使所有元素 > 0
        A_min = min(A[i][j] for i in range(m) for j in range(n))
        K     = Fraction(0)
        if A_min <= 0:
            K = abs(A_min) + Fraction(1)

        A_prime = [[A[i][j] + K for j in range(n)] for i in range(m)]
        shift_calcs = [
            f"矩阵最小元素 = {fmt(A_min)}",
            f"平移常数 K = {fmt(K)}（使 A' = A + K 所有元素 > 0）" if K > 0
            else "矩阵所有元素已 > 0，K = 0，无需平移",
        ]
        if K > 0:
            for i in range(m):
                shift_calcs.append(f"  A'[{i+1}] = [{', '.join(fmt(v) for v in A_prime[i])}]")

        self._add_step(self.snapshot(
            step=1,
            state_matrix=self._payoff_snap(A_prime, m, n, []),
            action=f"阶段二.1：矩阵平移 K={fmt(K)} → A'，准备构建 LP",
            calculation=shift_calcs,
            K=fmt(K),
        ))

        from modules.lp_simplex import SimplexModule

        # ── 步骤 2.2：甲方（行玩家）LP ───────────────────────────────────────
        # 变量 xi = pi / V'，min sum(xi)，s.t. A'^T * x >= 1，x >= 0
        # A'^T 的每一行对应乙方一列 j：sum_i(a'_ij * xi) >= 1
        A_T  = [[A_prime[i][j] for i in range(m)] for j in range(n)]   # shape: n × m
        lp1  = {
            "objective":        "min",
            "c":                [Fraction(1)] * m,
            "A":                A_T,
            "b":                [Fraction(1)] * n,
            "constraint_types": [">="] * n,
            "variable_names":   [f"x{i+1}" for i in range(m)],
        }

        lp1_calcs = [
            "甲方 LP（行玩家混合策略）：",
            f"  变量: x_i = p_i / V'（i=1..{m}）",
            "  min  Σx_i",
            "  s.t. A'^T · x ≥ 1（即：乙方每列期望收益 ≥ 1）",
            "  x_i ≥ 0",
            f"  A'^T（{n}×{m} 矩阵）：",
        ]
        for j in range(n):
            lp1_calcs.append(f"    列{j+1}约束: {' + '.join(f'{fmt(A_prime[i][j])}·x{i+1}' for i in range(m))} ≥ 1")

        self._add_step(self.snapshot(
            step=2,
            state_matrix={"lp_type": "player1", "A_prime": [[fmt(v) for v in row] for row in A_prime]},
            action="阶段二.2：构建甲方 LP（min Σxi，s.t. A'^T·x ≥ 1）",
            calculation=lp1_calcs,
        ))

        s1 = SimplexModule()
        r1 = s1.solve(lp1, {})
        if r1["status"] != "OPTIMAL":
            return self.build_output(STATUS_ERROR, final_result={},
                                     error_message=f"甲方 LP 求解失败：{r1.get('error_message')}")

        x_vals     = [to_fraction(r1["final_result"]["solution"].get(f"x{i+1}", "0")) for i in range(m)]
        sum_x      = sum(x_vals)
        V_prime    = Fraction(1) / sum_x        # V' = 1 / Σx_i（平移后对策值）
        p_vals     = [xi * V_prime for xi in x_vals]
        V          = V_prime - K                # 原始对策值

        decode_calcs_p1 = [
            "── 甲方 LP 解码 ──",
            f"  LP 最优解 x* = [{', '.join(fmt(v) for v in x_vals)}]",
            f"  Σx_i* = {fmt(sum_x)}",
            f"  V' = 1 / Σx_i* = {fmt(V_prime)}（平移后对策值）",
            f"  原始对策值 V = V' - K = {fmt(V_prime)} - {fmt(K)} = {fmt(V)}",
        ]
        for i in range(m):
            decode_calcs_p1.append(f"  p_{i+1} = x_{i+1}* × V' = {fmt(x_vals[i])} × {fmt(V_prime)} = {fmt(p_vals[i])}")
        decode_calcs_p1.append(f"  验证: Σp_i = {fmt(sum(p_vals))} ≈ 1 ✓")

        # ── 步骤 2.3：乙方（列玩家）LP ───────────────────────────────────────
        # min Σyj，s.t. A' * y <= 1 → 等价 max Σyj，s.t. A' * y <= 1，yj >= 0
        lp2 = {
            "objective":        "max",
            "c":                [Fraction(1)] * n,
            "A":                [list(row) for row in A_prime],
            "b":                [Fraction(1)] * m,
            "constraint_types": ["<="] * m,
            "variable_names":   [f"y{j+1}" for j in range(n)],
        }
        s2     = SimplexModule()
        r2     = s2.solve(lp2, {})
        if r2["status"] != "OPTIMAL":
            return self.build_output(STATUS_ERROR, final_result={},
                                     error_message=f"乙方 LP 求解失败：{r2.get('error_message')}")

        y_vals  = [to_fraction(r2["final_result"]["solution"].get(f"y{j+1}", "0")) for j in range(n)]
        sum_y   = sum(y_vals)
        W_prime = Fraction(1) / sum_y if sum_y != 0 else Fraction(0)
        q_vals  = [yj * W_prime for yj in y_vals]

        decode_calcs_p2 = [
            "── 乙方 LP 解码 ──",
            f"  LP 最优解 y* = [{', '.join(fmt(v) for v in y_vals)}]",
            f"  Σy_j* = {fmt(sum_y)}，W' = 1/Σy_j* = {fmt(W_prime)}",
            f"  理论上 W' = V' = {fmt(V_prime)}（对偶定理）",
        ]
        for j in range(n):
            decode_calcs_p2.append(f"  q_{j+1} = y_{j+1}* × W' = {fmt(y_vals[j])} × {fmt(W_prime)} = {fmt(q_vals[j])}")
        decode_calcs_p2.append(f"  验证: Σq_j = {fmt(sum(q_vals))} ≈ 1 ✓")

        self._add_step(self.snapshot(
            step=3,
            state_matrix={"lp_type": "both_players",
                          "x_vals": [fmt(v) for v in x_vals],
                          "y_vals": [fmt(v) for v in y_vals]},
            action=f"阶段二.3：LP 求解完成，对策值 V = {fmt(V)}",
            calculation=decode_calcs_p1 + [""] + decode_calcs_p2,
            game_value=fmt(V),
            p_vals=[fmt(v) for v in p_vals],
            q_vals=[fmt(v) for v in q_vals],
        ))

        final_result = {
            "type":             "mixed_strategy",
            "game_value":       fmt(V),
            "player1_strategy": {f"行{i+1}": fmt(p_vals[i]) for i in range(m)},
            "player2_strategy": {f"列{j+1}": fmt(q_vals[j]) for j in range(n)},
            "K_shift":          fmt(K),
            "V_prime":          fmt(V_prime),
        }
        return self.build_output(STATUS_OPTIMAL, final_result)

    # ─────────────────────────────────────────────────────────────────────────
    # 快照构建
    # ─────────────────────────────────────────────────────────────────────────

    def _payoff_snap(self, A, m, n, saddle_pts):
        """构建收益矩阵快照。"""
        saddle_set = set(saddle_pts)
        rows = []
        for i in range(m):
            cells = []
            for j in range(n):
                cells.append({
                    "value":   fmt(A[i][j]),
                    "saddle":  (i+1, j+1) in saddle_set,
                })
            rows.append({"row": i+1, "cells": cells})
        return {
            "type": "payoff_matrix",
            "rows": rows,
            "m": m, "n": n,
        }
