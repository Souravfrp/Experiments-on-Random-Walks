# Mac execution notes — observed before repository creation

The following numbers are transcribed from the Mac Terminal and Jupyter outputs supplied during the experiment. They are observations from two separate sessions, not a controlled statistical speed benchmark. The original Python/C++ programs and the optimized implementation were run with n=20, 2560 steps per chain, 3000 independent chains and seed 2026; C++ optimized used four worker threads. The previous code used an `-O2` compiler setting and optimized code used `-O3`, so optimization attribution requires a controlled comparison.

| Walk | Explicit Python (s) | Optimized Python (s) | Explicit C++ (s) | Optimized C++ (4 threads) (s) |
|:--|--:|--:|--:|--:|
| Ball Walk | 34.4591 | 1.0125 | 1.91061 | 0.384623 |
| Dikin Walk | 76.9352 | 5.2318 | 4.26996 | 0.607405 |
| Coordinate Hit-and-Run | 1.7080 | 0.0687 | 0.125431 | 0.027906 |
| Random Hit-and-Run | 64.1374 | 1.2887 | 1.90624 | 0.399739 |
| John's Walk | 52.7716 | 1.8439 | 2.43946 | 0.524032 |

Under the recorded diagnostic criteria the empirical checkpoints were 128, 1024, 64, 32 and 2048 steps respectively, in both languages. These are **not** certified total-variation mixing times. For Coordinate Hit-and-Run on the centred cube at n=20, starting at zero, exact TV tolerance 0.1 is first achieved at 103 steps; that reference is distinct from its 64-step empirical checkpoint.

I report these historical numbers because they motivated the computational changes. For publication-quality benchmarking, I should repeat runs across independently chosen seeds, multiple timing repetitions, the same compiler flags, and controlled single- versus multithreaded C++ cases.
