# fmt: off
# =============================================================================
# Author:       王梓轩
# Project:      运筹学算法推演引擎
# Description: 整数规划模块 - 分支定界法 (Branch and Bound)。
#              维护 DFS 搜索树，逐节点调用 SimplexModule 求解 LP 松弛，
#              记录完整的节点快照、剪枝原因和最优整数解发现过程。
# =============================================================================
# fmt: on

from __future__ import annotations
from fractions import Fraction
from math import floor, ceil
from typing import Any

from base_module import (
    BaseModule, STATUS_OPTIMAL, STATUS_INFEASIBLE,
    fmt, to_fraction
)


def _safe_to_fraction(val: Any) -> Fraction:
    if isinstance(val, dict):
        if "numerator" in val and "denominator" in val:
            return Fraction(int(val["numerator"]), int(val["denominator"]))
        if "display" in val:
            return to_fraction(str(val["display"]))
    return to_fraction(val)


def _is_integer(v: Fraction) -> bool:
    return v.denominator == 1


class BranchAndBoundModule(BaseModule):
    PROBLEM_TYPE = "IP"
    MAX_NODES = 200

    def solve(self, payload: dict, options: dict) -> dict:
        self._init_steps()

        from modules.lp_simplex import SimplexModule

        objective = payload.get("objective", "max")
        c_orig = [_safe_to_fraction(v) for v in payload["c"]]
        A_orig = [[_safe_to_fraction(v) for v in row] for row in payload["A"]]
        b_orig = [_safe_to_fraction(v) for v in payload["b"]]
        ctypes_orig = list(payload.get("constraint_types", payload.get("signs", ["<="] * len(b_orig))))

        raw_int_vars = payload.get("integer_vars", payload.get("integer_indices", list(range(len(c_orig)))))
        integer_vars = set(raw_int_vars)
        var_names_orig = payload.get("variable_names") or [f"x{i+1}" for i in range(len(c_orig))]
        n_orig = len(c_orig)

        node_counter = [0]
        incumbent_z: Fraction | None = None
        incumbent_x: dict[str, Fraction] | None = None
        is_max = (objective == "max")

        def better(z_new: Fraction) -> bool:
            if incumbent_z is None:
                return True
            return z_new > incumbent_z if is_max else z_new < incumbent_z

        def solve_node_lp(extra_constraints: list) -> dict:
            A = [list(row) for row in A_orig]
            b = list(b_orig)
            ct = list(ctypes_orig)
            for (row, rhs, ctype) in extra_constraints:
                A.append(list(row))
                b.append(rhs)
                ct.append(ctype)
            return {
                "objective": objective,
                "c": c_orig,
                "A": A,
                "b": b,
                "constraint_types": ct,
                "variable_names": var_names_orig,
            }

        stack: list[tuple[int, int, list, str]] = []
        root_id = node_counter[0]
        node_counter[0] += 1
        stack.append((root_id, -1, [], "根节点（原始 LP 松弛）"))

        step = 0

        while stack:
            if step >= self.MAX_NODES:
                break

            node_id, parent_id, extra, desc = stack.pop()

            lp_payload = solve_node_lp(extra)
            simplex = SimplexModule()
            lp_result = simplex.solve(lp_payload, {"display_mode": "fraction"})
            status = lp_result.get("status")

            extra_desc = [f"  附加约束 {i+1}: {' + '.join(fmt(v)+'·'+var_names_orig[j] for j,v in enumerate(row) if v!=0)} {ct} {fmt(rhs)}"
                          for i, (row, rhs, ct) in enumerate(extra)] if extra else ["  无附加约束"]

            if status != STATUS_OPTIMAL:
                prune_reason = f"LP 松弛非最优（{status}，剪枝：不可行）"
                node_action = f"节点 {node_id}（父节点 {parent_id}）：{desc} → {prune_reason}"
                calcs = extra_desc + [prune_reason]
                self._add_step(self.snapshot(
                    step=step,
                    state_matrix={"node_id": node_id, "parent_id": parent_id, "lp_status": status, "desc": desc, "pruned": True, "prune_reason": prune_reason},
                    action=node_action,
                    calculation=calcs,
                    node_id=node_id,
                    parent_id=parent_id,
                    pruned=True,
                    prune_reason=prune_reason,
                ))
                step += 1
                continue

            final_res = lp_result.get("final_result", {})
            obj_val = final_res.get("objective_value") or lp_result.get("objective", {}).get("value")
            z_lp = _safe_to_fraction(obj_val)

            sol_dict = final_res.get("solution") or lp_result.get("solution", {})
            x_vals = {k: _safe_to_fraction(v) for k, v in sol_dict.items()}

            if not better(z_lp):
                prune_reason = f"目标值 Z={fmt(z_lp)} 不优于当前整数最优 Z={fmt(incumbent_z)}（剪枝：界）"
                node_action = f"节点 {node_id}（父节点 {parent_id}）：{prune_reason}"
                calcs = extra_desc + [f"LP 松弛最优 Z = {fmt(z_lp)}", prune_reason]
                self._add_step(self.snapshot(
                    step=step,
                    state_matrix={"node_id": node_id, "parent_id": parent_id, "z_lp": fmt(z_lp), "desc": desc, "pruned": True, "prune_reason": prune_reason},
                    action=node_action,
                    calculation=calcs,
                    node_id=node_id,
                    parent_id=parent_id,
                    z_lp=fmt(z_lp),
                    pruned=True,
                    prune_reason=prune_reason,
                ))
                step += 1
                continue

            frac_var_idx = None
            frac_var_val = None
            for i in sorted(integer_vars):
                if i >= n_orig:
                    continue
                vname = var_names_orig[i]
                val = x_vals.get(vname, Fraction(0))
                if not _is_integer(val):
                    frac_var_idx = i
                    frac_var_val = val
                    break

            if frac_var_idx is None:
                action_line = (f"节点 {node_id}：发现整数可行解！Z = {fmt(z_lp)}，"
                               f"解 = { {var_names_orig[i]: fmt(x_vals.get(var_names_orig[i], Fraction(0))) for i in range(n_orig)} }")
                if better(z_lp):
                    incumbent_z = z_lp
                    incumbent_x = dict(x_vals)
                    action_line += "  → 更新全局最优整数解！"

                calcs = extra_desc + [
                    f"LP 松弛最优 Z = {fmt(z_lp)}",
                    "所有整数变量均取整数值",
                    f"当前最优整数解: Z = {fmt(incumbent_z)}",
                ]
                self._add_step(self.snapshot(
                    step=step,
                    state_matrix={"node_id": node_id, "parent_id": parent_id, "z_lp": fmt(z_lp), "x": {k: fmt(v) for k, v in x_vals.items()}, "integer_solution": True},
                    action=action_line,
                    calculation=calcs,
                    node_id=node_id,
                    parent_id=parent_id,
                    z_lp=fmt(z_lp),
                    integer_solution=True,
                    incumbent_z=fmt(incumbent_z),
                ))
                step += 1
                continue

            vname = var_names_orig[frac_var_idx]
            fl = Fraction(floor(frac_var_val))
            ce = Fraction(ceil(frac_var_val))

            action_line = (f"节点 {node_id}：LP 松弛 Z={fmt(z_lp)}，"
                           f"{vname}={fmt(frac_var_val)}（非整数），"
                           f"分支 → {vname}≤{fmt(fl)} 和 {vname}≥{fmt(ce)}")
            calcs = extra_desc + [
                f"LP 松弛 Z = {fmt(z_lp)}",
                f"选择分支变量: {vname} = {fmt(frac_var_val)}（分母≠1，非整数）",
                f"下支: {vname} ≤ {fmt(fl)}",
                f"上支: {vname} ≥ {fmt(ce)}",
            ]
            self._add_step(self.snapshot(
                step=step,
                state_matrix={"node_id": node_id, "parent_id": parent_id, "z_lp": fmt(z_lp), "branch_var": vname, "branch_val": fmt(frac_var_val)},
                action=action_line,
                calculation=calcs,
                node_id=node_id,
                parent_id=parent_id,
                z_lp=fmt(z_lp),
                branch_var=vname,
                branch_floor=fmt(fl),
                branch_ceil=fmt(ce),
            ))
            step += 1

            branch_row = [Fraction(1) if j == frac_var_idx else Fraction(0) for j in range(n_orig)]

            lo_id = node_counter[0]; node_counter[0] += 1
            hi_id = node_counter[0]; node_counter[0] += 1

            stack.append((lo_id, node_id, extra + [(branch_row, fl, "<=")], f"{vname} ≤ {fmt(fl)}"))
            stack.append((hi_id, node_id, extra + [(branch_row, ce, ">=")], f"{vname} ≥ {fmt(ce)}"))

        if incumbent_z is None:
            return self.build_output(
                STATUS_INFEASIBLE,
                final_result={},
                error_message="搜索完整分支定界树后未找到整数可行解"
            )

        final_result = {
            "objective_value": fmt(incumbent_z),
            "solution": {k: fmt(v) for k, v in incumbent_x.items() if k in var_names_orig},
            "nodes_explored": step,
        }
        return self.build_output(STATUS_OPTIMAL, final_result)