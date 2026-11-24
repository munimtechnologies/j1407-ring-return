# Copyright 2026 Munim, Inc.
# SPDX-License-Identifier: Apache-2.0
"""Stdlib tests for the J1407 ring-return test (hand-traced values)."""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import j1407 as J  # noqa: E402

T_IN = 2458210.5     # inside the central window of eclipse n = 1 for P = 4000 d
B = 2459000.0


def _rows(times, r=1.0, s=0.02, src="asassn"):
    return [(t, r, s, src) for t in times]


class TestConstants(unittest.TestCase):
    def test_windows(self):
        self.assertEqual(J.WINDOWS[0], (2454194.5, 2454198.5))
        self.assertEqual(J.WINDOWS[1], (2454204.5, 2454234.5))
        self.assertEqual(J.WINDOWS[2], (2454242.5, 2454246.5))
        self.assertEqual(J.CENTRE, 2454219.5)
        self.assertAlmostEqual(J.DEEP_RATIO, 0.630957, places=6)
        self.assertAlmostEqual(J.NORMAL_RATIO, 0.794328, places=6)

    def test_dates(self):
        self.assertEqual(J.jd_to_date(2454220.5), "2007-04-30")
        self.assertEqual(J.jd_to_date(2451544.5), "2000-01-01")

    def test_robust_scatter(self):
        self.assertAlmostEqual(J.robust_scatter([1.0, 2.0, 3.0, 4.0, 5.0]), 1.4826, places=6)


class TestVeto(unittest.TestCase):
    def test_veto_capable(self):
        self.assertTrue(J.veto_capable(0.95, 0.03, "asassn"))
        self.assertFalse(J.veto_capable(0.80, 0.05, "asassn"))   # 0.169 < 4 x 0.05
        self.assertFalse(J.veto_capable(0.70, 0.01, "asassn"))   # dimmer than 0.25 mag
        self.assertTrue(J.veto_capable(0.93, 0.5, "tess"))
        self.assertFalse(J.veto_capable(0.91, 0.0, "tess"))

    def test_count_nights(self):
        self.assertEqual(J.count_nights([0.0, 0.1, 0.2, 1.0, 1.05, 3.0]), 3)
        self.assertEqual(J.count_nights([]), 0)

    def test_eclipse_numbers(self):
        self.assertEqual(J.eclipse_numbers(4000.0, T_IN - 100, T_IN + 100), [1])

    def test_trial(self):
        pts = J.Points(_rows([T_IN, T_IN + 1.0], r=0.98))
        lo, hi = T_IN - 100, T_IN + 100
        ex, info = J.trial(4000.0, pts, lo, hi)
        self.assertTrue(ex)
        self.assertEqual(info["n"], 1)
        self.assertEqual(info["nights"], 2)
        self.assertEqual(info["by"], ["asassn"])
        self.assertTrue(J.trial(3990.0, pts, lo, hi)[0])
        self.assertFalse(J.trial(4010.0, pts, lo, hi)[0])
        self.assertFalse(J.trial(4000.0, pts, lo, hi, min_nights=3)[0])
        one = J.Points(_rows([T_IN], r=0.98))
        self.assertFalse(J.trial(4000.0, one, lo, hi)[0])
        self.assertTrue(J.trial(4000.0, one, lo, hi, min_nights=1)[0])
        # dimmed points cannot veto
        dim = J.Points(_rows([T_IN, T_IN + 1.0], r=0.5))
        self.assertFalse(J.trial(4000.0, dim, lo, hi, min_nights=1)[0])

    def test_scan_and_fractions(self):
        pts = J.Points(_rows([T_IN, T_IN + 1.0], r=0.98))
        grid = [3990.0, 4000.0, 4010.0]
        flags = J.scan(pts, grid, T_IN - 100, T_IN + 100)
        self.assertEqual(list(flags), [1, 1, 0])
        self.assertEqual(J.allowed_runs(grid, flags), [[4010.0, 4010.0, 1]])
        self.assertEqual(J.band_fraction(grid, flags, 3995.0 / J.YEAR, 4020.0 / J.YEAR), (2, 1, 0.5))
        b = J.binned(grid, flags, [3985.0 / J.YEAR, 4005.0 / J.YEAR, 4015.0 / J.YEAR])
        self.assertEqual(b[0][2:4], (2, 2))
        self.assertEqual(b[1][2:4], (1, 0))

    def test_period_grid(self):
        g = J.period_grid(1.0, 1.01, 0.25)
        self.assertEqual(len(g), 15)
        self.assertEqual(g[0], 365.25)
        self.assertEqual(g[-1], 368.75)

    def test_verdict(self):
        self.assertEqual(J.band_verdict(0.995), "CLOSED")
        self.assertEqual(J.band_verdict(0.95), "MOSTLY_CLOSED")
        self.assertEqual(J.band_verdict(0.6), "PARTLY_CLOSED")
        self.assertEqual(J.band_verdict(0.2), "OPEN")


