# Copyright 2026 Munim, Inc.
# SPDX-License-Identifier: Apache-2.0
"""ASAS-SN Sky Patrol v2 light curves through the public pyasassn client.

fetch() is network I/O (job only). load_points() and normalise() are stdlib and tested.
Same code as munimtechnologies/epic2202-second-eclipse asassn_io.py (itself from
munimtechnologies/asassn14ko-clock ko/asassn_io.py 0.1.1), importing robust_scatter from j1407.
"""
import csv
import math
import subprocess
import sys
import time

from j1407 import robust_scatter


def ensure_client():
    try:
        from pyasassn.client import SkyPatrolClient  # noqa: F401
        return "already installed"
    except ImportError:
        pass
    last = ""
    for spec in ("skypatrol", "git+https://github.com/asas-sn/skypatrol.git"):
        r = subprocess.run([sys.executable, "-m", "pip", "install", "-q", spec],
                           capture_output=True, text=True)
        try:
            from pyasassn.client import SkyPatrolClient  # noqa: F401
            return "installed " + spec
        except ImportError:
            last = (r.stdout or "")[-500:] + (r.stderr or "")[-1500:]
    raise RuntimeError("could not install pyasassn: " + last)


def _sep_arcsec(ra1, dec1, ra2, dec2):
    d1, d2 = math.radians(dec1), math.radians(dec2)
    dra = math.radians(ra2 - ra1)
    c = math.sin(d1) * math.sin(d2) + math.cos(d1) * math.cos(d2) * math.cos(dra)
    return math.degrees(math.acos(max(-1.0, min(1.0, c)))) * 3600.0


def _rows_for(df, asas_sn_id):
    if df is None or len(df) == 0 or "asas_sn_id" not in df.columns:
        return None
    return df[df["asas_sn_id"].astype(str) == str(asas_sn_id)]


def _by_id(client, asas_sn_id, log, tries=2):
    note = []
    for k in range(tries):
        try:
            lcs = client.query_list([int(asas_sn_id)], catalog="master_list",
                                    id_col="asas_sn_id", download=True, threads=1)
            df = getattr(lcs, "data", None)
            sub = _rows_for(df, asas_sn_id)
            n = 0 if sub is None else int(len(sub))
            note.append("try %d: %d rows" % (k + 1, n))
            if n > 0:
                return sub, "; ".join(note)
        except Exception as exc:
            note.append("try %d: %r" % (k + 1, exc))
        time.sleep(5)
    log("ASAS-SN by-ID %s: %s" % (asas_sn_id, "; ".join(note)))
    return None, "; ".join(note)


def fetch(ra, dec, out_csv, radius_arcsec=10.0, log=print):
    from pyasassn.client import SkyPatrolClient
    client = SkyPatrolClient()
    rad = radius_arcsec / 3600.0
    cat = client.cone_search(ra_deg=ra, dec_deg=dec, radius=rad, catalog="master_list")
    info = {"radius_arcsec": radius_arcsec}
    if cat is None or len(cat) == 0:
        info["status"] = "not_in_catalog"
        return info
    rows = cat.to_dict("records")
    for r in rows:
        r["sep_arcsec"] = _sep_arcsec(ra, dec, float(r["ra_deg"]), float(r["dec_deg"]))
    rows.sort(key=lambda r: r["sep_arcsec"])
    rows = [r for r in rows if r["sep_arcsec"] <= radius_arcsec]
    info["candidates"] = [{"asas_sn_id": str(r["asas_sn_id"]), "sep_arcsec": r["sep_arcsec"]}
                          for r in rows[:5]]
    df_all = None
    try:
        lcs = client.cone_search(ra_deg=ra, dec_deg=dec, radius=rad, catalog="master_list",
                                 download=True, threads=1)
        df_all = getattr(lcs, "data", None)
    except Exception as exc:
        info["cone_download_error"] = repr(exc)
    tried = []
    chosen = None
    for rank, r in enumerate(rows[:5]):
        sid = str(r["asas_sn_id"])
        sub = _rows_for(df_all, sid)
        n_cone = 0 if sub is None else int(len(sub))
        entry = {"rank": rank, "asas_sn_id": sid, "sep_arcsec": r["sep_arcsec"], "n_cone": n_cone}
        if n_cone == 0:
            sub, note = _by_id(client, sid, log)
            entry["by_id"] = note
        tried.append(entry)
        if sub is not None and len(sub) > 0:
            chosen = (rank, r, sub)
            break
    info["tried"] = tried
    if chosen is None:
        info["status"] = "no_rows"
        return info
    rank, best, df = chosen
    info.update({"asas_sn_id": str(best["asas_sn_id"]), "sep_arcsec": best["sep_arcsec"],
                 "chosen_rank": rank, "columns": [str(c) for c in df.columns],
                 "n_rows": int(len(df)), "status": "ok"})
    df.to_csv(out_csv, index=False)
    log("ASAS-SN %s (rank %d, %.1f\"): %d rows" % (info["asas_sn_id"], rank, best["sep_arcsec"],
                                                   info["n_rows"]))
    return info


