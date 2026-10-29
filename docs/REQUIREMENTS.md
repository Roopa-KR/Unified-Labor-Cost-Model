# MASTER DEVELOPMENT PROMPT
# GiNi Unified Labor Economics — Core Ledger & Labor Cost Intelligence

## 1. Your role and objective

Act as a senior Python software architect, warehouse management systems expert, US labor-cost accounting specialist, payroll and workforce analytics engineer, data architect, financial controller, and enterprise dashboard developer.

Your responsibility is to **design, implement, test, and deliver a fully working Python application** containing two interconnected products:

1. **GiNi Core Ledger — What did labor really cost?**
2. **GiNi Labor Cost Intelligence — Why did labor cost change, what should it have cost, and where are the financial improvement opportunities?**

The system must transform warehouse operational data, time-clock records, employee payroll, employer expenses, staffing-agency invoices, financial budgets, and relevant customer billing records into one consistent, transparent, auditable model of labor economics.

The core product promise is:

**Every paid hour must be explained. Every dollar must be categorized. Every allocated cost must be traceable. Every reported financial variance must be reconcilable. Every recommended saving must be clearly distinguished from actual realized financial benefit.**

This is intended to become a commercial, multi-client warehouse labor intelligence product that GiNi can deploy for US warehouse customers.

Do not build a superficial analytics demo with attractive charts but fabricated financial insights. Build the underlying accounting logic, transaction lineage, financial calculations, reconciliation engine, analysis services, and user interface correctly.

The application will later integrate a Gemini AI chatbot. Prepare a secure semantic and tool-based integration layer, but **all numerical calculations must be implemented and validated in deterministic Python/SQL code, independently of any language model**.

---

## 2. Mandatory input files and investigation

I am uploading a ZIP file named:

`GiNi_Synthetic_Data_by_Product (1).zip`

I am also uploading the presentation:

`GiNi_Products (1) (1).pptx`

If available, additionally use:

`Unified_Labor_Cost_Model_Feature_Blueprint.docx`

Study the actual file contents, not just the filenames.

The ZIP contains a synthetic warehouse environment with multiple interrelated datasets, data dictionaries, client data requests, financial workbooks, governance structures, and generation scripts.

Important workbooks:

### Shared foundation

`00_Shared_Foundation/00_GiNi_Foundation.xlsx`

Review its tables, including:

- `site`, `zone`, `location`, `activity`, `activity_mapping`
- `worker`, `worker_identity`, `employment`, `cost_center`, `agency`
- `source_system`, `ingestion_run`, `raw_record`
- `metric_definition`, `data_quality_issue`, `lineage_edge`
- `access_grant`, `audit_event`, `retention_policy`

`00_Shared_Foundation/01_GiNi_Raw_Source_Extracts.xlsx`

Review:

- `D101S1H`
- `LM005S1_snapshots_0907`
- `TI102H`
- `TI102_open_final`
- `TI102_snapshots_0907`
- `TI102X0`
- `M150`
- `M123`
- `M123T`
- `RESOURCE_MASTER`
- `order_release`
- `replenishment`

### Product 1 — operational labor ledger

`P1_Labor_Ledger/02_P1_Labor_Ledger_TierA_Operational.xlsx`

Review:

- `work_segment`
- `warehouse_task`
- `task_worker`
- `device_event`
- `labor_event`
- `standard`
- `standard_calibration`
- `operational_exception`
- `out_productivity_daily`
- `out_hourly_worktype`
- `out_readiness_gates`

### Product 1 — financial ledger

`P1_Labor_Ledger/03_P1_Labor_Ledger_TierB_Financial.xlsx`

Review:

- `time_punch`, `attendance_interval`, `shift`, `schedule`
- `labor_event`
- `pay_code`, `pay_policy`, `pay_policy_assignment`
- `payroll_period`, `payroll_line`, `payroll_correction_log`
- `employer_cost`, `worker_rate`, `tax_opening_balance`
- `agency_rate`, `agency_invoice_line`
- `labor_rate_assumption`
- `cost_event`, `cost_allocation`, `reconciliation`
- `gl_entry`, `cost_gl_link`
- `out_paid_vs_logged_daily`, `out_cost_by_category`

### Product 2 — cost intelligence

`P2_Cost_Intelligence/04_P2_Cost_Intelligence.xlsx`

Review:

- `standard`, `standard_component`, `task_standard_evaluation`
- `budget`, `activity_cost_view`
- `variance_result`, `out_variance_bridge`
- `customer`, `order_header`, `order_line`, `task_order_line`
- `material`, `uom_conversion`
- `contract_rate`, `billing_line`, `out_billing_leakage`
- `quality_event`, `sla_rule`, `shipment`, `shipment_order`
- `cost_allocation_customer`, `out_cost_to_serve`

### Future chatbot integration

`Platform_Copilot_Integration/08_Platform_Copilot_Integration.xlsx`

Study:

- `tool_catalog`
- `semantic_layer`
- `role_tool_policy`
- `guardrail_rule`
- `copilot_session`, `copilot_turn`
- `copilot_tool_call`, `copilot_answer`
- `eval_golden_set`, `eval_result`
- `connector_health`

Use these as inputs for planning the future Gemini integration. Do not assume their existence means an operational chatbot has already been implemented.

### Important dataset rules

The supplied dataset is fictional. Clearly mark its financial results as **Synthetic Demonstration Data**.

The ZIP describes one US-California distribution center with 40 workers and two closed weekly payroll periods. Confirm its actual scope before coding.

The `Test_Truth_NOT_FOR_PRODUCT` folder is intended for independent testing and must not be loaded into application dashboards, customer metrics, or Gemini's accessible dataset.

Keep restricted employee PII separated from operational and financial analysis.

Do not assume the ZIP regeneration scripts are executable without their original dependencies. Inspect them, identify missing dependencies such as the original synthetic generator, and make the application work directly from the supplied workbooks even if regeneration cannot run.

Before implementing business logic:

1. Inventory every relevant workbook and worksheet.
2. Extract the data dictionary and observed column types.
3. Identify primary keys and relationships.
4. Establish the grain of every table.
5. Identify record-version and correction semantics.
6. Identify duplicate or overlapping data.
7. Identify missing financial information.
8. Identify assumptions and unvalidated standards.
9. Identify existing derived outputs that can be independently reproduced.
10. Produce a source-to-canonical data mapping.

Preserve source identifiers and raw records. Do not fabricate missing financial inputs.

---

## 3. Product architecture and technology

Use a Python-first architecture.

Recommended stack:

- Python 3.11 or 3.12.
- FastAPI for backend services.
- Streamlit for the main customer-facing dashboard.
- Plotly for interactive financial charts.
- SQLAlchemy and Alembic for application database models and migrations.
- PostgreSQL for production metadata and transactional storage, with SQLite as a simple local demonstration fallback.
- DuckDB and Parquet for efficient analytical queries across large warehouse datasets.
- Polars, PyArrow, and memory-efficient spreadsheet ingestion where appropriate.
- Pydantic for validation and API schemas.
- `Decimal` or equivalent exact decimal handling for money.
- pytest for automated verification.
- `google-genai` for a future optional Gemini integration.

