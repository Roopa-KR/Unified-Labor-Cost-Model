# Calculation policies and assumptions — version 2.0

Version 2.0 keeps every version 1.0 rule below except item 8 (allocation), which now uses pay-tier-aware loaded rates. Section 16 describes the operator cost allocation added in 2.0.

1. **Financial basis:** recorded actual source expense. Payroll lines and employer-cost records are taken as supplied; agency invoices must have `posted_at`. A disputed invoice with a posting timestamp remains recorded expense and visible as a dispute. This does not imply approval. The $48.18 credit is signed; no extra employer burden is applied to agency rates.
2. **Money:** normalize each source financial amount to integer USD cents using Decimal and round-half-up. Allocation uses largest remainders on absolute cents, then restores the source sign. All child amounts sum exactly to their source event, including reversals.
3. **Period semantics:** payroll and employer expense use source `period_id`; agency expense uses the period containing `service_from`. Payroll period and service dates can differ for corrections. The UI calls the selector Accounting period, not a pure work-day or posting-date filter. These dataset-specific semantics reproduce supplied source period totals. An as-of posting cut and complete restatement accounting are not implemented.
4. **Payroll:** all signed posted lines are included once. REG represents straight time on all worked hours; OTP is premium-only as documented in pay_code. The app does not multiply OTP by 1.5 or add a second straight-time amount. It does not estimate taxes on top of the supplied employer-cost records. `cost_basis=allocated` employer expenses retain that qualification in source evidence.
5. **Corrections:** original, reversal and replacement rows remain separate source events. Source `adjusts_line_id` and the correction table provide lineage. No historical source row is overwritten.
6. **Time:** approved paid attendance is unioned per source worker/business date. WMS intervals are also unioned. Logged-paid is the intersection. Outside-paid is logged union duration minus that intersection. Timezone offsets are converted to UTC before subtraction. Business-date ownership is supplied; a generic shift-calendar/date-normalization engine is deferred.
7. **Classification:** source Tier B labor-event intervals are intersected with paid attendance and partitioned at all boundaries. One unique activity/class label is attributed. Multiple conflicting labels become conflict/unattributed; no label becomes unattributed. Supplied unexplained classes remain unexplained. Exact duplicate labels do not multiply time. Supplied direct classifications are operational evidence, not independently verified productive motion.
8. **Allocation (revised in 2.0):** each event spreads over its worker's paid time parts within `[service_from, service_to)`. Straight-time components (base wages, differentials, bonus, employer taxes, benefits, insurance, straight-time agency billing) spread by paid seconds. Overtime premiums (OTP; OTR on overtime and double-time hours) and the premium portion of agency OT billing go only to overtime/double-time seconds. If no overtime seconds exist in the window, the premium falls back to all paid time and is labeled `premium_fallback_paid_time_v2`. This is a cost attribution policy, not observed task cost. Paid leave and conversion fees remain unallocated. Missing driver time remains unallocated. No cost is discarded. Driver seconds repeat per component and must not be summed as hours; time_day is the denominator source.
9. **GL:** financial events are compared with posted expense accounts starting 6. The synthetic journal `JE-<period_code>` determines the GL comparison period; mixed service-date journal spans cannot safely identify a single period. Liability/clearing credits are excluded. The match is at aggregate period level only. GL rows never add another expense to the ledger.
10. **Task quantities:** one completed warehouse_task row is one completed line. Completed_qty is pieces. Open/cancelled tasks are excluded. Stable canonical source IDs are retained; rounded TI102ID is never used as a primary key. The supplied canonical task dataset is not independently reconstructed from raw WMS snapshots.
11. **Earned hours:** completed lines / units_per_hour for one effective, validated/approved standard with approved_by. Missing/ambiguous standards produce unavailable hours. The input standards were approved retrospectively. These are validated engineering hours, not authoritative finance savings. Multi-component seconds and engineered allowances are not applied.
12. **Budget bridge:** one budget version at a time. Baseline is source budget_amount, rounded to cents per row. Volume = `(actual lines - budget volume) × budget hours/unit × budget base rate`. Standard change = `(validated earned hours - actual lines × budget hours/unit) × budget base rate`. The residual is `actual - budget - volume - standard`. It deliberately retains efficiency, rate, other-pay, agency, burden, indirect, scope and interaction effects rather than inventing independent explanations.
13. **Customer attribution:** allocate activity dollars by completed-line share, using explicit task/order-line/order/customer links. Ambiguous customer links remain unassigned. Activities without completed output and unallocated site expense remain outside customer attribution. Billed revenue is signed billing_line.amount. Partial labor contribution = posted billing - attributed labor. It excludes unattributed cost, overhead, taxes on profit, penalties and quality costs; it is not profit.
14. **Missing inputs:** zero denominator returns unavailable, not zero dollars. No default financial rates are invented. The bundled source dictionaries and feature matrix identify feed dependencies. Client rules and approval are necessary before real deployment.
15. **Versioning:** file snapshots and calculation-run input-batch IDs/control results are preserved. Canonical tables are atomically recalculated. This is not a complete historical as-of ledger service. Failed normalization rolls back canonical changes; reporting is blocked if active sources are newer than the last completed calculation.

