# fmt: off
# =============================================================================
# Author:      王梓轩 (AI)
# Project:     OR_Engine - Streamlit Web Dashboard
# Description: 运筹学推演引擎的 Web 可视化页面。通过 st.data_editor 实现优雅矩阵录入，
#              可视化二维图解法解空间，并展开迭代推演步骤供人类研读。
# =============================================================================
# fmt: on

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
import traceback

from main import Launcher
from base_module import to_fraction

st.set_page_config(
    page_title="OR Engine 推演系统",
    page_icon="🚀",
    layout="wide",
)

@st.cache_resource
def get_launcher():
    return Launcher()

launcher = get_launcher()

# ─────────────────────────────────────────────────────────────────────────────
# 辅助函数：绘制图解法可行域
# ─────────────────────────────────────────────────────────────────────────────
def plot_graphical_method(final_result):
    boundary_lines = final_result["boundary_lines"]
    feasible_vertices = final_result["feasible_vertices"]
    solution = final_result["solution"]
    opt_val = final_result["objective_value"]
    var_names = list(solution.keys())
    
    fig, ax = plt.subplots(figsize=(8, 8))
    
    # 提取可行点并转为 float
    pts = []
    for pt in feasible_vertices:
        pts.append([float(to_fraction(pt["x1"])), float(to_fraction(pt["x2"]))])
        
    pts = np.array(pts)
    
    # 按极角排序画凸多边形
    if len(pts) > 2:
        center = pts.mean(axis=0)
        angles = np.arctan2(pts[:, 1] - center[1], pts[:, 0] - center[0])
        pts = pts[np.argsort(angles)]
        polygon = Polygon(pts, closed=True, facecolor='lightgreen', edgecolor='green', alpha=0.5, label='Feasible Region')
        ax.add_patch(polygon)
        
    # 计算极值，划定边界范围
    max_x1 = max(float(max([p[0] for p in pts])) * 1.5, 5) if len(pts)>0 else 10
    max_x2 = max(float(max([p[1] for p in pts])) * 1.5, 5) if len(pts)>0 else 10
    
    x1_vals = np.linspace(-1, max_x1 + 2, 400)
    for L in boundary_lines:
        a1, a2, d = (float(to_fraction(L[key])) for key in ("a1", "a2", "d"))
        if a2 != 0:
            x2_vals = (d - a1 * x1_vals) / a2
            ax.plot(x1_vals, x2_vals, linestyle='--', color='blue', alpha=0.3)
        else:
            x1_val = d / a1
            ax.axvline(x=x1_val, linestyle='--', color='blue', alpha=0.3)
            
    # 高亮顶点
    for pt in pts:
        ax.plot(pt[0], pt[1], 'ko', markersize=5)
        
    # 标星最优解
    opt_x1 = float(to_fraction(solution[var_names[0]]))
    opt_x2 = float(to_fraction(solution[var_names[1]]))
    ax.plot(opt_x1, opt_x2, marker='*', markersize=20, color='red', label=f'Optimal: ({opt_x1}, {opt_x2}), Z={opt_val}')
    
    ax.set_xlim(-0.5, max_x1)
    ax.set_ylim(-0.5, max_x2)
    ax.set_xlabel(var_names[0])
    ax.set_ylabel(var_names[1])
    ax.set_title('Linear Programming - Graphical Solution')
    ax.axhline(0, color='black', linewidth=1)
    ax.axvline(0, color='black', linewidth=1)
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc="upper right")
    
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# 辅助函数：推演步骤展示
# ─────────────────────────────────────────────────────────────────────────────
def display_iterations(iterations):
    with st.expander("📖 查看详细推演步骤 (Iteration Snapshots)", expanded=False):
        for idx, it in enumerate(iterations):
            st.markdown(f"**Step {it.get('step', idx)}**: `< {it.get('action', '')} >`")
            
            # 渲染 calculation 行（数学推导与计算过程）
            calcs = it.get("calculation", [])
            if calcs:
                calc_str = "\n".join([f"> {c}" for c in calcs])
                st.markdown(calc_str)
            
            # 如果存在状态矩阵 (单纯形表、或成本矩阵等)，可用 DataFrame 或者 Markdown 表格显示
            sm = it.get("state_matrix", {})
            if sm:
                if sm.get("type") == "simplex_tableau":
                    st.write("**当前单纯形表 (Tableau):**")
                    df = pd.DataFrame(sm["tableau"])
                    df.columns = sm["headers"]
                    st.dataframe(df, use_container_width=True)
                elif sm.get("type") == "transportation":
                    st.write("**当前供需运价基格表:**")
                    # 这里也可以深层渲染状态字典
                    st.json(sm) 
                else: # 其他各类矩阵或 JSON 状态兜底
                    st.json(sm)
            st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# 侧边栏导航
