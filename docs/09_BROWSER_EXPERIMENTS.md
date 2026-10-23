# Running an experiment on the research website

The research website offers two distinct operations:

1. **Run a new experiment in the browser.** This calculates fresh chain endpoints and empirical diagnostics using an independent JavaScript implementation of the same five transition rules. It is available to visitors without Python, C++ or Jupyter installed.
2. **Search the published archive.** This retrieves existing, reviewed numerical results, with source labels for Mac measurements and development-environment examples.

These modes must not be conflated. Selecting dimension n=15 in the browser calculator **runs a new local computation**, even if no n=15 row exists in the published archive. Entering n=15 in the saved-results search, on the other hand, cannot invent results; its dropdown lists only recorded dimensions.

## Browser experiment inputs

| Input | Supported values | Default |
| --- | --- | --- |
| Dimension n | Integer 1–30 | 3 |
| Random walk | Any of the five cube walks, or all five | All five |
| Steps per chain | Integer 16–2,048 | 256 |
| Independent chains | Integer 30–1,000 | 200 |
| Seed | Integer 0–4,294,967,295 | 2026 |

The browser enforces a work limit of **8 million approximate coordinate-updates**, calculated as n × steps × chains × number of chosen walks. Visitors may lower any parameter or run one walk at a time. This is a practical browser-safety limit, *not* an algorithmic dimensional limit: the native Python and C++ implementations retain their own broader parameter support.

The online interface includes ready-made configurations at n=2 and n=20, progress messages and a Cancel button. Results include endpoint projections or a 1D histogram, an empirical KS discrepancy curve, second-moment relative error, acceptance frequency and browser elapsed time. The exact total-variation distance for Coordinate Hit-and-Run on the cube, from the origin, is also calculated using the coupon-collector identity. No exact-TV claim is made for the other four walks.

## Mathematics and reproducibility

For each independent chain X₀=0 in K_n=[−1/2,1/2]^n. The proposal radius and acceptance rules in site/sim_worker.js correspond to those in baseline/python/walks.py:

- Ball Walk: uniform Euclidean-ball proposal, radius 0.8/√n, rejecting proposals outside the cube
- Dikin Walk: local diagonal log-barrier Hessian, uniform local ellipsoid proposal, reverse-support check and Metropolis–Hastings correction
- Coordinate Hit-and-Run: uniformly choose one coordinate and resample it from the interval
- Random Hit-and-Run: Gaussian direction and uniform choice on the feasible chord, using unnormalized direction (an invariant rescaling)
- John's Walk: cube-specialized symmetrization ellipsoid, radius 0.8, reverse-support check and Metropolis–Hastings correction

The browser computes the maximum empirical Kolmogorov–Smirnov discrepancy over single-coordinate marginals and selected pairwise coordinate sums, and relative second-moment error. A reported *empirical checkpoint* requires both KS ≤ 0.15 and moment error ≤ 0.25 at two consecutive recorded checkpoints (powers of two, plus the final step count). These are numerical diagnostics, not proof of mixing in total variation.

The browser uses a deterministic **Mulberry32 pseudorandom generator** with **Box–Muller Gaussian draws**, which is not the same random-number generator as Python or C++. The same seed and parameters are repeatable within this browser implementation, but the generated trajectories will not coincide bit-for-bit with the Python/C++ runs.

The browser time is observed JavaScript computation time on the visitor's device, including the diagnostic calculations; it must **not** be compared directly to previously published Python/C++ per-transition timings. A single sampled run also does not establish asymptotic mixing cost or a confidence interval.

## Publication and data provenance

The visitor's computation is performed locally in a dedicated browser worker. It uses no external numerical services and does not submit results, seeds or trajectories to the GitHub repository. The visitor can export a CSV file containing the parameters, diagnostic sequence and run timings. That download is personal to the visitor; it is **not automatically added to the public archive**.

The saved-results archive still comes from the curated source files listed in tools/build_public_index.py, with an explicit distinction between measurements on the author's Mac and development examples. Only a reviewed contribution should be incorporated in the public searchable history. The browser worker and user interface can be checked with:

~~~bash
node --check site/sim_worker.js
node --check site/playground.js
node tests/browser_sim_smoke.cjs
~~~

The mathematical transition rules can be inspected independently in the repository's explicit Python and C++ sources. I regard that independent check as essential before claiming correspondence among languages.
