# fmt: off
# =============================================================================
# Author:      王梓轩
# Project:     运筹学算法推演引擎
# Description: 整数规划模块 - Gomory 割平面法 (Cutting Plane / Gomory Cut)。
#              反复求解 LP 松弛，从最分数值行生成 Gomory 割约束，
#              将割约束回代到原变量空间后追加约束，重新用大M法求解。
#              全程 fractions.Fraction 精确运算，记录每条割平面的推导过程。
# =============================================================================
# fmt: on

from __future__ import annotations
from fractions import Fraction
from math import floor

from base_module import (
    BaseModule, STATUS_OPTIMAL, STATUS_INFEASIBLE, STATUS_ERROR,
    fmt, to_fraction
)


def _frac_part(v: Fraction) -> Fraction:
    """正小数部分：v - floor(v)，值域 [0, 1)。"""
    return v - Fraction(floor(v))


def _is_integer(v: Fraction) -> bool:
    return v.denominator == 1


class CuttingPlaneModule(BaseModule):
    """
    Gomory 割平面法。

    流程：
      1. 求解 LP 松弛（调用 SimplexModule）
      2. 若解全整数 → 最优
      3. 否则：选取最分数值的基变量所在行，生成 Gomory 割约束
      4. 通过 SimplexModule 的 _raw_* 属性 + 反代将割约束回到原变量空间
      5. 将新约束追加后重新用大M法求解，回到步骤 1
    """

    PROBLEM_TYPE = "IP"

    MAX_ITER = 50  # 防止无限循环

    def solve(self, payload: dict, options: dict) -> dict:
        self._init_steps()

        from modules.lp_simplex import SimplexModule

        objective    = payload["objective"]
        c_orig       = [to_fraction(v) for v in payload["c"]]
        A_orig       = [[to_fraction(v) for v in row] for row in payload["A"]]
        b_orig       = [to_fraction(v) for v in payload["b"]]
        ctypes_orig  = list(payload["constraint_types"])
        integer_vars = set(payload.get("integer_vars", range(len(c_orig))))
        var_names    = payload.get("variable_names") or [f"x{i+1}" for i in range(len(c_orig))]
        n_orig       = len(c_orig)

        # 维护当前约束集合（原始 + 历次 Gomory 割）
        current_A  = [list(row) for row in A_orig]
        current_b  = list(b_orig)
        current_ct = list(ctypes_orig)
        cuts_added = 0
        step       = 0

        for iteration in range(self.MAX_ITER):

            # ── Step A：求解当前 LP 松弛 ──────────────────────────────────
            lp_payload = {
                "objective":        objective,
                "c":                c_orig,
                "A":                current_A,
                "b":                current_b,
                "constraint_types": current_ct,
                "variable_names":   var_names,
            }
            simplex = SimplexModule()
            lp_result = simplex.solve(lp_payload, {"display_mode": "fraction"})

            if lp_result["status"] != "OPTIMAL":
                self._add_step(self.snapshot(
                    step=step,
                    state_matrix={"iteration": iteration, "lp_status": lp_result["status"]},
                    action=f"第 {iteration} 轮 LP 松弛：{lp_result['status']}，原问题不可行",
                    calculation=[lp_result.get("error_message", "LP 松弛无可行解")],
                ))
                return self.build_output(
                    STATUS_INFEASIBLE,
                    final_result={},
                    error_message=f"第 {iteration} 轮 LP 松弛不可行，问题无整数解"
                )

            z_lp   = to_fraction(lp_result["final_result"]["objective_value"])
            x_vals = {k: to_fraction(v) for k, v in lp_result["final_result"]["solution"].items()}

            # ── Step B：检查整数性 ────────────────────────────────────────
            tableau = simplex.get_final_tableau()
            basis_indices = tableau["basis_indices"]
            rhs_values = tableau["b"]
            fractional_vars = {
                var_names[col]: rhs_values[idx]
                for idx, col in enumerate(basis_indices)
                if col < n_orig and col in integer_vars
                   and not _is_integer(rhs_values[idx])
            }

            if not fractional_vars:
                # 所有整数变量已是整数 → 最优
                sol_desc = {var_names[i]: fmt(x_vals.get(var_names[i], Fraction(0)))
                            for i in range(n_orig)}
                self._add_step(self.snapshot(
                    step=step,
                    state_matrix={"iteration": iteration, "z": fmt(z_lp), "solution": sol_desc},
                    action=f"第 {iteration} 轮：所有整数变量均为整数，Z = {fmt(z_lp)}，已最优",
                    calculation=["整数性检验：所有指定变量分母 = 1 ✓",
                                 f"共添加 {cuts_added} 条 Gomory 割平面约束"],
                    z_lp=fmt(z_lp), solution=sol_desc,
                ))
                step += 1
                final_result = {
                    "objective_value": fmt(z_lp),
                    "solution":        sol_desc,
                    "cuts_added":      cuts_added,
                }
                return self.build_output(STATUS_OPTIMAL, final_result)

            # ── Step C：生成 Gomory 割平面 ────────────────────────────────
            # 选取分数部分最大的整数基变量所在行
            raw_A    = tableau["matrix_a"]
            raw_b    = tableau["b"]
            raw_basis = tableau["basis_indices"]
            var_names_ext = tableau["var_names"]

            best_row   = -1
            best_frac  = Fraction(0)
            for idx, col in enumerate(raw_basis):
                if col < n_orig and col in integer_vars:
                    f = _frac_part(raw_b[idx])
                    if f > best_frac:
                        best_frac = f
                        best_row  = idx

            if best_row == -1:
                # 没有整数基变量是分数（只有非基整数变量非零时的边缘情况）
                return self.build_output(STATUS_ERROR, final_result={},
                                         error_message="无法确定 Gomory 割目标行")

            r      = best_row
            f_rhs  = _frac_part(raw_b[r])  # frac(b_bar_r)
            basic_var_name = var_names_ext[raw_basis[r]]

            # ── 核心：生成割约束（回代到原变量空间）─────────────────────
            # 从最终单纯形表第 r 行的非基列生成割平面
            # 割约束（扩展空间中）: sum(frac(a_bar_rj) * x_j  for non-basic j) >= frac(b_bar_r)
            # 通过反代将松弛/剩余变量替换为原变量：
            #   s_k（<=约束 k 的松弛）:  s_k = b_k - sum(current_A[k] * x)
            #   e_k（>=约束 k 的剩余）:  e_k = sum(current_A[k] * x) - b_k
            cut_coeffs  = [Fraction(0)] * n_orig
            cut_rhs_acc = f_rhs            # 割约束右端项累积值

            deriv_log = [
                f"选取基变量 {basic_var_name}（行 {r+1}），b_bar = {fmt(raw_b[r])}，"
                f"小数部分 f = {fmt(f_rhs)}",
                f"Gomory 割：∑ frac(ā_rj) · xj ≥ {fmt(f_rhs)}（对所有非基变量 j）",
                "反代过程（将松弛/剩余变量还原为原始决策变量）：",
            ]

            basic_set = set(raw_basis)
            for j, vname in enumerate(var_names_ext):
                if j in basic_set:
                    continue  # 基变量在本行系数为 0 或 1，不参与割
                f_coeff = _frac_part(raw_A[r][j])
                if f_coeff == Fraction(0):
                    continue

                if j < n_orig:
                    # 原始决策变量：直接加入
                    cut_coeffs[j] += f_coeff
                    deriv_log.append(f"  列 {vname}（原始变量）: 系数 += frac({fmt(raw_A[r][j])}) = {fmt(f_coeff)}")

                elif vname.startswith("s") and vname[1:].isdigit():
                    # 松弛变量 s{k+1}，对应 current_A[k]（<= 约束 k）
                    k = int(vname[1:]) - 1
                    if k < len(current_A):
                        deriv_log.append(f"  列 {vname}（约束 {k+1} 松弛, frac_coeff={fmt(f_coeff)}）："
                                         f" s{k+1} = b{k+1} - A{k+1}·x，反代：")
                        for j2 in range(n_orig):
                            contrib = -f_coeff * current_A[k][j2]
                            if contrib != 0:
                                cut_coeffs[j2] += contrib
                                deriv_log.append(f"    x{j2+1} 系数 += {fmt(contrib)}")
                        # b_k 移到右端（符号取反进入 RHS 累积）
                        cut_rhs_acc -= f_coeff * current_b[k]
                        deriv_log.append(f"    cut_rhs -= {fmt(f_coeff)} × {fmt(current_b[k])} "
                                         f"= {fmt(f_coeff * current_b[k])}")

                elif vname.startswith("e") and vname[1:].isdigit():
                    # 剩余变量 e{k+1}，对应 current_A[k]（>= 约束 k）
                    k = int(vname[1:]) - 1
                    if k < len(current_A):
                        deriv_log.append(f"  列 {vname}（约束 {k+1} 剩余, frac_coeff={fmt(f_coeff)}）："
                                         f" e{k+1} = A{k+1}·x - b{k+1}，反代：")
                        for j2 in range(n_orig):
                            contrib = f_coeff * current_A[k][j2]
                            if contrib != 0:
                                cut_coeffs[j2] += contrib
                                deriv_log.append(f"    x{j2+1} 系数 += {fmt(contrib)}")
                        cut_rhs_acc += f_coeff * current_b[k]
                        deriv_log.append(f"    cut_rhs += {fmt(f_coeff)} × {fmt(current_b[k])}")
                # 人工变量不出现在最优解（忽略）

            # 格式化割平面方程
            cut_str_lhs = " + ".join(
                f"({fmt(cut_coeffs[j])}){var_names[j]}"
                for j in range(n_orig)
                if cut_coeffs[j] != 0
            ) or "0"
            cut_str = f"{cut_str_lhs} ≥ {fmt(cut_rhs_acc)}"
            deriv_log.append(f"最终 Gomory 割约束：{cut_str}")

            # 记录割平面生成步骤
            self._add_step(self.snapshot(
                step=step,
                state_matrix={
                    "iteration": iteration,
                    "z_lp":      fmt(z_lp),
                    "fractional_vars": {k: fmt(v) for k, v in fractional_vars.items()},
                    "gomory_cut": cut_str,
                },
                action=(f"第 {iteration} 轮 LP 最优 Z={fmt(z_lp)}，"
                        f"变量 {basic_var_name}={fmt(raw_b[r])} 非整数，"
                        f"生成第 {cuts_added+1} 条 Gomory 割约束: {cut_str}"),
                calculation=deriv_log,
                z_lp=fmt(z_lp),
                gomory_cut=cut_str,
                cut_row=best_row,
            ))
            step += 1
            cuts_added += 1

            # ── 将割约束追加到当前约束集（预翻转以与 SimplexModule 内部行为同步）─
            # SimplexModule 当约束右端 b<0 时会自动翻转：>= b_neg → <= -b_neg，A 取反。
            # 必须以翻转后的形式存储，才能在下轮反代时套用 s_k = b_k - A_k·x 的公式。
            if cut_rhs_acc < Fraction(0):
                store_A  = [-cut_coeffs[j] for j in range(n_orig)]  # A 取反
                store_b  = -cut_rhs_acc                               # b 取正
                store_ct = "<="                                        # 切换 <= 后用松弛变量
            else:
                store_A  = [cut_coeffs[j] for j in range(n_orig)]
                store_b  = cut_rhs_acc
                store_ct = ">="

            current_A.append(store_A)
            current_b.append(store_b)
            current_ct.append(store_ct)

        # 超过最大迭代次数
        return self.build_output(
            STATUS_ERROR,
            final_result={},
            error_message=f"超过最大迭代次数 {self.MAX_ITER}，割平面法未收敛"
        )
