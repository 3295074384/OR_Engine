import sys, os, json
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

results = {}

r_bb = launcher.solve({"problem_type":"IP","options":{"integer_method":"branch_bound"},"payload":PROBLEM})
results["bb_status"] = r_bb["status"]
results["bb_z"] = r_bb["final_result"].get("objective_value")
results["bb_steps"] = len(r_bb["iterations"])

r_cp = launcher.solve({"problem_type":"IP","options":{"integer_method":"cutting_plane"},"payload":PROBLEM})
results["cp_status"] = r_cp["status"]
results["cp_z"] = r_cp["final_result"].get("objective_value")
results["cp_steps"] = len(r_cp["iterations"])

try:
    json.dumps(r_bb, ensure_ascii=False)
    results["bb_json"] = "OK"
except Exception as e:
    results["bb_json"] = str(e)

try:
    json.dumps(r_cp, ensure_ascii=False)
    results["cp_json"] = "OK"
except Exception as e:
    results["cp_json"] = str(e)

# Infeasible test
r_inf = launcher.solve({
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
results["inf_status"] = r_inf["status"]
results["inf_error"] = r_inf.get("error_message", "")

results["t1_pass"] = (r_bb["status"] == "OPTIMAL" and r_bb["final_result"].get("objective_value") == "4")
results["t2_pass"] = (r_cp["status"] == "OPTIMAL" and r_cp["final_result"].get("objective_value") == "4")
results["t3_pass"] = (results["bb_json"] == "OK" and results["cp_json"] == "OK")
results["t4_pass"] = (r_inf["status"] in ("INFEASIBLE","OPTIMAL"))

with open("tests/ip_results.json", "w", encoding="ascii") as f:
    json.dump(results, f, indent=2)
print("Results written to tests/ip_results.json")
