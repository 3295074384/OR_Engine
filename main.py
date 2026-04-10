# fmt: off
# =============================================================================
# Author:      王梓轩
# Project:     运筹学算法推演引擎
# Description: 主启动器（Launcher）。
#              作为系统的统一入口：接收标准 JSON 格式输入，执行输入校验，
#              根据 problem_type 路由到对应算法模块，并将结果序列化为
#              JSON 字符串返回。支持 Python 3.10+ match-case 路由语法。
# =============================================================================
# fmt: on

"""
main.py — 运筹学辅助计算与推演系统 主启动器

用法示例（命令行）:
    python main.py input.json
    python main.py input.json --pretty
    python main.py --stdin         (从标准输入读取 JSON)
    python main.py --example lp   (运行内置示例：lp / tp / ip / ap / gt)

用法示例（作为模块导入）:
    from main import Launcher
    launcher = Launcher()
    result = launcher.solve(problem_dict)
"""

from __future__ import annotations

import json
import sys
import textwrap
from typing import Any

from base_module import (
    ORValidationError,
    ORRuntimeError,
    STATUS_ERROR,
    STATUS_OPTIMAL,
)


# ─────────────────────────────────────────────────────────────────────────────
# 节 1：输入校验器 (InputValidator)
# ─────────────────────────────────────────────────────────────────────────────

