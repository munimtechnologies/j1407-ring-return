# Copyright 2026 Munim, Inc.
# SPDX-License-Identifier: Apache-2.0
"""Core of the J1407 (V1400 Cen) ring-return test (stdlib only; imported by the tests).

The eclipse model follows Mentel, Kenworthy, Cameron et al. (2018, A&A; arXiv:1810.05171),
section 3: the 2007 eclipse is represented by three boxcar windows in which the 2007 photometry
was more than 0.5 mag below the out-of-eclipse level: MJD 54194-54198, 54204-54234 and
54242-54246. (The paper prints the first window as "MJD 54194 to MJD 54298" while calling it a
4-day window; we read it as 54194-54198.) A trial period P predicts the same three windows
shifted by n P.

Everything here is fixed by PREREGISTRATION.md (2026-11-24) before any post-2018 data were
analysed by this code.
"""
import bisect
import datetime
import math
import statistics

VERSION = "0.1.0"

MJD0 = 2400000.5
YEAR = 365.25
WINDOWS_MJD = ((54194.0, 54198.0), (54204.0, 54234.0), (54242.0, 54246.0))
WINDOWS = tuple((a + MJD0, b + MJD0) for a, b in WINDOWS_MJD)
W_LO = WINDOWS[0][0]
W_HI = WINDOWS[-1][1]
CENTRE = 0.5 * (WINDOWS[1][0] + WINDOWS[1][1])  # JD 2454219.5 (MJD 54219)

DEEP_RATIO = 10 ** (-0.2)     # 0.5 mag fainter
NORMAL_RATIO = 10 ** (-0.1)   # 0.25 mag fainter
VETO_NSIGMA = 4.0             # ground point must sit > 4 sigma above the 0.5-mag level
TESS_NORMAL = 0.92            # TESS daily bin: dip below 8 percent (blend-safe, see PREREGISTRATION)
MIN_VETO_NIGHTS = 2           # vetoing points on >= 2 distinct nights inside one predicted eclipse
NIGHT_GAP = 0.5               # days separating two "nights"
DIP_NSIGMA = 5.0
EVENT_GAP = 60.0              # dip points closer than this (days) form one event
STRONG_MIN_POINTS = 3
STRONG_MIN_NIGHTS = 2
TESS_DIP_RATIO = 0.85
P_LO_YR, P_HI_YR = 1.0, 25.0
P_STEP_D = 0.25
BAND = (11.0, 18.0)           # Mentel et al. 2018: allowed 11-18 yr (and > 22 yr)
CORE_BAND = (14.0, 17.0)      # their "most plausible" 14-17 yr
INJECT_MAG = 1.0


def jd_to_date(jd):
    d = datetime.datetime(2000, 1, 1, 12) + datetime.timedelta(days=jd - 2451545.0)
    return d.strftime("%Y-%m-%d")


def robust_scatter(values):
    """1.4826 x median absolute deviation."""
    v = [x for x in values if x == x]
    if len(v) < 2:
        return float("nan")
    m = statistics.median(v)
    return 1.4826 * statistics.median([abs(x - m) for x in v])


def veto_capable(r, s, src):
    """Can this point, if it falls inside a predicted window, show that no eclipse happened?"""
    if src == "tess":
        return r > TESS_NORMAL
    return r > NORMAL_RATIO and (r - DEEP_RATIO) > VETO_NSIGMA * s


class Points:
    """Normalised photometry rows (t_jd, r, sigma, source), sorted by time."""

    def __init__(self, rows):
        rows = sorted(rows, key=lambda x: x[0])
        self.t = [x[0] for x in rows]
        self.r = [x[1] for x in rows]
        self.s = [x[2] for x in rows]
        self.src = [x[3] for x in rows]
        vc = [x for x in rows if veto_capable(x[1], x[2], x[3])]
        self.vt = [x[0] for x in vc]
        self.vsrc = [x[3] for x in vc]

    def __len__(self):
        return len(self.t)

    def rows(self):
        return list(zip(self.t, self.r, self.s, self.src))

    def subset(self, keep):
        return Points([x for x in self.rows() if keep(x)])


def count_nights(times, gap=NIGHT_GAP):
    if not times:
        return 0
    ts = sorted(times)
    n = 1
    for a, b in zip(ts, ts[1:]):
        if b - a > gap:
            n += 1
    return n


def eclipse_numbers(P, t_lo, t_hi):
    """n != 0 whose predicted windows overlap [t_lo, t_hi]."""
    n0 = int(math.ceil((t_lo - W_HI) / P))
    n1 = int(math.floor((t_hi - W_LO) / P))
    return [n for n in range(n0, n1 + 1) if n != 0]


def window_hits(times, n, P):
    """Indices of sorted `times` inside the three windows shifted by n P."""
    out = []
    for a, b in WINDOWS:
        i = bisect.bisect_left(times, a + n * P)
        j = bisect.bisect_right(times, b + n * P)
        out.extend(range(i, j))
    return out


def trial(P, pts, t_lo, t_hi, min_nights=MIN_VETO_NIGHTS):
    """(excluded?, info): excluded if one predicted eclipse has vetoing points on >= min_nights."""
    for n in eclipse_numbers(P, t_lo, t_hi):
        idx = window_hits(pts.vt, n, P)
        if not idx:
            continue
        nights = count_nights([pts.vt[i] for i in idx])
        if nights >= min_nights:
            return True, {"n": n, "start_jd": W_LO + n * P, "nights": nights,
                          "by": sorted(set(pts.vsrc[i] for i in idx))}
    return False, None


