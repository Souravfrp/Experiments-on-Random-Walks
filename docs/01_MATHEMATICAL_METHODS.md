# Mathematical setup and transition rules

These are first-person research-note drafts to review before publication; results are separated from theory.

## The body and the target

I study the centred cube \(K_n=[-1/2,1/2]^n\) for arbitrary positive integer dimension \(n\). All chains start at the origin; the target measure \(\pi\) is uniform on the cube. In particular, under \(\pi\) every coordinate is independently uniform on \([-1/2,1/2]\), and

\[\mathbb{E}_{\pi}\left[\|X\|_2^2/n\right]=1/12.\]

I compare five transition rules under the same target and initial point. The CPU time per transition and the number of transitions needed for a numerical discrepancy criterion are **different quantities**.

## 1. Ball Walk

For a point \(x\in K_n\), sample a vector \(U\) uniformly from the Euclidean unit ball, set \(y=x+(0.8/\sqrt n)U\), and accept \(y\) if \(y\in K_n\). Otherwise stay at \(x\). A translation-invariant ball proposal is symmetric, so the ordinary accept/reject-at-boundary mechanism preserves uniform measure. The radius 0.8/sqrt(n) is an experiment parameter and **not a universally optimal radius**.

## 2. Dikin Walk

Use the logarithmic barrier

\[\Phi(x)=-\sum_{i=1}^n\big(\log(1/2-x_i)+\log(1/2+x_i)\big).\]

On this cube the Hessian is diagonal:

\[H_{ii}(x)=\frac1{(1/2-x_i)^2}+\frac1{(1/2+x_i)^2}.\]

Given a unit-ball draw \(U\), propose \(y=x+H(x)^{-1/2}U\). This depends on the local barrier geometry, and so the reverse proposal need not have the same density as the forward proposal. Reject infeasible points and those failing the reverse ellipsoid support condition \(\sum_i H_{ii}(y)(x_i-y_i)^2\leq1\). Otherwise accept with probability

\[\min\big(1,\sqrt{\det H(y)/\det H(x)}\big).\]

This is the unit-ball proposal specialized to a diagonal Hessian; it is *not* a ready-made optimizer or an external Dikin sampler. Its local scale differs from other Dikin variants in the literature.

## 3. Coordinate Hit-and-Run

Choose \(i\) uniformly from \(1,\ldots,n\) and replace \(x_i\) with an independent \(U[-1/2,1/2]\) draw. All remaining coordinates are unchanged. This is exactly the cube chord in the selected coordinate direction. From the origin, the total-variation distance after \(t\) steps equals the probability that at least one coordinate has never been selected. The exact baseline is calculated via the coupon-collector recursion in both implementations.

## 4. Random Hit-and-Run

Draw a random Gaussian direction \(d\in\mathbb{R}^n\), which has uniform direction once normalized. Find the chord parameter interval

\[I(x,d)=\{\lambda:x+\lambda d\in K_n\}.\]

Draw \(\lambda\) uniformly from this interval and set \(y=x+\lambda d\). There is no need to normalize \(d\) explicitly: replacing \(d\) with a positive multiple only rescales \(\lambda\), leaving \(y\) invariant. The exact full-chord sample is uniform conditional on the chosen direction.

## 5. John's Walk on the cube

I use the **symmetrized-body** John's Walk of Gustafson and Narayanan, not the weighted John-metric Dikin variant. At \(x\), symmetrize about the current point:

\[ (K_n-x)\cap(x-K_n)=\prod_i[-d_i,d_i],\qquad d_i=1/2-|x_i|.\]

The John ellipsoid of this box is the axis-aligned ellipsoid with semiaxes \(d_i\). Draw \(U\) uniformly in the Euclidean unit ball and propose \(y=x+0.8\operatorname{diag}(d_i)U\). Because the local proposal ellipsoid changes with \(x\), accept only if the reverse proposal is supported and apply the determinant/Jacobian ratio

\[\min\left(1,\prod_i\frac{d_i(x)}{d_i(y)}\right).\]

No general ellipsoid solver is needed for this specific cube, since the ellipsoid has an exact closed form. The scale 0.8 is an empirical choice. This specialization should not be confused with a generic implementation for arbitrary convex bodies.

## What's genuinely being measured?

The empirical tables compare a pair of diagnostics (coordinate/pair-sum KS and second-moment error) checked at powers of two plus the final step. They do not prove total-variation mixing times for Ball, Dikin, Random Hit-and-Run or John's Walk, nor do they identify universally optimal proposal parameters.

See `docs/04_SOURCES.md` for the named references and `docs/02_MEASUREMENT_AND_LIMITATIONS.md` for details of the threshold.
