# How to read the comparison matrices

Every matrix has one row per walk and one column per dimension. These numerical results are **pilot observations**, not proofs.

**Empirical convergence checkpoint:** The later checkpoint in the first pair of consecutive passing measured checkpoints at which (i) the maximum of coordinate and pair-sum Kolmogorov–Smirnov statistics is at most **0.15**, and (ii) the relative error in E[||X||²/n] is at most **0.25**. For a conservative across-repetition summary, the table reports the **latest** passing checkpoint among all repetitions; an entry is given only if *every repetition* passes. Otherwise it says **not reached**. Checkpoints were tested at 1, 2, 4, 8, ... and the final step, not at every integer. The result changes with the choice of thresholds, sample size and randomness. This is an **empirical convergence proxy, not the total-variation mixing time**.

**Exact coordinate mixing:** Only for Coordinate Hit-and-Run, the displayed number is the **exact total-variation mixing time at epsilon=0.1 from the origin** for the explicitly implemented kernel. At time t its TV distance equals the probability that at least one of the n coordinates has not yet been updated, by the coupon collector argument.

**Cost:** microseconds per transition of one chain, averaged over repetitions. Timings exclude diagnostics, plots and CSV writing. This depends on the machine, Python/compiler version and system load; C++ here was compiled with -O2. C++ and Python use distinct random generators, so individual trajectories are not expected to match exactly.

**The reported binned-TV statistic elsewhere is 1D marginal histogram discrepancy, not the full high-dimensional TV distance.** A projection can look uniform even if the joint measure has not mixed.
