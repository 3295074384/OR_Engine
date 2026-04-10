"""Direct test bypassing Launcher to see real errors"""
import sys, os, traceback
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root)
from modules.cutting_plane import CuttingPlaneModule
from modules.lp_simplex import SimplexModule
from fractions import Fraction
from base_module import fmt, to_fraction
from math import floor

payload = {
    "objective": "max",
    "c": [1, 1],
    "A": [[-1,1],[3,2],[2,3]],
    "b": [1, 12, 12],
    "constraint_types": ["<=","<=","<="],
    "variable_names": ["x1","x2"],
    "integer_vars": [0,1],
}

# Manually simulate what CuttingPlaneModule does
c_orig = [to_fraction(v) for v in payload["c"]]
A_orig = [[to_fraction(v) for v in r] for r in payload["A"]]
b_orig = [to_fraction(v) for v in payload["b"]]
ct_orig = list(payload["constraint_types"])
iv = {0, 1}
vn = ["x1","x2"]
n_orig = 2

# LP 1: solve original
s1 = SimplexModule()
r1 = s1.solve({**payload, **{"A": A_orig, "b": b_orig, "constraint_types": ct_orig}}, {})
print("LP1 status:", r1["status"], "z=", r1["final_result"]["objective_value"])
print("BASIS:", [s1._raw_var_names[c] for c in s1._raw_basis])
print("b_bar:", [str(v) for v in s1._raw_b])

def fp(v):
    return v - Fraction(int(v) if v >= 0 else int(v)-1)

# better frac_part using floor
from math import floor as mfloor
def frac_part(v):
    return v - Fraction(mfloor(v))

# find most fractional
best_idx = max(
    ((idx, col) for idx, col in enumerate(s1._raw_basis) if col < n_orig and col in iv),
    key=lambda x: frac_part(s1._raw_b[x[0]])
)
r_row, r_col = best_idx
print(f"Cut row: {r_row}, var: {s1._raw_var_names[r_col]}, b={s1._raw_b[r_row]}, frac={frac_part(s1._raw_b[r_row])}")

# Generate cut
cut_c = [Fraction(0)] * n_orig
cut_rhs = frac_part(s1._raw_b[r_row])
basic_set = set(s1._raw_basis)
cur_A = A_orig
cur_b = b_orig

for j, vname in enumerate(s1._raw_var_names):
    if j in basic_set: continue
    fcoef = frac_part(s1._raw_A[r_row][j])
    if fcoef == 0: continue
    print(f"  j={j} {vname} abar={s1._raw_A[r_row][j]} frac={fcoef}")
    if j < n_orig:
        cut_c[j] += fcoef
    elif vname.startswith("s") and vname[1:].isdigit():
        k = int(vname[1:])-1
        print(f"    -> slack k={k}, A[k]={[str(v) for v in cur_A[k]]}, b[k]={cur_b[k]}")
        for j2 in range(n_orig):
            cut_c[j2] -= fcoef * Fraction(cur_A[k][j2])
        cut_rhs -= fcoef * Fraction(cur_b[k])
        print(f"    cut_rhs now = {cut_rhs}")

print(f"Cut coeffs: {[str(c) for c in cut_c]}")
print(f"Cut rhs: {cut_rhs}")
print(f"Cut: sum({[str(c) for c in cut_c]} * [x1,x2]) >= {cut_rhs}")

# Test if x1=2,x2=2 satisfies cut
lhs22 = sum(cut_c[j]*2 for j in range(n_orig))
print(f"At x1=2,x2=2: {lhs22} >= {cut_rhs}? {lhs22 >= cut_rhs}")

# Now solve LP2 with this cut
new_A = [list(r) for r in A_orig] + [[cut_c[j] for j in range(n_orig)]]
new_b = list(b_orig) + [cut_rhs]
new_ct = list(ct_orig) + [">="]

print(f"\nLP2 constraints:")
for i, (a, b2, c2) in enumerate(zip(new_A, new_b, new_ct)):
    print(f"  {i}: {[str(v) for v in a]} {c2} {b2}")

s2 = SimplexModule()
try:
    r2 = s2.solve({
        "objective": "max",
        "c": c_orig,
        "A": new_A,
        "b": new_b,
        "constraint_types": new_ct,
        "variable_names": vn,
    }, {})
    print("LP2 status:", r2["status"])
    print("LP2 z:", r2["final_result"].get("objective_value"))
    print("LP2 error:", r2.get("error_message"))
except Exception as e:
    traceback.print_exc()
