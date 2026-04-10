# fmt: off
# =============================================================================
# Author:      王梓轩
# Project:     运筹学算法推演引擎
# Description: 二维线性规划图解法模块 (LP Graphical Method)
#              严格使用纯 Python 和 fractions 精确推演。
#              求出所有边界交点，过滤可行域顶点，计算各顶点 Z 值并确定最优解。
# =============================================================================
# fmt: on

from __future__ import annotations
from fractions import Fraction
from base_module import (
    BaseModule, STATUS_OPTIMAL, STATUS_INFEASIBLE, STATUS_ERROR,
    fmt, to_fraction
)

class GraphicalModule(BaseModule):
    """图解法模块，仅适用于 2 变量线性规划。"""

    PROBLEM_TYPE = "LP"

    def solve(self, payload: dict, options: dict) -> dict:
        self._init_steps()
        
        c = [to_fraction(v) for v in payload["c"]]
        A = [[to_fraction(v) for v in r] for r in payload["A"]]
        b = [to_fraction(v) for v in payload["b"]]
        constraint_types = payload["constraint_types"]
        var_names = payload.get("variable_names", ["x1", "x2"])
        objective = payload.get("objective", "max")

        if len(c) != 2:
            return self.build_output(STATUS_ERROR, {}, error_message="图解法仅支持 2 个决策变量")

        m = len(A)
        # 提取所有边界直线
        # 形式：a*x1 + b*x2 = d
        lines = []
        for i in range(m):
            lines.append({
                "source": f"约束 {i+1}",
                "a1": A[i][0], "a2": A[i][1], "d": b[i],
                "type": constraint_types[i]
            })
        
        # 加上非负约束直线
        lines.append({"source": "非负 x1>=0", "a1": Fraction(1), "a2": Fraction(0), "d": Fraction(0), "type": ">="})
        lines.append({"source": "非负 x2>=0", "a1": Fraction(0), "a2": Fraction(1), "d": Fraction(0), "type": ">="})

        step0_calcs = [f" {L['source']}: {fmt(L['a1'])}*{var_names[0]} + {fmt(L['a2'])}*{var_names[1]} = {fmt(L['d'])}" for L in lines]
        self._add_step(self.snapshot(
            step=0,
            state_matrix={},
            action=f"步骤 1：提取方程的所有 {len(lines)} 条边界直线",
            calculation=step0_calcs
        ))

        # 两两求交点
        intersections = []
        inter_calcs = []
        n_lines = len(lines)
        for i in range(n_lines):
            for j in range(i + 1, n_lines):
                L1, L2 = lines[i], lines[j]
                # a1*x + b1*y = d1
                # a2*x + b2*y = d2
                det = L1["a1"] * L2["a2"] - L1["a2"] * L2["a1"]
                if det == 0:
                    inter_calcs.append(f"{L1['source']} 与 {L2['source']} 平行或重合，无唯一交点")
                    continue
                
                x1 = (L1["d"] * L2["a2"] - L1["a2"] * L2["d"]) / det
                x2 = (L1["a1"] * L2["d"] - L1["d"] * L2["a1"]) / det
                
                # Check if it already exists to avoid duplicates
                duplicate = False
                for pt in intersections:
                    if pt["x1"] == x1 and pt["x2"] == x2:
                        pt["sources"].append(f"{L1['source']} ∩ {L2['source']}")
                        duplicate = True
                        break
                
                if not duplicate:
                    intersections.append({
                        "x1": x1, "x2": x2, 
                        "sources": [f"{L1['source']} ∩ {L2['source']}"]
                    })
                    inter_calcs.append(f"{L1['source']} ∩ {L2['source']} => ({fmt(x1)}, {fmt(x2)})")

        self._add_step(self.snapshot(
            step=1,
            state_matrix={},
            action=f"步骤 2：约束直线两两联立，求得 {len(intersections)} 个不重复交点",
            calculation=inter_calcs
        ))

        # 过滤可行域顶点
        feasible_vertices = []
        filter_calcs = []
        for pt in intersections:
            x1, x2 = pt["x1"], pt["x2"]
            is_feasible = True
            reasons = []
            
            # 检测非负
            if x1 < 0:
                is_feasible = False
                reasons.append(f"{var_names[0]}={fmt(x1)} < 0")
            if x2 < 0:
                is_feasible = False
                reasons.append(f"{var_names[1]}={fmt(x2)} < 0")
            
            # 检测约束
            for i in range(m):
                val = A[i][0] * x1 + A[i][1] * x2
                if constraint_types[i] == "<=" and val > b[i]:
                    is_feasible = False
                    reasons.append(f"违反约束{i+1}: {fmt(val)} > {fmt(b[i])}")
                elif constraint_types[i] == ">=" and val < b[i]:
                    is_feasible = False
                    reasons.append(f"违反约束{i+1}: {fmt(val)} < {fmt(b[i])}")
                elif constraint_types[i] == "=" and val != b[i]:
                    is_feasible = False
                    reasons.append(f"违反约束{i+1}: {fmt(val)} != {fmt(b[i])}")
            
            if is_feasible:
                feasible_vertices.append(pt)
                filter_calcs.append(f"点 ({fmt(x1)}, {fmt(x2)}) 满足所有约束，保留为顶点")
            else:
                filter_calcs.append(f"点 ({fmt(x1)}, {fmt(x2)}) 被界外剔除: {', '.join(reasons)}")

        if not feasible_vertices:
            self._add_step(self.snapshot(
                step=2,
                state_matrix={},
                action="步骤 3：过滤可行域顶点完成，可行域为空集",
                calculation=filter_calcs
            ))
            return self.build_output(STATUS_INFEASIBLE, {}, error_message="可行域为空集，问题无解")

        self._add_step(self.snapshot(
            step=2,
            state_matrix={},
            action=f"步骤 3：过滤可行域顶点完成，共得到 {len(feasible_vertices)} 个有效极点",
            calculation=filter_calcs
        ))

        # 计算 Z 值
        best_pt = None
        best_z = float('-inf') if objective == "max" else float('inf')
        z_calcs = []
        
        for pt in feasible_vertices:
            x1, x2 = pt["x1"], pt["x2"]
            z_val = c[0] * x1 + c[1] * x2
            pt["z"] = z_val
            z_calcs.append(f"顶点 ({fmt(x1)}, {fmt(x2)}) 的目标函数 Z = {fmt(c[0])}*{fmt(x1)} + {fmt(c[1])}*{fmt(x2)} = {fmt(z_val)}")
            
            if objective == "max" and z_val > best_z:
                best_z = z_val
                best_pt = pt
            elif objective == "min" and z_val < best_z:
                best_z = z_val
                best_pt = pt

        action_str = f"步骤 4：计算各顶点 Z 值，最优解在 ({fmt(best_pt['x1'])}, {fmt(best_pt['x2'])}) 处取得 Z={fmt(best_z)}"
        z_calcs.append(f"综合比较，最优点为: ({fmt(best_pt['x1'])}, {fmt(best_pt['x2'])}), 最优Z = {fmt(best_z)}")

        self._add_step(self.snapshot(
            step=3,
            state_matrix={},
            action=action_str,
            calculation=z_calcs
        ))

        final_result = {
            "objective_value": fmt(best_z),
            "solution": {
                var_names[0]: fmt(best_pt["x1"]),
                var_names[1]: fmt(best_pt["x2"])
            },
            "feasible_vertices": [{"x1": fmt(pt["x1"]), "x2": fmt(pt["x2"]), "z": fmt(pt["z"])} for pt in feasible_vertices],
            "boundary_lines": [{"a1": fmt(L["a1"]), "a2": fmt(L["a2"]), "d": fmt(L["d"]), "type": L["type"]} for L in lines]
        }

        return self.build_output(STATUS_OPTIMAL, final_result)