Choose mature libraries with compatible versions and verify compatibility.

**Do not require Node.js, MongoDB, or unnecessary infrastructure simply to run the local application.**

Use a modular architecture with at least the following logical layers:

1. Source connectors and ingestion.
2. Raw immutable source storage.
3. Canonical operational data.
4. Canonical financial data.
5. Labor-time classification.
6. Cost-event creation.
7. Cost allocation.
8. Financial reconciliation.
9. Standards and earned-cost calculations.
10. Cost intelligence and variance analysis.
11. Reporting and visualization.
12. Approved financial-query tools for Gemini.
13. Authentication, authorization, lineage, and auditing.

Separate calculation logic from Streamlit UI code.

The application must support repeatable ingestion and recalculation without duplicating costs or changing historical results silently.

---

# PART A — CORE LEDGER

## 4. Core Ledger's primary purpose

The Core Ledger must answer:

**How much did this warehouse spend on labor, what created that expense, when was it incurred, which operator and activity is associated with it, and where is the supporting financial record?**

Users must be able to begin at the warehouse-level labor expense and drill down to:

Warehouse → Date/Period → Cost Center → Work Type → Operator → Labor Category → Cost Component → Cost Event → Original Source Record.

For directly attributable work, also support task-level and order-level drilldowns.

The Core Ledger must not be a simple summary table. It must provide a complete itemized view of labor cost, time, transactions, allocations, adjustments, and financial evidence.

### Ledger views

Build at least:

- Warehouse labor-cost overview.
- Daily ledger.
- Weekly ledger.
- Payroll-period ledger.
- Monthly ledger.
- Operator financial ledger.
- Work-type financial ledger.
- Cost-center ledger.
- Direct versus indirect labor ledger.
- Agency labor ledger.
- Payroll-components ledger.
- Employer-expenses ledger.
- Unallocated and unreconciled cost ledger.
- Financial adjustments and corrections ledger.
- GL reconciliation ledger.
- Source-record explorer.

Every view must reconcile to the same approved total for a given cost basis, period, and scope.

---

## 5. Maintain complete financial separation

Do not combine all labor expenses into one unexplained hourly rate.

Create explicit financial categories.

### A. Permanent employee earnings

Track separately:

- Regular straight-time earnings.
- Overtime straight-time portion.
- Overtime premium.
- Double-time straight-time portion.
- Double-time additional premium.
- Shift differentials.
- Night and weekend differentials where contractually applicable.
- Holiday pay.
- Paid leave.
- Sick leave and PTO where recognized.
- Paid break time.
- Training pay.
- Nondiscretionary bonuses.
- Discretionary bonuses.
- Incentive compensation.
- Meal/rest-period premiums where applicable.
- Retroactive payroll adjustments.
- Payroll corrections and reversals.
- Other posted employer wage expenses.

Do not add overtime full-pay amounts on top of straight-time amounts that already include the same hours. Normalize source pay-code treatments first.

### B. Employer-side labor expenses

Separate:

- Employer Social Security.
- Employer Medicare.
- Federal unemployment insurance.
- State unemployment insurance.
- Workers' compensation insurance.
- Employer-paid healthcare.
- Retirement contributions.
- Other employer benefits.
- Contractual benefits.
- Other employer-paid labor expenses.

Use actual client employer-cost records whenever available.

Estimated burden is allowed only in explicitly marked modeled or accrued views.

Do not treat employee tax withholding as an additional employer expense.

Employer payroll taxes and wage caps must follow effective-dated jurisdictional and client-specific rules.

### C. Temporary and staffing-agency labor

Separate:

- Regular agency billings.
- Agency overtime charges.
- Agency double-time charges.
- Agency markups.
- Agency administration fees.
- Minimum-shift charges.
- Conversion fees.
- Other approved contract charges.
- Invoice adjustments.
- Invoice credits.
- Disputed or pending invoices.

A staffing agency's billed amount generally represents the warehouse customer's cost for that labor service. Do not additionally apply employee payroll burdens already included in the contract bill rate.

If the agency's internal wages are known, they may be analyzed separately but must not be added again to warehouse labor expense.

### D. Other costs

Allow configuration for:

- Training costs.
- Recruiting and onboarding costs.
- Labor-related equipment expenses.
- Safety-related expenses.
- Temporary labor mobilization expenses.
- Allocated operational overhead.
- Other client-approved indirect expenses.

Separate labor expenses from wider operating costs and overhead.

Show a definition for each component so customers know what is included or excluded.

---

## 6. Build multiple financial cost books

Maintain distinct reporting bases.

**Actual posted:** Financial transactions already posted by payroll, agency billing, or the approved accounting system.

**Accrued:** Costs economically attributable to the service period but not yet finally posted.

**Estimated:** Costs modeled from rates, hours, and assumptions before actual financial transactions are received.

**Budget:** The approved plan for the selected scope and budget version.

**Standard or earned:** The approved benchmark cost of completed workload.

**Forecast:** Expected future expense based on workload and staffing assumptions.

Never silently mix these categories.

The customer must always know whether a displayed dollar amount represents actual, accrued, estimated, budgeted, or forecast cost.

Distinguish:

- Service date.
- Work date.
- Payroll earned period.
- Payroll posting date.
- Invoice date.
- GL posting date.
- Data ingestion date.
- Reporting as-of date.

Support late adjustments without rewriting closed historical source records.

Use versioned recalculations, restatement records, or reversal-and-replacement records.

---

## 7. Time accounting and activity classification

Build an interval-based labor-time engine.

Use:

- Actual time punches.
- Approved attendance intervals.
- GiNi work-type login segments.
- Device activity events.
- Work assignments.
- Breaks and meals.
- Training events.
- Indirect-work classifications.
- Schedule information.

The system must distinguish:

1. Paid time.
2. Worked time.
3. Logged WMS time.
4. Direct productive work.
5. Indirect operational work.
6. Paid breaks.
7. Unpaid meals.
8. Training time.
9. Authorized waiting time.
10. System downtime.
11. Idle or interrupted time with recorded reason.
12. Unexplained logged time.
13. Paid time not attributable to an activity.
14. WMS activity outside recorded paid intervals.
15. Overlapping or invalid time records.
16. Unmapped worker time.

Use correct interval arithmetic with timestamp normalization and timezone awareness.

Handle overnight shifts and daylight-saving transitions.

Never sum overlapping intervals blindly.

Important formulas:

`Paid Hours = union of approved paid attendance intervals, measured in hours`

`Logged Paid Hours = intersection of WMS logged intervals and approved paid attendance intervals`

`Unattributed Paid Hours = Paid Hours - sum of mutually exclusive attributed paid categories`

`Logged Outside Paid Hours = WMS logged interval duration outside approved paid attendance intervals`

`Direct Productivity = Completed Eligible Units / Direct Work Hours`

`Paid-Hour Productivity = Completed Eligible Units / Paid Hours`

