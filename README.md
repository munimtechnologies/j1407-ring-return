# j1407-ring-return

Did the giant ring system that eclipsed the young star J1407 (V1400 Cen) in 2007 come back?

In April-May 2007 J1407 was eclipsed for 56 days by what looks like an enormous ring system around
an unseen companion, J1407b. It has never been seen again. Mentel et al. (2018,
[arXiv:1810.05171](https://arxiv.org/abs/1810.05171)) narrowed the orbital period to 11-18 years
(or above 22 years) and expected the next eclipse "no earlier than Spring 2018", most plausibly
between spring 2021 and spring 2024. That window has passed and public photometry covers it, but
no one has published the test.

This repository holds a pre-registered test with ASAS-SN Sky Patrol (2014-2026) and TESS
(Sectors 11, 38, 64, 102). The rules are in [PREREGISTRATION.md](PREREGISTRATION.md), fixed on
2026-11-24 before the analysis ran. Results will appear under `results/`. Gaia DR4 epoch photometry
will be added after its release on 2026-12-02.

- `j1407.py`: eclipse windows, vetoes, period scan, dip events, injections (stdlib, tested)
- `asassn_io.py`, `io_tess.py`: public data access (ASAS-SN Sky Patrol v2, MAST TESScut)
- `job.py`: the full run: `python job.py --data-dir /data --out-dir /out`
- `test_j1407.py`: `python -m unittest -v`

Credit: the eclipse windows and period constraints are from R. T. Mentel, M. A. Kenworthy,
D. A. Cameron et al. (2018); discovery and ring model from E. E. Mamajek et al. (2012) and
M. A. Kenworthy & E. E. Mamajek (2015). Data: ASAS-SN Sky Patrol v2, TESS (NASA, MAST).

By MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents working in his name; no human expert
has checked it yet. Code Apache-2.0; text and results CC BY 4.0.
