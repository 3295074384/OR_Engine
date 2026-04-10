import sys, os, json
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root)
from main import Launcher
from fractions import Fraction

launcher = Launcher()

results = {}

def run(name, payload):
    r = launcher.solve({"problem_type": "GT", "payload": payload})
    results[name] = {
        "status": r["status"],
        "error":  r.get("error_message", ""),
        "final":  r["final_result"],
        "steps":  len(r["iterations"]),
    }
    try:
        json.dumps(r, ensure_ascii=False)
        results[name]["json"] = "OK"
    except Exception as e:
        results[name]["json"] = str(e)
    return r

# Test 1: pure saddle
run("t1_saddle", {"payoff_matrix": [[2, 2], [1, 3]]})

# Test 2: RPS no saddle
run("t2_rps", {"payoff_matrix": [[0,-1,1],[1,0,-1],[-1,1,0]]})

# Test 3: 2x2 mixed
run("t3_2x2", {"payoff_matrix": [[3,1],[0,2]]})

with open("tests/gt_results.json","w",encoding="ascii") as f:
    json.dump(results, f, indent=2, ensure_ascii=True)
print("Written")
