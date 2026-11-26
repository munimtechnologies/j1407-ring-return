# Grading of the J1407 ring-return test v0.1.0

Graded 2026-11-26 (UTC) against [PREREGISTRATION.md](PREREGISTRATION.md) (frozen 2026-11-24).
Job `j1407-return-v1` ran 2026-11-26 05:07-05:27 UTC; all files are in `results/v0.1.0/`.
MV2, Munim, Inc. Made with AI agents working in MV2's name; no human expert has checked it yet.

## Outcome: BAND_11_18_PARTLY_CLOSED (no eclipse candidate)

| Scan | 11-18 yr excluded | 14-17 yr excluded | Allowed runs |
|---|---|---|---|
| primary (ASAS-SN, 2 nights) | **0.7703** (7,879 / 10,228) | 0.8492 (3,723 / 4,384) | 45 |
| one_night (sensitivity) | 0.8214 | 0.8761 | 44 |
| with_tess | 0.7703 | 0.8492 | 46 |
| asassn_from_2018_03 (only data Mentel et al. 2018 did not have) | 0.7703 | 0.8492 | 62 |

- **No strong dip event and no ASAS-SN dip point** (r <= 0.631 at 5 sigma) anywhere in 1,372 ASAS-SN
  points, 2014-05-12 to 2025-06-11. So **no ECLIPSE_CANDIDATE**.
- **Injection test:** of 200 periods in 11-18 yr, 148 had their predicted windows covered by >= 3
  points on >= 2 nights, and a 1-mag injected eclipse was recovered in **148 of 148**.
- Every exclusion inside 11-18 yr comes from data taken after 2018-03-01 (the `asassn_from_2018_03`
  scan gives the same fraction), i.e. from data the period paper did not have.
- Round periods (n = 1 central window, ASAS-SN nights inside it): 11 yr excluded (24 nights), 12 yr
  (25), 14 yr (21), 15 yr (22), 16 yr (28), 17 yr (15). **13 yr and 18 yr stay allowed.**

## What is still allowed inside 11-18 yr (allowed_periods_primary.csv)

| Allowed period range (yr) | Where its first predicted central window falls | Why it survives |
|---|---|---|
| 11.44-11.60 | 2018-10-06 .. 2018-12-04 | J1407 behind the Sun (solar conjunction) |
| 12.44-12.63 | 2019-10-05 .. 2019-12-16 | solar conjunction |
| **12.96-13.02** | **2020-04-13 .. 2020-05-05** | **ASAS-SN has no J1407 data from 2020-03-24 to 2020-05-19** (survey pause in spring 2020) |
| 13.31-13.62 | 2020-08-19 .. 2020-12-11 | late season / solar conjunction |
| 14.45-14.61 | 2021-10-10 .. 2021-12-06 | solar conjunction |
| 15.45-15.61 | 2022-10-09 .. 2022-12-07 | solar conjunction |
| 16.41-16.61 | 2023-09-27 .. 2023-12-09 | solar conjunction |
| 17.42-17.68, 17.77-17.78 | 2024-09-30 .. 2025-02-06 | solar conjunction / sparse 2025 data |
| >= 17.80 | from 2025-02-13 | after the ASAS-SN data effectively end (6 points in 2025) |

The expectation written before the run ("mostly, not fully, closed, with allowed islands near
half-integer periods") was right about the islands and too optimistic about the fraction: the band
is partly (77%), not mostly (>= 90%), closed. The extra open ground is the spring-2020 gap and the
late-season windows.

## Checks made by hand (not in the pre-registered rules, reported for transparency)

1. **Blending.** ASAS-SN's median V flux for the source (41.18 mJy, camera bf; 38.08 mJy camera be,
   `results.json`) equals the flux of a V = 12.36 star (about 41.5 mJy), so the photometry measures
   J1407's own light; a neighbour is not diluting a possible eclipse.
2. **Spring-2020 gap.** `asassn_points.csv` has no point between 2020-03-24 (BJD 2458933.37) and
   2020-05-19 (BJD 2458989.35); this gap is what keeps the 13.0-yr island open.
3. **TESS Sector 64 is unusable.** Its cutout came back on a different flux scale (median 0.219
   against about 4,100 in Sectors 11, 38 and 102), so all 22 daily bins have ratios near 5e-5. The
   22 "TESS dip bins" listed in `results.json` are this unit artefact, not dips. By the frozen rule a
   TESS bin vetoes only when r > 0.92, so Sector 64 vetoed nothing and changed no result. Sectors 11
   (2019-04-23 .. 05-20), 38 (2021-04-29 .. 05-26) and 102 (2026-03-27 .. 04-21) are normal (daily
   minima 0.958, 0.951 and 1.031 of the reference); 11 and 38 fall in the 12-yr and 14-yr windows
   already excluded by ASAS-SN.

## Deviations

None to the rules. The Sector 64 problem above is a data-format failure in one TESS sector,
disclosed here; it did not change any graded number.

## What it means

Mentel et al. (2018) expected the next eclipse "no earlier than Spring 2018", most plausibly between
spring 2021 and spring 2024 (periods of 14-17 yr). In ASAS-SN's observing seasons from 2018 to 2024
no 2007-like eclipse occurred: 85% of the 14-17 yr band and 77% of the 11-18 yr band are now
excluded. A bound J1407b with a period in Mentel et al.'s band survives only if its eclipse fell
while J1407 was behind the Sun (October-December), in the spring-2020 ASAS-SN pause (P = 12.96-13.02
yr), or after early 2025 (P >= 17.8 yr). Gaia DR4 (2 December 2026, epoch photometry 2014-2020) can
test the 2018 and 2019 conjunction islands (pre-registered in AMENDMENT-2026-11-25-gaia-dr4.md).

## Limits

- Assumption A1: a return dims the star by >= 0.5 mag within the 2007 windows. A precessed or
  evolved ring could give a shallower or differently timed eclipse.
- An excluded period means no 2007-like eclipse at that period in these data, not that no
  companion exists.
- Periods are on a 0.25-day grid; fractions are counts of grid trials.

## Credit

Eclipse windows and period band: R. T. Mentel, M. A. Kenworthy, D. A. Cameron et al. 2018
([arXiv:1810.05171](https://arxiv.org/abs/1810.05171)). Discovery and ring model: E. E. Mamajek et
al. 2012; M. A. Kenworthy & E. E. Mamajek 2015. Data: ASAS-SN Sky Patrol v2 (Hart et al. 2023;
Kochanek et al. 2017); TESS (NASA; MAST TESScut).