def period_grid(lo_yr=P_LO_YR, hi_yr=P_HI_YR, step=P_STEP_D):
    n = int(math.floor((hi_yr - lo_yr) * YEAR / step + 1e-9))
    return [lo_yr * YEAR + k * step for k in range(n + 1)]


def scan(pts, grid, t_lo, t_hi, min_nights=MIN_VETO_NIGHTS):
    flags = bytearray(len(grid))
    for k, P in enumerate(grid):
        if trial(P, pts, t_lo, t_hi, min_nights)[0]:
            flags[k] = 1
    return flags


def allowed_runs(grid, flags):
    runs, cur = [], None
    for P, f in zip(grid, flags):
        if f:
            if cur is not None:
                runs.append(cur)
                cur = None
        elif cur is None:
            cur = [P, P, 1]
        else:
            cur[1] = P
            cur[2] += 1
    if cur is not None:
        runs.append(cur)
    return runs


def band_fraction(grid, flags, lo_yr, hi_yr):
    """(n_trials, n_excluded, excluded fraction) for lo_yr <= P/yr <= hi_yr."""
    i = bisect.bisect_left(grid, lo_yr * YEAR - 1e-9)
    j = bisect.bisect_right(grid, hi_yr * YEAR + 1e-9)
    n = j - i
    ex = sum(flags[i:j])
    return n, ex, (ex / n) if n else float("nan")


def binned(grid, flags, edges_yr):
    out = []
    for a, b in zip(edges_yr, edges_yr[1:]):
        i = bisect.bisect_left(grid, a * YEAR)
        j = bisect.bisect_left(grid, b * YEAR)
        n = j - i
        ex = sum(flags[i:j])
        out.append((a, b, n, ex, (ex / n) if n else float("nan")))
    return out


def band_verdict(E):
    if E >= 0.99:
        return "CLOSED"
    if E >= 0.90:
        return "MOSTLY_CLOSED"
    if E >= 0.50:
        return "PARTLY_CLOSED"
    return "OPEN"


def dip_points(pts, sources=("asassn",)):
    return [(t, r, s, c) for t, r, s, c in pts.rows()
            if c in sources and r <= DEEP_RATIO and (1.0 - r) >= DIP_NSIGMA * s]


def group_events(dips, gap=EVENT_GAP):
    groups = []
    for d in sorted(dips):
        if groups and d[0] - groups[-1][-1][0] <= gap:
            groups[-1].append(d)
        else:
            groups.append([d])
    out = []
    for g in groups:
        nights = count_nights([x[0] for x in g])
        rmin = min(x[1] for x in g)
        out.append({"t_first": g[0][0], "t_last": g[-1][0], "t_mid": sum(x[0] for x in g) / len(g),
                    "date_first": jd_to_date(g[0][0]), "date_last": jd_to_date(g[-1][0]),
                    "n": len(g), "nights": nights,
                    "depth_mag_max": -2.5 * math.log10(rmin) if rmin > 0 else float("inf"),
                    "sources": sorted(set(x[3] for x in g)),
                    "strong": len(g) >= STRONG_MIN_POINTS and nights >= STRONG_MIN_NIGHTS})
    return out


def implied_periods(t, lo_yr=P_LO_YR, hi_yr=P_HI_YR):
    """Periods (days) putting the 2007 central-window midpoint n cycles before t."""
    dt = t - CENTRE
    out = []
    n = 1
    while True:
        P = abs(dt) / n
        if P < lo_yr * YEAR:
            break
        if P <= hi_yr * YEAR:
            out.append((n if dt > 0 else -n, P))
        n += 1
    return out


def window_number(t, P):
    """n (may be 0) if t lies inside a window of eclipse n for period P, else None."""
    n = int(math.floor((t - W_LO) / P))
    for a, b in WINDOWS:
        if a + n * P <= t <= b + n * P:
            return n
    return None


def inject(rows, P, depth_mag=INJECT_MAG):
    """Rows with every point inside a predicted window (n != 0) dimmed by depth_mag."""
    f = 10 ** (-0.4 * depth_mag)
    out = []
    for t, r, s, c in rows:
        n = window_number(t, P)
        out.append((t, r * f if (n is not None and n != 0) else r, s, c))
    return out


def covered(pts, P, t_lo, t_hi):
    """True if some predicted eclipse has >= 3 points on >= 2 nights inside its windows."""
    for n in eclipse_numbers(P, t_lo, t_hi):
        idx = window_hits(pts.t, n, P)
        if len(idx) >= STRONG_MIN_POINTS and count_nights([pts.t[i] for i in idx]) >= STRONG_MIN_NIGHTS:
            return True
    return False


def bin_series(t, r, width):
    """Average sorted series into bins of `width` days from t[0]. Returns [(t_mean, r_mean, n)]."""
    out = []
    if not t:
        return out
    t0 = t[0]
    cur_k, acc = None, []
    for ti, ri in zip(t, r):
        k = int((ti - t0) // width)
        if cur_k is not None and k != cur_k and acc:
            out.append((sum(a for a, _ in acc) / len(acc), sum(b for _, b in acc) / len(acc), len(acc)))
            acc = []
        cur_k = k
        acc.append((ti, ri))
    if acc:
        out.append((sum(a for a, _ in acc) / len(acc), sum(b for _, b in acc) / len(acc), len(acc)))
    return out