class TestDips(unittest.TestCase):
    def test_dip_points(self):
        pts = J.Points([(B + 1.0, 0.30, 0.02, "asassn"), (B + 2.0, 0.62, 0.1, "asassn"),
                        (B + 3.0, 0.5, 0.02, "tess"), (B + 4.0, 0.7, 0.01, "asassn")])
        self.assertEqual([d[0] for d in J.dip_points(pts)], [B + 1.0])

    def test_group_events(self):
        dips = [(B, 0.3, 0.02, "asassn"), (B + 1.0, 0.3, 0.02, "asassn"),
                (B + 40.0, 0.3, 0.02, "asassn"), (B + 200.0, 0.3, 0.02, "asassn")]
        ev = J.group_events(dips)
        self.assertEqual(len(ev), 2)
        self.assertEqual(ev[0]["n"], 3)
        self.assertEqual(ev[0]["nights"], 3)
        self.assertTrue(ev[0]["strong"])
        self.assertAlmostEqual(ev[0]["depth_mag_max"], -2.5 * math.log10(0.3))
        self.assertAlmostEqual(ev[0]["t_mid"], B + 41.0 / 3.0)
        self.assertFalse(ev[1]["strong"])

    def test_implied_periods(self):
        ps = J.implied_periods(J.CENTRE + 5000.0)
        self.assertEqual(len(ps), 13)
        self.assertEqual(ps[0], (1, 5000.0))
        self.assertEqual(ps[1], (2, 2500.0))
        neg = J.implied_periods(J.CENTRE - 1000.0)
        self.assertEqual(neg, [(-1, 1000.0), (-2, 500.0)])


class TestInjection(unittest.TestCase):
    def test_window_number(self):
        self.assertEqual(J.window_number(T_IN, 4000.0), 1)
        self.assertIsNone(J.window_number(2458300.5, 4000.0))
        self.assertEqual(J.window_number(2454210.5, 4000.0), 0)

    def test_inject(self):
        rows = _rows([T_IN, 2458300.5, 2454210.5])
        out = J.inject(rows, 4000.0)
        self.assertAlmostEqual(out[0][1], 0.3981071705534972, places=12)
        self.assertEqual(out[1][1], 1.0)
        self.assertEqual(out[2][1], 1.0)

    def test_injected_eclipse_found_not_vetoed(self):
        rows = _rows([T_IN, T_IN + 1.0, T_IN + 2.0])
        lo, hi = T_IN - 100, T_IN + 100
        self.assertTrue(J.trial(4000.0, J.Points(rows), lo, hi)[0])
        inj = J.Points(J.inject(rows, 4000.0))
        self.assertFalse(J.trial(4000.0, inj, lo, hi, min_nights=1)[0])
        ev = J.group_events(J.dip_points(inj))
        self.assertEqual(len(ev), 1)
        self.assertTrue(ev[0]["strong"])

    def test_covered(self):
        lo, hi = T_IN - 100, T_IN + 100
        self.assertTrue(J.covered(J.Points(_rows([T_IN, T_IN + 1.0, T_IN + 2.0])), 4000.0, lo, hi))
        self.assertFalse(J.covered(J.Points(_rows([T_IN, T_IN + 1.0])), 4000.0, lo, hi))


class TestBin(unittest.TestCase):
    def test_bin_series(self):
        b = J.bin_series([0.0, 0.2, 0.4, 1.3, 1.6], [1.0, 2.0, 3.0, 4.0, 6.0], 1.0)
        self.assertEqual(len(b), 2)
        self.assertAlmostEqual(b[0][0], 0.2)
        self.assertAlmostEqual(b[0][1], 2.0)
        self.assertEqual(b[0][2], 3)
        self.assertAlmostEqual(b[1][0], 1.45)
        self.assertAlmostEqual(b[1][1], 5.0)


class TestAsassnNormalise(unittest.TestCase):
    def test_normalise(self):
        import asassn_io
        by = {"g": [(2459000.0 + k, 10.0, 0.1, "bA") for k in range(25)]
              + [(2459100.0 + k, 5.0, 0.05, "bB") for k in range(5)], "V": []}
        pts, meta = asassn_io.normalise(by)
        self.assertEqual(len(pts), 25)
        self.assertTrue(meta["g:bA"]["used"])
        self.assertFalse(meta["g:bB"]["used"])
        self.assertAlmostEqual(pts[0][1], 1.0)
        self.assertAlmostEqual(pts[0][2], 0.01)


if __name__ == "__main__":
    unittest.main()