All denominators must be named and consistent.

If available information does not explain a time interval, mark it as unattributed or under investigation, rather than automatically classifying it as unproductive employee behavior.

Build a timeline visualization where a supervisor or finance analyst can see a complete operator day with paid periods, work sessions, breaks, indirect activities, gaps, and recorded reasons.

---

## 8. Operator-level labor economics

Every operator must have an explainable financial profile.

Calculate:

- Total paid hours.
- Total worked hours.
- Regular hours.
- Overtime hours.
- Double-time hours.
- Direct hours.
- Indirect hours.
- Break and training hours.
- Unattributed paid hours.
- Total posted wage expense.
- Employer burden.
- Total loaded cost.
- Agency-billed cost, when applicable.
- Loaded cost per paid hour.
- Direct-work allocated cost.
- Indirect-work allocated cost.
- Cost per completed work unit.
- Earned hours.
- Earned cost.
- Actual versus earned cost variance.
- Task-level attributed expense.
- Operator contribution to customer/service work where defensibly measured.
- Data-quality and reconciliation status.

Use:

`Loaded Labor Cost = Employer Wage Expense + Employer Burden + Other Included Employer Labor Expenses`

For agency staff:

`Agency Labor Cost = Approved Net Agency Service Charges + Separately Billable Nonduplicated Agency Expenses`

`Loaded Cost Per Paid Hour = Total Loaded Labor Cost / Paid Hours`

`Labor Cost Per Line = Allocated Labor Cost / Completed Eligible Lines`

`Labor Cost Per Order = Allocated Labor Cost / Completed Eligible Orders`

`Labor Cost Per Piece = Allocated Labor Cost / Completed Eligible Pieces`

Use `null / unavailable` when a denominator is zero or missing. Do not invent a zero-dollar cost.

For operators who perform different work types, separately calculate costs and quantities for each activity.

Clearly distinguish operator-level allocated costs from the operator's total payroll expense.

Do not present allocated revenue as personal employee profit without a defensible attribution policy.

---

## 9. Payroll and overtime reconciliation

Build a configurable pay-policy engine.

Read the existing `pay_policy`, `pay_code`, `pay_policy_assignment`, and payroll records.

Support jurisdiction-specific, effective-dated rules.

At minimum, the demonstration must correctly model:

- Federal weekly overtime principles for covered nonexempt employees.
- California daily overtime.
- California daily double time.
- California seventh-day provisions where applicable.
- Different overtime treatment for qualifying exempt classifications.
- Bonuses that require regular-rate adjustments.
- Shift differentials.
- Paid leave excluded from worked hours where applicable.
- Retroactive payroll corrections.
- Effective-dated rate changes.

Use payroll posted amounts as the authoritative source of historical wage expense.

Use the pay-policy engine to generate independent expected-pay checks and to identify potential exceptions; do not automatically replace the client's official payroll figures.

Build:

- Timeclock-to-payroll hours reconciliation.
- Pay-code reconciliation.
- Expected versus posted overtime expense.
- Premium reconciliation.
- Employer burden reconciliation.
- Payroll corrections history.

Flag policy exceptions for payroll specialists rather than automatically declaring a legal violation.

---

## 10. Financial event ledger

Build a canonical, append-only financial event ledger.

Every cost event should contain, as applicable:

- Event ID.
- Source system.
- Source file/table.
- Original source key.
- Original row or transaction reference.
- Worker ID.
- Site ID.
- Cost-center ID.
- Payroll or agency period.
- Cost-book classification.
- Financial component.
- Employment type.
- Event currency.
- Original transaction amount.
- Signed normalized amount.
- Service period.
- Posting date.
- Adjustment reference.
- Source record version.
- Calculation version.
- Import batch ID.
- Record quality status.
- Reconciliation status.
- Created timestamp.

Use signed adjustments, reversal links, and valid record versions.

Make ingestion idempotent.

Prevent the same payroll or agency invoice line from entering the financial book twice.

Distinguish the analytical cost-event ledger from general ledger debit/credit journal entries.

Do not sum both the cost-event ledger and GL expense entries as though they are independent expenses.

---

## 11. Activity-based cost allocation

Connect financial expenses to actual warehouse work.

Support allocation from cost events to:

- Operator.
- Shift.
- Activity/work type.
- Zone.
- Warehouse.
- Cost center.
- Work assignment.
- Task.
- Order.
- Customer, where appropriate.

Create configurable allocation methods:

1. Direct observed task time.
2. Direct activity time share.
3. Paid direct-work time share.
4. Paid-time share.
5. Completed lines or units.
6. Earned standard hours.
7. Order-specific task participation.
8. Approved overhead absorption.
9. Unallocated pending investigation.

Every allocation must record the method and input drivers.

If several workers contribute to one order, ensure cost is allocated according to documented participation rather than duplicating the full order cost against each worker.

Required control:

`Sum of Allocated Amounts + Unallocated Amount = Original Cost Event Amount`

The same requirement applies to quantities and attributable hours wherever these are allocated.

Calculate residuals and flag any allocation that does not reconcile within a documented rounding tolerance.

Use exact monetary calculations and controlled rounding so child amounts sum to the parent amount.

---

## 12. Full financial reconciliation

Build automated reconciliation across all major financial sources.

Required checks:

### Labor-time reconciliation

`Paid Hours = Classified Paid Hours + Unattributed Paid Hours`

Reconcile worked hours to the correct payroll basis separately.

### Payroll reconciliation

`Posted Payroll Expense = Sum of Included Normalized Payroll Cost Events`

### Employer-expense reconciliation

`Posted Employer Costs = Sum of Employer-Cost Events`

### Agency reconciliation

`Net Approved Agency Invoice Amount = Sum of Agency Cost Events`

Account for credits, disputes, adjustments, and invoice statuses correctly.

### Total expense reconciliation

`Loaded Labor Cost = Wage Expense + Employer Expenses + Net Agency Labor Cost + Other Approved Nonduplicated Labor Expenses`

### Allocation reconciliation

`Total Cost Events = Allocated Cost + Unallocated Cost`

### General ledger reconciliation

Reconcile expense subledger totals to GL expense postings based on documented account, cost-center, service-period, and posting-date mappings.

Account for timing differences, accruals, reversals, clearing accounts, and cutoff policies.

Do not assume bank payments and expense recognition occur on the same date.

Provide a reconciliation dashboard with:

- Source total.
- Ledger total.
- Matched amount.
- Difference.
- Explained difference.
- Unexplained difference.
- Status.
- Responsible reviewer.
- Evidence.
- Approval date.

Prevent a period from appearing "fully reconciled" while material unresolved differences remain.

---

# PART B — LABOR COST INTELLIGENCE

## 13. Cost Intelligence's primary purpose

The second product must answer:

**Why did labor cost increase or decrease, what should this workload have cost, where is the financial leakage, and what operational decisions could improve cost efficiency or contribution?**

The intelligence layer must consume approved ledger results and operational standards.

Do not duplicate or independently redefine financial totals within this product.

