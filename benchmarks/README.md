# Small development benchmark

I keep the original and optimized measurement CSVs from the development-machine smoke test here. This was a 128-step, 600-chain experiment at n=20, not the later Mac execution. A one-thread C++ comparison was made, but the original was compiled at `-O2` and the optimized source at `-O3`; I should not attribute the difference to buffer reuse alone. See `docs/03_OPTIMIZATION_CHANGES.md`.
