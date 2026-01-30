"""Programmatic batch processing over multiple load impedances."""

from double_stub import DoubleStubMatcher

# A list of load impedances to match
loads = [
    complex(38.9, -26.7),
    complex(60, 40),
    complex(100, 50),
    complex(25, -10),
    complex(75, 0),
]

print(f"{'Load':>20s}  {'Solutions':>9s}  {'Best |Gamma|':>12s}")
print("-" * 48)

for z_load in loads:
    matcher = DoubleStubMatcher(
        distance_to_first_stub=0.07,
        distance_between_stubs=0.375,
        load_impedance=z_load,
        line_impedance=50.0,
        stub_impedance=50.0,
        stub_type='short',
    )
    solutions = matcher.calculate()

    if solutions:
        best_gamma = min(
            matcher.verify_solution(l1, l2)['reflection_coefficient']
            for l1, l2 in solutions
        )
        print(f"{str(z_load):>20s}  {len(solutions):9d}  {best_gamma:12.2e}")
    else:
        print(f"{str(z_load):>20s}  {'none':>9s}  {'N/A':>12s}")
