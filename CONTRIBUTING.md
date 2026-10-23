# Contributing experiments

I welcome corrections to the mathematics, implementation, and statistical interpretation. A contribution should identify which transition rule changed, explain why the invariant uniform law remains valid, and provide a test rather than only a new plot.

To contribute a measurement, include the dimension, step budget, independent chains, seed, code revision, random-walk parameters, hardware/compiler, threads, convergence diagnostic and whether its threshold was reached. Do not submit enormous trajectory dumps in ordinary Git commits. Keep privately identifying machine details out of public metadata where they are not necessary.

I review contributed results before including them in the public summary history. This policy is about reproducibility, not about automatically collecting run data.


## Contributing to the searchable public archive

I publish only compact, reviewed summaries. To propose a new experiment, open a pull request with the numerical CSV, complete run parameters and code revision. Please indicate whether the measurement came from the repository's explicit or optimized implementation, the exact platform and compiler settings, and whether it is a local measurement or an illustrative example. The data source and its provenance must be preserved.

The public index is derived from selected source CSVs by `tools/build_public_index.py`; it is not a collection endpoint and it does not ingest arbitrary uploaded files. I will review new observations and extend that builder to include an additional supported source. Full trajectories, private machine information and raw multi-gigabyte files should not be submitted.
