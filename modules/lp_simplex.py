"""Exact two-phase simplex solver."""
from __future__ import annotations
from copy import deepcopy
from fractions import Fraction
from base_module import (BaseModule, STATUS_OPTIMAL, STATUS_INFEASIBLE,
    STATUS_UNBOUNDED, STATUS_MAX_ITER_REACHED, fmt, to_fraction, rationalize)


class SimplexModule(BaseModule):
    PROBLEM_TYPE = "LP"

    def __init__(self):
        self.final_tableau = None
        self._basis_matrix = []
        self._original_variable_count = 0
        self._original_variable_names = []
        self._is_min = False

    def solve(self, payload: dict, options: dict) -> dict:
        self._init_steps()
        self.final_tableau = None
        self._is_min = payload["objective"] == "min"
        c0 = [to_fraction(v) for v in payload["c"]]
        A0 = [[to_fraction(v) for v in row] for row in payload["A"]]
        b = [to_fraction(v) for v in payload["b"]]
        types = list(payload["constraint_types"])
        n0, m = len(c0), len(b)
        self._original_variable_count = n0
        self._original_variable_names = payload.get("variable_names") or [f"x{i+1}" for i in range(n0)]
        for i in range(m):
            if b[i] < 0:
                b[i] = -b[i]
                A0[i] = [-v for v in A0[i]]
                types[i] = {"<=": ">=", ">=": "<="}.get(types[i], types[i])
        A = [list(row) for row in A0]
        names = list(self._original_variable_names)
        basis, artificial = [], set()

        def add_col(name, values):
            j = len(names)
            names.append(name)
            for row, value in zip(A, values): row.append(value)
            return j

        for i, kind in enumerate(types):
            unit = [Fraction(int(k == i)) for k in range(m)]
            if kind == "<=":
                basis.append(add_col(f"s{i+1}", unit))
            elif kind == ">=":
                add_col(f"e{i+1}", [-v for v in unit])
                j = add_col(f"a{i+1}", unit)
                basis.append(j); artificial.add(j)
            elif kind == "=":
                j = add_col(f"a{i+1}", unit)
                basis.append(j); artificial.add(j)
            else:
                return self.build_output("ERROR", {}, error_message=f"未知约束类型: {kind}")
        self._basis_matrix = [list(row) for row in A]
        limit = int(options.get("max_iterations", 1000))
        costs1 = [Fraction(-1) if j in artificial else Fraction(0) for j in range(len(names))]
        result = self._phase(A, b, basis, names, costs1, "I", limit)
        if result["status"] == STATUS_MAX_ITER_REACHED:
            return self.build_output(STATUS_MAX_ITER_REACHED, {}, error_message="Phase I 超过最大迭代次数")
        if result["status"] == STATUS_UNBOUNDED:
            return self.build_output(STATUS_INFEASIBLE, {}, error_message="Phase I 无界，原问题不可行")
        A, b, basis = result["A"], result["b"], result["basis"]
        sigma, z = result["sigma"], result["z"]
        if z < 0 or any(b[i] > 0 and basis[i] in artificial for i in range(len(basis))):
            self._save_final(A, b, basis, names, costs1, sigma, z, "I")
            return self.build_output(STATUS_INFEASIBLE, {}, error_message="Phase I 最优值小于 0，原问题无可行解")
        # Pivot artificial basic variables out where possible, then drop redundant rows.
        i = 0
        while i < len(basis):
            if basis[i] in artificial:
                entering = next((j for j in range(len(names)) if j not in artificial and A[i][j] != 0), None)
                if entering is not None:
                    self._pivot(A, b, basis, i, entering)
                else:
                    A.pop(i); b.pop(i); basis.pop(i); continue
            i += 1
        keep = [j for j in range(len(names)) if j not in artificial]
        remap = {old: new for new, old in enumerate(keep)}
        A = [[row[j] for j in keep] for row in A]
        names = [names[j] for j in keep]
        basis = [remap[j] for j in basis]
        # This is the Phase II standard-form coefficient matrix. It remains
        # immutable while tableau pivots proceed and defines B for B^-1.
        self._basis_matrix = deepcopy(A)
        costs2 = [(-v if self._is_min else v) for v in c0] + [Fraction(0)] * (len(names) - n0)
        result = self._phase(A, b, basis, names, costs2, "II", limit, result["steps"])
        if result["status"] == STATUS_MAX_ITER_REACHED:
            return self.build_output(STATUS_MAX_ITER_REACHED, {}, error_message="Phase II 超过最大迭代次数")
        if result["status"] == STATUS_UNBOUNDED:
            return self.build_output(STATUS_UNBOUNDED, {}, error_message="目标函数无界")
        A, b, basis, sigma, z = result["A"], result["b"], result["basis"], result["sigma"], result["z"]
        self._save_final(A, b, basis, names, costs2, sigma, z, "II")
        values = {name: Fraction(0) for name in self._original_variable_names}
        for i, j in enumerate(basis):
            if j < n0: values[self._original_variable_names[j]] = b[i]
        objective = z if not self._is_min else -z
        return self.build_output(STATUS_OPTIMAL, {"objective_value": fmt(objective),
            "solution": {k: fmt(v) for k, v in values.items()}})

    def _phase(self, A, b, basis, names, costs, phase, limit, start=0):
        sigma, z = self._reduced_costs(A, b, basis, costs)
        self._snapshot(start, A, b, basis, names, costs, sigma, z, phase)
        for step in range(1, limit + 1):
            entering = next((j for j, value in enumerate(sigma) if value > 0), None)
            if entering is None:
                self._snapshot(start + step, A, b, basis, names, costs, sigma, z, phase, optimal=True)
                return {"status": STATUS_OPTIMAL, "A": A, "b": b, "basis": basis,
                    "sigma": sigma, "z": z, "steps": start + step}
            theta = [b[i] / A[i][entering] if A[i][entering] > 0 else None for i in range(len(b))]
            leaving = min((i for i, value in enumerate(theta) if value is not None), key=lambda i: (theta[i], i), default=None)
            if leaving is None:
                self._snapshot(start + step, A, b, basis, names, costs, sigma, z, phase,
                    entering, theta, unbounded=True)
                return {"status": STATUS_UNBOUNDED}
            leaving_var = basis[leaving]
            pivot_value = A[leaving][entering]
            self._pivot(A, b, basis, leaving, entering)
            sigma, z = self._reduced_costs(A, b, basis, costs)
            self._snapshot(start + step, A, b, basis, names, costs, sigma, z, phase,
                entering, theta, leaving_var, pivot_value)
        return {"status": STATUS_MAX_ITER_REACHED}

    @staticmethod
    def _pivot(A, b, basis, row, col):
        p = A[row][col]
        A[row] = [v / p for v in A[row]]; b[row] /= p
        for i in range(len(A)):
            if i != row and A[i][col] != 0:
                f = A[i][col]
                A[i] = [A[i][j] - f * A[row][j] for j in range(len(A[i]))]
                b[i] -= f * b[row]
        basis[row] = col

    @staticmethod
    def _reduced_costs(A, b, basis, costs):
        cb = [costs[j] for j in basis]
        zj = [sum(cb[i] * A[i][j] for i in range(len(A))) for j in range(len(costs))]
        return [costs[j] - zj[j] for j in range(len(costs))], sum(cb[i] * b[i] for i in range(len(b)))

    def _dto(self, A, b, basis, names, costs, sigma, z, phase, theta=None, pivot=None, optimal=False, unbounded=False):
        return {"type": "simplex_tableau", "phase": phase, "var_names": list(names), "c_j": list(costs),
            "basis_indices": list(basis), "basis_var_names": [names[j] for j in basis],
            "c_b": [costs[j] for j in basis], "b": list(b), "matrix_a": [list(row) for row in A],
            "sigma": list(sigma), "current_z": z, "theta": theta, "pivot": pivot,
            "is_optimal": optimal, "is_unbounded": unbounded}

    def _snapshot(self, step, A, b, basis, names, costs, sigma, z, phase, entering=None,
                  theta=None, leaving=None, pivot_value=None, optimal=False, unbounded=False):
        pivot = None if entering is None else {"entering_var": names[entering],
            "leaving_var": names[leaving] if leaving is not None else None,
            "pivot_element": pivot_value, "pivot_position": [leaving, entering]}
        dto = self._dto(A, b, basis, names, costs, sigma, z, phase,
            theta, pivot, optimal, unbounded)
        self._add_step(self.snapshot(step, dto,
            "最优" if optimal else ("无界" if unbounded else f"Phase {phase} 单纯形换基"), [],
            phase=phase, pivot=pivot))

    @staticmethod
    def _format(value):
        if isinstance(value, Fraction): return fmt(value)
        if isinstance(value, list): return [SimplexModule._format(v) for v in value]
        if isinstance(value, dict): return {k: SimplexModule._format(v) for k, v in value.items()}
        return value

    def _save_final(self, A, b, basis, names, costs, sigma, z, phase):
        self.final_tableau = self._dto(A, b, basis, names, costs, sigma, z, phase, optimal=True)

    def get_final_tableau(self) -> dict:
        """Return the exact Fraction final tableau DTO."""
        return deepcopy(self.final_tableau) if self.final_tableau is not None else {}

    def get_final_tableau_json(self) -> dict:
        """Return a JSON-safe final tableau for API consumers."""
        return rationalize(self.get_final_tableau())

    def get_basis_matrix_inverse(self) -> list[list[Fraction]]:
        """Return the inverse of the final standard-form basis matrix."""
        dto = self.final_tableau or {}
        basis = dto.get("basis_indices", [])
        B = [[self._basis_matrix[i][j] for j in basis] for i in range(len(basis))]
        I = [[Fraction(int(i == j)) for j in range(len(basis))] for i in range(len(basis))]
        for col in range(len(basis)):
            pivot = next(i for i in range(col, len(basis)) if B[i][col] != 0)
            B[col], B[pivot] = B[pivot], B[col]; I[col], I[pivot] = I[pivot], I[col]
            p = B[col][col]
            B[col] = [v / p for v in B[col]]; I[col] = [v / p for v in I[col]]
            for i in range(len(basis)):
                if i != col and B[i][col] != 0:
                    f = B[i][col]
                    B[i] = [B[i][j] - f * B[col][j] for j in range(len(basis))]
                    I[i] = [I[i][j] - f * I[col][j] for j in range(len(basis))]
        return I