def load_points(csv_path, g_cut_mjd=58450.0):
    """{'g': [(bjd, flux, err, camera)], 'V': [...]} from the saved CSV. Quality 'G' only.
    Band = phot_filter column when present, else by date (g from MJD 58450)."""
    out = {"g": [], "V": []}
    meta = {"band_source": None, "n_total": 0, "n_bad_quality": 0}
    with open(csv_path, newline="") as fh:
        rd = csv.DictReader(fh)
        cols = rd.fieldnames or []
        fcol = next((c for c in ("phot_filter", "filter", "band") if c in cols), None)
        meta["band_source"] = fcol or "date"
        for row in rd:
            meta["n_total"] += 1
            try:
                jd = float(row["jd"])
                flux = float(row["flux"])
                err = float(row["flux_err"])
            except (KeyError, ValueError):
                continue
            q = (row.get("quality") or "G").strip()
            if q and q != "G":
                meta["n_bad_quality"] += 1
                continue
            bjd = jd if jd > 2400000 else jd + 2400000.5
            mjd = bjd - 2400000.5
            if fcol:
                band = (row.get(fcol) or "").strip()
                band = "g" if band.lower().startswith("g") else ("V" if band.upper().startswith("V") else band)
            else:
                band = "g" if mjd >= g_cut_mjd else "V"
            if band in out:
                out[band].append((bjd, flux, err, (row.get("camera") or "?").strip()))
    return out, meta


def normalise(by_band, max_rel_err=0.05, min_n=20):
    """Per (band, camera): r = flux / median flux; sigma_eff = max(err/median, robust scatter).
    Drops flux <= 0, relative error > max_rel_err and groups with fewer than min_n points.
    Returns [(bjd, r, sigma_eff, 'asassn', band, camera)], meta."""
    groups = {}
    for band, rows in by_band.items():
        for t, f, e, cam in rows:
            if f > 0 and e > 0:
                groups.setdefault((band, cam), []).append((t, f, e))
    out = []
    meta = {}
    for (band, cam), rows in sorted(groups.items()):
        fl = sorted(f for _, f, _ in rows)
        n = len(fl)
        med = fl[n // 2] if n % 2 else 0.5 * (fl[n // 2 - 1] + fl[n // 2])
        keep = [(t, f / med, e / med) for t, f, e in rows if e / med <= max_rel_err]
        key = band + ":" + cam
        if len(keep) < min_n:
            meta[key] = {"n": len(keep), "used": False}
            continue
        sc = robust_scatter([r for _, r, _ in keep])
        for t, r, s in keep:
            out.append((t, r, max(s, sc), "asassn", band, cam))
        meta[key] = {"n": len(keep), "used": True, "median_flux": med, "scatter": sc,
                     "t_first": min(x[0] for x in keep), "t_last": max(x[0] for x in keep)}
    return out, meta