---

## 14. Standards and earned labor economics

Build separate support for:

- Original WMS standards.
- Unvalidated standards.
- Calibrated standards.
- Finance-approved standards.
- Versioned engineered standards.
- Task-level calculated standard hours.
- Standard labor rates.
- Standard cost.

The supplied synthetic dataset contains original M150 rates and separately calibrated standards. Do not automatically use the original rates for financial conclusions.

Required formulas:

`Earned Hours = Sum of Approved Standard Hours for Completed Eligible Work`

For a simple validated units-per-hour standard:

`Earned Hours = Completed Eligible Units / Approved Units Per Hour`

For multi-component standards:

`Task Earned Seconds = Fixed Time + Sum(Quantity Driver × Approved Component Seconds) + Applicable Approved Allowances`

Document whether travel, indirect allowances, and other components are already included.

`Earned Labor Cost = Earned Hours × Approved Standard Cost Rate`

`Direct Hour Variance = Actual Direct Hours - Earned Hours`

`Direct Efficiency Cost Variance = Direct Hour Variance × Comparable Standard Labor Rate`

Clearly indicate positive-unfavorable and negative-favorable conventions.

Do not calculate labor savings twice from both earned-hour variance and productivity-rate variance.

Provide standard-version comparisons and validation-status indicators.

---

## 15. Complete cost metrics

Implement the following financial metrics, subject to data readiness.

### Labor expense metrics

- Total actual labor cost.
- Permanent labor cost.
- Agency labor cost.
- Total wage expense.
- Employer payroll burden.
- Overtime premium expense.
- Double-time premium expense.
- Shift differential expense.
- Paid-leave expense.
- Training labor expense.
- Indirect labor expense.
- Unattributed labor cost.
- Loaded hourly cost.
- Agency premium over comparable eligible staffing alternatives.
- Cost per paid hour.
- Cost per productive hour.
- Cost per earned hour.

### Productivity and efficiency metrics

- Completed lines.
- Completed orders.
- Completed pieces.
- Completed cases.
- Paid hours per 100 lines.
- Direct hours per 100 lines.
- Actual lines per direct hour.
- Actual lines per paid hour.
- Approved standard rate.
- Earned hours.
- Efficiency attainment.
- Workload-adjusted productivity variance.
- Cost per earned hour.
- Cost per unit versus approved baseline.

### Cost-to-serve metrics

- Cost per order.
- Cost per picking line.
- Cost per shipped piece.
- Cost per case.
- Cost per work type.
- Cost per warehouse zone.
- Cost per customer.
- Cost per shipment.
- Cost per order complexity group.
- Cost per activity unit.
- Fully allocated cost-to-serve, where data is available.

Always identify which expense components are included in each measure.

### Financial performance metrics

- Budget labor cost.
- Actual labor cost.
- Variance in dollars.
- Variance percentage.
- Earned cost.
- Efficiency variance.
- Volume variance.
- Workload mix variance.
- Wage-rate variance.
- Overtime-premium variance.
- Agency-cost variance.
- Indirect labor variance.
- Unattributed cost variance.
- Employer burden variance.
- Other-pay variance.
- Unexplained variance residual.

### Revenue-related metrics

Only where actual billing/contract data exists:

- Billable activity value.
- Billed revenue.
- Unbilled eligible work.
- Contract-rate variance.
- Billing leakage.
- Labor cost as a percentage of billed revenue.
- Contribution after attributable labor costs.
- Customer labor contribution.
- Customer cost-to-serve variance.
- Contractual SLA penalty exposure.
- Confirmed penalties and credits.
- Quality-related financial adjustments.

A labor contribution margin is not equivalent to net profit.

---

## 16. Budget-to-actual financial variance bridge

Create an interactive dollar waterfall that shows the financial causes of budget deviations.

Use the decomposition present in `out_variance_bridge` as a reference, but independently validate the equations.

Support:

- Budget baseline.
- Volume impact.
- Workload mix and standard impact.
- Direct efficiency impact.
- Indirect and unattributed time impact.
- Wage-rate impact.
- Agency premium.
- Overtime premium.
- Other pay and leave.
- Employer burden.
- Actual result.

The waterfall must reconcile exactly:

`Budget Cost + Sum of Mutually Exclusive Variance Components = Actual Cost`

The precise decomposition must be defined using a consistent sequence of counterfactual calculations to avoid interaction and double-counting errors.

If another decomposition is selected, document it and implement a residual/interaction component when necessary.

For every variance show:

- Dollar amount.
- Favorable or unfavorable.
- Percent of total variance.
- Affected activity.
- Affected operator group when appropriate.
- Exact calculation method.
- Underlying source records.
- Suggested questions for further investigation.

Example illustrative bridge:

Budget $100,000

Volume +$8,000

Mix +$3,000

Rate +$2,000

Overtime +$4,000

Efficiency −$3,000

Indirect +$5,000

Actual $119,000

Every number must be derived from data, not copied from the example.

---

## 17. Actual versus expected cost analysis

Show what the completed workload was expected to cost under approved standards.

For every work type:

- Completed work.
- Earned hours.
- Actual direct hours.
- Actual indirect hours.
- Actual allocated expense.
- Earned baseline expense.
- Actual versus earned variance.
- Cost per unit.
- Cost per unit trend.
- Difference from budget.
- Sources of the difference.

Enable comparison by:

- Day.
- Week.
- Payroll period.
- Shift.
- Warehouse.
- Zone.
- Activity.
- Customer.
- Employment type.
- Cost center.

Separate changes caused by rates, workload mix, direct efficiency, indirect time, and missing attribution.

Do not imply that all favorable standard variances are realized financial savings.

---

## 18. Identify operational financial leakage

Build an explainable financial exception engine.

Detect at least:

1. High indirect labor expense.
2. Unattributed paid hours.
3. WMS logged time outside paid intervals.
4. Incorrect or missing worker identities.
5. Duplicate payroll source records.
6. Duplicate agency invoice lines.
7. Inconsistent agency rates.
8. Incorrect pay-code mapping.
9. Unexpected overtime premiums.
10. Payroll corrections to closed periods.
11. Unallocated financial costs.
12. Missing employer expense data.
13. Missing GL links.
14. Cost-allocation reconciliation failures.
15. Original WMS standard versus approved standard inconsistencies.
16. Activity cost per unit above baseline.
17. Cost per order substantially above comparable workloads.
18. Increased time spent in indirect categories.
19. Unexplained shifts in rate mix.
20. Agency invoice credits or disputes not reflected in net expense.
21. Apparent unbilled eligible service activity.
22. Contract-rate mismatches.
23. Duplicated billable units.
24. Unusual customer cost-to-serve changes.
25. Material time gaps requiring investigation.
26. Financial data arriving later than its expected cadence.
27. Incomplete or stale payroll periods.
28. Unsupported assumptions used in financial KPIs.

Each alert must contain:

- Alert category.
- Severity.
- Affected scope.
- Amount at issue.
- Financial classification.
- Calculation method.
- Supporting evidence.
- Confidence or readiness.
- Responsible reviewer.
- Action status.

