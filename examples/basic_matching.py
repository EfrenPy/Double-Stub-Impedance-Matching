"""Basic double-stub impedance matching example."""

from double_stub import DoubleStubMatcher

# Create a matcher with typical parameters
matcher = DoubleStubMatcher(
    distance_to_first_stub=0.07,
    distance_between_stubs=0.375,
    load_impedance=complex(38.9, -26.7),
    line_impedance=50.0,
    stub_impedance=50.0,
    stub_type='short',
    stub_topology='shunt',
)

# Calculate all matching solutions
solutions = matcher.calculate()
print(f"Found {len(solutions)} solution(s)\n")

# Verify and display each solution
for i, (l1, l2) in enumerate(solutions, 1):
    vr = matcher.verify_solution(l1, l2)
    status = "PASS" if vr['valid'] else "FAIL"
    print(f"Solution {i}:")
    print(f"  l1 = {l1:.6f} wavelengths ({l1 * 360:.2f} deg)")
    print(f"  l2 = {l2:.6f} wavelengths ({l2 * 360:.2f} deg)")
    print(f"  Verification: {status}  |Gamma| = {vr['reflection_coefficient']:.2e}")
    print(f"  VSWR = {vr['vswr']:.3f}")
    print()
