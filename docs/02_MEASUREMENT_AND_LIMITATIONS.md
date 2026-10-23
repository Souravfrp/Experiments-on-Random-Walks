# Measurement protocol, reproducibility, and limitations

## What I mean by the convergence checkpoint

At each saved checkpoint t, I use many **independent chains** started at zero. I compare their endpoints against the cube's uniform target. The main empirical checks are (i) the maximum coordinate-wise KS discrepancy, enlarged with KS for three pairwise sums when n>=3, and (ii) the relative error in \(E[\|X\|^2/n]=1/12\). I require KS<=0.15 and moment relative error<=0.25 at **two consecutive positive checkpoints**. The reported number is the second checkpoint and is not an estimate at every intermediate integer time. When there are multiple repetitions, every repetition must meet the criterion and the reported checkpoint is the largest such value.

This threshold is descriptive, user configurable (`--ks-limit`, `--moment-limit`), and **not a certified total-variation error of 0.15**. Marginal measures can be close while the full law is still singular or strongly dependent. The exact Coordinate Hit-and-Run coupon-collector recursion in `diagnostics.py` is a countercheck of this limitation.

## Fair comparison

Python and C++ have the same target, initial state, cube, proposal geometry, checkpoint schedule and statistic definitions. They do **not** share an identical pseudorandom generator or generate the same sample path for a common seed. In C++, `--threads` changes the measured wall-time but not the theoretical Markov transition. A timing comparison against the original C++ code is best begun with `--threads 1`; only then consider `--threads 4` for throughput.

A single seed and single experiment do not supply statistical confidence intervals. For a polished research conclusion, use several independent seeds and repeated wall timings under comparable system load. Check dimensions beyond the first ten, compare with exact coordinate coupon-collector TV, and analyze the effect of tuning the local proposal radii.

The reported `us_per_step` is **wall microseconds divided by (steps × chains)**, excluding computation of diagnostics, plots and CSV writing. This is amortized wall time per chain transition, not CPU cycles or the work complexity of an individual instruction. `cost_to_threshold_s = proxy_steps × chains × us_per_step / 10^6` is estimated transition-only wall cost to satisfy the empirical criterion, not the wall time of an adaptive stopping implementation and not a proof of mixing complexity.

For this cube, the current per-transition arithmetic cost is O(1) for Coordinate Hit-and-Run and O(n) for the other four walks (with diagonal Hessian/John ellipsoid formulas), ignoring RNG and Python vectorization overhead. The empirical number of transitions to a threshold has a separate dependence on n and on the chosen proposal parameters. We cannot derive an asymptotic mixing-time exponent from ten or eleven measurements.

## Storage and public GitHub

Each run creates a new folder with `parameters.json`, result CSVs and plots. `--snapshot-chains 300` stores only a chosen subset at checkpoints, not every state at every Markov transition. This prevents large files when n=20, chains=3000, steps=2560. A contributor running the scripts on their own computer will not automatically upload data to your GitHub. Publishing reviewed numerical summaries can happen separately.

## Test and publication checklist

- Validate cube containment for all proposals and all five walks.
- Check full-chord and coordinate procedures against known uniform marginal laws.
- Compare finite-sample diagnostics over multiple independent seeds.
- Record the CPU, compiler, Python, NumPy and thread count.
- Keep the full `parameters.json` and raw numerical CSV before drawing conclusions.
- State which numerical results are observations and which conclusions are mathematical proofs.