class InputValidator:
    """
    对 Launcher 接收的原始输入字典进行语义校验。

    验证流程：
      1. 顶层字段完整性（problem_type / payload 必须存在）
      2. problem_type 合法性
      3. payload 的模块专属字段校验（由对应的 _validate_<type> 方法执行）

    所有校验失败均抛出 ORValidationError。
    """

    VALID_TYPES = {"LP", "TP", "IP", "AP", "GT"}

    def validate(self, raw: dict) -> dict:
        """
        校验并返回规范化后的输入字典。
        规范化包括：填充 options 默认值、sub_type 推断等。
        """
        self._check_top_level(raw)
        raw = self._normalize_options(raw)
        self._dispatch_payload_check(raw)
        return raw

    # ── 顶层字段校验 ──────────────────────────────────────────────────────

    def _check_top_level(self, raw: dict) -> None:
        if not isinstance(raw, dict):
            raise ORValidationError("input", "输入必须是一个 JSON 对象（dict）")

        if "problem_type" not in raw:
            raise ORValidationError("problem_type", "缺少必要字段 'problem_type'")

        pt = raw["problem_type"]
        if not isinstance(pt, str) or pt.upper() not in self.VALID_TYPES:
            raise ORValidationError(
                "problem_type",
                f"无效的问题类型 '{pt}'。合法值：{sorted(self.VALID_TYPES)}"
            )

        if "payload" not in raw:
            raise ORValidationError("payload", "缺少必要字段 'payload'")

        if not isinstance(raw["payload"], dict):
            raise ORValidationError("payload", "'payload' 必须是一个 JSON 对象（dict）")

    # ── 选项规范化：填充默认值 ─────────────────────────────────────────────

    def _normalize_options(self, raw: dict) -> dict:
        defaults: dict[str, Any] = {
            "sensitivity_analysis": False,
            "integer_method":       "branch_bound",
            "display_mode":         "fraction",   # fraction | decimal | mixed
        }
        raw.setdefault("options", {})
        raw.setdefault("sub_type", None)
        # 仅对缺失键填充默认值，不覆盖用户显式设定
        for key, val in defaults.items():
            raw["options"].setdefault(key, val)
        # 大写规范化
        raw["problem_type"] = raw["problem_type"].upper()
        return raw

    # ── Payload 校验分发 ──────────────────────────────────────────────────

    def _dispatch_payload_check(self, raw: dict) -> None:
        match raw["problem_type"]:
            case "LP": self._validate_lp(raw["payload"])
            case "TP": self._validate_tp(raw["payload"])
            case "IP": self._validate_ip(raw["payload"])
            case "AP": self._validate_ap(raw["payload"])
            case "GT": self._validate_gt(raw["payload"])

    # ── LP payload 校验 ───────────────────────────────────────────────────

    def _validate_lp(self, p: dict) -> None:
        self._require(p, "payload.LP", ["objective", "c", "A", "b", "constraint_types"])

        obj = p["objective"]
        if obj not in ("max", "min"):
            raise ORValidationError("payload.objective", f"必须为 'max' 或 'min'，得到 '{obj}'")

        c  = p["c"]
        A  = p["A"]
        b  = p["b"]
        ct = p["constraint_types"]

        if not isinstance(c, list) or len(c) == 0:
            raise ORValidationError("payload.c", "目标函数系数向量 'c' 不能为空列表")

        n_vars = len(c)

        if not isinstance(A, list) or len(A) == 0:
            raise ORValidationError("payload.A", "约束矩阵 'A' 不能为空")

        n_cons = len(A)

        for i, row in enumerate(A):
            if not isinstance(row, list) or len(row) != n_vars:
                raise ORValidationError(
                    f"payload.A[{i}]",
                    f"第 {i} 行长度为 {len(row)}，应与 c 的长度 {n_vars} 一致"
                )

        if not isinstance(b, list) or len(b) != n_cons:
            raise ORValidationError(
                "payload.b",
                f"右端项向量 'b' 长度 {len(b)} 应与约束行数 {n_cons} 一致"
            )

        if not isinstance(ct, list) or len(ct) != n_cons:
            raise ORValidationError(
                "payload.constraint_types",
                f"'constraint_types' 长度 {len(ct)} 应与约束行数 {n_cons} 一致"
            )

        for i, t in enumerate(ct):
            if t not in ("<=", ">=", "="):
                raise ORValidationError(
                    f"payload.constraint_types[{i}]",
                    f"无效约束类型 '{t}'，合法值：'<=', '>=', '='"
                )

        # variable_names 可选，若提供则长度需匹配
        if "variable_names" in p:
            vn = p["variable_names"]
            if not isinstance(vn, list) or len(vn) != n_vars:
                raise ORValidationError(
                    "payload.variable_names",
                    f"变量名列表长度 {len(vn)} 应与 c 的长度 {n_vars} 一致"
                )

    # ── TP payload 校验 ───────────────────────────────────────────────────

    def _validate_tp(self, p: dict) -> None:
        self._require(p, "payload.TP", ["supply", "demand", "cost"])

        supply = p["supply"]
        demand = p["demand"]
        cost   = p["cost"]

        if not isinstance(supply, list) or len(supply) == 0:
            raise ORValidationError("payload.supply", "产量向量 'supply' 不能为空")

        if not isinstance(demand, list) or len(demand) == 0:
            raise ORValidationError("payload.demand", "销量向量 'demand' 不能为空")

        m, n = len(supply), len(demand)

        if not isinstance(cost, list) or len(cost) != m:
            raise ORValidationError(
                "payload.cost",
                f"运价矩阵行数 {len(cost)} 应等于产地数 {m}"
            )

        for i, row in enumerate(cost):
            if not isinstance(row, list) or len(row) != n:
                raise ORValidationError(
                    f"payload.cost[{i}]",
                    f"运价矩阵第 {i} 行长度 {len(row)} 应等于销地数 {n}"
                )

    # ── IP payload 校验 ───────────────────────────────────────────────────

    def _validate_ip(self, p: dict) -> None:
        # IP 使用与 LP 相同的基础结构，额外需要 integer_vars 字段
        self._require(p, "payload.IP", ["objective", "c", "A", "b", "constraint_types"])
        self._validate_lp(p)  # 复用 LP 校验

        if "integer_vars" not in p:
            raise ORValidationError(
                "payload.integer_vars",
                "整数规划必须指定 'integer_vars'（需要取整的变量索引列表，从 0 开始）"
            )

        iv = p["integer_vars"]
        if not isinstance(iv, list):
            raise ORValidationError("payload.integer_vars", "'integer_vars' 必须是列表")

        n_vars = len(p["c"])
        for idx in iv:
            if not isinstance(idx, int) or not (0 <= idx < n_vars):
                raise ORValidationError(
                    "payload.integer_vars",
                    f"索引 {idx} 超出变量范围 [0, {n_vars - 1}]"
                )

    # ── AP payload 校验 ───────────────────────────────────────────────────

    def _validate_ap(self, p: dict) -> None:
        self._require(p, "payload.AP", ["objective", "cost_matrix"])

        obj = p["objective"]
        if obj not in ("min", "max"):
            raise ORValidationError("payload.objective", f"指派问题目标必须为 'min' 或 'max'，得到 '{obj}'")

        cm = p["cost_matrix"]
        if not isinstance(cm, list) or len(cm) == 0:
            raise ORValidationError("payload.cost_matrix", "成本矩阵 'cost_matrix' 不能为空")

        # 允许非方阵（模块内部自动补齐虚拟行/列）
        col_len = len(cm[0]) if cm else 0
        for i, row in enumerate(cm):
            if not isinstance(row, list):
                raise ORValidationError(f"payload.cost_matrix[{i}]", "矩阵每行必须是列表")

    # ── GT payload 校验 ───────────────────────────────────────────────────

    def _validate_gt(self, p: dict) -> None:
        self._require(p, "payload.GT", ["payoff_matrix"])

        pm = p["payoff_matrix"]
        if not isinstance(pm, list) or len(pm) == 0:
            raise ORValidationError("payload.payoff_matrix", "收益矩阵 'payoff_matrix' 不能为空")

        col_count = len(pm[0])
        for i, row in enumerate(pm):
            if not isinstance(row, list) or len(row) != col_count:
                raise ORValidationError(
                    f"payload.payoff_matrix[{i}]",
                    "收益矩阵各行列数必须一致（矩形矩阵）"
                )

    # ── 通用工具 ──────────────────────────────────────────────────────────

    @staticmethod
    def _require(d: dict, prefix: str, fields: list[str]) -> None:
        for f in fields:
            if f not in d:
                raise ORValidationError(f"{prefix}.{f}", f"缺少必要字段 '{f}'")


