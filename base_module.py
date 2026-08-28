# fmt: off
# =============================================================================
# Author:      王梓轩
# Project:     运筹学算法推演引擎
# Description: 抽象基类与通用快照工具模块。
#              定义所有算法模块必须遵守的接口契约（BaseModule），
#              提供结构化迭代快照（IterationStep）的构造与格式化工具，
#              以及 Fraction 有理数的显示辅助函数。
# =============================================================================
# fmt: on

"""
base_module.py — 抽象基类 & 快照工具层

所有算法模块（SimplexModule、TransportationModule 等）必须：
  1. 继承 BaseModule
  2. 实现 solve(payload, options) 方法
  3. 通过 self.snapshot(...) 工厂方法构造每一个迭代快照
  4. 通过 self.new_output(...) 构造统一的 OutputContract 字典

数值规范：
  - 所有内部计算值必须是 fractions.Fraction
  - 对外展示时通过 fmt() / fmt_matrix() 转换为可读字符串
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from fractions import Fraction
from typing import Any
import copy


@dataclass(frozen=True)
class RationalNumber:
    """JSON-safe representation of an exact rational value."""

    display: str
    numerator: int
    denominator: int
    decimal: float

    @classmethod
    def from_value(cls, value: Fraction | int | float | str) -> "RationalNumber":
        fraction = to_fraction(value)
        return cls(
            display=fmt(fraction),
            numerator=fraction.numerator,
            denominator=fraction.denominator,
            decimal=float(fraction),
        )

    def to_dict(self) -> dict[str, str | int | float]:
        return {
            "display": self.display,
            "numerator": self.numerator,
            "denominator": self.denominator,
            "decimal": self.decimal,
        }


def rationalize(value: Any) -> Any:
    """Convert Fraction values recursively to RationalNumber dictionaries."""
    if isinstance(value, Fraction):
        return RationalNumber.from_value(value).to_dict()
    if isinstance(value, list):
        return [rationalize(item) for item in value]
    if isinstance(value, tuple):
        return [rationalize(item) for item in value]
    if isinstance(value, dict):
        return {key: rationalize(item) for key, item in value.items()}
    return value


# ─────────────────────────────────────────────────────────────────────────────
# 节 1：有理数格式化工具
# ─────────────────────────────────────────────────────────────────────────────

def fmt(value: Fraction | int | float | None, *, mode: str = "fraction") -> str:
    """
    将 Fraction 转换为人类可读的字符串。

    Parameters
    ----------
    value : Fraction | int | float | None
        待格式化的数值。None 代表占位符（如 θ 列中无效项）。
    mode : str
        "fraction" → 保留真分数形式，如 "3/2"；整数则直接显示整数。
        "decimal"  → 转换为保留 6 位小数的十进制字符串，尾零截断。
        "mixed"    → 带分数形式，如 "1 1/2"（整部分 + 真分数）。

    Returns
    -------
    str
    """
    if value is None:
        return "—"
    if not isinstance(value, Fraction):
        value = Fraction(value)

    match mode:
        case "decimal":
            result = float(value)
            # 截断无效尾零，最多 6 位小数
            return f"{result:.6f}".rstrip("0").rstrip(".")
        case "mixed":
            if value.denominator == 1:
                return str(value.numerator)
            integer_part = int(value)          # 向零取整
            remainder = abs(value) - abs(integer_part)
            if integer_part == 0:
                return f"{value.numerator}/{value.denominator}"
            sign = "-" if value < 0 else ""
            return f"{sign}{abs(integer_part)} {remainder.numerator}/{remainder.denominator}"
        case _:  # "fraction" (default)
            if value.denominator == 1:
                return str(value.numerator)
            return f"{value.numerator}/{value.denominator}"


def fmt_matrix(
    matrix: list[list[Fraction | None]],
    *,
    mode: str = "fraction"
) -> list[list[str]]:
    """
    对二维矩阵（list of list）批量格式化，返回等尺寸的字符串矩阵。
    """
    return [[fmt(cell, mode=mode) for cell in row] for row in matrix]


def to_fraction(value: int | float | str | Fraction) -> Fraction:
    """
    安全地将任意数值转换为 Fraction。
    支持字符串分数 "3/4"、整数、浮点数。
    注意：浮点数通过字符串中转以避免精度丢失（如 0.1 → Fraction("0.1")）。
    """
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, float):
        # 通过字符串中转，避免 float 精度污染
        return Fraction(str(value))
    if isinstance(value, str):
        return Fraction(value)
    raise TypeError(f"无法将 {type(value).__name__} 转换为 Fraction: {value!r}")


def matrix_to_fraction(matrix: list[list]) -> list[list[Fraction]]:
    """对二维列表递归调用 to_fraction，返回全 Fraction 矩阵。"""
    return [[to_fraction(cell) for cell in row] for row in matrix]


def vector_to_fraction(vec: list) -> list[Fraction]:
    """对一维列表调用 to_fraction，返回全 Fraction 列表。"""
    return [to_fraction(v) for v in vec]


# ─────────────────────────────────────────────────────────────────────────────
# 节 2：IterationStep —— 单次迭代快照数据结构
# ─────────────────────────────────────────────────────────────────────────────

class IterationStep:
    """
    一次迭代的完整快照。

    Attributes
    ----------
    step : int
        迭代编号，0 表示初始状态（预处理后）。
    state_matrix : list[list[str]] | dict
        当前核心矩阵的字符串快照。格式取决于算法：
          - 单纯形法：单纯形表（二维列表 + header）
          - 运输问题：运输矩阵
          - 指派问题：收益/成本矩阵
          - 分支定界：当前节点的 LP 松弛表
    action : str
        本步骤的核心操作描述（人类语言）。
        例："入基变量 x2（检验数=3），出基变量 x4（θ=4）"
    calculation : list[str]
        具体的初等行变换公式列表。
        例：["R1 = R1 / 2", "R2 = R2 - 1×R1", "Z行 = Z行 - 3×R1"]
    extra : dict
        模块自定义的额外字段（如 basis、penalty、pivot 坐标等）。
    """

    def __init__(
        self,
        step: int,
        state_matrix: list | dict,
        action: str,
        calculation: list[str],
        **extra: Any,
    ) -> None:
        self.step = step
        self.state_matrix = state_matrix
        self.action = action
        self.calculation = calculation
        self.extra = extra  # 存储模块专属字段

    def to_dict(self) -> dict:
        """序列化为纯字典，可被 JSON 直接序列化。"""
        d: dict[str, Any] = {
            "step":         self.step,
            "state_matrix": self.state_matrix,
            "action":       self.action,
            "calculation":  self.calculation,
        }
        d.update(self.extra)
        return d

    def __repr__(self) -> str:
        return (
            f"IterationStep(step={self.step}, "
            f"action={self.action!r}, "
            f"calculations={len(self.calculation)})"
        )


# ─────────────────────────────────────────────────────────────────────────────
# 节 3：OutputContract —— 统一输出字典的构造辅助
# ─────────────────────────────────────────────────────────────────────────────

# 合法状态常量
STATUS_OPTIMAL    = "OPTIMAL"
STATUS_INFEASIBLE = "INFEASIBLE"
STATUS_UNBOUNDED  = "UNBOUNDED"
STATUS_ERROR      = "ERROR"
STATUS_MAX_ITER_REACHED = "MAX_ITER_REACHED"


def build_output(
    problem_type: str,
    status: str,
    final_result: dict,
    iterations: list[IterationStep],
    *,
    sensitivity: dict | None = None,
    error_message: str | None = None,
) -> dict:
    """
    构造标准 OutputContract 字典。

    所有算法模块的 solve() 方法最终都必须调用此函数打包结果。

    Parameters
    ----------
    problem_type  : 问题类型标识，如 "LP"、"TP"
    status        : 求解状态，使用上方 STATUS_* 常量
    final_result  : 最终解字典（各模块自定义内容）
    iterations    : IterationStep 列表（完整迭代历史）
    sensitivity   : 灵敏度分析结果（可选，LP 专属）
    error_message : 错误信息（status=ERROR 时填充）
    """
    return {
        "problem_type":  problem_type,
        "status":        status,
        "final_result":  final_result,
        "iterations":    [rationalize(it.to_dict()) for it in iterations],
        "sensitivity":   sensitivity,
        "error_message": error_message,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 节 4：BaseModule —— 所有算法模块的抽象基类
# ─────────────────────────────────────────────────────────────────────────────

class BaseModule(ABC):
    """
    所有运筹学算法模块的抽象基类。

    子类必须实现：
      - solve(payload, options) -> dict

    子类可直接调用的工具方法：
      - self.snapshot(...)  → 构造 IterationStep
      - self.build_output(...) → 构造 OutputContract dict（代理静态函数）
      - self._deep_copy_matrix(matrix) → 安全深拷贝矩阵
    """

    # 子类必须声明此属性，用于输出中的 problem_type 字段
    PROBLEM_TYPE: str = "UNKNOWN"

    @abstractmethod
    def solve(self, payload: dict, options: dict) -> dict:
        """
        执行算法并返回 OutputContract 字典。

        Parameters
        ----------
        payload : dict
            从 Launcher 传入的问题数据（已通过输入校验）。
        options : dict
            从 Launcher 传入的求解选项（如是否需要灵敏度分析）。

        Returns
        -------
        dict
            标准 OutputContract 字典（通过 build_output() 构造）。
        """
        ...

    # ── 快照工厂 ───────────────────────────────────────────────────────────

    def snapshot(
        self,
        step: int,
        state_matrix: list | dict,
        action: str,
        calculation: list[str],
        **extra: Any,
    ) -> IterationStep:
        """
        构造一个迭代快照（IterationStep）。
        所有矩阵内容应在调用前已转换为格式化字符串（通过 fmt_matrix）。

        Usage (in subclass)
        -------------------
        snap = self.snapshot(
            step=1,
            state_matrix=fmt_matrix(current_table),
            action="入基 x2，出基 x4",
            calculation=["R1 = R1/2", "R2 = R2 - R1"],
            basis=["x2", "x3"],        # 模块自定义 extra
            pivot={"entering": "x2", "leaving": "x4"},
        )
        self._steps.append(snap)
        """
        return IterationStep(step, state_matrix, action, calculation, **extra)

    # ── 输出打包代理 ───────────────────────────────────────────────────────

    def build_output(
        self,
        status: str,
        final_result: dict,
        *,
        sensitivity: dict | None = None,
        error_message: str | None = None,
    ) -> dict:
        """
        打包为 OutputContract 字典。
        使用 self._steps 作为 iterations 列表。
        """
        return build_output(
            problem_type=self.PROBLEM_TYPE,
            status=status,
            final_result=final_result,
            iterations=getattr(self, "_steps", []),
            sensitivity=sensitivity,
            error_message=error_message,
        )

    # ── 通用工具 ───────────────────────────────────────────────────────────

    def _init_steps(self) -> None:
        """在 solve() 开头调用，初始化迭代快照列表。"""
        self._steps: list[IterationStep] = []

    def _add_step(self, step: IterationStep) -> None:
        """将快照追加到列表。"""
        self._steps.append(step)

    @staticmethod
    def _deep_copy_matrix(matrix: list[list]) -> list[list]:
        """
        对矩阵进行深拷贝。
        Fraction 是不可变对象，直接 copy.deepcopy 即可。
        """
        return copy.deepcopy(matrix)

    @staticmethod
    def _deep_copy(obj: Any) -> Any:
        """通用深拷贝。"""
        return copy.deepcopy(obj)


# ─────────────────────────────────────────────────────────────────────────────
# 节 5：输入校验异常
# ─────────────────────────────────────────────────────────────────────────────

class ORValidationError(ValueError):
    """
    输入校验失败时抛出。
    携带 field（出错字段路径）和 message（描述）。
    """

    def __init__(self, field: str, message: str) -> None:
        self.field = field
        self.message = message
        super().__init__(f"[{field}] {message}")


class ORRuntimeError(RuntimeError):
    """
    算法运行过程中遇到不可恢复错误时抛出。
    """

    def __init__(self, module: str, message: str) -> None:
        self.module = module
        self.message = message
        super().__init__(f"[{module}] {message}")
