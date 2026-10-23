"""Five explicit Markov transitions on the centred cube [-1/2,1/2]^n.
Only the Python standard library is used. Each call attempts one transition.
"""
import math
import random

WALKS = ("ball", "dikin", "coordinate_hit_run", "random_hit_run", "john")


def inside_cube(x):
    return all(-0.5 < v < 0.5 for v in x)


def unit_ball(n, rng):
    """Return a point uniformly distributed in the Euclidean unit n-ball."""
    direction = [rng.gauss(0.0, 1.0) for _ in range(n)]
    length = math.sqrt(sum(v*v for v in direction))
    while length == 0.0:
        direction = [rng.gauss(0.0, 1.0) for _ in range(n)]
        length = math.sqrt(sum(v*v for v in direction))
    radius = rng.random() ** (1.0 / n)
    return [radius * v / length for v in direction]


def random_direction(n, rng):
    v = [rng.gauss(0.0, 1.0) for _ in range(n)]
    length = math.sqrt(sum(z*z for z in v))
    while length == 0.0:
        v = [rng.gauss(0.0, 1.0) for _ in range(n)]
        length = math.sqrt(sum(z*z for z in v))
    return [z/length for z in v]


def ball_step(x, rng):
    n = len(x)
    # Use a dimension-dependent step radius, explicitly recorded in the notes.
    delta = 0.8 / math.sqrt(n)
    u = unit_ball(n, rng)
    y = [x[i] + delta*u[i] for i in range(n)]
    if inside_cube(y):
        x[:] = y
        return True
    return False


def dikin_hessian(x):
    # Log barrier F(x)=-sum_i [log(0.5-x_i)+log(0.5+x_i)].
    # Its Hessian is diagonal for a box.
    return [1/(0.5-v)**2 + 1/(0.5+v)**2 for v in x]


def dikin_step(x, rng):
    n = len(x)
    h_x = dikin_hessian(x)
    u = unit_ball(n, rng)
    radius = 1.0
    y = [x[i] + radius*u[i]/math.sqrt(h_x[i]) for i in range(n)]
    if not inside_cube(y):
        return False
    h_y = dikin_hessian(y)
    # Symmetry of support must be tested, since local ellipsoids vary with x.
    reverse_squared = sum(h_y[i]*(y[i]-x[i])**2 for i in range(n))
    if reverse_squared > radius*radius + 1e-11:
        return False
    # q_y(x)/q_x(y) = sqrt(det H_y / det H_x).
    log_ratio = 0.5*sum(math.log(h_y[i]/h_x[i]) for i in range(n))
    if math.log(max(rng.random(), 1e-300)) <= min(0.0, log_ratio):
        x[:] = y
        return True
    return False


def coordinate_hit_run_step(x, rng):
    i = rng.randrange(len(x))
    x[i] = rng.uniform(-0.5, 0.5)
    return True


def random_hit_run_step(x, rng):
    d = random_direction(len(x), rng)
    left, right = -math.inf, math.inf
    for xi, di in zip(x, d):
        if abs(di) < 1e-15:
            continue
        lo = (-0.5-xi)/di
        hi = (0.5-xi)/di
        left = max(left, min(lo, hi))
        right = min(right, max(lo, hi))
    t = rng.uniform(left, right)
    for i in range(len(x)):
        x[i] += t*d[i]
    return True


def john_step(x, rng):
    """Cube-specialized symmetrization John ellipsoid with MH correction.

    At x, (K-x) cap (x-K) = product_i [-d_i,d_i], d_i=.5-|x_i|.
    Its maximum-volume inscribed ellipsoid has semiaxes d_i.
    """
    n = len(x)
    d_x = [0.5-abs(v) for v in x]
    u = unit_ball(n, rng)
    radius = 0.8
    y = [x[i] + radius*d_x[i]*u[i] for i in range(n)]
    if not inside_cube(y):
        return False
    d_y = [0.5-abs(v) for v in y]
    reverse_squared = sum(((y[i]-x[i])/d_y[i])**2 for i in range(n))
    if reverse_squared > radius*radius + 1e-11:
        return False
    # q_x(y) = 1 / (V_n * radius^n * product_i d_x[i]).
    log_ratio = sum(math.log(d_x[i]/d_y[i]) for i in range(n))
    if math.log(max(rng.random(), 1e-300)) <= min(0.0, log_ratio):
        x[:] = y
        return True
    return False

STEPS = {
    "ball": ball_step,
    "dikin": dikin_step,
    "coordinate_hit_run": coordinate_hit_run_step,
    "random_hit_run": random_hit_run_step,
    "john": john_step,
}