# ─────────────────────────────────────────────────────────────────────────────
st.sidebar.title("🛠️ OR Engine 导航")
problem_type = st.sidebar.radio(
    "选择推演问题类型：",
    [
        "线性规划 (图解法)",
        "线性规划 (单纯形法)",
        "运输问题",
        "整数规划",
        "指派问题",
        "博弈论",
    ]
)

st.title(f"🚀 OR Engine > {problem_type}")
st.markdown("基于纯 Python 标准库构建，严格使用 `fractions` 消灭每一丝浮点误差。上帝视角还原每一步算法推演的心智路径。")

payload = {}
# ─────────────────────────────────────────────────────────────────────────────
# 表单生成逻辑分发
# ─────────────────────────────────────────────────────────────────────────────
try:
    if problem_type in ["线性规划 (图解法)", "线性规划 (单纯形法)", "整数规划"]:
        # 通用 LP 输入框
        col1, col2 = st.columns(2)
        with col1:
            objective = st.radio("目标函数方向:", ["max", "min"], horizontal=True)
        with col2:
            n_vars = 2 if "图解法" in problem_type else st.number_input("决策变量数量 (N)", min_value=1, value=2, step=1)
        
        st.subheader("1. 目标函数系数 (C向量)")
        default_c = [1] * n_vars
        df_c = pd.DataFrame([default_c], columns=[f"x{i+1}" for i in range(n_vars)])
        edited_c = st.data_editor(df_c, key="c_editor", use_container_width=True, hide_index=True)
        
        st.subheader("2. 约束条件组")
        st.caption("直接修改数值。可以通过加号在底部动态添加新约束。可以修改约束符号 (<=, >=, =)。")
        # 构建约束默认表格
        default_A = [[1] * n_vars, [1] * n_vars]
        cols = [f"x{i+1}" for i in range(n_vars)]
        df_A = pd.DataFrame(default_A, columns=cols)
        df_A["Type"] = ["<=", "<="]
        df_A["rhs"] = [10, 10]
        
        edited_A = st.data_editor(
            df_A, 
            num_rows="dynamic", 
            key="a_editor", 
            use_container_width=True,
            column_config={
                "Type": st.column_config.SelectboxColumn("符号", options=["<=", ">=", "="], required=True)
            }
        )
        
        # 组装 Payload
        payload = {
            "problem_type": "LP" if "整数" not in problem_type else "IP",
            "payload": {
                "objective": objective,
                "c": edited_c.iloc[0].tolist(),
                "A": edited_A[cols].values.tolist(),
                "b": edited_A["rhs"].tolist(),
                "constraint_types": edited_A["Type"].tolist(),
                "variable_names": cols
            }
        }
        
        if "图解法" in problem_type:
            payload["sub_type"] = "graphical"
            
        elif "整数规划" in problem_type:
            integer_vars_options = st.multiselect("需要取整的变量:", options=cols, default=cols)
            payload["payload"]["integer_vars"] = [int(v[1:]) - 1 for v in integer_vars_options] # x1 -> 0
            
            method = st.selectbox("核心求解算法:", ["branch_bound", "cutting_plane"], 
                                  format_func=lambda x: "分支定界法 (Branch & Bound)" if x=="branch_bound" else "Gomory 割平面法 (Cutting Plane)")
            payload["options"] = {"integer_method": method}


    elif problem_type == "运输问题":
        col1, col2 = st.columns(2)
        with col1:
            m_supply = st.number_input("产地数量 (Rows)", min_value=1, value=3)
        with col2:
            n_demand = st.number_input("销地数量 (Cols)", min_value=1, value=3)
        
        st.subheader("1. 供需量设定")
        col_s, col_d = st.columns(2)
        with col_s:
            st.caption("产地产量 (Supply)")
            df_s = pd.DataFrame([[10] * m_supply], columns=[f"S{i+1}" for i in range(m_supply)])
            edited_s = st.data_editor(df_s, key="s", hide_index=True)
        with col_d:
            st.caption("销地需求 (Demand)")
            df_d = pd.DataFrame([[10] * n_demand], columns=[f"D{i+1}" for i in range(n_demand)])
            edited_d = st.data_editor(df_d, key="d", hide_index=True)
            
        st.subheader("2. 单位运价矩阵 (Cost)")
        df_cost = pd.DataFrame([[1] * n_demand for _ in range(m_supply)], 
                               columns=[f"D{i+1}" for i in range(n_demand)],
                               index=[f"S{i+1}" for i in range(m_supply)])
        edited_cost = st.data_editor(df_cost, key="cost", use_container_width=True)
        
        payload = {
            "problem_type": "TP",
            "payload": {
                "supply": edited_s.iloc[0].tolist(),
                "demand": edited_d.iloc[0].tolist(),
                "cost": edited_cost.values.tolist(),
            }
        }

    elif problem_type == "指派问题":
        objective = st.radio("目标方向:", ["min (最少成本)", "max (最大利润)"], horizontal=True)
        obj_key = "min" if "min" in objective else "max"
        
        col1, col2 = st.columns(2)
        with col1:
            m_workers = st.number_input("员工/行数", min_value=1, value=4)
        with col2:
            n_tasks = st.number_input("任务/列数", min_value=1, value=4)
            
        st.subheader("成本/效益矩阵")
        st.caption("允许非方阵，引擎将自动用虚拟代价补齐！")
        df_assign = pd.DataFrame([[1]*n_tasks for _ in range(m_workers)], 
                                 columns=[f"T{i+1}" for i in range(n_tasks)],
                                 index=[f"W{i+1}" for i in range(m_workers)])
        edited_assign = st.data_editor(df_assign, key="assign", use_container_width=True)
        
        payload = {
            "problem_type": "AP",
            "payload": {
                "objective": obj_key,
                "cost_matrix": edited_assign.values.tolist()
            }
        }

    elif problem_type == "博弈论":
        st.markdown("⚠️ 请以 **一行游戏者 (Player A)** 的收益为视角填入矩阵。")
        col1, col2 = st.columns(2)
        with col1:
            m_a = st.number_input("甲方策略数", min_value=1, value=2)
        with col2:
            n_b = st.number_input("乙方策略数", min_value=1, value=2)
            
        df_gt = pd.DataFrame([[0]*n_b for _ in range(m_a)], 
                            columns=[f"B策略{i+1}" for i in range(n_b)],
                            index=[f"A策略{i+1}" for i in range(m_a)])
        edited_gt = st.data_editor(df_gt, key="gt", use_container_width=True)
        
        payload = {
            "problem_type": "GT",
            "payload": {
                "payoff_matrix": edited_gt.values.tolist()
            }
        }

