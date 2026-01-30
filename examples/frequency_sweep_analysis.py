"""Frequency sweep analysis with bandwidth and group delay metrics."""

import numpy as np

from double_stub import DoubleStubMatcher, frequency_sweep, rank_solutions

# Set up the matcher
matcher = DoubleStubMatcher(
    distance_to_first_stub=0.07,
    distance_between_stubs=0.375,
    load_impedance=complex(38.9, -26.7),
    line_impedance=50.0,
    stub_impedance=50.0,
    stub_type='short',
)

solutions = matcher.calculate()
print(f"Found {len(solutions)} solution(s)\n")

# Sweep each solution across a 1 GHz band centred at 1 GHz
center_freq = 1e9
freq_start = 0.5e9
freq_stop = 1.5e9

for i, (l1, l2) in enumerate(solutions, 1):
    sr = frequency_sweep(
        matcher, l1, l2,
        center_freq=center_freq,
        freq_start=freq_start,
        freq_stop=freq_stop,
        num_points=201,
    )
    print(f"Solution {i}:")
    print(f"  3 dB Bandwidth:      {sr.bandwidth_3db / 1e6:.2f} MHz")
    print(f"  10 dB RL Bandwidth:  {sr.bandwidth_10db_rl / 1e6:.2f} MHz")
    print(f"  VSWR<2 Bandwidth:    {sr.bandwidth_vswr2 / 1e6:.2f} MHz")
    print(f"  Fractional BW:       {sr.fractional_bandwidth:.1f}%")
    q_str = f"{sr.q_factor:.1f}" if sr.q_factor != float('inf') else "inf"
    print(f"  Loaded Q:            {q_str}")
    print(f"  Phase range:         {sr.phase_deg[0]:.1f} .. {sr.phase_deg[-1]:.1f} deg")
    print(f"  Group delay (center):{sr.group_delay_ns[len(sr.group_delay_ns) // 2]:.3f} ns")
    print()

# Rank solutions by bandwidth
print("Ranking (by 10 dB RL bandwidth):")
rankings = rank_solutions(
    matcher, solutions,
    center_freq=center_freq,
    freq_start=freq_start,
    freq_stop=freq_stop,
)
for rank, r in enumerate(rankings, 1):
    print(f"  #{rank}: Solution {r['solution_index']}  "
          f"BW_10dB = {r['bandwidth_10db_rl'] / 1e6:.2f} MHz")
