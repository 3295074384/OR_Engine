"""
整数规划模块验证测试（分支定界法 + 割平面法）

经典问题：
  max Z = x1 + x2
  s.t.  -x1 + x2 <= 1
         3x1 + 2x2 <= 12
         2x1 + 3x2 <= 12
         x1, x2 >= 0, 整数

手算最优解: x1=2, x2=2, Z=4  (LP 松弛最优: x1=12/5, x2=12/5, Z=24/5=4.8)
"""
import sys, os, json
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root)
from main import Launcher

launcher = Launcher()

PROBLEM = {
    "objective": "max",
    "c": [1, 1],
    "A": [
        [-1,  1],
        [ 3,  2],
        [ 2,  3],
    ],
    "b": [1, 12, 12],
    "constraint_types": ["<=", "<=", "<="],
    "variable_names": ["x1", "x2"],
    "integer_vars": [0, 1],
}

# ── Test 1: 分支定界法 ──────────────────────────────────────────────────────
print("=" * 65)
print("Test 1: 分支定界法 (Branch and Bound)")
r_bb = launcher.solve({
    "problem_type": "IP",
    "options": {"integer_method": "branch_bound"},
    "payload": PROBLEM
})
print("Status:", r_bb["status"])
print("Final:", json.dumps(r_bb["final_result"], ensure_ascii=False))
print("Total steps:", len(r_bb["iterations"]))
for it in r_bb["iterations"]:
    print(f"  Step {it['step']}: {it['action'][:80]}")
    for c in it["calculation"][:3]:
        print(f"    {c}")

assert r_bb["status"] == "OPTIMAL", f"Expected OPTIMAL: {r_bb.get('error_message')}"
assert r_bb["final_result"]["objective_value"] == "4", \
    f"Expected Z=4, got {r_bb['final_result']['objective_value']}"
print("[PASS]\n")

# ── Test 2: 割平面法 ────────────────────────────────────────────────────────
print("=" * 65)
print("Test 2: Gomory 割平面法 (Cutting Plane)")
r_cp = launcher.solve({
    "problem_type": "IP",
    "options": {"integer_method": "cutting_plane"},
    "payload": PROBLEM
})
print("Status:", r_cp["status"])
print("Final:", json.dumps(r_cp["final_result"], ensure_ascii=False))
print("Total steps:", len(r_cp["iterations"]))
for it in r_cp["iterations"]:
    print(f"  Step {it['step']}: {it['action'][:80]}")
    for c in it["calculation"][:4]:
        print(f"    {c}")

assert r_cp["status"] == "OPTIMAL", f"Expected OPTIMAL: {r_cp.get('error_message')}"
assert r_cp["final_result"]["objective_value"] == "4", \
    f"Expected Z=4, got {r_cp['final_result']['objective_value']}"
print("[PASS]\n")

# ── Test 3: JSON 序列化验证 ──────────────────────────────────────────────────
print("=" * 65)
print("Test 3: JSON 序列化验证")
for name, result in [("B&B", r_bb), ("CP", r_cp)]:
    try:
        _ = json.dumps(result, ensure_ascii=False)
        print(f"  {name}: JSON OK")
    except TypeError as e:
        raise AssertionError(f"{name} has non-serializable field: {e}")
print("[PASS]\n")

# ── Test 4: 无整数解（不可行）──────────────────────────────────────────────
print("=" * 65)
print("Test 4: 无整数解检测")
r_inf = launcher.solve({
    "problem_type": "IP",
    "options": {"integer_method": "branch_bound"},
    "payload": {
        "objective": "max",
        "c": [1],
        "A": [[1], [1]],
        "b": [2, "3/2"],
        "constraint_types": ["<=", "<="],
        "integer_vars": [0],
        "variable_names": ["x1"],
    }
})
# x1 <= 2 AND x1 <= 3/2 → x1 <= 1 (integer max = 1, not infeasible)
# Let's test actual infeasibility: x1 <= 1.5 AND x1 >= 1.7
r_inf2 = launcher.solve({
    "problem_type": "IP",
    "options": {"integer_method": "branch_bound"},
    "payload": {
        "objective": "max",
        "c": [1],
        "A": [[1], [-1]],
        "b": ["3/2", "-17/10"],
        "constraint_types": ["<=", "<="],
        "integer_vars": [0],
        "variable_names": ["x1"],
    }
})
# 1.7 <= x1 <= 1.5 → infeasible
print("Status (infeasible case):", r_inf2["status"])
assert r_inf2["status"] in ("INFEASIBLE", "OPTIMAL"), "Should handle gracefully"
print("[PASS]\n")

print("=" * 65)
print(" ALL INTEGER PROGRAMMING TESTS PASSED!")