An alert's amount at issue is not necessarily a recoverable cash saving.

Do not frame ambiguous time records as proof of worker misconduct.

---

## 19. Customer and activity profitability analysis

Support two warehouse operating models.

### Internal warehouse

Focus on:

- Actual labor expense.
- Budget variance.
- Cost per order.
- Cost per line.
- Cost to serve.
- Cost reduction opportunities.
- Capacity made available.
- Confirmed cost avoidance.

Do not assign fictional revenue to internal tasks simply to calculate operator profit.

### Third-party logistics warehouse

Where real contract and billing data is available, support:

`Labor Contribution = Attributable Service Revenue - Attributable Labor Cost`

For a broader contribution metric:

`Service Contribution = Attributable Revenue - Attributable Labor and Other Approved Variable/Direct Costs`

Calculate margin with a clearly defined denominator.

Use:

- `customer`
- `contract_rate`
- `billing_line`
- `order_header`
- `order_line`
- `task_order_line`
- `cost_allocation_customer`

Develop:

- Customer cost-to-serve.
- Customer labor contribution.
- Activity contribution.
- Revenue per order/line.
- Actual billing versus expected contractual billing.
- Financially expensive customer service patterns.
- Quality/rework cost where supported.
- SLA penalty exposure versus actual booked penalty.

The customer should be able to drill from contribution margin to labor and billing evidence.

---

## 20. Financial opportunities and realized savings

A customer must be able to distinguish:

**Measured historical expense:** Actual financial cost already recorded.

**Modeled opportunity:** Estimated avoidable cost based on a counterfactual or improvement scenario.

**Verified operational improvement:** An observed improvement relative to an approved comparable baseline.

**Realized financial saving:** A validated reduction in eligible expense or a documented improvement in contribution, supported by financial evidence.

Implement calculations such as:

`Opportunity = Comparable Baseline Cost - Modeled Improved Cost`

`Verified Efficiency Benefit = Adjusted Baseline Cost - Actual Comparable Cost`

`Realized Cost Saving = Approved Adjusted Financial Baseline - Eligible Actual Financial Cost`

The realized calculation must control for changes in workload, mix, staffing, rates, volume, scope, and other relevant factors, and must be supported by the client-approved measurement policy.

Freed labor hours must not automatically be converted into cash savings.

A freed hour could:

- Reduce scheduled hours.
- Avoid overtime.
- Avoid agency hours.
- Be reassigned to other work.
- Remain paid but unused.

Only report actual financial benefit when supported by a defensible mechanism.

Avoid reporting overlapping savings from the same time reduction.

Include a savings evidence status even if the full separate Savings Verification product is reserved for a later phase.

---

# PART C — CUSTOMER INSIGHTS AND USER EXPERIENCE

## 21. Dashboard 1 — Financial Executive Overview

Build an executive dashboard containing:

- Total labor cost.
- Cost by period.
- Actual versus budget.
- Permanent versus agency spend.
- Direct versus indirect spend.
- Overtime and burden components.
- Cost per order.
- Cost per line.
- Earned versus actual cost.
- Financial variance.
- Unattributed cost.
- Reconciliation status.
- Major financial exceptions.

Charts:

- Labor cost trend.
- Cost-component composition.
- Budget versus actual waterfall.
- Cost by work type.
- Cost by employment type.
- Cost per unit over time.
- Major expense drivers.

Every dollar card must show its cost basis and selected period.

---

## 22. Dashboard 2 — Core Ledger Explorer

Build an interactive transactional ledger.

Required columns:

- Service date.
- Posting date.
- Operator.
- Employment type.
- Activity.
- Labor class.
- Cost component.
- Hours.
- Source amount.
- Allocated amount.
- Currency.
- Source system.
- Financial book.
- Reconciliation status.
- Source reference.

Functions:

- Search.
- Filter.
- Sort.
- Group.
- Drill down.
- Export.
- View source evidence.
- View adjustments.
- Trace original transaction.
- Recalculate totals for the selected scope.

Users must be able to reproduce a displayed total by summing the visible underlying ledger entries at the appropriate grain.

---

## 23. Dashboard 3 — One Paid Day Explained

Create a detailed operator-day investigation screen.

For example, show:

- Direct work: 7 hours.
- Indirect work: 0.5 hours.
- Paid break: 0.5 hours.
- Total paid: 8 hours.
- Base rate: $20/hour.
- Wages: $160.
- Employer burden: $32.
- Loaded labor cost: $192.

This is an illustrative case only.

The actual screen must calculate every category and amount from source data.

Visualizations:

- Paid-time timeline.
- Direct/indirect/break composition.
- Financial component breakdown.
- Source punches.
- Work sessions.
- Work completed.
- Unattributed intervals.
- Ledger entries.
- Reconciliation evidence.

Allow the customer to understand the operator's entire day from both an operational and financial perspective.

---

## 24. Dashboard 4 — Cost Intelligence

Build:

- Actual versus earned cost.
- Cost per activity.
- Expense-driver waterfall.
- Cost trend by activity.
- Period-over-period changes.
- High-cost work types.
- Efficiency-cost variation.
- Indirect and unattributed cost trends.
- Operator/task cost comparisons where valid.

Insights must explain whether a cost increase came from more work, a different mix of work, higher hourly expense, overtime, agency premiums, or additional time.

Avoid simplistic assumptions that high payroll expenses imply poor performance.

---

## 25. Dashboard 5 — Operator Financial Analysis

Show an operator profile containing:

- Paid and worked hours.
- Direct and indirect time.
- Actual cost.
- Loaded hourly cost.
- Cost by activity.
- Units completed.
- Earned hours.
- Cost per completed unit.
- Quality-related expense where supported.
- Recent cost trends.
- Comparable standard performance.
- Financial variance.

Provide an explanatory note for workload complexity, incomplete activity attribution, and unavailable financial inputs.

Do not create punitive rankings based on unexplained productivity differences.

---

## 26. Dashboard 6 — Work-Type Economics

For Prescription, OTC, Vault, Cage, Cooler, Cases, and any other configured work type, display:

- Paid and direct hours.
- Labor cost.
- Completed units.
- Standard earned hours.
- Actual cost per line/piece/order.
- Target cost per unit.
- Direct efficiency variance.
- Indirect allocation.
- Overtime and agency mix.
- Historical trend.
- Exceptions and contributing factors.

Use flexible activity names and source mappings so the product supports other warehouses without rewriting code.

---

## 27. Dashboard 7 — Payroll, Agency and Expense Reconciliation

Separate tabs for:

- Payroll.
- Employer expenses.
- Agency invoices.
- Cost allocations.
- GL.
- Reconciling items.
- Corrections and reversals.

Use status indicators such as:

- Matched.
- Matched with approved timing difference.
- Partially matched.
- Unmatched.
- Awaiting source.
- Needs review.
- Reconciled and approved.

Show exact unmatched dollars and supporting transactions.

---

