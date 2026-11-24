# Copyright 2026 Munim, Inc.
# SPDX-License-Identifier: Apache-2.0
"""TESS full-frame-image cutouts from MAST TESScut and simple aperture photometry.
Job only (needs numpy and astropy); not imported by the tests. Same code as
munimtechnologies/epic2202-second-eclipse io_tess.py."""
import glob
import io
import json
import os
import time
import urllib.request
import zipfile

SECTOR_URL = "https://mast.stsci.edu/tesscut/api/v0.1/sector?ra={ra:.6f}&dec={dec:.6f}&radius=0m"
CUT_URL = ("https://mast.stsci.edu/tesscut/api/v0.1/astrocut?ra={ra:.6f}&dec={dec:.6f}"
           "&y={n}&x={n}&units=px&sector={s}")
BAD_BITS = 1 | 2 | 4 | 8 | 32 | 128  # attitude tweak, safe mode, coarse/earth point, desat, manual exclude


def _get(url, tries=4, timeout=600, log=print):
    last = None
    for k in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=timeout) as resp:
                return resp.read()
        except Exception as exc:
            last = repr(exc)
            log("GET try %d failed (%s): %s" % (k + 1, url[:90], last))
            time.sleep(30 * (k + 1))
    raise RuntimeError(last)


def sectors(ra, dec, log=print):
    data = json.loads(_get(SECTOR_URL.format(ra=ra, dec=dec), log=log).decode())
    return sorted(int(r["sector"]) for r in data.get("results", []))


def fetch_cutout(ra, dec, sector, out_dir, n=11, log=print):
    os.makedirs(out_dir, exist_ok=True)
    have = glob.glob(os.path.join(out_dir, "*s%04d*.fits" % sector))
    if have:
        return have[0]
    blob = _get(CUT_URL.format(ra=ra, dec=dec, n=n, s=sector), log=log)
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        names = [x for x in z.namelist() if x.endswith(".fits")]
        z.extractall(out_dir, members=names)
    paths = [os.path.join(out_dir, x) for x in names]
    log("TESScut sector %d: %s" % (sector, ", ".join(os.path.basename(p) for p in paths)))
    return paths[0] if paths else None


def photometry(path):
    """Returns dict with bjd list, f3 (3x3 aperture) and f1 (peak pixel) background-subtracted
    fluxes, cadence (days) and notes. Background = per-cadence median of pixels >= 4 px from the
    aperture centre whose median-image value is below the 60th percentile."""
    import numpy as np
    from astropy.io import fits
    with fits.open(path, memmap=False) as h:
        d = h[1].data
        t = np.array(d["TIME"], dtype=float)
        flux = np.array(d["FLUX"], dtype=float)
        q = np.array(d["QUALITY"], dtype=int)
    nt, ny, nx = flux.shape
    good = np.isfinite(t) & ((q & BAD_BITS) == 0) & np.isfinite(flux[:, ny // 2, nx // 2])
    t, flux = t[good], flux[good]
    med = np.nanmedian(flux, axis=0)
    cy, cx = ny // 2, nx // 2
    sub = med[cy - 1:cy + 2, cx - 1:cx + 2]
    dy, dx = np.unravel_index(int(np.nanargmax(sub)), sub.shape)
    py, px = cy - 1 + dy, cx - 1 + dx
    yy, xx = np.mgrid[0:ny, 0:nx]
    dist = np.hypot(yy - py, xx - px)
    ap = (np.abs(yy - py) <= 1) & (np.abs(xx - px) <= 1)
    thr = np.nanpercentile(med, 60)
    bmask = (dist >= 4) & (med < thr) & np.isfinite(med)
    bkg = np.nanmedian(flux[:, bmask], axis=1)
    f3 = np.nansum(flux[:, ap], axis=1) - ap.sum() * bkg
    f1 = flux[:, py, px] - bkg
    ok = np.isfinite(f3) & np.isfinite(f1) & (f3 > 0) & (f1 > 0)
    t, f3, f1 = t[ok], f3[ok], f1[ok]
    cad = float(np.median(np.diff(t))) if len(t) > 1 else float("nan")
    return {"bjd": (t + 2457000.0).tolist(), "f3": f3.tolist(), "f1": f1.tolist(),
            "cadence_days": cad, "n_good": int(len(t)), "n_all": int(nt),
            "aperture_centre": [int(py), int(px)], "n_bkg_pixels": int(bmask.sum()),
            "frac_aperture_in_peak": float(np.nanmedian(f1 / f3)) if len(t) else float("nan")}
