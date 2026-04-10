"""
运输问题模块验证测试
包含：产销平衡 + 产销不平衡（虚拟产地）两个用例
"""
import sys, os, json
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root)
from main import Launcher

launcher = Launcher()


# ============================================================
# 测试 1：产销平衡标准运输问题
# 产地: A(30), B(40), C(50)  销地: 1(25), 2(35), 3(40), 4(20) 合计120
# 参考教材最优解: 总费用 = 510
# ============================================================
print("=" * 60)
print("Test 1: 产销平衡运输问题")
r1 = launcher.solve({
    "problem_type": "TP",
    "payload": {
        "supply": [30, 40, 50],
        "demand": [25, 35, 40, 20],
        "cost": [
            [2, 3, 11,  7],
            [1, 0,  6,  1],
            [5, 8, 15,  9],
        ]
    }
})
print("Status:", r1["status"])
print("Final:", json.dumps(r1["final_result"], ensure_ascii=False))
print("Total steps:", len(r1["iterations"]))
for it in r1["iterations"]:
    print(f"  Step {it['step']}: {it['action']}")
assert r1["status"] == "OPTIMAL", f"Expected OPTIMAL, got {r1['status']}: {r1.get('error_message')}"
print("[PASS]\n")


# ============================================================
# 测试 2：产销不平衡 — 总产量 > 总销量（添加虚拟销地）
#
# 产地: P1(40), P2(50)   → 总产量 = 90
# 销地: D1(30), D2(25)   → 总销量 = 55
# 差额 = 35 → 需新增虚拟销地 D3(35)，运价 = 0
# 手算验证: 虚拟列吸收多余产量，不影响实际运费
# ============================================================
print("=" * 60)
print("Test 2: 产销不平衡（总产量 > 总销量，添加虚拟销地）")
r2 = launcher.solve({
    "problem_type": "TP",
    "payload": {
        "supply": [40, 50],
        "demand": [30, 25],
        "cost": [
            [4, 8],
            [1, 9],
        ]
    }
})
print("Status:", r2["status"])
print("Final:", json.dumps(r2["final_result"], ensure_ascii=False))
print("Total steps:", len(r2["iterations"]))

# Step 0 必须是平衡检测快照
step_0 = r2["iterations"][0]
assert step_0["step"] == 0, "Step 0 should be balance check"
assert "不平衡" in step_0["action"] or "虚拟" in step_0["action"], \
    f"Step 0 action should mention imbalance: {step_0['action']}"
print(f"  Step 0 action: {step_0['action']}")

for it in r2["iterations"]:
    print(f"  Step {it['step']}: {it['action']}")

assert r2["status"] == "OPTIMAL", f"Expected OPTIMAL, got {r2['status']}: {r2.get('error_message')}"
print("[PASS]\n")


# ============================================================
# 测试 3：产销不平衡 — 总销量 > 总产量（添加虚拟产地）
#
# 产地: P1(20), P2(30)   → 总产量 = 50
# 销地: D1(25), D2(40)   → 总销量 = 65
# 差额 = 15 → 需新增虚拟产地 P3(15)，运价 = 0
# ============================================================
print("=" * 60)
print("Test 3: 产销不平衡（总销量 > 总产量，添加虚拟产地）")
r3 = launcher.solve({
    "problem_type": "TP",
    "payload": {
        "supply": [20, 30],
        "demand": [25, 40],
        "cost": [
            [3, 5],
            [2, 7],
        ]
    }
})
print("Status:", r3["status"])
print("Final:", json.dumps(r3["final_result"], ensure_ascii=False))
for it in r3["iterations"]:
    print(f"  Step {it['step']}: {it['action']}")

step_0_r3 = r3["iterations"][0]
assert "虚拟产地" in step_0_r3["action"] or "不平衡" in step_0_r3["action"], \
    f"Should detect imbalance: {step_0_r3['action']}"
assert r3["status"] == "OPTIMAL"
print("[PASS]\n")


# ============================================================
# 验证：JSON 序列化无 Fraction 对象泄露
# ============================================================
print("=" * 60)
print("Test 4: JSON 序列化验证")
for test_name, result in [("T1", r1), ("T2", r2), ("T3", r3)]:
    try:
        _ = json.dumps(result, ensure_ascii=False)
        print(f"  {test_name}: JSON serialization OK")
    except TypeError as e:
        raise AssertionError(f"{test_name} has non-serializable field: {e}")
print("[PASS]\n")

print("=" * 60)
print("ALL 4 TRANSPORTATION TESTS PASSED!")