## 28. Dashboard 8 — Missing Time and Financial Attribution

Show:

- Paid hours.
- WMS logged hours.
- Matched logged-paid hours.
- Direct hours.
- Indirect hours.
- Paid breaks.
- Unattributed paid hours.
- WMS time outside paid intervals.
- Financial value of unattributed paid time.

Show operational observations and financial expense as different measures.

Provide reasons, timestamps, and drilldowns.

Missing time should be treated as a classification/reconciliation problem first, not automatically a productivity-loss conclusion.

---

## 29. Dashboard 9 — Customer Cost-to-Serve

Where data is available, display:

- Customer activity volume.
- Allocated labor cost.
- Cost per order.
- Cost per line.
- Billed revenue.
- Contractually billable value.
- Billing leakage.
- Labor contribution.
- Penalties/credits.
- Quality-related adjustments.
- Margin trends.

If the warehouse is not a 3PL or customer billing data is absent, disable revenue-dependent metrics and explain why.

---

## 30. Dashboard 10 — Financial Exceptions and Investigations

Create an investigation workspace showing:

- Exception.
- Estimated financial exposure.
- Original transactions.
- Calculation details.
- Likely contributing factors.
- Missing evidence.
- Reviewer.
- Status.
- Resolution.
- Approved financial adjustment, if any.

The application should not make irreversible financial corrections automatically.

---

## 31. Dashboard 11 — Data Reliability and Auditability

Show:

- Last successful source ingestion.
- Record counts.
- Failed rows.
- Duplicate records.
- Worker mapping coverage.
- Financial coverage.
- Unmatched time.
- Unallocated cost.
- Reconciliation residual.
- Closed/open period status.
- Standards approval coverage.
- Calculation versions.
- Data lineage completeness.

Financial insights should be labeled incomplete if the underlying data is insufficient.

---

## 32. Dashboard 12 — Customer Insights Center

Build a dedicated executive-insights page.

Generate deterministic, data-driven insight narratives, such as:

- "Labor expense increased by $X compared with the previous comparable period."
- "$Y of that increase is explained by overtime premiums."
- "The cost per completed picking line increased from $A to $B."
- "Receiving experienced an increase in indirect time."
- "$Z remains unallocated because the source activity could not be identified."
- "Agency billing was higher than the selected contractual rate."
- "A recalculated standard indicates a material difference from the original M150 target."
- "A customer activity appears billable but has not been matched to a billing line."

For every insight include:

1. Financial amount.
2. Comparison period.
3. Calculation.
4. Source evidence.
5. Business interpretation.
6. Confidence or qualification.
7. Suggested investigation.
8. Whether it represents actual expense, risk, estimated opportunity, or verified benefit.

Customers should be able to click each insight to see the exact records behind it.

---

# PART D — GEMINI CHATBOT READINESS

## 33. Prepare a financial intelligence semantic layer

The chatbot will be added after Core Ledger and Cost Intelligence are reliable.

Implement a documented semantic layer containing:

- Metric name.
- Business definition.
- Formula.
- Unit.
- Aggregation rule.
- Valid dimensions.
- Approved cost basis.
- Data freshness.
- Source tables.
- Permissions.
- Limitations.
- Calculation version.

Use the existing `semantic_layer` and `metric_definition` workbooks as references.

Examples:

- `total_loaded_labor_cost`
- `regular_wage_cost`
- `overtime_premium_cost`
- `agency_cost`
- `cost_per_line`
- `cost_per_order`
- `unattributed_paid_hours`
- `unattributed_paid_cost`
- `earned_hours`
- `direct_efficiency_variance`
- `cost_to_serve`
- `billing_leakage`
- `budget_actual_variance`
- `financial_reconciliation_difference`

Implement these metrics once and reuse them in dashboards, exports, and the future chatbot.

---

## 34. Build approved query tools

Prepare read-only, validated Python functions such as:

`get_labor_cost_summary(site_id, date_from, date_to, cost_basis)`

`get_operator_cost_breakdown(worker_id, period_id)`

`get_paid_vs_logged_time(worker_id, business_date)`

`get_overtime_analysis(site_id, period_id)`

`get_cost_by_worktype(site_id, period_id)`

`get_budget_variance(site_id, period_id)`

`get_variance_bridge(activity_id, period_id)`

`get_cost_per_unit(activity_id, period_id)`

`get_agency_cost_analysis(site_id, period_id)`

`get_unattributed_time(site_id, business_date)`

`get_customer_cost_to_serve(customer_id, period_id)`

`get_billing_leakage(customer_id, period_id)`

`get_reconciliation_status(period_id)`

`get_financial_lineage(metric_id, filters)`

`get_source_records(approved_reference_ids)`

Each tool must validate arguments, apply user-level authorization, limit returned records, and return typed structured results.

Every numerical result should carry calculation metadata and source references.

Do not allow a chatbot to execute arbitrary unrestricted SQL, access restricted payroll without authorization, or make changes to source financial records.

---

## 35. Future Gemini integration

When a Gemini API key is provided, use the maintained Google GenAI Python SDK.

Use function calling and structured response schemas.

The architecture should be:

User question → authorization check → intent/approved metric selection → deterministic backend query → verified result → Gemini explanation → numeric/citation verification → user-visible answer.

Gemini should explain calculations, identify reported drivers, and help users investigate.

It should not independently invent numbers, payroll assumptions, or financial conclusions.

Example user questions:

- Why did labor costs increase yesterday?
- Which work type cost the most last week?
- How much did we spend on overtime?
- Show the regular wages, OT premiums, employer taxes, and agency charges separately.
- Which workers had paid time that could not be linked to work activities?
- How much of our labor budget variance is related to workload volume?
- What caused picking cost per line to increase?
- Show me the exact source records behind the $X amount.
- Which agency invoice lines were corrected?
- Which customers have high labor cost-to-serve?
- How much financial exposure comes from unbilled work?
- What percentage of the ledger is reconciled?

Answers should explicitly say when a question cannot be answered from the current data.

Support source references and drilldown links.

Use role-based access control and never expose another customer's records.

Keep the chatbot optional. The complete application must still function when `GEMINI_API_KEY` is absent.

---

# PART E — DATA ENGINEERING AND FINANCIAL TRUST

## 36. Source ingestion

Build robust Excel/CSV ingestion that:

- Handles large files without excessive memory usage.
- Reads actual worksheet schemas.
- Preserves original IDs.
- Retains source file and row references.
- Converts Excel serial dates correctly.
- Handles nullable values.
- Supports timezone-aware timestamps.
- Handles late-arriving records.
- Normalizes financial amounts.
- Rejects invalid monetary and time records appropriately.
- Uses stable source keys and versions.
- Tracks batch IDs and content hashes.
- Does not duplicate records on re-import.

Do not discard raw data after normalizing it.

Provide a clear separation between immutable source evidence and transformed canonical records.

---

## 37. Required data quality checks

Validate:

