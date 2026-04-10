"""
博弈论模块验证测试

测试 1：有纯策略鞍点（α = β）
测试 2：无鞍点 3×3 矩阵 → LP 混合策略（精确分数验证）
测试 3：含负元素矩阵（触发 K 平移后 LP）
测试 4：JSON 序列化验证
"""
import sys, os, json
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root)
from main import Launcher
from fractions import Fraction

launcher = Launcher()

# ── Test 1：有纯策略鞍点 ──────────────────────────────────────────────────────
# 矩阵：
#       乙1  乙2  乙3    行最小
# 甲1 [  3,   2,   4 ]    2
# 甲2 [  1,   5,   3 ]    1
# 甲3 [  4,   3,   2 ]    2
# 列最大: 4  5  4
# α = max(2,1,2) = 2,  β = min(4,5,4) = 4  → α ≠ β ... 这不对，换矩阵
#
# 改用经典鞍点例题：
#       乙1  乙2  乙3  行最小
# 甲1 [  4,   6,   3 ]   3
# 甲2 [  1,   6,   4 ]   1
# 甲3 [  5,   4,   3 ]   3
# 列最大: 5   6   4
# α = max(3,1,3) = 3,  β = min(5,6,4) = 4  → 仍然不等

# 用教材标准鞍点矩阵：
#       乙1  乙2   行最小
# 甲1 [  2,   4 ]   2
# 甲2 [  6,   3 ]   3
# 列最大: 6   4
# α=max(2,3)=3, β=min(6,4)=4 仍不等...

# 直接使用行最小=列最大的明确鞍点：
#       乙1  乙2  乙3   行最小
# 甲1 [  1,   2,   3 ]   1
# 甲2 [  5,   4,   3 ]   3  ← saddle at (2,3)
# 甲3 [  2,   3,   4 ]   2
# 列最大: 5   4   4
# α = max(1,3,2) = 3,  β = min(5,4,4) = 4!  还是不等...

# Let me use the classic matrix that definitely has a saddle point:
# A = [[2, 2], [1, 3]]
# row mins: 2, 1 → α = 2
# col maxs: 2, 3 → β = 2  → α = β = 2! saddle at (1,1)
print("=" * 60)
print("Test 1: 有纯策略鞍点（α = β = 2）")
r1 = launcher.solve({
    "problem_type": "GT",
    "payload": {
        "payoff_matrix": [
            [2, 2],
            [1, 3],
        ]
    }
})
print("Status:", r1["status"])
print("Final:", json.dumps(r1["final_result"], ensure_ascii=False))
print("Steps:", len(r1["iterations"]))

assert r1["status"] == "OPTIMAL", f"Expected OPTIMAL: {r1.get('error_message')}"
fr = r1["final_result"]
assert fr["type"] == "pure_strategy", f"Should be pure_strategy: {fr}"
assert fr["game_value"] == "2", f"Game value should be 2, got {fr['game_value']}"
print(f"  Game value = {fr['game_value']}, saddle = {fr['saddle_points']}")
print("[PASS]\n")


# ── Test 2：无鞍点 3×3，触发混合策略 LP（精确分数验证） ─────────────────────
# 经典石头剪刀布类矩阵（无鞍点，混合策略均匀分布）
# A = [[ 0, -1,  1],
#      [ 1,  0, -1],
#      [-1,  1,  0]]
# 对策值 V = 0，最优策略 p = q = (1/3, 1/3, 1/3)
print("=" * 60)
print("Test 2: 3×3 无鞍点矩阵（石头剪刀布）→ 混合策略 V=0, p=q=(1/3,1/3,1/3)")
r2 = launcher.solve({
    "problem_type": "GT",
    "payload": {
        "payoff_matrix": [
            [ 0, -1,  1],
            [ 1,  0, -1],
            [-1,  1,  0],
        ]
    }
})
print("Status:", r2["status"])
print("Final:", json.dumps(r2["final_result"], ensure_ascii=False))
print("Steps:", len(r2["iterations"]))

