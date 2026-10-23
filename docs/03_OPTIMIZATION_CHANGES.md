# Optimization change log and measured baseline comparison

The implementation-level adjustments are recorded at the **end of README.md** in an appendix. This file provides the corresponding numerical benchmark and cautions.

## Measured smoke benchmark (development runtime, not the user's Mac)

Setup: centred n=20 cube, 128 transitions per chain, 600 chains, one repetition, seed=2026. C++ original compiled with `-O2`; the new C++ binary uses `-O3` and **one thread** here for comparison. Values are observed wall microseconds per chain transition, excluding diagnostics and output.

| Walk | Baseline Python µs | Optimized Python µs | Speed factor | Baseline C++ µs | Optimized C++ µs | Speed factor |
|:--|--:|--:|--:|--:|--:|--:|
| Ball Walk | 8.543 | 0.443 | 19.28× | 0.568 | 0.596 | 0.95× |
| Dikin Walk | 20.934 | 0.937 | 22.34× | 1.127 | 0.994 | 1.13× |
| Coordinate Hit-and-Run | 0.460 | 0.036 | 12.72× | 0.024 | 0.015 | 1.64× |
| Random Hit-and-Run | 12.950 | 0.562 | 23.06× | 0.639 | 0.504 | 1.27× |
| John's Walk | 13.850 | 0.604 | 22.93× | 0.787 | 0.731 | 1.08× |

**Interpretation:** NumPy batching produced a large improvement here, especially at moderate/high numbers of independent chains. Single-thread C++ showed modest gains or a small loss; `Ball Walk` was *slightly slower* in this particular run, and the one-repetition experiment is noisy. Large multithreaded workloads can benefit from parallel independent chains but this must be tested on the user's machine before reporting a speedup. These results cannot be presented as a universal statement that one language or algorithm is better.

See `benchmarks/reference/` and `benchmarks/optimized/` for the actual measurement CSVs; no rows were inserted by hand into those data files. The historical Version 1 n=20 measurements supplied by the user belong to a **different execution environment** and should be retained as a separate series rather than merged into this benchmark.

## Functional changes

- Python: NumPy arrays allow transition updates across many chains at once; all acceptance formulas and chord computations remain explicit.
- C++: preallocated scratch vectors and independent-chain threading, with thread count selectable.
- Output: short coordinate snapshots at checkpoints and a timestamped archive avoid huge files and accidental overwrites.
- Tool use: NumPy for numerical throughput, Matplotlib only for graphics, C++17 standard library only.
- Compiler: `-O3` instead of baseline `-O2`; this is part of the measured optimization and a possible confounder when attributing gains.
- All Python and C++ algorithms continue to target the same uniform cube law.