- Unique canonical keys.
- Valid foreign keys.
- Identity crosswalks.
- Time overlaps.
- Positive/negative duration semantics.
- Payroll and agency invoice duplicates.
- Source record revisions.
- Missing pay rates.
- Incorrect currency.
- Inconsistent units of measure.
- Activity mapping coverage.
- Missing source timestamps.
- Financial component mapping.
- Reconciliation differences.
- Cost allocation totals.
- Unapproved labor standards.
- Ambiguous task attribution.
- Financial period boundaries.
- Missing or delayed source data.

Do not silently fill unknown data with artificial defaults.

Keep uncertain data visible as exceptions.

---

## 38. User roles and permissions

Implement meaningful access controls.

Suggested roles:

**Finance Controller:** Detailed posted expense, payroll reconciliation, cost accounting, approved budgets, and financial adjustments.

**Warehouse Manager:** Warehouse-level operational costs, cost drivers, trends, financial opportunities, and approved aggregated labor information.

**Supervisor:** Authorized shift/team operational information and approved cost measures, without unrestricted access to worker payroll or personal records.

**HR/Payroll:** Employee payroll, timecard corrections, compensation policy, and payroll-specific reconciliation.

**Executive:** Approved financial summaries, warehouse comparisons, margin analysis, and aggregate opportunity reports.

**System Administrator:** Data connectivity, identity mappings, ingestion and system configuration, without automatic entitlement to all sensitive financial content.

Enforce authorization in backend queries, exports, and future chatbot tools—not just in the UI.

Create audit logs for access to sensitive data, financial adjustments, approvals, and exports.

Respect applicable worker protections, break requirements, privacy obligations, and warehouse quota regulations.

---

# PART F — TESTING AND CORRECTNESS

## 39. Mandatory calculation test cases

Create independent pytest tests for:

1. One employee with 8 paid hours and normal pay.
2. Paid hours comprising direct, indirect, and break time.
3. Paid time with unattributed intervals.
4. Logged WMS activity outside paid time.
5. Overlapping device sessions.
6. Cross-midnight shifts.
7. Daylight-saving transitions.
8. Multiple activity assignments.
9. Multiple workers on one task.
10. A task linked to multiple order lines.
11. Overtime and double-time accounting.
12. State-specific pay-policy versions.
13. Nondiscretionary bonus overtime adjustment.
14. Employer burden with applicable wage caps.
15. Agency invoice with included burden.
16. Agency credit and invoice correction.
17. Payroll correction after period close.
18. GL timing difference.
19. Allocation fractions summing to one.
20. Allocation rounding without residual drift.
21. Duplicate import of the same source file.
22. Re-import of a corrected source row.
23. Missing or unapproved standards.
24. Zero completed quantities.
25. Missing financial rates.
26. Failed operator identity mapping.
27. Budget versus actual variance reconciliation.
28. Volume/mix/rate/efficiency variance separation.
29. Missing customer billing information.
30. Unbilled eligible activity.
31. Correct recognition of financial versus operational opportunity.
32. Permission-controlled financial queries.
33. Future chatbot tool argument validation.
34. Golden-set numerical question validation.
35. Multi-client data isolation.

Test that all included cost components reconcile and that excluded categories are not accidentally counted.

---

## 40. Minimum financial invariants

The following must hold:

`Source Expense = Normalized Posted Expense`

`Normalized Posted Expense = Allocated Expense + Unallocated Expense`

`Paid Time = Classified Paid Time + Unattributed Paid Time`

`Budget + Bridge Steps = Actual`

`Net Agency Expense = Included Agency Charges + Signed Credits/Adjustments`

`Financial Source Totals = Reconciled Ledger Totals + Documented Differences`

Where values depend on scope or timing, use identical definitions on both sides.

These checks should be automated, visible in the app, and included in test reports.

Do not mark the ledger "reconciled" simply because the UI looks correct.

---

# PART G — DEVELOPMENT PHASES

## 41. Build in this order

### Phase 0 — Dataset audit and readiness

Deliver:

- File inventory.
- Actual schema mapping.
- Data dictionary.
- Relationship mapping.
- Source-to-canonical mapping.
- Data quality assessment.
- Financial requirements gap analysis.
- Defined money and time accounting policies.

### Phase 1 — Operational Core Ledger

Implement:

- Raw WMS ingestion.
- Worker identity resolution.
- Work sessions.
- Task history.
- Direct/indirect event classification.
- Paid versus logged reconciliation when time-clock data is supplied.
- Operator-day timelines.
- Operational productivity.
- Exception analysis.

### Phase 2 — Financial Core Ledger

Implement:

- Payroll import.
- Employer-cost import.
- Agency invoice import.
- Cost-event creation.
- Cost books.
- Cost allocation.
- Financial components.
- Reconciliation.
- GL linkage.
- Operator and activity cost ledgers.

### Phase 3 — Labor Cost Intelligence

Implement:

- Approved standards.
- Earned hours.
- Earned cost.
- Cost per unit.
- Budget versus actual analysis.
- Reconciled variance bridge.
- Financial exception engine.
- Cost-to-serve.
- 3PL contribution where data permits.
- Financial insights and evidence.

### Phase 4 — Integration readiness

Implement:

- Semantic metrics.
- Approved query tools.
- Role-based financial query policies.
- Gemini-compatible service interfaces.
- Golden question test suite.

Do not prioritize AI chat styling over ledger correctness.

---

## 42. Financial readiness tiers

Support two modes.

### Tier A — Operational intelligence

Uses GiNi operational records.

Can provide:

- Work sessions.
- Work-type activity.
- Completed workload.
- Operational productivity.
- Unvalidated/validated standards where available.
- Direct/indirect classifications.
- Missing activity attribution.
- Nonfinancial efficiency metrics.

Do not call this a fully reconciled financial ledger.

### Tier B — Reconciled financial intelligence

Requires client financial sources including:

- Time punches.
- Payroll records.
- Employer expenses.
- Agency invoices.
- Financial cost mappings.
- Applicable policies and approved assumptions.

Can provide:

- Posted loaded labor expense.
- Full component breakdown.
- Financial allocation.
- Payroll and agency reconciliation.
- GL reconciliation.
- Financial cost intelligence.

Budget, cost-to-serve, and billing-dependent features require additional supporting records.

Build a customer onboarding checklist explaining which data feed enables which feature.

When a required feed is absent, show the precise missing-data dependency.

---

# PART H — DELIVERABLES

## 43. Complete application deliverables

Deliver a complete working project as a ZIP folder.

Suggested project name:

`GiNi_Labor_Economics`

Include:

- Working source code.
- Ingestion pipelines.
- Canonical data models.
- Database migrations.
- Financial calculation engine.
- Cost allocation engine.
- Reconciliation engine.
- Standards engine.
- Cost intelligence engine.
- FastAPI services.
- Streamlit dashboard.
- Export capabilities.
- Gemini-ready semantic and tool interfaces.
- Automated tests.
- Sample configuration.
- `.env.example`.
- `requirements.txt` or a locked `pyproject.toml`.
- README.
- Source mapping documentation.
- Financial formulas guide.
- Assumptions register.
- Data quality report.
- Test execution report.
- Customer onboarding checklist.
- Demonstration walkthrough.

