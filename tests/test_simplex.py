"""单纯形法模块验证测试"""
import sys, json, os
# 让测试无论从哪个目录运行都能找到 OR_Engine 根路径
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root)
from main import Launcher

launcher = Launcher()

# === 测试1: 标准 <= 约束（纯松弛变量） ===
# max Z = 2x1 + 3x2, s.t. x1+2x2<=14, 2x1+x2<=14, x2<=6
result = launcher.solve({
    "problem_type": "LP",
    "sub_type": "simplex",
    "payload": {
        "objective": "max",
        "c": [2, 3],
        "A": [[1,2],[2,1],[0,1]],
        "b": [14, 14, 6],
        "constraint_types": ["<=","<=","<="],
        "variable_names": ["x1","x2"]
    }
})
print("=== Test 1: Pure <= (max) ===")
print("Status:", result["status"])
print("Final:", result["final_result"])
print("Iterations:", len(result["iterations"]))
for it in result["iterations"]:
    print(f"  Step {it['step']}: {it['action']}")
    for c in it["calculation"]:
        print(f"    {c}")
assert result["status"] == "OPTIMAL", f"Expected OPTIMAL, got {result['status']}: {result.get('error_message')}"
print()

# === 测试2: 带 >= 约束的大 M 法 (min 问题) ===
# min Z = 2x1 + 3x2, s.t. x1+x2>=4, x1+3x2>=6, x1,x2>=0
# 手算最优解: x1=3, x2=1, Z=9
result2 = launcher.solve({
    "problem_type": "LP",
    "sub_type": "simplex",
    "payload": {
        "objective": "min",
        "c": [2, 3],
        "A": [[1,1],[1,3]],
        "b": [4, 6],
        "constraint_types": [">=",">="],
        "variable_names": ["x1","x2"]
    }
})
print("=== Test 2: Big M (>= constraints, min) ===")
print("Status:", result2["status"])
print("Final:", result2["final_result"])
print("Iterations:", len(result2["iterations"]))
for it in result2["iterations"]:
    print(f"  Step {it['step']}: {it['action']}")
    for c in it["calculation"]:
        print(f"    {c}")
assert result2["status"] == "OPTIMAL", f"Expected OPTIMAL, got {result2['status']}: {result2.get('error_message')}"
print()

# === 测试3: 带 = 约束的大 M 法 ===
# max Z = 3x1+5x2, s.t. x1<=4, x2<=6, x1+x2=8
# 手算最优解: x1=2, x2=6, Z=36
result3 = launcher.solve({
    "problem_type": "LP",
    "sub_type": "simplex",
    "payload": {
        "objective": "max",
        "c": [3, 5],
        "A": [[1,0],[0,1],[1,1]],
        "b": [4, 6, 8],
        "constraint_types": ["<=","<=","="],
        "variable_names": ["x1","x2"]
    }
})
print("=== Test 3: Equality constraint ===")
print("Status:", result3["status"])
print("Final:", result3["final_result"])
assert result3["status"] == "OPTIMAL", f"Expected OPTIMAL, got {result3['status']}: {result3.get('error_message')}"
print()

# === 测试4: 无可行解 ===
# max Z = x1+x2, s.t. x1+x2<=2, x1+x2>=5
result4 = launcher.solve({
    "problem_type": "LP",
    "sub_type": "simplex",
    "payload": {
        "objective": "max",
        "c": [1, 1],
        "A": [[1,1],[1,1]],
        "b": [2, 5],
        "constraint_types": ["<=",">="],
    }
})
print("=== Test 4: Infeasible ===")
print("Status:", result4["status"])
assert result4["status"] == "INFEASIBLE", f"Expected INFEASIBLE, got {result4['status']}"
print()

print("=" * 50)
print("ALL 4 SIMPLEX TESTS PASSED!")
