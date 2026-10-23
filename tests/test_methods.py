"""Mathematical and numerical consistency checks; standard unittest only."""
import unittest
import sys
from pathlib import Path

import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))
from fast_walks import step, hessian, unit_ball, WALKS
from diagnostics import coordinate_exact_tv


class TransitionTests(unittest.TestCase):
    def test_hessian_at_origin(self):
        self.assertTrue(np.allclose(hessian(np.zeros((4, 3))), 8.0))

    def test_all_walking_states_in_cube(self):
        for walk in WALKS:
            with self.subTest(walk=walk):
                rng = np.random.default_rng(2026)
                X = np.zeros((250, 6))
                for _ in range(80):
                    count = step(X, walk, rng)
                    self.assertTrue(0 <= count <= 250)
                    self.assertTrue(np.all(np.isfinite(X)))
                    self.assertTrue(np.all(X >= -0.5))
                    self.assertTrue(np.all(X <= 0.5))

    def test_seed_reproducibility(self):
        for walk in WALKS:
            with self.subTest(walk=walk):
                x = np.zeros((20, 4))
                y = np.zeros((20, 4))
                r1 = np.random.default_rng(2126)
                r2 = np.random.default_rng(2126)
                for _ in range(10):
                    step(x,walk,r1)
                    step(y,walk,r2)
                np.testing.assert_array_equal(x,y)

    def test_unit_ball(self):
        z=unit_ball(10000, 8, np.random.default_rng(2026))
        self.assertTrue(np.all(np.linalg.norm(z,axis=1) <= 1.0+1e-12))

    def test_coordinate_coupon_collector(self):
        self.assertAlmostEqual(coordinate_exact_tv(1,0), 1)
        self.assertAlmostEqual(coordinate_exact_tv(1,1), 0)
        self.assertAlmostEqual(coordinate_exact_tv(2,2), .5)
        self.assertGreater(coordinate_exact_tv(20,64), .5)
        self.assertLess(coordinate_exact_tv(20,128), .05)

    def test_uniform_endpoints_for_coordinate_walk(self):
        # With all coordinates refreshed many times the marginal moments should
        # be close to E U = 0 and E U² = 1/12.
        x=np.zeros((1000,3))
        rng=np.random.default_rng(2026)
        for _ in range(70):step(x,'coordinate_hit_run',rng)
        self.assertLess(abs(float(x.mean())),.02)
        self.assertLess(abs(float((x*x).mean())-1/12),.008)

if __name__ == '__main__':unittest.main()
