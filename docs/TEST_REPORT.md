# Verification report

## Version 2.0 additions

101 automated tests pass (63 from version 1.0, 38 new in `tests/test_operators.py`). New coverage:

- Interval split, California rest-break count, daily, weekly and seventh-day overtime positions, and tier cuts across parts.
- Rest allowance before unscheduled breaks. Idle explained by equipment is operational, not operator. Supervisor-noted no-output time is operational. Slow pace and breaks are never automatically operator-controlled.
- Every operator dollar allocated once, per worker and period. Time parts partition paid time per worker-day. Overtime premium only on overtime hours. Unpaid meals carry no cost. Order costs reconcile to direct cost. All new controls are zero.
- Productive + unproductive + non-time = loaded cost per operator. Category table sums to loaded cost. Pace + rate variance = actual vs standard. The site cost bridge closes, for each period and in total.
- Timeclock-derived overtime matches payroll for all but two operator-weeks.
- Drill-down routes, supervisor scope, operator CSV export, bad inputs, policy save/load validation, and CSRF and role checks on Cost policy.
- Policy change end to end on a database copy: saving recalculated in about 10 s, figures changed, and restoring the policy restored them.
- Every page was rendered in headless Chromium at 1440 px and 390 px for the Finance, Supervisor and Executive roles, with no console errors.


The final automated test transcript is in test_results.txt. Version 2.0 tests ran on Linux, Python 3.13; Windows execution instructions are supplied but were not executed on a Windows machine.

## Verified

- Every dashboard route with all periods and W37 selected.
- Login, unauthenticated API denial, Executive denial of payroll/source/export access.
- CSRF rejection and approved-tool argument validation.
- Filtered CSV export and source-record drilldown.
- Independent financial-source sums and 624-event normalized ledger.
- Exact signed-cent allocation for every financial event.
- Source correction reversal/replacement and signed agency credit.
- Paid-time partition and logged = matched + outside invariants.
- Activity totals and customer assigned + unassigned conservation.
- Budget bridge exact closure, including explicit residual.
- Test truth and restricted PII exclusion.
- Repeated import idempotence and preservation of corrected source snapshots.
- Decimal rounding, missing/nonfinite monetary input, allocation rounding and negative amounts.
- Normal paid day, unattributed time, duplicate/overlapping intervals, conflicting activity, overnight elapsed time and both DST transitions.
- Basic ordinary-week overtime helper: daily/weekly non-pyramiding, double-time, seventh-day, federal-only and exempt mode. This helper is not a full payroll validation implementation.

## Financial reconciliation

| Period | Payroll | Employer cost | Net agency | Calculated total | GL expense total |
|---|---:|---:|---:|---:|---:|
| 2026-W37 | $35,162.89 | $6,557.34 | $12,565.15 | $54,285.38 | $54,285.38 |
| 2026-W38 | $37,223.16 | $6,774.35 | $15,445.38 | $59,442.89 | $59,442.89 |
| Both | $72,386.05 | $13,331.69 | $28,010.53 | $113,728.27 | $113,728.27 |

Posted disputed expense is included and flagged; aggregate matches do not constitute controller approval. Journal-period mapping, not service-start-date grouping, is used for the GL comparison. Detailed checks and mapping notes are in RECONCILIATION.json and ACCOUNTING_POLICIES.md.

## Not verified / not implemented

The 35-item master-brief test list is not claimed complete. Full bonus regular-rate recalculation, employer tax caps, all jurisdiction/alternative-workweek rules, task-level shared-cost attribution, exact contract billing leakage, approval workflows, historical as-of books and real multi-client isolation are not implemented. See FEATURE_MATRIX.md. No claim of comprehensive financial compliance or production readiness is made.

## Browser verification

Version 2.0 pages were rendered and reviewed in headless Chromium (Playwright) on Linux. Windows execution was not tested.