## Financial metric dictionary

| Metric | Formula / grain | Inclusion / limitation | Validation |
|---|---|---|---|
| Total labor expense | Sum event.cents / 100, accounting period | Wages + employer costs + posted agency net charges, including disputes | Independent source sums |
| Wage expense | Event sum where source=payroll_line | Signed base/premiums/bonus/leave/corrections | Pay code/source control |
| Employer expense | Event sum where source=employer_cost | Source actual and source allocated costs, separately labeled in evidence | Source control |
| Agency expense | Event sum where source=agency_invoice_line | Posted labor, fees and credits; no additional burden | Source control and signed credit test |
| Allocated activity cost | Sum allocation.cents by activity | Paid-time-share policy, retains explicit unallocated bucket | Parent-child exact-cent invariant |
| Paid hours | Union approved paid intervals / 3600 | Worker and business date | Interval and time conservation tests |
| Unattributed paid hours | Unlabeled/conflicting/unexplained slice seconds / 3600 | Attribution problem, not misconduct | Partition invariant |
| Cost per completed line | Total site expense / completed task count | Includes indirect and unallocated cost | Consistent numerator/denominator scope |
| Activity cost per line | Activity allocated cost / activity completed lines | Unavailable without output; no indirect respreading | Grouped conservation |
| Earned hours | Eligible completed lines / validated rate | Retrospective operational standard only | Deterministic task aggregation |
| Budget residual | Actual - baseline - volume - standard effects | Not independently diagnosed causes | Exact bridge closure |
| Partial customer labor contribution | Billed revenue - attributed activity labor | Not fully loaded contribution or net profit | Customer allocation + unassigned = site cost |

All financial amounts are USD. No accrued/estimated/forecast total is mixed into actual recorded expense. No realized savings metric is enabled.


## 16. Operator cost allocation (version 2.0)

**Goal.** Show where each operator's loaded labor cost is spent: productive work, unproductive time by cause and who controls it, and how work pace affects the cost of completed work. Wages are never raised or lowered because of pace.

**Loaded labor cost.** The posted source amounts linked to the operator: base wages, overtime premiums, differentials, bonus, meal premiums, paid leave, employer taxes (Social Security, Medicare, FUTA, SUTA), benefits (health, retirement), workers' compensation insurance and, for agency staff, net agency billing (which already includes agency burden and is not burdened again).

**Applicable loaded hourly rate.** Pay tiers are re-derived from approved paid attendance under the operator's assigned pay policy (California: daily overtime after 8 h, double time after 12 h, weekly overtime after 40 regular hours, seventh-day rule). The earliest paid seconds of a day are straight time. Straight-time loaded rate = cost on straight-time seconds ÷ straight-time hours. Overtime loaded rate = cost on overtime seconds ÷ overtime hours, so it carries the premium. Loaded labor cost = Σ tier hours × tier loaded rate + non-time items (paid leave, agency fees). This reconciles to the cent. Re-derived overtime hours are compared with posted payroll/agency OT hours as a control. In W37 they differ by 0.9 h and in W38 by 0.1 h. Posted payroll remains authoritative.

**Time partition.** Every approved paid second gets exactly one category:

| Category | Source evidence | Control group |
|---|---|---|
| Direct work | Login segments minus device idle (Tier A labor events) | Productive |
| Indirect tasks | QA, housekeeping, supervisor-directed reason codes | Productive (configurable) |
| Training | Training reason code | Planned / policy (configurable) |
| Authorized rest breaks | Rest allowance: rest minutes per 4 paid hours (CA 10 min), applied first to personal-break reason codes, then to unpunched paid time outside any login | Planned / policy |
| Paid leave | PTO pay lines (cost only, no worked time) | Planned / policy |
| Waiting: replenishment | Replenishment-request device events | Operational |
| Waiting: device or system | Idle or out-of-login time overlapping device-offline exceptions | Operational |
| Waiting: no work released | Idle while the logged work type had no released, uncompleted task | Operational |
| Waiting: equipment | Idle overlapping the equipment downtime log (**synthesized**, see below) | Operational |
| Work not performed | Direct-logged stretches longer than the no-output threshold (900 s) with no confirmed line. Supervisor-annotated stretches are operational; the rest have no established cause | Operational / Cause not established |
| Unscheduled break time | Personal-break time beyond the rest allowance | Operator-controlled |
| Excessive idle | Device idle with no reason entered after the prompt, longer than the threshold (300 s), and not explained by equipment, system or work availability | Operator-controlled |
| Short idle | Unexplained idle at or under the threshold | Cause not established |
| Slow-pace time | Direct hours beyond standard hours for the lines completed that day and work type (± tolerance) | Cause not established |
| Unaccounted paid time | Paid time outside any login after the rest allowance; conflicting classifications | Cause not established |
| Non-time charges | Agency conversion fee | Non-time |

Unpaid meals are outside paid time and carry no cost; their hours are reported. Only excess breaks and unresponsive idle are operator-controlled. Slow pace, unexplained gaps and unannotated no-output stretches are never assumed to be operator fault.

**Formulas.**
- Category cost = Σ allocated cents on that category's paid seconds (hours × applicable loaded rate, exact cents by largest remainder).
- Productive cost = Σ productive-category cost. Unproductive cost = loaded cost − productive cost − non-time charges.
- Utilization = productive hours ÷ paid hours. Pace = standard hours earned ÷ direct hours (direct + slow-pace).
- Standard hours = completed lines ÷ validated lines-per-hour standard. Standard cost = standard hours × the operator's straight-time loaded rate.
- Actual vs standard = actual direct cost (direct + slow-pace) − standard cost = pace effect ((direct hours − standard hours) × straight-time rate) + overtime and rate mix (remainder).
- Cost per line / piece / order = loaded cost ÷ completed lines / pieces / distinct warehouse orders (unavailable when the denominator is zero).
- Site bridge: standard cost of completed lines → pace (net) → overtime and rate mix → indirect → policy time → operational delays → operator-controlled → cause not established → non-time charges = total loaded cost. It closes exactly.

**Orders.** A worker-day-work-type's direct cost is split across the warehouse orders worked, by elapsed time on each order (task_worker start/complete, clipped to direct time). Concurrent orders share elapsed time equally. Direct time between orders stays as its own row, so no hour or dollar is counted twice.

**Synthesized data.** No equipment downtime log was supplied. A deterministic log (64 rows) is generated from source idle events in equipment-dependent work types (pallet jack, cooler door, RF scanner). It is stored as its own snapshot (namespace `supplement`, `data_origin = gini_synthesized`) and labeled wherever it appears. It moves 8.0 h ($241) from idle to waiting for equipment, and it can be switched off in Cost policy. Every other figure uses supplied source data.

**Configuration.** Cost policy (Finance) holds the rest allowance, idle and no-output thresholds, pace tolerance, whether indirect and training count as productive, the synthesized-equipment switch and the flag thresholds. Saving recalculates everything, in about 10–15 seconds. The policy signature is stored with each calculation run, and reporting is blocked if the policy and the last calculation differ.

**Results (all periods).** Loaded cost $113,728.27 = productive $90,388.40 + unproductive time $20,053.47 + non-time $3,286.40. By control: planned/policy $5,419.50, operational $3,703.69, operator-controlled $925.98, cause not established $10,004.30. Paid 3,870.5 h, utilization 82.6%, pace 99.2%, standard cost of completed lines $86,690.86.
