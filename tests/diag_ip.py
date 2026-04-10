import sys, os, traceback
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root)
from main import Launcher

launcher = Launcher()

PROBLEM = {
    "objective": "max",
    "c": [1, 1],
    "A": [[-1,1],[3,2],[2,3]],
    "b": [1, 12, 12],
    "constraint_types": ["<=","<=","<="],
    "variable_names": ["x1","x2"],
    "integer_vars": [0,1],
}

# Test Branch and Bound
print("--- Branch and Bound ---")
try:
    r = launcher.solve({
        "problem_type": "IP",
        "options": {"integer_method": "branch_bound"},
        "payload": PROBLEM
    })
    print("Status:", r["status"])
    print("Error:", r.get("error_message"))
    print("Final:", r["final_result"])
    print("Steps:", len(r["iterations"]))
    for it in r["iterations"]:
        print(f"  Step {it['step']}: {it['action']}")
except Exception as e:
    traceback.print_exc()

print()
print("--- Cutting Plane ---")
try:
    r2 = launcher.solve({
        "problem_type": "IP",
        "options": {"integer_method": "cutting_plane"},
        "payload": PROBLEM
    })
    print("Status:", r2["status"])
    print("Error:", r2.get("error_message"))
    print("Final:", r2["final_result"])
    print("Steps:", len(r2["iterations"]))
    for it in r2["iterations"]:
        print(f"  Step {it['step']}: {it['action']}")
        for c in it["calculation"]:
            print(f"    {c}")
except Exception as e:
    traceback.print_exc()
