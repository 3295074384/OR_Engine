import sys
import os
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

# Ensure main launcher can be imported
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root)
from main import Launcher

def solve_and_visualize():
    launcher = Launcher()
    
    # 示例题目: 
    # max Z = 3x1 + 5x2
    # s.t. 
    # x1 <= 4
    # 2x2 <= 12  => x2 <= 6
    # 3x1 + 2x2 <= 18
    # x1, x2 >= 0
    payload = {
        "problem_type": "LP",
        "sub_type": "graphical",
        "payload": {
            "objective": "max",
            "c": [3, 5],
            "A": [
                [1, 0],
                [0, 2],
                [3, 2]
            ],
            "b": [4, 12, 18],
            "constraint_types": ["<=", "<=", "<="],
            "variable_names": ["x1", "x2"]
        }
    }
    
    # 获取 JSON 结果
    result = launcher.solve(payload)
    if result["status"] != "OPTIMAL":
        print(f"求解失败: {result.get('error_message')}")
        return
    
    final = result["final_result"]
    boundary_lines = final["boundary_lines"]
    feasible_vertices = final["feasible_vertices"]
    solution = final["solution"]
    opt_val = final["objective_value"]
    
    print(f"最优解: x1 = {solution['x1']}, x2 = {solution['x2']}")
    print(f"最优值 Z = {opt_val}")
    
    # 准备绘图
    plt.figure(figsize=(8, 8))
    
    # 解析顶点转换成 float 画多边形
    pts = []
    for pt in feasible_vertices:
        pts.append([float(eval(pt["x1"])), float(eval(pt["x2"]))])
        
    pts = np.array(pts)
    
    # 按极角排序顶点以绘制凸多边形
    if len(pts) > 2:
        center = pts.mean(axis=0)
        angles = np.arctan2(pts[:, 1] - center[1], pts[:, 0] - center[0])
        pts = pts[np.argsort(angles)]
        
        polygon = Polygon(pts, closed=True, facecolor='lightgreen', edgecolor='green', alpha=0.5, label='Feasible Region')
        plt.gca().add_patch(polygon)
        
    # 寻找最大坐标以设定坐标轴范围
    max_x1 = max(float(max([p[0] for p in pts])) * 1.5, 5) if len(pts)>0 else 10
    max_x2 = max(float(max([p[1] for p in pts])) * 1.5, 5) if len(pts)>0 else 10
    
    # 绘制直线
    x1_vals = np.linspace(-1, max_x1 + 2, 400)
    
    for L in boundary_lines:
        a1, a2, d = float(eval(L["a1"])), float(eval(L["a2"])), float(eval(L["d"]))
        # a1*x1 + a2*x2 = d
        if a2 != 0:
            x2_vals = (d - a1 * x1_vals) / a2
            plt.plot(x1_vals, x2_vals, linestyle='--', color='blue', alpha=0.7)
        else:
            # 垂直线
            x1_val = d / a1
            plt.axvline(x=x1_val, linestyle='--', color='blue', alpha=0.7)
            
    # 高亮所有顶点
    for pt in pts:
        plt.plot(pt[0], pt[1], 'ko', markersize=5)
        
    # 醒目地高亮最优解 ⭐
    opt_x1 = float(eval(solution['x1']))
    opt_x2 = float(eval(solution['x2']))
    plt.plot(opt_x1, opt_x2, marker='*', markersize=20, color='red', label=f'Optimal: ({opt_x1}, {opt_x2}), Z={opt_val}')
    
    plt.xlim(-0.5, max_x1)
    plt.ylim(-0.5, max_x2)
    plt.xlabel('x1')
    plt.ylabel('x2')
    plt.title('Linear Programming - Graphical Method')
    plt.axhline(0, color='black', linewidth=1)
    plt.axvline(0, color='black', linewidth=1)
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend()
    
    # 保存并展示图形
    out_path = os.path.join(os.path.dirname(__file__), 'graphical_output.png')
    plt.savefig(out_path, dpi=150)
    print(f"图解法可视化结果已保存至: {out_path}")

if __name__ == "__main__":
    solve_and_visualize()
    