# ─────────────────────────────────────────────────────────────────────────────
# 节 2：模块注册表 (ModuleRegistry)
# ─────────────────────────────────────────────────────────────────────────────

class ModuleRegistry:
    """
    惰性加载算法模块，避免启动时全部导入。
    当首次调用某模块时才执行 import。
    """

    def get_module(self, problem_type: str, sub_type: str | None, options: dict):
        """
        根据 problem_type 和 sub_type 返回对应算法模块实例。

        Parameters
        ----------
        problem_type : str  — "LP" | "TP" | "IP" | "AP" | "GT"
        sub_type     : str  — 可选覆盖，如 "graphical" 强制使用图解法
        options      : dict — 包含 integer_method 等选项
        """
        match problem_type:
            case "LP":
                return self._get_lp_module(sub_type, options)
            case "TP":
                from modules.transportation import TransportationModule
                return TransportationModule()
            case "IP":
                return self._get_ip_module(options)
            case "AP":
                from modules.hungarian import HungarianModule
                return HungarianModule()
            case "GT":
                from modules.game_theory import GameTheoryModule
                return GameTheoryModule()
            case _:
                raise ORRuntimeError("Registry", f"未注册的模块类型：{problem_type}")

    def _get_lp_module(self, sub_type: str | None, options: dict):
        # 强制图解法 || 自动推断（变量数在 payload 中，由 Launcher 二次判断后决定）
        match sub_type:
            case "graphical":
                from modules.lp_graphical import GraphicalModule
                return GraphicalModule()
            case _:
                from modules.lp_simplex import SimplexModule
                return SimplexModule()

    def _get_ip_module(self, options: dict):
        match options.get("integer_method", "branch_bound"):
            case "cutting_plane":
                from modules.cutting_plane import CuttingPlaneModule
                return CuttingPlaneModule()
            case _:
                from modules.branch_and_bound import BranchAndBoundModule
                return BranchAndBoundModule()


# ─────────────────────────────────────────────────────────────────────────────
# 节 3：主启动器 (Launcher)
# ─────────────────────────────────────────────────────────────────────────────

class Launcher:
    """
    运筹学推演引擎的统一入口。

    外部调用接口：
        launcher = Launcher()
        result_dict = launcher.solve(problem_dict)
        result_json = launcher.solve_json(json_string)
    """

    def __init__(self) -> None:
        self._validator = InputValidator()
        self._registry  = ModuleRegistry()

    # ── 主入口：接收 dict ─────────────────────────────────────────────────

    def solve(self, raw_input: dict) -> dict:
        """
        执行完整求解流程并返回 OutputContract 字典。

        Steps:
          1. 输入校验与规范化
          2. LP 变量数自动路由（n=2 且非强制 simplex → 图解法）
          3. 惰性加载对应算法模块
          4. 调用 module.solve(payload, options)
          5. 捕获异常，封装为错误输出

        Parameters
        ----------
        raw_input : dict
            未经校验的原始输入字典。

        Returns
        -------
        dict
            标准 OutputContract 字典。
        """
        # Step 1：校验
        try:
            validated = self._validator.validate(raw_input)
        except ORValidationError as e:
            return self._error_output(
                raw_input.get("problem_type", "UNKNOWN"),
                f"输入校验失败 [{e.field}]：{e.message}"
            )

        pt      = validated["problem_type"]
        payload = validated["payload"]
        options = validated["options"]
        sub     = validated["sub_type"]

        # Step 2：LP 变量数自动路由
        if pt == "LP" and sub is None:
            n_vars = len(payload["c"])
            if n_vars == 2:
                sub = "graphical"
                validated["sub_type"] = "graphical"

        # Step 3 & 4：加载模块并求解
        try:
            module = self._registry.get_module(pt, sub, options)
            result = module.solve(payload, options)
        except ORValidationError as e:
            return self._error_output(pt, f"[{e.field}] {e.message}")
        except ORRuntimeError as e:
            return self._error_output(pt, f"[{e.module}] {e.message}")
        except NotImplementedError:
            return self._error_output(pt, f"模块 '{pt}' 尚未实现，敬请期待后续版本。")
        except Exception as e:
            # 捕获所有未预期异常，保证接口健壮性
            return self._error_output(pt, f"未预期错误：{type(e).__name__}: {e}")

        return result

    # ── JSON 字符串接口 ───────────────────────────────────────────────────

    def solve_json(self, json_str: str, *, indent: int | None = 2) -> str:
        """
        接受 JSON 字符串，返回 JSON 字符串。
        适用于 HTTP API、命令行管道等场景。
        """
        try:
            raw = json.loads(json_str)
        except json.JSONDecodeError as e:
            err = self._error_output("UNKNOWN", f"JSON 解析失败：{e}")
            return json.dumps(err, ensure_ascii=False, indent=indent)

        result = self.solve(raw)
        return json.dumps(result, ensure_ascii=False, indent=indent)

    # ── 错误输出封装 ──────────────────────────────────────────────────────

    @staticmethod
    def _error_output(problem_type: str, message: str) -> dict:
        return {
            "problem_type":  problem_type,
            "status":        STATUS_ERROR,
            "final_result":  {},
            "iterations":    [],
            "sensitivity":   None,
            "error_message": message,
        }


