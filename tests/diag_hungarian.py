import sys, os, json
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root)
from main import Launcher

launcher = Launcher()

results = {}

# Test 1: 4x4 min
r1 = launcher.solve({
    "problem_type": "AP",
    "payload": {
        "objective": "min",
        "cost_matrix": [[9,2,7,8],[6,4,3,7],[5,8,1,8],[7,6,9,4]]
    }
})
results["t1_status"] = r1["status"]
results["t1_z"] = r1["final_result"].get("total_cost")
results["t1_assign"] = r1["final_result"].get("assignment")
results["t1_steps"] = len(r1["iterations"])

# Test 2: 3x4 non-square
r2 = launcher.solve({
    "problem_type": "AP",
    "payload": {
        "objective": "min",
        "cost_matrix": [[10,5,9,7],[3,6,2,8],[7,1,4,10]]
    }
})
results["t2_status"] = r2["status"]
results["t2_z"] = r2["final_result"].get("total_cost")
results["t2_steps"] = len(r2["iterations"])
results["t2_step0"] = r2["iterations"][0]["action"] if r2["iterations"] else ""

# Test 3: 3x3 max
r3 = launcher.solve({
    "problem_type": "AP",
    "payload": {
        "objective": "max",
        "cost_matrix": [[3,5,4],[6,3,2],[4,4,5]]
    }
})
results["t3_status"] = r3["status"]
results["t3_z"] = r3["final_result"].get("total_cost")
results["t3_steps"] = len(r3["iterations"])

# JSON check
for name, r in [("r1",r1),("r2",r2),("r3",r3)]:
    try:
        json.dumps(r, ensure_ascii=False)
        results[name+"_json"] = "OK"
    except Exception as e:
        results[name+"_json"] = str(e)

results["all_pass"] = (
    r1["status"]=="OPTIMAL" and
    r2["status"]=="OPTIMAL" and
    r3["status"]=="OPTIMAL" and
    results["r1_json"]=="OK" and
    results["r2_json"]=="OK" and
    results["r3_json"]=="OK"
)

with open("tests/hungarian_results.json","w",encoding="ascii") as f:
    json.dump(results, f, indent=2, ensure_ascii=True)
print("Written")
