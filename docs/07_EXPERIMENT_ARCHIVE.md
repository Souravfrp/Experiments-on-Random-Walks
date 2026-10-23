# Reproducible experiment records

I want another researcher to be able to retrieve a previous run from the same dimension, number of steps, chains and seed, then compare the numerical summaries with a new run. I do not need to preserve every trajectory or produce every figure in a public archive.

I keep the full local result in `runs/` or `runs_baseline/`. A run is identified by its UTC timestamp and ID. `parameters.json` records dimension, steps, independent chains, seed, repetitions, code-file hashes, relevant Python/NumPy metadata, compiler command, thread count and the empirical thresholds. Two runs with the same `(n, steps, chains, seed)` are not fully comparable until the code version, walk parameters, thread strategy and numerical criteria have also been checked.

For a published result, I retain a compact summary with one record per dimension and walk, including implementation, empirical convergence checkpoint if observed, final discrepancies, transition runtime, platform and status. I interpret "no checkpoint reached" as censored by the run budget rather than as a missing numerical value or a proof of nonconvergence.

A local Jupyter session cannot silently upload another researcher's data to my GitHub repository. Contributors may run the program locally and propose a reviewed CSV summary in a pull request. I should inspect its parameter metadata before admitting it to the public historical index. A static GitHub Pages view can search already published summary files but cannot directly run unrestricted Python or C++ programs without a separate execution service.

Large raw samples and all generated figures remain outside ordinary Git history. Git LFS, releases, or external storage may be appropriate if a future research question genuinely requires them, but the first repository does not depend on a paid service.

## Fields that matter

- Run ID and UTC creation time
- Walk, language, algorithm version and code hash
- Dimension, step budget, independent chains, repetitions and seed
- Proposal scale, diagnostic definitions and threshold
- Checkpoint and whether it was observed
- Wall microseconds per chain transition, compiler settings and thread count
- Source of the record (`generated locally`, `developer example`, or `transcribed user observation`)

I do not merge example timings from different machines into one benchmark series.
