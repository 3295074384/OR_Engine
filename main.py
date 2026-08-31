# fmt: off
# =============================================================================
# Author:       王梓轩
# Project:      运筹学算法推演引擎
# Description: 主启动器（Launcher）。
#              作为系统的统一入口：接收标准 JSON 格式输入，执行输入校验，
#              根据 problem_type 路由到对应算法模块，并将结果序列化为
#              JSON 字符串返回。支持 Python 3.10+ match-case 路由语法。
# =============================================================================
# fmt: on

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


class InputValidator:
    VALID_TYPES = {"LP", "TP", "IP", "AP", "GT"}

    def validate(self, raw: dict) -> dict:
        self._check_top_level(raw)
        raw = self._normalize_options(raw)
        self._dispatch_payload_check(raw)
        return raw

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

    def _normalize_options(self, raw: dict) -> dict:
        raw.setdefault("options", {})
        raw.setdefault("sub_type", None)
        raw["problem_type"] = raw["problem_type"].upper()

        if not isinstance(raw["options"], dict):
            raise ORValidationError("options", "'options' 必须是一个 JSON 对象（dict）")

        if raw["problem_type"] == "IP":
            im = raw["options"].get("integer_method") or raw.get("sub_type") or "branch_bound"
            if im in {"branch_and_bound", "branch_bound"}:
                raw["options"]["integer_method"] = "branch_bound"
            elif im == "cutting_plane":
                raw["options"]["integer_method"] = "cutting_plane"

        if raw["problem_type"] == "LP" and raw["sub_type"] not in {None, "simplex", "graphical"}:
            raise ORValidationError("sub_type", "LP 的 sub_type 必须为 'simplex'、'graphical' 或 null")

        raw["options"].setdefault("sensitivity_analysis", False)
        raw["options"].setdefault("display_mode", "fraction")
        return raw

    def _dispatch_payload_check(self, raw: dict) -> None:
        match raw["problem_type"]:
            case "LP": self._validate_lp(raw["payload"])
            case "TP": self._validate_tp(raw["payload"])
            case "IP": self._validate_ip(raw["payload"])
            case "AP": self._validate_ap(raw["payload"])
            case "GT": self._validate_gt(raw["payload"])

    def _validate_lp(self, p: dict) -> None:
        self._require(p, "payload.LP", ["objective", "c", "A", "b", "constraint_types"])

        obj = p["objective"]
        if obj not in ("max", "min"):
            raise ORValidationError("payload.objective", f"必须为 'max' 或 'min'，得到 '{obj}'")

        c = p["c"]
        A = p["A"]
        b = p["b"]
        ct = p["constraint_types"]

        if not isinstance(c, list) or len(c) == 0:
            raise ORValidationError("payload.c", "目标函数系数向量 'c' 不能为空列表")

        n_vars = len(c)

        if not isinstance(A, list) or len(A) == 0:
            raise ORValidationError("payload.A", "约束矩阵 'A' 不能为空")

        n_cons = len(A)

        for i, row in enumerate(A):
            if not isinstance(row, list) or len(row) != n_vars:
                actual_length = len(row) if isinstance(row, list) else "非列表"
                raise ORValidationError(
                    f"payload.A[{i}]",
                    f"第 {i} 行长度为 {actual_length}，应与 c 的长度 {n_vars} 一致"
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

        if "variable_names" in p:
            vn = p["variable_names"]
            if not isinstance(vn, list) or len(vn) != n_vars:
                raise ORValidationError(
                    "payload.variable_names",
                    f"变量名列表长度 {len(vn)} 应与 c 的长度 {n_vars} 一致"
                )

    def _validate_tp(self, p: dict) -> None:
        self._require(p, "payload.TP", ["supply", "demand", "cost"])

        supply = p["supply"]
        demand = p["demand"]
        cost = p["cost"]

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

    def _validate_ip(self, p: dict) -> None:
        self._require(p, "payload.IP", ["objective", "c", "A", "b", "constraint_types"])
        self._validate_lp(p)

        if "integer_vars" not in p and "integer_indices" not in p:
            raise ORValidationError(
                "payload.integer_vars",
                "整数规划必须指定 'integer_vars' 或 'integer_indices'"
            )

        iv = p.get("integer_vars", p.get("integer_indices"))
        if not isinstance(iv, list):
            raise ORValidationError("payload.integer_vars", "'integer_vars' 必须是列表")

        n_vars = len(p["c"])
        for idx in iv:
            if not isinstance(idx, int) or not (0 <= idx < n_vars):
                raise ORValidationError(
                    "payload.integer_vars",
                    f"索引 {idx} 超出变量范围 [0, {n_vars - 1}]"
                )

    def _validate_ap(self, p: dict) -> None:
        self._require(p, "payload.AP", ["objective", "cost_matrix"])

        obj = p["objective"]
        if obj not in ("min", "max"):
            raise ORValidationError("payload.objective", f"指派问题目标必须为 'min' 或 'max'，得到 '{obj}'")

        cm = p["cost_matrix"]
        if not isinstance(cm, list) or len(cm) == 0:
            raise ORValidationError("payload.cost_matrix", "成本矩阵 'cost_matrix' 不能为空")

        col_len = None
        for i, row in enumerate(cm):
            if not isinstance(row, list) or not row:
                raise ORValidationError(f"payload.cost_matrix[{i}]", "矩阵每行必须是非空列表")
            if col_len is None:
                col_len = len(row)
            elif len(row) != col_len:
                raise ORValidationError("payload.cost_matrix", "成本矩阵各行列数必须一致")

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

    @staticmethod
    def _require(d: dict, prefix: str, fields: list[str]) -> None:
        for f in fields:
            if f not in d:
                raise ORValidationError(f"{prefix}.{f}", f"缺少必要字段 '{f}'")


class ModuleRegistry:
    def get_module(self, problem_type: str, sub_type: str | None, options: dict):
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


class Launcher:
    def __init__(self) -> None:
        self._validator = InputValidator()
        self._registry = ModuleRegistry()

    def solve(self, raw_input: dict) -> dict:
        try:
            validated = self._validator.validate(raw_input)
        except ORValidationError as e:
            problem_type = raw_input.get("problem_type", "UNKNOWN") if isinstance(raw_input, dict) else "UNKNOWN"
            return self._error_output(
                problem_type,
                f"输入校验失败 [{e.field}]：{e.message}"
            )

        pt = validated["problem_type"]
        payload = validated["payload"]
        options = validated["options"]
        sub = validated["sub_type"]

        if pt == "LP" and sub is None:
            n_vars = len(payload["c"])
            if n_vars == 2:
                sub = "graphical"
                validated["sub_type"] = "graphical"

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
            return self._error_output(pt, f"未预期错误：{type(e).__name__}: {e}")

        return result

    def solve_json(self, json_str: str, *, indent: int | None = 2) -> str:
        try:
            raw = json.loads(json_str)
        except json.JSONDecodeError as e:
            err = self._error_output("UNKNOWN", f"JSON 解析失败：{e}")
            return json.dumps(err, ensure_ascii=False, indent=indent)

        result = self.solve(raw)
        return json.dumps(result, ensure_ascii=False, indent=indent)

    @staticmethod
    def _error_output(problem_type: str, message: str) -> dict:
        return {
            "problem_type": problem_type,
            "status": STATUS_ERROR,
            "final_result": {},
            "iterations": [],
            "sensitivity": None,
            "error_message": message,
        }