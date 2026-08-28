# 🚀 OR_Engine (运筹学推演引擎)

> **"不只是给出答案，更是重现思考的轨迹。"**
 
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Precision](https://img.shields.io/badge/precision-Fraction-orange.svg)]()
[![License](https://img.shields.io/badge/license-MIT-blue.svg)]()

**OR_Engine** 是一个基于纯 Python 构建的轻量级、高精度运筹学算法引擎。与传统的优化器（如 Gurobi, SciPy）只返回干瘪的最终结果不同，OR_Engine 专为**教育、算法推演与解题追踪**而生。它能够生成高度结构化的 JSON 迭代快照，完美复刻人类手工计算的每一步细节。

---

## ✨ 核心卖点 (Core Features)

*   🎯 **绝对数学精度 (Zero Floating-Point Error)**
    坚守纯 Python 标准库底线，全链路运算强制采用 `fractions.Fraction`。彻底消灭浮点误差，无论是迭代几十轮的矩阵求逆还是 Gomory 割平面生成，确保最后输出的 `12/7` 绝不是尴尬的 `1.714285...`。
*   🎬 **上帝视角推演 (Iteration Snapshots)**
    每次运算不仅反馈最终最优解，还提供极度详尽的 `iterations` JSON 状态流。包含：单纯形表结构、初等行变换计算公式、闭回路寻址路径（Stepping Stone）、DFS 剪枝界限等，简直是活生生的运筹学教科书。
*   🧩 **优雅的解耦与复用 (Elegant Composition)**
    高阶算法架构极致优雅。例如在处理复杂的博弈论混合策略、或是整数规划时，引擎内部会自动将其转化为标准的线性规划 Payload，并在内部平滑调用底层 `SimplexModule` 核进行求解与逆变换。

---

## 🧰 模块支持清单 (Supported Modules)

目前引擎已全线支持 6 大核心运筹学经典模块：

- **[模块 1A] 线性规划 — 单纯形法 (`lp_simplex.py`)**：支持大 M 法自动处理 `>=` 和 `=` 约束，严格推演初等行变换。
- **[模块 1B] 线性规划 — 图解可视化 (`lp_graphical.py`)**：特化 2 变量平面求解器，精确生成凸多边形极点边界。（附赠 `visualize_graph.py` Matplotlib 外挂渲染脚本）。
- **[模块 2] 运输问题 (`transportation.py`)**：集成 Vogel（伏格尔逼近法）初始解建树，MODI（位势法）最优性检验，及闭回路调整全套工作流，产销不平衡自动修补。
- **[模块 3] 整数规划 (`branch_and_bound.py`, `cutting_plane.py`)**：囊括 DFS 分支定界搜索树生成 以及 Gomory 割平面分数反代数约束注入。
- **[模块 4] 指派问题 (`hungarian.py`)**：匈牙利法全态推演，涵盖行列化简、König 定理最少划线覆盖及特征矩阵缩减调整。
- **[模块 5] 博弈论 (`game_theory.py`)**：全自动识别完全状态二人零和博弈（鞍点甄别），对无鞍点情况自动构筑概率密度的混合策略 LP 求解器。

---

## 📂 目录结构 (Directory Structure)

```text
OR_Engine/
├── main.py                  # 🚀 引擎主启动器 & 路由调度
├── base_module.py           # 🧬 基类与约束契约、Fraction 高精度算子
├── modules/                 # 核心算法模块库
│   ├── lp_simplex.py        # 单纯形法推演模块
│   ├── lp_graphical.py      # 图解推演模块
│   ├── transportation.py    # 运输问题计算与推演
│   ├── branch_and_bound.py  # 整数规划：分支定界
│   ├── cutting_plane.py     # 整数规划：割平面
│   ├── hungarian.py         # 指派问题 (匈牙利法)
│   └── game_theory.py       # 二人零和博弈
└── tests/                   # 单元测试与外挂应用
    └── visualize_graph.py   # 独立的可视化渲染脚本 (需要 matplotlib)
```

---

## ⚡ 快速上手 (Quick Start)

你可以借由 `Launcher` 非常轻易地将引擎嵌入至任意 Python 工作流中：

```python
import json
from main import Launcher

# 1. 初始化启动器
launcher = Launcher()

# 2. 准备 payload（以指派问题为例）
payload = {
    "problem_type": "AP",
    "payload": {
        "objective": "min",
        "cost_matrix": [
            [9, 2, 7, 8],
            [6, 4, 3, 7],
            [5, 8, 1, 8],
            [7, 6, 9, 4]
        ]
    }
}

# 3. 点火计算
result = launcher.solve(payload)

# 4. 提取上帝视角的精确结果
if result["status"] == "OPTIMAL":
    print("🎯 最优分配方案:", json.dumps(result["final_result"], indent=2, ensure_ascii=False))
    print(f"📖 总计推演步数: {len(result['iterations'])} 步")
else:
    print("⚠️ 求解报错:", result["error_message"])
```

**命令行测试与体验：**
引擎内置了丰富示例群，开箱即用：
```bash
python main.py --example lp_simplex
python main.py --example gt
```

---

## 🧱 当前架构

```text
OR_Engine/
├── main.py                  # Launcher、输入校验与 CLI
├── base_module.py           # BaseModule、Fraction 与 RationalNumber
├── modules/                 # LP/IP/TP/AP/GT 算法模块
├── schemas/                 # FastAPI/Pydantic 请求与响应模型
├── services/                # Launcher 结果适配与统一 API 响应
├── api/                     # FastAPI 应用与路由
├── frontend/                # Vue 3 + Vite + Pinia 工作台
└── tests/                   # 算法回归脚本
```

单纯形模块使用精确 `Fraction` 的 Two-Phase Simplex。API 层将数值转换为包含 `display`、`numerator`、`denominator` 和 `decimal` 的 `RationalNumber` 对象，同时保留 `final_result.objective_value` 与 `final_result.solution` 以兼容旧调用方。

## 🚀 FastAPI API

安装 Python 依赖：

```bash
python -m pip install -r requirements.txt
```

启动 API：

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

可用接口：

- `GET /api/health`
- `GET /api/examples`
- `POST /api/solve`
- `GET /docs`

`POST /api/solve` 请求示例：

```json
{
  "problem_type": "LP",
  "sub_type": "simplex",
  "payload": {
    "objective": "max",
    "c": [2, 3],
    "A": [[1, 2], [2, 1]],
    "b": [14, 14],
    "constraint_types": ["<=", "<="]
  }
}
```

## 🖥️ Vue 前端

```bash
cd frontend
npm install
npm run dev
```

开发服务器默认运行在 `http://localhost:5173`，并将 `/api` 代理到 `http://localhost:8000`。生产构建使用：

```bash
npm run build
```

Cloudflare Pages 只负责托管 `frontend/dist` 静态文件；Python FastAPI 必须独立部署。部署前端时，将 `VITE_API_BASE` 设置为公开 API 服务地址，并在 API 服务中将 CORS 白名单限制为实际前端域名。

## ✅ 测试

标准环境中执行：

```bash
python -m pytest -q
```

也可以直接运行现有回归脚本：

```bash
PYTHONIOENCODING=utf-8 python tests/test_simplex.py
PYTHONIOENCODING=utf-8 python tests/test_integer_programming.py
```

CLI 示例：

```bash
python main.py --example lp_simplex
python main.py --example gt
```