Do not hardcode synthetic business amounts into the dashboard.

All amounts must come from reproducible transformations or explicitly identified assumptions.

---

## 44. Running the application

The project should work on Windows through VS Code.

Provide clear PowerShell setup instructions.

The intended local workflow should be approximately:

1. Extract the ZIP.
2. Open the application folder in VS Code.
3. Create a Python virtual environment.
4. Install dependencies.
5. Run an initialization or ingestion command.
6. Execute tests.
7. Start backend services if needed.
8. Start the Streamlit dashboard.

Use a configurable default Streamlit port of **5007**.

For example:

`python -m streamlit run app.py --server.port 5007`

Do not require unavailable external infrastructure for the local demonstration.

The application must start even if Gemini is not configured.

Document any optional production dependencies separately.

---

## 45. Required output documentation

### A. Technical architecture

Explain system components, data flow, and why each technology was selected.

### B. Canonical schema documentation

Describe every new table, relationship, column, data type, primary key, and source mapping.

### C. Financial calculation dictionary

For every financial metric, provide:

- Name.
- Business description.
- Formula.
- Cost inclusion/exclusion.
- Numerator.
- Denominator.
- Required data.
- Grain.
- Cost basis.
- Units.
- Treatment of missing information.
- Calculation version.
- Validation method.

### D. Feature completion matrix

List every requested feature with:

- Feature name.
- Implemented status.
- Data source.
- Financial formula.
- Result generated.
- Page location.
- Validation status.
- Limitations.

### E. Customer insight catalogue

Provide examples of the questions customers can answer and the exact dataset dependencies.

### F. Reconciliation report

Show the complete reconciliation between the uploaded financial source data and computed ledgers for both closed payroll periods.

### G. Known assumptions and gaps

List every assumption, limitation, unavailable field, unsupported calculation, and feature that requires more client data.

Never claim a feature is verified when it has not been tested.

---

# PART I — BUSINESS AND UX EXPECTATIONS

## 46. Customer-facing quality

Design the application as an enterprise financial operations product, not a student analytics dashboard.

Recommended primary navigation:

**Financial Overview**

**Core Ledger**

**Operator Economics**

**Activity Economics**

**Payroll & Agency**

**Cost Intelligence**

**Variance Analysis**

**Customer Cost-to-Serve**

**Financial Exceptions**

**Reconciliation Center**

**Insights Center**

**Data Quality & Administration**

**Ask GiNi (future Gemini integration)**

Use readable financial charts, consistent units, US-dollar formatting, configurable date filters, loading states, useful empty states, and drilldown details.

Always show whether the data is synthetic.

Do not use misleading green/red visualizations for results whose financial significance is uncertain.

Provide accessible explanations of financial formulas within the UI.

---

## 47. Practical business outcome

The application should ultimately help a warehouse customer answer:

1. Exactly how much did we spend on warehouse labor?
2. How much went toward permanent versus temporary staff?
3. How much did overtime actually cost?
4. How much was employer payroll burden?
5. How much labor expense was direct, indirect, or unattributed?
6. Which work types consume the most dollars?
7. Which tasks have the highest labor cost per unit?
8. Which operators and tasks account for these costs?
9. Why did labor cost increase compared with the previous period?
10. Why did cost rise even when productivity improved?
11. Was higher cost caused by volume, work complexity, rates, efficiency, overtime, or indirect hours?
12. Which activity has the highest unfavorable cost variance?
13. Which expenses have not been reconciled?
14. Are agency invoice charges consistent with contracts?
15. What portion of labor cost is not allocated to a known activity?
16. What does processing an order actually cost?
17. Which customers or activities are most expensive to serve?
18. Are we missing billable warehouse activity?
19. What opportunities could reduce avoidable expense?
20. Which improvements actually reduced recorded financial cost?
21. What supporting records explain each financial answer?
22. How much confidence should we place in each insight?

The ultimate differentiator is not simply displaying labor-cost numbers.

**It is producing a financially consistent, explainable, reconciled model that connects every dollar back to warehouse operations and original financial evidence.**

---

## 48. Research references

Study official material relevant to implementation, including:

**EasyMetrics**

- https://www.easymetrics.com/
- https://www.easymetrics.com/opsfm-operations-financial-management/
- https://www.easymetrics.com/warehouse-performance-management-platform/profit-management/
- https://www.easymetrics.com/blog/three-factors-to-consider-when-measuring-roi/
- https://www.easymetrics.com/blog/cost-serve-4th-dimension-labor-standards/

**US Department of Labor**

- https://www.dol.gov/agencies/whd/fact-sheets/23-flsa-overtime-pay
- https://www.dol.gov/agencies/whd/fact-sheets/56a-regular-rate
- https://www.dol.gov/agencies/whd/fact-sheets/21-flsa-recordkeeping

**California labor guidance**

- https://www.dir.ca.gov/dlse/faq_overtime.htm
- https://www.dir.ca.gov/dlse/FAQ_warehousequotas.htm

**IRS**

- https://www.irs.gov/publications/p15

**Google Gemini**

- https://ai.google.dev/gemini-api/docs/libraries
- https://ai.google.dev/gemini-api/docs/function-calling
- https://ai.google.dev/gemini-api/docs/structured-output

Use current official documentation to verify technical APIs and applicable rules. Historical financial calculations must use rules effective during the relevant transaction period.

Treat published vendor capabilities as research references, not evidence that the supplied datasets already support every capability.

Do not copy another vendor's proprietary implementation.

---

## 49. Final mandatory development instructions

- Implement actual working code, not pseudocode.
- Do not invent financial transactions.
- Do not assume every WMS time interval is paid time.
- Do not assume faster work necessarily reduces payroll expense.
- Do not double-count employer burden or agency costs.
- Do not double-count financial records through GL reconciliation.
- Do not use unvalidated productivity targets for authoritative financial savings.
- Do not show operator profit where revenue attribution is unsupported.
- Do not alter original records to make totals reconcile.
- Do not expose restricted payroll or employee information to unauthorized users.
- Do not allow Gemini to calculate or invent financial totals.
- Do not expose the generator's test truth to product queries.
- Do not change unrelated future product datasets unnecessarily.
- Do not introduce sample-only shortcuts that break real client deployment.

Work incrementally, validate each phase, and maintain a clear implementation checklist.

If complete implementation cannot fit in one development pass, prioritize a fully functional end-to-end pipeline for the Core Ledger, then extend Cost Intelligence using the same validated cost events.

A small, correctly reconciled financial implementation is more valuable than a large dashboard with unreliable figures.

**Begin by inspecting the uploaded ZIP and presentation thoroughly. Produce an evidence-based data inventory, source-to-canonical mapping, implementation plan, and financial assumptions register. Then implement the application and its tests.**

**Final required output: a downloadable ZIP containing the working Python application, a customer-ready demonstration using the provided synthetic data, full financial calculations, all implemented dashboards, documentation, and verified test results.**