except Exception as e:
    st.error(f"UI构造出现异常: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# 求解与结果展示
# ─────────────────────────────────────────────────────────────────────────────
st.divider()

if st.button("🚀 启动引擎求解", type="primary", use_container_width=True):
    with st.spinner("系统推演中...（完全基于 Fraction 无浮点模拟）"):
        try:
            # 运行核心引擎
            result = launcher.solve(payload)
            
            if result.get("status") == "OPTIMAL":
                st.success("✅ 解析成功: STATUS_OPTIMAL", icon="🎉")
                
                # 顶部看板：结果总览
                final = result["final_result"]
                
                # 不同问题的特定展示逻辑
                if problem_type in ["线性规划 (图解法)", "线性规划 (单纯形法)", "整数规划"]:
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        st.metric("最优目标函数值 (Z)", final["objective_value"])
                    with col2:
                        st.write("最优变量解:")
                        st.json(final["solution"], expanded=True)
                        
                    if "图解法" in problem_type:
                        st.subheader("🗺️ 可行域图解空间")
                        fig = plot_graphical_method(final)
                        st.pyplot(fig)
                        
                elif problem_type == "运输问题":
                    st.metric("底总运费成本 (Z)", final["total_cost"])
                    st.write("最优配送方案 (分配矩阵中的非零格):")
                    # 将 {"x(1,2)": "25", ...} 转为更易读的 DataFrame
                    alloc_df = pd.DataFrame([{"路径": k, "运量": v} for k, v in final["allocation"].items()])
                    st.dataframe(alloc_df, use_container_width=True)

                elif problem_type == "指派问题":
                    st.metric("指派总成本/回报 (Z)", final["total_cost"])
                    st.write("最优指派对应配对:")
                    st.dataframe(pd.DataFrame(final["assignment"]))

                elif problem_type == "博弈论":
                    st.metric("对策值 (Game Value)", final["game_value"])
                    if final["type"] == "pure_strategy":
                        st.info("🎯 这是一个【纯策略】博弈！(存在鞍点)")
                        st.write("鞍点坐标: ", final["saddle_points"])
                    else:
                        st.info("🎲 这是一个【混合策略】博弈！(Alpha ≠ Beta)")
                    
                    st.write("**Player A (行玩家) 策略分布:**")
                    st.json(final["player1_strategy"])
                    st.write("**Player B (列玩家) 策略分布:**")
                    st.json(final["player2_strategy"])

                # 推演步骤挂载
                display_iterations(result.get("iterations", []))

            elif result.get("status") == "INFEASIBLE":
                st.warning(f"❌ 警告：未找到可行解 (INFEASIBLE) -> {result.get('error_message')}")
                display_iterations(result.get("iterations", []))
            
            else:
                st.error(f"⚠️ 引擎运行抛出异常: {result.get('error_message', 'Unknown Error')}")
                
        except Exception as e:
            st.error(f"系统运行崩溃: {e}")
            st.code(traceback.format_exc())