# ─────────────────────────────────────────────────────────────────────────────
# 节 4：内置示例问题集
# ─────────────────────────────────────────────────────────────────────────────

EXAMPLES: dict[str, dict] = {
    "lp": {
        "problem_type": "LP",
        "options": {"sensitivity_analysis": True},
        "payload": {
            "objective": "max",
            "c":  [5, 4],
            "A":  [[6, 4], [1, 2], [0, 1]],
            "b":  [24, 6, 1],
            "constraint_types": ["<=", "<=", "<="],
            "variable_names": ["x1", "x2"],
        },
    },
    "lp_simplex": {
        # 三变量，强制走单纯形法
        "problem_type": "LP",
        "sub_type": "simplex",
        "payload": {
            "objective": "max",
            "c":  [2, 3, 0, 0, 0],
            "A":  [
                [1, 2, 1, 0, 0],
                [2, 1, 0, 1, 0],
                [0, 1, 0, 0, 1],
            ],
            "b":  [14, 14, 6],
            "constraint_types": ["<=", "<=", "<="],
        },
    },
    "tp": {
        "problem_type": "TP",
        "payload": {
            "supply": [30, 40, 50],
            "demand": [25, 35, 40, 20],
            "cost": [
                [2, 3, 11, 7],
                [1, 0,  6, 1],
                [5, 8, 15, 9],
            ],
        },
    },
    "ap": {
        "problem_type": "AP",
        "payload": {
            "objective": "min",
            "cost_matrix": [
                [9, 2, 7, 8],
                [6, 4, 3, 7],
                [5, 8, 1, 8],
                [7, 6, 9, 4],
            ],
        },
    },
    "gt": {
        "problem_type": "GT",
        "payload": {
            "payoff_matrix": [
                [ 3, -1],
                [-2,  4],
            ],
        },
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# 节 5：命令行入口
# ─────────────────────────────────────────────────────────────────────────────

def _print_usage() -> None:
    print(textwrap.dedent("""
        运筹学辅助计算与推演系统 — 命令行用法
        ───────────────────────────────────────
        python main.py <input.json> [--pretty]
            从 JSON 文件读取输入并求解。
            --pretty  输出带缩进的格式化 JSON（默认已开启）

        python main.py --stdin
            从标准输入（管道）读取 JSON。

        python main.py --example <name>
            运行内置示例。name 可选：
              lp          两变量 LP（自动图解法）
              lp_simplex  多变量 LP（单纯形法）
              tp          运输问题
              ap          指派问题（匈牙利法）
              gt          博弈论

        python main.py --list-examples
            列出所有可用示例名称。
    """).strip())


def main() -> None:
    launcher = Launcher()
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        _print_usage()
        return

    if "--list-examples" in args:
        print("可用示例：", ", ".join(EXAMPLES.keys()))
        return

    # 运行内置示例
    if "--example" in args:
        idx = args.index("--example")
        if idx + 1 >= len(args):
            print("错误：--example 需要指定示例名称", file=sys.stderr)
            sys.exit(1)
        name = args[idx + 1]
        if name not in EXAMPLES:
            print(f"错误：未知示例 '{name}'。可选：{list(EXAMPLES.keys())}", file=sys.stderr)
            sys.exit(1)
        raw = EXAMPLES[name]
        result = launcher.solve(raw)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    # 从标准输入读取
    if "--stdin" in args:
        json_str = sys.stdin.read()
        print(launcher.solve_json(json_str))
        return

    # 从文件读取
    filepath = args[0]
    try:
        with open(filepath, encoding="utf-8") as f:
            json_str = f.read()
    except FileNotFoundError:
        print(f"错误：找不到文件 '{filepath}'", file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        print(f"错误：无法读取文件：{e}", file=sys.stderr)
        sys.exit(1)

    print(launcher.solve_json(json_str))


if __name__ == "__main__":
    main()
