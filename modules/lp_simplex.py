# fmt: off
# =============================================================================
# Author:      王梓轩
# Project:     运筹学算法推演引擎
# Description: 单纯形法模块（Simplex Method）。
#              处理标准线性规划问题，使用大 M 法解决 >= 和 = 约束。
#              维护并记录每一步迭代的单纯形表和初等行变换。
# =============================================================================
# fmt: on

from base_module import (
    BaseModule, ORRuntimeError, STATUS_OPTIMAL,
    STATUS_INFEASIBLE, STATUS_UNBOUNDED,
    fmt, fmt_matrix, to_fraction
)
from fractions import Fraction

# 大 M 法使用的一个巨大的有理数常量，用于识别人工变量的检验数
M_VALUE = Fraction(10**9)


class SimplexModule(BaseModule):
    PROBLEM_TYPE = "LP"

    def solve(self, payload: dict, options: dict) -> dict:
        self._init_steps()

        # 解析与预处理
        is_min = payload["objective"] == "min"
        
        # 转换为有理数，防止浮点误差
        A = [[to_fraction(v) for v in row] for row in payload["A"]]
        b = [to_fraction(v) for v in payload["b"]]
        c = [to_fraction(v) for v in payload["c"]]
        constraint_types = list(payload["constraint_types"])

        n_orig_vars = len(c)
        m = len(b)

        orig_var_names = payload.get("variable_names")
        if not orig_var_names:
            orig_var_names = [f"x{i+1}" for i in range(n_orig_vars)]

        # ----- 1. 右端项置正 -----
        for i in range(m):
            if b[i] < 0:
                b[i] *= -1
                A[i] = [-val for val in A[i]]
                if constraint_types[i] == "<=":
                    constraint_types[i] = ">="
                elif constraint_types[i] == ">=":
                    constraint_types[i] = "<="

        # ----- 2. 目标函数转化为 max，并引入新变量 -----
        # 如果原始是 min，这里取反，使得算法内部只解 max
        c_work = [-val for val in c] if is_min else list(c)
        
        var_names = list(orig_var_names)
        basis = []          # 记录基变量的下标 (0-indexed)
        artificials = set() # 记录人工变量下标
        
        # 遍历每一行，依据 constraint_types 添加变量
        for i in range(m):
            ctype = constraint_types[i]
            if ctype == "<=":
                # 加上松弛变量 (Slack)
                var_names.append(f"s{i+1}")
                c_work.append(Fraction(0))
                for j in range(m):
                    A[j].append(Fraction(1) if i == j else Fraction(0))
                basis.append(len(var_names) - 1)
            elif ctype == ">=":
                # 减去剩余变量 (Surplus)
                var_names.append(f"e{i+1}")
                c_work.append(Fraction(0))
                for j in range(m):
                    A[j].append(Fraction(-1) if i == j else Fraction(0))
                # 加上人工变量 (Artificial)
                var_names.append(f"a{i+1}")
                c_work.append(-M_VALUE) # 大 M
                for j in range(m):
                    A[j].append(Fraction(1) if i == j else Fraction(0))
                basis.append(len(var_names) - 1)
                artificials.add(len(var_names) - 1)
            elif ctype == "=":
                # 加上人工变量 (Artificial)
                var_names.append(f"a{i+1}")
                c_work.append(-M_VALUE) # 大 M
                for j in range(m):
                    A[j].append(Fraction(1) if i == j else Fraction(0))
                basis.append(len(var_names) - 1)
                artificials.add(len(var_names) - 1)

        n_total_vars = len(var_names)
        
        # 为了方便后续的初等行变换，我们在单纯形表里面维护 Cj - Zj。
        # 初始时，Zj = C_B * A，我们通过初等行变换将基变量列归一为标准单位阵的形式，同时也把检验数行归零。
        # 我们用额外的一行 (m 索引) 来存放 Cj - Zj。
        
        # 初始化检验数行 (Cj - Zj)。由于尚未计入人工变量对应基的影响，它直接赋值为 c_work
        # 也就是还不是最终的检验数，必须通过将基变量所在列对应的系数消为 0，来得到正确的初始检验数。
        check_row = list(c_work) 
        
        # ----- 3. 构建初始单纯形表，并归一化检验数行 -----
        for i in range(m):
            b_var = basis[i]
            b_cost = c_work[b_var]
            if b_cost != 0:
                # 检验数行 R_c = R_c - b_cost * R_i
                for j in range(n_total_vars):
                    check_row[j] -= b_cost * A[i][j]
                    
        # current_z 代表目标函数的相反数，即 -Z。当基变量改变，-Z 也会经过同样的行变换
        # -Z 的初始值为 0 - sum(c_Bi * b_i)
        current_z = Fraction(0)
        for i in range(m):
            current_z -= c_work[basis[i]] * b[i]

        iteration_count = 0
        
        # --- 记录初始单纯形表 (Step 0) ---
        self._record_snapshot(
            step=iteration_count,
            A=A, b=b, check_row=check_row, current_z=current_z, 
            basis=basis, var_names=var_names, 
            action="添加松弛/人工变量，构建初始单纯形表（基于大M法）",
            calculation=[], entering=None, leaving=None, thetas=None
        )
        
        # ----- 4. 开始迭代寻找最优解 -----
        while True:
            # 找到最大的正检验数
            max_check_val = Fraction(0)
            entering_var = -1
            
            for j in range(n_total_vars):
                if check_row[j] > max_check_val:
                    max_check_val = check_row[j]
                    entering_var = j
            
            # 如果没有正检验数，则达到最优状态
            if max_check_val <= 0:
                break
                
            # 寻找最小的正比值 theta
            min_theta = None
            leaving_index = -1
            thetas = []
            
            for i in range(m):
                a_ij = A[i][entering_var]
                if a_ij > 0:
                    theta = b[i] / a_ij
                    thetas.append(theta)
                    if min_theta is None or theta < min_theta:
                        min_theta = theta
                        leaving_index = i
                else:
                    thetas.append(None)
                    
            if leaving_index == -1:
                # 均无正元素，无界解
                self._record_snapshot( # 再记录一次为了在结果里展示无界在哪列
                    step=iteration_count+1,
                    A=A, b=b, check_row=check_row, current_z=current_z, 
                    basis=basis, var_names=var_names, 
                    action=f"入基变量 {var_names[entering_var]} 所在列全部系数 <= 0，问题无界",
                    calculation=[], entering=entering_var, leaving=None, thetas=thetas
                )
                return self.build_output(
                    STATUS_UNBOUNDED,
                    final_result={},
                    error_message=f"变量 {var_names[entering_var]} 进入基底时无界解"
                )

            # ----- 5. 换基与矩阵行变换 -----
            iteration_count += 1
            pivot_row = leaving_index
            pivot_elem = A[pivot_row][entering_var]
            leaving_var = basis[pivot_row]
            
            action_desc = f"入基：{var_names[entering_var]} (检验数={self._fmt_M(check_row[entering_var])})，" \
                          f"出基：{var_names[leaving_var]} (\u03b8={fmt(min_theta)})"
                          
            calc_logs = []
            
            # (1) 主元行归一化
            if pivot_elem != 1:
                A[pivot_row] = [val / pivot_elem for val in A[pivot_row]]
                b[pivot_row] = b[pivot_row] / pivot_elem
                calc_logs.append(f"R{pivot_row+1} = R{pivot_row+1} / {fmt(pivot_elem)}")
            
            # (2) 消去其他行的该列
            for i in range(m):
                if i != pivot_row and A[i][entering_var] != 0:
                    factor = A[i][entering_var]
                    A[i] = [A[i][j] - factor * A[pivot_row][j] for j in range(n_total_vars)]
                    b[i] = b[i] - factor * b[pivot_row]
                    sign = "-" if factor > 0 else "+"
                    calc_logs.append(f"R{i+1} = R{i+1} {sign} {fmt(abs(factor))} \u00d7 R{pivot_row+1}")
                    
            # (3) 消去检验数行的该列
            if check_row[entering_var] != 0:
                factor = check_row[entering_var]
                check_row = [check_row[j] - factor * A[pivot_row][j] for j in range(n_total_vars)]
                current_z = current_z - factor * b[pivot_row]
                sign = "-" if factor > 0 else "+"
                calc_logs.append(f"\u68c0\u9a8c\u884c = \u68c0\u9a8c\u884c {sign} {self._fmt_M(abs(factor))} \u00d7 R{pivot_row+1}")
                
            # 更新基变量
            basis[pivot_row] = entering_var
            
            # 记录当前迭代结果（pivot_elem_str 在行变换前已格式化，避免变换后恒为1）
            self._record_snapshot(
                step=iteration_count,
                A=A, b=b, check_row=check_row, current_z=current_z,
                basis=basis, var_names=var_names,
                action=action_desc,
                calculation=calc_logs, entering=entering_var, leaving=leaving_index,
                thetas=thetas, pivot_elem_str=fmt(pivot_elem)
            )
            
        # ----- 6. 终局状态判定 -----
        # 判断可行性：是否存在人工变量且取值大于零
        infeasible = False
        for i in range(m):
            if basis[i] in artificials and b[i] > 0:
                infeasible = True
                break
                
        if infeasible:
            return self.build_output(
                STATUS_INFEASIBLE,
                final_result={},
                error_message="最优状态下仍包含非零人工变量，原问题无可行解"
            )
            
        # 组装最优解
        opt_z = current_z * -1 # 因为 current_z 实际上是 -Z
        if is_min:
            opt_z = opt_z * -1 # 若原来是 min 问题则取反回来
            
        vars_result = {}
        for idx in range(n_orig_vars): # 仅返回原问题变量的值
            vars_result[orig_var_names[idx]] = 0
            
        for i in range(m):
            if basis[i] < n_orig_vars:
                # 只赋予原本决策变量值
                vars_result[orig_var_names[basis[i]]] = b[i]
                
        final_result = {
            "objective_value": fmt(opt_z),
            "solution": {k: fmt(v) for k, v in vars_result.items()}
        }

        # ── 保存原始最终状态（供 IP 模块提取 Gomory 割平面用）────────────────
        # 注意：这些属性是 Fraction 对象，不进入 JSON 序列化路径
        self._raw_A         = A                  # 最终单纯形表（二维 Fraction 列表）
        self._raw_b         = b                  # 最终 RHS（Fraction 列表）
        self._raw_basis     = basis              # 基变量列索引列表
        self._raw_var_names = var_names          # 所有变量名称列表
        self._raw_check_row = check_row          # 最终检验数行
        self._raw_n_orig    = n_orig_vars        # 原始决策变量数
        self._raw_is_min    = is_min             # 是否为 min 问题

        return self.build_output(STATUS_OPTIMAL, final_result)

    # ----- 辅助工具方法 -----
    
    def _fmt_M(self, value: Fraction) -> str:
        """
        专门处理携带大 M 的数值格式化。
        如果接近于大M的倍数，转换为带 M 的表达式展示，以更符合手算直觉。
        """
        val_f = float(value)
        # 用一个较小的比例判断是否属于大 M 范畴
        m_float = float(M_VALUE)
        coeff_m = round(val_f / m_float)
        
        if coeff_m != 0:
            remainder = value - Fraction(coeff_m) * M_VALUE
            m_str = f"{coeff_m}M" if coeff_m != 1 else "M"
            if coeff_m == -1: m_str = "-M"
            
            if remainder == 0:
                return m_str
            elif remainder > 0:
                return f"{m_str}+{fmt(remainder)}"
            else:
                return f"{m_str}{fmt(remainder)}" # 自带负号
        return fmt(value)

    def _record_snapshot(self, step, A, b, check_row, current_z, basis, var_names,
                          action, calculation, entering, leaving, thetas,
                          pivot_elem_str: str | None = None):
        """格式化并记录单纯形表快照（所有数值均转为字符串以保证 JSON 可序列化）"""
        m = len(A)
        n = len(var_names)
        headers = ["", *var_names, "b", "\u03b8"]

        # 组装约束行数据（A 矩阵系数全部格式化为字符串）
        rows = []
        for i in range(m):
            # A[i][j] 是普通 Fraction，用 fmt；b[i] 也是普通 Fraction，用 fmt
            formatted_coefs = [self._fmt_M(x) for x in A[i]] + [fmt(b[i])]

            # θ 列
            theta_val = thetas[i] if (thetas is not None and i < len(thetas)) else None
            formatted_coefs.append(fmt(theta_val) if theta_val is not None else "\u2014")

            rows.append({
                "basis_var": var_names[basis[i]],
                "coefficients": formatted_coefs
            })

        # 检验数行（c_j - z_j）和当前目标值，全部字符串化
        check_fmt = [self._fmt_M(c) for c in check_row] + [self._fmt_M(current_z), "\u2014"]

        matrix_dict = {
            "headers": headers,
            "rows":    rows,
            "check_row": check_fmt
        }

        # pivot 信息（仅在正常换基时填充）
        pivot = None
        if entering is not None and leaving is not None:
            pivot = {
                "entering_var":  var_names[entering],
                "leaving_var":   var_names[basis[leaving]],
                # pivot_elem_str 是行变换前传入的原始主元（已格式化字符串，JSON 安全）
                "pivot_element": pivot_elem_str,
                "pivot_position": [leaving, entering]
            }

        snap = self.snapshot(
            step=step,
            state_matrix=matrix_dict,
            action=action,
            calculation=calculation,
            basis=[var_names[i] for i in basis],
            pivot=pivot
        )
        self._add_step(snap)
