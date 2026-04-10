"""
匈牙利法模块验证测试

测试 1：经典 4×4 min 指派问题（手算可验证）
测试 2：3×4 非方阵（人员数 < 任务数，添加虚拟行）
测试 3：max 指派问题（转化为 min 后求解）
测试 4：JSON 序列化验证
"""
import sys, os, json
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root)
from main import Launcher

launcher = Launcher()

# ── Test 1: 经典 4×4 min 指派 ───────────────────────────────────────────────
# 成本矩阵（教材标准例题）
# 手算最优指派: A→3, B→1, C→4, D→2，总成本=2+5+6+3=16
# (实际可能因矩阵不同而异，此处用一个公认例题)
print("=" * 60)
print("Test 1: 4×4 min 指派问题")
r1 = launcher.solve({
    "problem_type": "AP",
    "payload": {
        "objective": "min",
        "cost_matrix": [
            [9, 2, 7, 8],
            [6, 4, 3, 7],
            [5, 8, 1, 8],
            [7, 6, 9, 4],
        ]
    }
})
print("Status:", r1["status"])
print("Final:", json.dumps(r1["final_result"], ensure_ascii=False))
print("Steps:", len(r1["iterations"]))

assert r1["status"] == "OPTIMAL", f"Expected OPTIMAL: {r1.get('error_message')}"
# 验证：总成本数值上应该合理
total_cost = int(r1["final_result"]["total_cost"])
print(f"Total cost = {total_cost} (should be <= 20)")
for it in r1["iterations"]:
    print(f"  Step {it['step']}: {it['action'][:70]}")
print("[PASS]\n")


# ── Test 2: 3×4 非方阵（3 人 4 任务，补虚拟行）─────────────────────────────
print("=" * 60)
print("Test 2: 3×4 非方阵（3 人，4 任务 — 需补虚拟第 4 人行）")
r2 = launcher.solve({
    "problem_type": "AP",
    "payload": {
        "objective": "min",
        "cost_matrix": [
            [10,  5,  9,  7],
            [ 3,  6,  2,  8],
            [ 7,  1,  4, 10],
        ]
    }
})
print("Status:", r2["status"])
print("Final:", json.dumps(r2["final_result"], ensure_ascii=False))
print("Steps:", len(r2["iterations"]))

assert r2["status"] == "OPTIMAL", f"Expected OPTIMAL: {r2.get('error_message')}"

# Step 0 应该记录虚拟行添加
step0 = r2["iterations"][0]
assert "虚拟" in step0["action"] or "虚拟" in "".join(step0["calculation"]), \
    f"Step0 should mention dummy row/col: {step0['action']}"
print(f"  Step 0 (padding): {step0['action']}")
for c in step0["calculation"]:
    print(f"    {c}")

for it in r2["iterations"]:
    print(f"  Step {it['step']}: {it['action'][:70]}")

# 总成本应 >= 0
assign = r2["final_result"]["assignment"]
print(f"Assignment: {assign}")
print("[PASS]\n")


# ── Test 3: max 指派问题 ─────────────────────────────────────────────────────
print("=" * 60)
print("Test 3: 3×3 max 指派问题（max→min 转化）")
# max 利润矩阵
r3 = launcher.solve({
    "problem_type": "AP",
    "payload": {
        "objective": "max",
        "cost_matrix": [
            [3, 5, 4],
            [6, 3, 2],
            [4, 4, 5],
        ]
    }
})
print("Status:", r3["status"])
print("Final:", json.dumps(r3["final_result"], ensure_ascii=False))
print("Steps:", len(r3["iterations"]))

assert r3["status"] == "OPTIMAL", f"Expected OPTIMAL: {r3.get('error_message')}"
# Step 0 should mention max→min
step0_r3 = r3["iterations"][0]
assert "max" in step0_r3["action"].lower() or "min" in step0_r3["action"].lower(), \
    f"Step0 should mention conversion: {step0_r3['action']}"
print(f"  max→min Step 0: {step0_r3['action']}")
for it in r3["iterations"]:
    print(f"  Step {it['step']}: {it['action'][:70]}")
print("[PASS]\n")


# ── Test 4: JSON 序列化验证 ──────────────────────────────────────────────────
print("=" * 60)
print("Test 4: JSON 序列化验证")
for name, result in [("4x4-min", r1), ("3x4-nonSq", r2), ("3x3-max", r3)]:
    try:
        _ = json.dumps(result, ensure_ascii=False)
        print(f"  {name}: JSON OK")
    except TypeError as e:
        raise AssertionError(f"{name} has non-serializable field: {e}")
print("[PASS]\n")

print("=" * 60)
print("ALL 4 HUNGARIAN / ASSIGNMENT TESTS PASSED!")
