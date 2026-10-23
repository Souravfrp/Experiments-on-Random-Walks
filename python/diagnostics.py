"""Distribution diagnostics derived explicitly, without statistical packages."""
import math


def uniform_cdf(x):
    return max(0., min(1., x+0.5))


def triangle_cdf(z):
    """CDF of (U+V), for independent U,V uniform on [-1/2,1/2]."""
    if z <= -1: return 0.
    if z >= 1: return 1.
    if z < 0: return 0.5*(z+1)**2
    return 1-0.5*(1-z)**2


def ks_distance(values, cdf):
    arr = sorted(values)
    m = len(arr)
    if m == 0: return float('nan')
    discrepancy = 0.
    for j, x in enumerate(arr):
        fx = cdf(x)
        discrepancy = max(discrepancy, abs(fx-j/m), abs((j+1)/m-fx))
    return discrepancy


def binned_tv_1d(values, bins=12):
    """Binned variation discrepancy for a 1D marginal, not full nD TV."""
    counts = [0]*bins
    for x in values:
        j = max(0, min(bins-1, int((x+0.5)*bins)))
        counts[j] += 1
    total = len(values)
    return 0.5*sum(abs(c/total-1/bins) for c in counts)


def measure(points):
    """Independent chain endpoints at fixed t; target is uniform on cube."""
    n = len(points[0])
    max_ks = max(ks_distance([x[i] for x in points], uniform_cdf) for i in range(n))
    # Under uniform cube each pairwise sum is triangular; check 3 planes.
    # Unlike marginal KS, this notices some dependence between coordinates.
    pair_ks = 0.
    if n > 1:
        pairs = [(0, 1)] if n == 2 else [(0, 1), (1, 2), (2, 0)]
        for i, j in pairs:
            pair_ks = max(pair_ks, ks_distance([x[i]+x[j] for x in points], triangle_cdf))
    max_ks = max(max_ks, pair_ks)
    avg_square = sum(sum(v*v for v in x)/n for x in points)/len(points)
    moment_relative_error = abs(avg_square-(1/12))/(1/12)
    # Average across marginal distributions; this isn't total variation of chain.
    btv = sum(binned_tv_1d([x[i] for x in points]) for i in range(n))/n
    return max_ks, moment_relative_error, btv, pair_ks


def coordinate_exact_tv(n, steps):
    """Exact TV distance from point mass at zero for coordinate hit-and-run.

    It equals the coupon-collector probability of not updating all n coordinates.
    """
    p = [0.]*(n+1)
    p[0] = 1.
    for _ in range(steps):
        q = [0.]*(n+1)
        for k in range(n+1):
            q[k] += p[k]*k/n
            if k < n:
                q[k+1] += p[k]*(n-k)/n
        p = q
    return max(0., 1. - p[n])


def coordinate_exact_mixing(n, epsilon=0.1):
    p = [0.]*(n+1)
    p[0] = 1.
    # We compute the coupon distribution incrementally, rather than repeating it.
    for t in range(1, max(10000, 100*n*n)):
        q = [0.]*(n+1)
        for k in range(n+1):
            q[k] += p[k]*k/n
            if k < n: q[k+1] += p[k]*(n-k)/n
        p=q
        if 1-p[n] <= epsilon:
            return t
    return None
