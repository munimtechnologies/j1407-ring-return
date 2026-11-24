# Pre-registration: did the J1407b ring system come back in 2018-2026?

Frozen 2026-11-24 (UTC), before the job below has run and before we have looked at any post-2018
photometry of J1407. MV2, Munim, Inc. The work, code and text were made with AI agents working in
MV2's name; no human expert has checked them yet. Licence: Apache-2.0 (code), CC BY 4.0 (text
and results).

## 1. The near miss

In April-May 2007 the young K star J1407 (V1400 Cen, 1SWASP J140747.93-394542.6, V = 12.36)
went through a 56-day series of deep eclipses, interpreted as a giant ring system around an unseen
companion, J1407b (Mamajek et al. 2012; Kenworthy & Mamajek 2015). It has never been seen again.

- Kenworthy et al. 2015 ([arXiv:1410.6577](https://arxiv.org/abs/1410.6577)): for circular orbits
  the period is 3.5-13.8 yr.
- Rieder & Kenworthy 2016 ([arXiv:1609.08485](https://arxiv.org/abs/1609.08485)): a retrograde ring
  around a 60-100 M_Jup companion on an 11-yr orbit is long-lived.
- **Mentel, Kenworthy, Cameron et al. 2018** ([arXiv:1810.05171](https://arxiv.org/abs/1810.05171)),
  using photographic plates (1890-1990) and photometry to 2018: "strongly constrain the orbital
  period to a value between 11 and 18 years and values above 22 years", and "we expect the next
  transit no earlier than Spring 2018 (corresponding to an orbital period of 11 years)", "most
  plausibly between Spring 2021 (orbital period of 14 years) and Spring 2024 (orbital period of 17
  years)". They added that periods above 14-15 yr (circular) or 18 yr (eccentric) are
  dynamically improbable.
- Kenworthy et al. 2020 ([arXiv:1912.03314](https://arxiv.org/abs/1912.03314)) found an ALMA source
  that could be a free-floating J1407b; Klaassen et al. 2025
  ([arXiv:2512.13254](https://arxiv.org/abs/2512.13254)) did not see it again in 2024.

The predicted window (2018-2025) is over, and public photometry covers it, but no paper has tested
the bound-orbit periods with post-2018 data (searches 2026-11-24, notes/scoop-check-2026-11-24.md).

**The question:** which bound-orbit periods of J1407b, especially Mentel et al.'s allowed 11-18
yr band, are still possible after ASAS-SN (2014-2026) and TESS (Sectors 11, 38, 64, 102)?

**The wow if it works:** either the second eclipse of the most famous exoring candidate, or the
closing of its last short-period window, which would leave an unbound (free-floating) J1407b or a
very long, dynamically disfavoured orbit as the only options.

## 2. Data (all public, fetched by job.py)

| Source | Access | Use |
|---|---|---|
| ASAS-SN Sky Patrol v2 | pyasassn, nearest source within 10" with rows, quality G, error/median <= 0.05 | primary: veto and dip points |
| TESS FFI | MAST TESScut 11x11, all sectors listed (11, 38, 64, 102) | secondary: daily bins |

Gaia DR4 epoch photometry (2014-2020) will be added on/after 2026-12-02 as a separately dated
amendment. ATLAS needs an account and is not used. ZTF does not reach Dec -40.

No post-2018 J1407 photometry was looked at before this file was frozen. The TESS sector list was
read from the MAST sector service (positions only, no fluxes).

## 3. Method (code: j1407.py, job.py)

**Eclipse model (Mentel et al. 2018, section 3).** Three boxcar windows in which the 2007
photometry was more than 0.5 mag below normal: MJD 54194-54198, 54204-54234, 54242-54246 (the paper
prints the first as "54194 to 54298" while calling it a 4-day window; we read 54194-54198). A trial
period P predicts the same windows shifted by n P (n != 0). Assumption A1: a return of the ring
system dims the star by at least 0.5 mag in those windows.

**Normalisation.** ASAS-SN: per band (V, g) and camera, r = flux / median flux; sigma = max(error /
median, 1.4826 MAD of that group). TESS: 3x3-pixel aperture minus a per-cadence median background,
1-day bins (at least half a day of cadences), each divided by the median of the per-sector median
fluxes.

**Veto.** An ASAS-SN point vetoes if it falls inside a predicted window, is less than 0.25 mag
below normal (r > 0.794), and lies more than 4 sigma above the 0.5-mag level (r - 0.631 > 4
sigma). A TESS daily bin vetoes if r > 0.92 (a 0.5-mag eclipse of J1407 still shows as a dip of
at least 9% if up to 75% of the aperture light came from other stars). A trial period is
**excluded** if one predicted eclipse has vetoing points on **at least 2 distinct nights**
(points more than 0.5 d apart). Sensitivity analysis: 1 night.

**Grid.** P = 1-25 yr in 0.25-d steps (35,065 trials).

**Scans.** primary = ASAS-SN, 2 nights. Also reported: one_night (ASAS-SN, 1 night), with_tess
(ASAS-SN + TESS, 2 nights), asassn_from_2018_03 (ASAS-SN after 2018-03-01 only, i.e. data
Mentel et al. did not have).

**Dips.** An ASAS-SN dip point has r <= 0.631 (0.5 mag) and 1 - r >= 5 sigma. Dip points closer than
60 d form an event; an event is **strong** with >= 3 points on >= 2 nights. For each strong event
we list implied periods (time from the 2007 central-window midpoint, MJD 54219, divided by n). TESS
daily bins below 0.85 are listed separately.

**Injection test.** 200 periods evenly spaced in 11-18 yr; every ASAS-SN point inside that
period's predicted windows is dimmed by 1 mag; we count periods where the windows hold >= 3 points
on >= 2 nights (covered) and, of those, the fraction where a strong event is found within 60 d of a
predicted central window (recovered).

## 4. Pre-registered outcomes

Primary metric E = excluded fraction of trial periods in **11-18 yr** (primary scan).
- **BAND_11_18_CLOSED**: E >= 0.99.
- **BAND_11_18_MOSTLY_CLOSED**: 0.90 <= E < 0.99.
- **BAND_11_18_PARTLY_CLOSED**: 0.50 <= E < 0.90.
- **BAND_11_18_OPEN**: E < 0.50.

**ECLIPSE_CANDIDATE** is added if any strong ASAS-SN event exists. A candidate is not called a
detection until it is checked against neighbouring stars, ASAS-SN image quality and TESS (or
Gaia DR4); that check will be a dated amendment. The 14-17 yr "most plausible" band is reported
alongside, as are the allowed period intervals and the dates their next central windows fall.

Expected (stated before running): J1407 is near the Sun in October-December, so predicted
eclipses at half-year periods (11.5, 12.5, ... yr) can fall in the seasonal gap. We therefore expect
the band to be mostly, not fully, closed, with allowed islands near half-integer periods.

## 5. Limits fixed in advance

- A1 can fail: a changed or precessed ring could give a shallower or differently timed eclipse.
  The test is about a repeat of an eclipse like the 2007 one.
- An excluded period means "no 2007-like eclipse at that period in these data", not that no
  companion exists.
- Periods above about 19 yr put the first return after the data end (2026); they stay untested.
- ASAS-SN times are HJD, TESS BJD; the differences (minutes) are irrelevant for 4-30-day windows.
- Combining with Mentel et al.'s own constraints is done in words, not by re-analysing their data.

## 6. Deviations

Any change after the job runs is logged in a dated DEVIATION file and reported with the results.
A failed download is retried in a new job version; it does not change the rules.

## 7. Credit

Setup and eclipse windows: R. T. Mentel, M. A. Kenworthy, D. A. Cameron et al. (2018). Discovery
and ring model: E. E. Mamajek et al. (2012); M. A. Kenworthy & E. E. Mamajek (2015). Data: ASAS-SN
Sky Patrol v2 (Hart et al. 2023; Kochanek et al. 2017), TESS (NASA; MAST TESScut, Brasseur et al.
2019).
