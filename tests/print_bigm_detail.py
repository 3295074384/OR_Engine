"""打印大M法（带>=约束，min问题）的完整迭代推演过程"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import Launcher

launcher = Launcher()

result = launcher.solve({
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

print("=" * 60)
print("问题：min Z = 2x1 + 3x2")
print("约束：x1+x2 >= 4,  x1+3x2 >= 6,  x1,x2 >= 0")
print("方法：大 M 法（内部转化为 max 问题）")
print("=" * 60)
print()
print("最终结果:", json.dumps(result["final_result"], ensure_ascii=False))
print()

for it in result["iterations"]:
    step_num = it["step"]
    action   = it["action"]
    sm       = it["state_matrix"]
    calcs    = it["calculation"]

    print(f"【第 {step_num} 步】{action}")
    print()

    # 打印表头
    headers = sm["headers"]
    col_w   = 14
    header_line = "".join(h.center(col_w) for h in headers)
    print("  " + header_line)
    print("  " + "-" * (col_w * len(headers)))

    # 打印约束行
    for row in sm["rows"]:
        bv   = row["basis_var"]
        vals = row["coefficients"]
        line = bv.center(col_w) + "".join(str(v).center(col_w) for v in vals)
        print("  " + line)

    # 打印检验数行
    check = sm["check_row"]
    check_line = "检验数(cj-zj)".center(col_w) + "".join(str(v).center(col_w) for v in check)
    print("  " + "-" * (col_w * len(headers)))
    print("  " + check_line)
    print()

    if calcs:
        print("  初等行变换：")
        for c in calcs:
            print(f"    {c}")
    else:
        print("  （初始状态，无行变换）")

    if it.get("pivot"):
        pv = it["pivot"]
        print(f"  主元信息：进基={pv['entering_var']}，出基={pv['leaving_var']}，"
              f"主元位置={pv['pivot_position']}")
    print()

print("=" * 60)
print("验证结束")
