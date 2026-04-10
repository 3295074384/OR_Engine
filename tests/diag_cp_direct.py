import sys, os, json, traceback
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root)
from modules.cutting_plane import CuttingPlaneModule

cp = CuttingPlaneModule()
payload = {
    "objective": "max",
    "c": [1, 1],
    "A": [[-1,1],[3,2],[2,3]],
    "b": [1, 12, 12],
    "constraint_types": ["<=","<=","<="],
    "variable_names": ["x1","x2"],
    "integer_vars": [0,1],
}

try:
    result = cp.solve(payload, {})
    print("STATUS:", result["status"])
    print("ERROR:", result.get("error_message"))
    print("FINAL:", result["final_result"])
    print("STEPS:", len(result["iterations"]))
    # Try JSON serialization
    try:
        s = json.dumps(result, ensure_ascii=False)
        print("JSON: OK")
    except TypeError as e:
        print("JSON FAIL:", e)
        # Find which field fails
        for k, v in result.items():
            try:
                json.dumps({k: v})
            except TypeError as e2:
                print(f"  FIELD {k!r} fails: {e2}")
                if k == "iterations":
                    for i, it in enumerate(v):
                        try:
                            json.dumps(it)
                        except TypeError as e3:
                            print(f"    iter {i} fails")
                            for k2, v2 in it.items():
                                try:
                                    json.dumps({k2: v2})
                                except TypeError as e4:
                                    print(f"      field {k2!r}: {type(v2).__name__} - {repr(v2)[:60]}")
except Exception as e:
    traceback.print_exc()
