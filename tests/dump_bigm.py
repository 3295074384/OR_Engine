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

out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bigm_result.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print(f"Written to {out_path}")
print("final_result:", result["final_result"])
print("total iterations:", len(result["iterations"]))