assert r2["status"] == "OPTIMAL", f"Expected OPTIMAL: {r2.get('error_message')}"
fr2 = r2["final_result"]
assert fr2["type"] == "mixed_strategy", f"Should be mixed_strategy: {fr2}"

# 验证对策值 V = 0
assert fr2["game_value"] == "0", f"Game value should be 0, got {fr2['game_value']}"

# 验证概率分布精确为 1/3
from fractions import Fraction
one_third = Fraction(1, 3)
for k, v_str in fr2["player1_strategy"].items():
    p = Fraction(v_str)
    assert p == one_third, f"p({k}) should be 1/3, got {v_str}"
for k, v_str in fr2["player2_strategy"].items():
    q = Fraction(v_str)
    assert q == one_third, f"q({k}) should be 1/3, got {v_str}"

print(f"  Game value = {fr2['game_value']}")
print(f"  Player 1: {fr2['player1_strategy']}")
print(f"  Player 2: {fr2['player2_strategy']}")
print("[PASS]\n")


# ── Test 3：另一个经典 2×2 混合策略矩阵 ─────────────────────────────────────
# A = [[3, 1], [0, 2]]
# row mins: 1, 0 → α = 1
# col maxs: 3, 2 → β = 2  → α ≠ β → 混合策略
# 手算: p1*(3-0) = p1*3+p2*0 = p1*3 = p1*1+p2*2 → 3p1=p1+2(1-p1) → 3p1=2-p1 → p1=1/2
# q1*(3-1)=q1*2=(1-q1)*1+(q1)*(0) → wait let me recalculate
# V = (a11*a22-a12*a21)/((a11+a22)-(a12+a21)) = (3*2-1*0)/((3+2)-(1+0)) = 6/4 = 3/2
# p1: p1*(3-0)=V-0 → 3p1=3/2 → wait, standard formula:
# p1 = (a22-a21)/((a11+a22)-(a12+a21)) = (2-0)/(5-1) = 2/4 = 1/2
# p2 = 1 - p1 = 1/2
# q1 = (a22-a12)/(same) = (2-1)/4 = 1/4
# q2 = 3/4
# V = a11*q1 + a12*q2 = 3*1/4 + 1*3/4 = 3/4+3/4 = 6/4 = 3/2
print("=" * 60)
print("Test 3: 2×2 混合策略（V=3/2，精确分数验证）")
r3 = launcher.solve({
    "problem_type": "GT",
    "payload": {
        "payoff_matrix": [
            [3, 1],
            [0, 2],
        ]
    }
})
print("Status:", r3["status"])
print("Final:", json.dumps(r3["final_result"], ensure_ascii=False))

assert r3["status"] == "OPTIMAL"
fr3 = r3["final_result"]
assert fr3["type"] == "mixed_strategy"

# 验证 V = 3/2
assert Fraction(fr3["game_value"]) == Fraction(3, 2), \
    f"Game value should be 3/2, got {fr3['game_value']}"

p1_val = Fraction(fr3["player1_strategy"]["行1"])
p2_val = Fraction(fr3["player1_strategy"]["行2"])
q1_val = Fraction(fr3["player2_strategy"]["列1"])
q2_val = Fraction(fr3["player2_strategy"]["列2"])
assert p1_val == Fraction(1, 2), f"p1 should be 1/2, got {p1_val}"
assert q1_val == Fraction(1, 4), f"q1 should be 1/4, got {q1_val}"
print(f"  V = {fr3['game_value']}, p = ({p1_val}, {p2_val}), q = ({q1_val}, {q2_val})")
print("[PASS]\n")


# ── Test 4：JSON 序列化 ───────────────────────────────────────────────────────
print("=" * 60)
print("Test 4: JSON 序列化验证")
for name, result in [("Saddle", r1), ("RPS_3x3", r2), ("2x2_mix", r3)]:
    try:
        _ = json.dumps(result, ensure_ascii=False)
        print(f"  {name}: JSON OK")
    except TypeError as e:
        raise AssertionError(f"{name} has non-serializable field: {e}")
print("[PASS]\n")

print("=" * 60)
print("ALL 4 GAME THEORY TESTS PASSED!")
