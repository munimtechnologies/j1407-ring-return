# Copyright 2026 Munim, Inc.
# SPDX-License-Identifier: Apache-2.0
"""J1407 (V1400 Cen) ring-return test (pre-registered 2026-11-24, PREREGISTRATION.md).

python job.py --data-dir /data --out-dir /out
Writes /out/results.json (rewritten after every stage, key "stage"), CSVs and summary.md.
"""
import argparse
import csv
import json
import math
import os
import statistics
import sys
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import j1407 as J  # noqa: E402

RA, DEC = 211.949708, -39.761861  # 1SWASP J140747.93-394542.6 = V1400 Cen (Mentel et al. 2018, Table 1)
START = time.time()
N_INJECT = 200


def log(msg):
    print("[%7.1fs] %s" % (time.time() - START, msg), flush=True)


def write_json(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(obj, fh, indent=1, default=str)
    os.replace(tmp, path)


def write_csv(path, header, rows):
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        for r in rows:
            w.writerow(r)


def get_asassn(data_dir, res):
    import asassn_io
    out = {}
    res["data"]["asassn"] = out
    try:
        out["client"] = asassn_io.ensure_client()
        path = os.path.join(data_dir, "asassn_lc.csv")
        info = None
        for k in range(3):
            try:
                info = asassn_io.fetch(RA, DEC, path, log=log)
                if info.get("status") == "ok":
                    break
            except Exception as exc:
                info = {"status": "error", "error": repr(exc)}
                log("ASAS-SN try %d: %r" % (k + 1, exc))
            time.sleep(60)
        out["fetch"] = info
        if not info or info.get("status") != "ok":
            return []
        by_band, lmeta = asassn_io.load_points(path)
        pts, nmeta = asassn_io.normalise(by_band)
        out["load"] = lmeta
        out["groups"] = nmeta
        out["n_used"] = len(pts)
        log("ASAS-SN points used: %d" % len(pts))
        return pts
    except Exception as exc:
        out["error"] = repr(exc)
        out["traceback"] = traceback.format_exc()[-2000:]
        log("ASAS-SN failed: %r" % exc)
        return []


def get_tess(data_dir, out_dir, res):
    """Daily bins of 3x3-aperture flux, each divided by the median of the per-sector medians."""
    import io_tess
    info = {"sectors": {}}
    res["data"]["tess"] = info
    per = {}
    try:
        secs = io_tess.sectors(RA, DEC, log=log)
    except Exception as exc:
        info["error"] = "sector list: %r" % exc
        return []
    info["sector_list"] = secs
    for s in secs:
        si = {}
        info["sectors"][str(s)] = si
        try:
            path = io_tess.fetch_cutout(RA, DEC, s, os.path.join(data_dir, "tesscut"), log=log)
            ph = io_tess.photometry(path)
        except Exception as exc:
            si["error"] = repr(exc)
            log("TESS sector %d failed: %r" % (s, exc))
            continue
        t, f = ph["bjd"], ph["f3"]
        si.update({k: ph[k] for k in ("cadence_days", "n_good", "n_all", "aperture_centre",
                                      "n_bkg_pixels", "frac_aperture_in_peak")})
        if len(t) < 50:
            si["note"] = "too few points"
            continue
        med = statistics.median(f)
        bins = J.bin_series(t, f, 1.0)
        need = 0.5 / ph["cadence_days"]
        bins = [b for b in bins if b[2] >= need]
        si.update({"median_flux": med, "t_first": t[0], "t_last": t[-1],
                   "date_first": J.jd_to_date(t[0]), "date_last": J.jd_to_date(t[-1]),
                   "n_daily_bins": len(bins)})
        per[s] = (med, bins)
    if not per:
        return []
    ref = statistics.median([m for m, _ in per.values()])
    info["reference_flux"] = ref
    rows = []
    chart = []
    for s, (med, bins) in sorted(per.items()):
        rs = [b[1] / ref for b in bins]
        info["sectors"][str(s)].update({"sector_median_ratio": med / ref,
                                        "daily_min_ratio": min(rs) if rs else None,
                                        "daily_scatter": J.robust_scatter(rs)})
        for (tb, fb, nb), r in zip(bins, rs):
            rows.append((tb, r, 0.0, "tess"))
            chart.append((s, "%.4f" % tb, J.jd_to_date(tb), "%.4f" % r, nb))
        log("TESS sector %d: %d daily bins, sector/ref %.3f, min %.3f" % (s, len(bins), med / ref, min(rs) if rs else float("nan")))
    write_csv(os.path.join(out_dir, "tess_daily.csv"), ["sector", "bjd", "date", "ratio", "n"], chart)
    return rows


def run_scan(label, pts, grid, min_nights, res, out_dir):
    t_lo, t_hi = pts.t[0], pts.t[-1]
    flags = J.scan(pts, grid, t_lo, t_hi, min_nights)
    runs = J.allowed_runs(grid, flags)
    nb, eb, Eb = J.band_fraction(grid, flags, *J.BAND)
    nc, ec, Ec = J.band_fraction(grid, flags, *J.CORE_BAND)
    edges = [round(J.P_LO_YR + 0.1 * k, 1) for k in range(int(round((J.P_HI_YR - J.P_LO_YR) / 0.1)) + 1)]
    fr = J.binned(grid, flags, edges)
    res["scans"][label] = {"min_nights": min_nights, "n_trials": len(grid), "n_excluded": sum(flags),
                           "band_11_18": {"n": nb, "excluded": eb, "frac": Eb},
                           "band_14_17": {"n": nc, "excluded": ec, "frac": Ec},
                           "verdict_11_18": J.band_verdict(Eb), "n_allowed_runs": len(runs),
                           "t_lo": t_lo, "t_hi": t_hi}
    write_csv(os.path.join(out_dir, "allowed_periods_%s.csv" % label),
              ["P_first_d", "P_last_d", "P_first_yr", "P_last_yr", "n_trials", "n1_centre_date_first", "n1_centre_date_last"],
              [("%.2f" % a, "%.2f" % b, "%.3f" % (a / J.YEAR), "%.3f" % (b / J.YEAR), n,
                J.jd_to_date(J.CENTRE + a), J.jd_to_date(J.CENTRE + b)) for a, b, n in runs])
    write_csv(os.path.join(out_dir, "chart_excluded_by_period_%s.csv" % label),
              ["P_lo_yr", "P_hi_yr", "n_trials", "n_excluded", "frac_excluded"],
              [("%.1f" % a, "%.1f" % b, n, e, "%.4f" % f) for a, b, n, e, f in fr])
    log("scan %s: band 11-18 yr excluded %.4f (%d/%d) -> %s; 14-17 yr %.4f; allowed runs %d"
        % (label, Eb, eb, nb, J.band_verdict(Eb), Ec, len(runs)))
    return flags, runs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="/data")
    ap.add_argument("--out-dir", default="/out")
    a = ap.parse_args()
    os.makedirs(a.data_dir, exist_ok=True)
    os.makedirs(a.out_dir, exist_ok=True)
    rpath = os.path.join(a.out_dir, "results.json")
    res = {"version": J.VERSION, "target": "J1407 = V1400 Cen = 1SWASP J140747.93-394542.6",
           "ra": RA, "dec": DEC, "stage": "start", "data": {}, "scans": {},
           "preregistration": "PREREGISTRATION.md (2026-11-24)",
           "windows_jd": J.WINDOWS}
    write_json(rpath, res)

    asn = get_asassn(a.data_dir, res)
    res["stage"] = "asassn"
    write_json(rpath, res)
    try:
        tess = get_tess(a.data_dir, a.out_dir, res)
    except Exception as exc:
        res["data"]["tess_error"] = repr(exc)
        tess = []
    res["stage"] = "tess"
    write_json(rpath, res)

    write_csv(os.path.join(a.out_dir, "asassn_points.csv"), ["bjd", "date", "r", "sigma", "band", "camera"],
              [("%.5f" % p[0], J.jd_to_date(p[0]), "%.5f" % p[1], "%.5f" % p[2], p[4], p[5]) for p in asn])
    prim = J.Points([(p[0], p[1], p[2], "asassn") for p in asn])
    if len(prim) == 0:
        res["stage"] = "done"
        res["outcome"] = ["NO_DATA"]
        write_json(rpath, res)
        log("OUTCOME NO_DATA (ASAS-SN unavailable); re-file as a new version")
        return
    years = {}
    for t in prim.t:
        y = J.jd_to_date(t)[:4]
        years[y] = years.get(y, 0) + 1
    res["span"] = {"t_lo": prim.t[0], "t_hi": prim.t[-1], "date_lo": J.jd_to_date(prim.t[0]),
                   "date_hi": J.jd_to_date(prim.t[-1]), "n_points": len(prim),
                   "n_veto_capable": len(prim.vt), "points_per_year": years,
                   "n_tess_daily_bins": len(tess)}

    # dips and events (ASAS-SN), TESS dip bins
    dips = J.dip_points(prim)
    ev = J.group_events(dips)
    strong = [e for e in ev if e["strong"]]
    for e in strong:
        e["implied_periods"] = [(n, P, P / J.YEAR) for n, P in J.implied_periods(e["t_mid"])]
    tess_dips = [(t, r) for t, r, _, _ in tess if r < J.TESS_DIP_RATIO]
    res["events"] = {"n_dip_points": len(dips), "events": ev, "n_strong": len(strong),
                     "tess_dip_bins": [{"bjd": t, "date": J.jd_to_date(t), "ratio": r} for t, r in tess_dips]}
    write_csv(os.path.join(a.out_dir, "dip_points.csv"), ["bjd", "date", "r", "sigma"],
              [("%.5f" % d[0], J.jd_to_date(d[0]), "%.4f" % d[1], "%.4f" % d[2]) for d in dips])
    res["stage"] = "events"
    write_json(rpath, res)
    log("dip points %d, events %d, strong %d, TESS dip bins %d" % (len(dips), len(ev), len(strong), len(tess_dips)))

    # period scans
    grid = J.period_grid()
    log("grid: %d trial periods %.1f-%.1f yr" % (len(grid), J.P_LO_YR, J.P_HI_YR))
    flags, runs = run_scan("primary", prim, grid, J.MIN_VETO_NIGHTS, res, a.out_dir)
    write_json(rpath, res)
    run_scan("one_night", prim, grid, 1, res, a.out_dir)
    write_json(rpath, res)
    if tess:
        run_scan("with_tess", J.Points(prim.rows() + tess), grid, J.MIN_VETO_NIGHTS, res, a.out_dir)
        write_json(rpath, res)
    post = prim.subset(lambda x: x[0] >= 2458179.5)  # from 2018-03-01 (Mentel et al. data end 2018)
    if len(post):
        run_scan("asassn_from_2018_03", post, grid, J.MIN_VETO_NIGHTS, res, a.out_dir)
        write_json(rpath, res)

    # which predicted eclipse excludes the round-number periods
    marks = {}
    for yr in (11, 12, 13, 14, 15, 16, 17, 18):
        P = yr * J.YEAR
        ex, info = J.trial(P, prim, prim.t[0], prim.t[-1])
        marks[str(yr)] = {"excluded": ex, "info": info,
                          "n1_central_window": [J.jd_to_date(J.WINDOWS[1][0] + P), J.jd_to_date(J.WINDOWS[1][1] + P)]}
    res["round_periods"] = marks

    # injection-recovery inside the 11-18 yr band (primary data)
    lo, hi = J.BAND[0] * J.YEAR, J.BAND[1] * J.YEAR
    inj = {"n": 0, "covered": 0, "recovered": 0, "vetoed_anyway": 0}
    rows = prim.rows()
    for k in range(N_INJECT):
        P = lo + (hi - lo) * (k + 0.5) / N_INJECT
        ip = J.Points(J.inject(rows, P))
        inj["n"] += 1
        if not J.covered(ip, P, ip.t[0], ip.t[-1]):
            continue
        inj["covered"] += 1
        evs = [e for e in J.group_events(J.dip_points(ip)) if e["strong"]]
        if any(abs(e["t_mid"] - (J.CENTRE + n * P)) <= 60.0 for e in evs
               for n in range(1, 4)):
            inj["recovered"] += 1
        if J.trial(P, ip, ip.t[0], ip.t[-1])[0]:
            inj["vetoed_anyway"] += 1
    res["injection"] = inj
    log("injection: %s" % inj)

    # outcome
    pv = res["scans"]["primary"]
    out = []
    if strong:
        out.append("ECLIPSE_CANDIDATE")
    out.append("BAND_11_18_" + pv["verdict_11_18"])
    res["outcome"] = out
    res["stage"] = "done"
    res["runtime_s"] = time.time() - START
    write_json(rpath, res)
    with open(os.path.join(a.out_dir, "summary.md"), "w") as fh:
        fh.write("# J1407 ring-return test v%s\n\n" % J.VERSION)
        fh.write("Outcome: %s\n\n" % ", ".join(out))
        for k, v in res["scans"].items():
            fh.write("- %s: 11-18 yr excluded %.4f (%d/%d), 14-17 yr %.4f, verdict %s, allowed runs %d\n"
                     % (k, v["band_11_18"]["frac"], v["band_11_18"]["excluded"], v["band_11_18"]["n"],
                        v["band_14_17"]["frac"], v["verdict_11_18"], v["n_allowed_runs"]))
        fh.write("\nStrong dip events: %d. Injection: %s\n" % (len(strong), json.dumps(inj)))
    log("OUTCOME " + " ".join(out))


if __name__ == "__main__":
    main()
