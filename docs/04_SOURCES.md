# Sources and mathematical context

These references motivate the geometric constructions and the distinction between experimental diagnostics and mixing-time theorems. The code formulas are written explicitly for the centred cube. They are **not** claims that this package implements every general-body or metric variant described in the cited work.

1. Adam Gustafson and Hariharan Narayanan, **John's Walk** (arXiv:1803.02032; *Advances in Applied Probability*, published 2022). The symmetrized-body John-ellipsoid construction. https://arxiv.org/abs/1803.02032 ; https://doi.org/10.1017/apr.2022.34
2. László Lovász and Santosh Vempala, **Hit-and-Run from a Corner**, *SIAM Journal on Computing* 35(4), 985–1005 (2006). Hit-and-Run and its rapid-mixing analysis. https://doi.org/10.1137/S009753970544727X
3. László Lovász, **Hit-and-Run Mixes Fast**, *Mathematical Programming* 86, 443–461 (1999). https://doi.org/10.1007/s101070050099
4. Hariharan Narayanan, **Randomized interior point methods for sampling and optimization**, Dikin-walk/barrier geometry. https://www.mit.edu/~har/Dikin2.pdf
5. NumPy documentation for array arithmetic and random generation: https://numpy.org/doc/stable/ ; Matplotlib for scientific figures: https://matplotlib.org/stable/

## Scope note

My diagonal Dikin-Hessian and local John-ellipsoid formulas are specializations to the cube, and the local proposal radii are explicit experimental parameters. The stated mixing bounds in the literature apply under their own assumptions and must not be attached to our particular empirical checkpoints as if proven here.
