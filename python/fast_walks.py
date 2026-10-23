"""Vectorized implementations of exactly the five cube transition kernels.

State X has shape (number_of_independent_chains, dimension).
All transition mathematics remains explicit; NumPy handles arithmetic over chains.
Different RNG streams mean paths need not match the baseline bit for bit.
"""
import numpy as np

WALKS = ('ball', 'dikin', 'coordinate_hit_run', 'random_hit_run', 'john')


def unit_ball(m, n, rng):
    """Gaussian direction times U^(1/n), uniform in the unit Euclidean ball."""
    z = rng.standard_normal((m, n))
    norms = np.sqrt(np.sum(z*z, axis=1))
    while np.any(norms == 0):
        bad = (norms == 0)
        z[bad] = rng.standard_normal((bad.sum(), n))
        norms = np.sqrt(np.sum(z*z, axis=1))
    radii = rng.random(m) ** (1.0 / n)
    return z * (radii / norms)[:, None]


def hessian(x):
    """Diagonal entries of the log-barrier Hessian on the centred cube."""
    return (0.5-x)**(-2) + (0.5+x)**(-2)


def step(x, walk, rng):
    """In-place update of all independent chains; return acceptance count."""
    m, n = x.shape
    if walk == 'coordinate_hit_run':
        indices = rng.integers(0, n, size=m)
        x[np.arange(m), indices] = rng.random(m)-0.5
        return m

    if walk == 'random_hit_run':
        # The Gaussian direction can remain UNNORMALIZED: replacing d by c*d
        # rescales the chord coordinate by 1/c, leaving the chosen endpoint identical.
        d = rng.standard_normal((m,n))
        bad = np.all(d == 0.0, axis=1)
        while np.any(bad):
            d[bad] = rng.standard_normal((bad.sum(),n))
            bad = np.all(d == 0.0, axis=1)
        safe = np.where(d == 0.0, 1.0, d)
        a = (-0.5-x)/safe
        b = (0.5-x)/safe
        lo = np.where(d == 0.0, -np.inf, np.minimum(a,b)).max(axis=1)
        hi = np.where(d == 0.0, np.inf, np.maximum(a,b)).min(axis=1)
        t = lo+(hi-lo)*rng.random(m)
        x[:] = x + t[:,None]*d
        return m

    u = unit_ball(m, n, rng)
    if walk == 'ball':
        y = x+(0.8/np.sqrt(n))*u
        accepted = np.all((y>-0.5)&(y<0.5),axis=1)
    elif walk == 'dikin':
        hx = hessian(x)
        y = x + u/np.sqrt(hx)
        feasible = np.all((y>-0.5)&(y<0.5),axis=1)
        # Invalid proposals are replaced only for safe floating-point evaluation.
        safe_y = np.where(feasible[:,None], y, x)
        hy = hessian(safe_y)
        reverse = np.sum(hy*(safe_y-x)**2,axis=1)
        log_ratio = 0.5*np.log(hy/hx).sum(axis=1)
        accepted = feasible & (reverse <= 1+1e-11) & (np.log(np.maximum(rng.random(m),1e-300)) <= np.minimum(0,log_ratio))
    elif walk == 'john':
        dx = 0.5 - np.abs(x)
        y = x + 0.8*dx*u
        feasible = np.all((y>-0.5)&(y<0.5),axis=1)
        safe_y = np.where(feasible[:,None],y,x)
        dy = 0.5-np.abs(safe_y)
        reverse = np.sum(((safe_y-x)/dy)**2,axis=1)
        log_ratio = np.log(dx/dy).sum(axis=1)
        accepted = feasible & (reverse <= 0.8**2+1e-11) & (np.log(np.maximum(rng.random(m),1e-300)) <= np.minimum(0,log_ratio))
    else:
        raise ValueError('Unknown walk: '+walk)
    x[accepted] = y[accepted]
    return int(accepted.sum())
