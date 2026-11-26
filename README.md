# j1407-ring-return

Did the giant ring system that eclipsed the young star J1407 (V1400 Cen) in 2007 come back?

In April-May 2007 J1407 was eclipsed for 56 days by what looks like an enormous ring system around
an unseen companion, J1407b. It has never been seen again. Mentel et al. (2018,
[arXiv:1810.05171](https://arxiv.org/abs/1810.05171)) narrowed the orbital period to 11-18 years
(or above 22 years) and expected the next eclipse "no earlier than Spring 2018", most plausibly
between spring 2021 and spring 2024.

## Result (v0.1.0, graded 2026-11-26): BAND_11_18_PARTLY_CLOSED

No 2007-like eclipse in ASAS-SN (2014-2025) or TESS. **77% of the 11-18 yr period band and 85% of
the "most plausible" 14-17 yr band are excluded**, all by data taken after March 2018. A bound
J1407b in that band survives only where its eclipse fell while J1407 was behind the Sun
(October-December), in ASAS-SN's spring-2020 pause (P = 12.96-13.02 yr), or after early 2025
(P >= 17.8 yr). Injected 1-mag eclipses were recovered in 148 of 148 covered trials. Full grading:
[GRADING.md](GRADING.md); files in `results/v0.1.0/`. Gaia DR4 (2 December 2026) will test the 2018
and 2019 islands ([AMENDMENT-2026-11-25-gaia-dr4.md](AMENDMENT-2026-11-25-gaia-dr4.md)).

The rules are in [PREREGISTRATION.md](PREREGISTRATION.md), fixed on 2026-11-24 before the analysis ran.

- `j1407.py`: eclipse windows, vetoes, period scan, dip events, injections (stdlib, tested)
- `asassn_io.py`, `io_tess.py`: public data access (ASAS-SN Sky Patrol v2, MAST TESScut)
- `job.py`: the full run: `python job.py --data-dir /data --out-dir /out`
- `test_j1407.py`: `python -m unittest -v`

Credit: the eclipse windows and period constraints are from R. T. Mentel, M. A. Kenworthy,
D. A. Cameron et al. (2018); discovery and ring model from E. E. Mamajek et al. (2012) and
M. A. Kenworthy & E. E. Mamajek (2015). Data: ASAS-SN Sky Patrol v2, TESS (NASA, MAST).

By MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents working in his name; no human expert
has checked it yet. Code Apache-2.0; text and results CC BY 4.0.
