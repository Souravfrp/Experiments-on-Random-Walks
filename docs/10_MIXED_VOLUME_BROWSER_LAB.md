# Browser demonstration: volume and mixed-volume components of a rounded cube

I have added a deliberately small numerical companion to my separate [Mixed Volume Approximations research](https://github.com/Souravfrp/estimates-of-mixed-volume-components). The new section on the [interactive research website](https://souravfrp.github.io/Experiments-on-Random-Walks/mixed-volumes.html#mixed-volume-lab) lets a visitor enter a dimension, scaling parameter, target component index, independent sample count and random seed. It calculates approximate body volume and one mixed-volume coefficient, draws component-probability comparisons and makes a downloadable CSV.

## Geometry and exact calculation

**This demonstration uses a different cube from the random-walk study.** Here
$$
P=[-1,1]^n,\quad Q_\lambda=P+\lambda B_2^n,
$$
whereas the Random Walks study uses the side-length-1 cube $[-\tfrac12,\tfrac12]^n$. For this cube and Euclidean ball, the Steiner polynomial is
$$
\operatorname{Vol}(Q_\lambda)=\sum_{j=0}^{n}\binom{n}{j}M_j\lambda^j,\quad
M_j=2^{n-j}\kappa_j,\quad
\kappa_j=\operatorname{Vol}(B_2^j).
$$

To reproduce $\kappa_j$ without dependencies, the code uses $\kappa_0=1$, $\kappa_1=2$, and $\kappa_j=2\pi\,\kappa_{j-2}/j$ for $j\geq2$. These are exact geometric references, not outputs of a simulation.

## What the browser actually estimates

It draws $N$ **independent** points uniformly from the enclosing box
$$
E_\lambda=[-1-\lambda,1+\lambda]^n.
$$
Clipping each coordinate to $[-1,1]$ gives the Euclidean projection $\Pi_P(x)$. I accept a sampled point when
$$
\|x-\Pi_P(x)\|_2\leq\lambda.
$$

For an accepted point the component label $j$ is the number of coordinates with $|x_i|>1$. This partitions $Q_\lambda$ up to measure-zero boundaries. Let $N_{\mathrm{in}}$ count all accepted points and $N_k$ count accepted points assigned to label $k$. The two independent-draw Monte Carlo estimators are
$$
\widehat{\operatorname{Vol}(Q_\lambda)}
=(2+2\lambda)^n\frac{N_{\mathrm{in}}}{N},\qquad
\widehat M_k=\frac{(2+2\lambda)^n(N_k/N)}
  {\binom nk\lambda^k}.
$$
The conditional sampled component probability is $N_k/N_{\mathrm{in}}$ when $N_{\mathrm{in}}>0$, compared against the exact probability $\binom nkM_k\lambda^k/\operatorname{Vol}(Q_\lambda)$.

The interface calculates an approximate **Wilson binomial interval** for the unconditional probabilities $N_{\mathrm{in}}/N$ and $N_k/N$, then rescales the endpoints to body volume and $M_k$. This captures simple independent-sample uncertainty, but it is only an approximate interval and rare target components can yield zero hits even when $M_k>0$. The estimator can become computationally inefficient as dimension or scaling changes. Limits $1\leq n\leq6$, $0.1\leq\lambda\leq2$, and $1000\leq N\leq50000$ constrain browser work; they do not limit the mathematical framework.

## Relationship to the original mixed-volume research

This browser experiment is **not** my theoretical B1/B2/B3 ideal-oracle framework or my numerical Algorithm 1–3 implementation. The original separate repository implements continuing hit-and-run chains, phase-volume ratios, noisy parameter search and mixed-volume recovery. Those estimators have correlated samples and additional assumptions; the browser's bounding-box sampler does not reproduce them.

Instead, this is a checkable educational special case. Visitors can immediately see the relation among exact coefficients, projection-component regions, finite Monte Carlo counts and sampling uncertainty before opening the full Python/C++ notebooks. The reported browser elapsed time is not a benchmark of my native implementations.

All samples and parameters stay on the visitor's machine. Nothing is uploaded to the repository. The JavaScript source is `site/mixed_volume_worker.js` and `site/mixed_volume.js`; its exact-reference and reproducibility checks are in `tests/mixed_volume_browser_smoke.cjs`.
