# Architecture and source-to-canonical mapping

## Data flow

Workbook snapshots → immutable `batch` + `raw` rows → active namespace snapshot → deterministic `event`, `time_day`, `time_slice`, `allocation`, `task`, `check_result` → shared services → Flask HTML / CSV / approved JSON endpoints.

The importer reads openpyxl worksheets in read-only mode and inserts in 2,000-row batches. Raw JSON preserves source IDs and original types as supplied by openpyxl. File hashes and physical Excel row numbers accompany the evidence. Datetimes supplied as strings retain their original offsets. Financial values are normalized separately to cents, never silently rewritten in raw rows.

The SQLite schema is in SCHEMA.sql. Its declared columns/types and foreign keys are authoritative. `raw` is namespaced: finance.labor_event is not operations.labor_event, and intelligence.standard is not operations.standard. This prevents accidental duplicate inclusion.

## Canonical table mapping and grains

| Table | Grain / key | Source and calculation | Relationships |
|---|---|---|---|
| batch | One imported workbook version / integer ID | Filename, SHA-256, import time | Referenced by raw and active_file |
| raw | One nonempty physical worksheet row / integer ID | Original JSON payload, namespace, sheet, row number, source key | batch_id → batch; unique batch/sheet/row |
| active_file | One current workbook per namespace | Latest successfully imported snapshot | batch_id → batch |
| event | One source financial row / `source:id` | finance.payroll_line, employer_cost, posted agency_invoice_line | raw_id → raw; worker/center/period source identifiers retained |
| time_day | One worker / business date | Union approved paid attendance; union WMS work segments; intersection | worker/date composite primary key |
| time_slice | One mutually exclusive paid interval | Source finance.labor_event clipped to paid time | Worker/date references time_day logically |
| allocation | One event / day / activity / labor class | Paid-time-share, exact integer-cent allocation | event_id → event |
| task | One completed source warehouse_task / source ID | Completed canonical task, pieces, date, worker, activity | raw_id → raw logically; customer from explicit joins |
| check_result | One control / accounting period | Independently summed source vs normalized ledger and allocations/GL | Period keys shared with event |
| calculation_run | One completed rebuild | Version, active batch IDs, control result snapshot | Immutable audit of input set and control outcome |
| audit | One application access/action | Login, page, export, source read, query, investigation | Principal role and timestamp |
| investigation | One reviewed event ID | Status, reviewer role, note | Logical reference to event, no change to financial amount |

Source dictionaries include source-declared types and relationship information. DATA_INVENTORY.json contains headers and sample-observed types; it is not a complete per-cell type-quality profile. IDs and relationship assumptions are validated in code where required for this implementation, not for every optional imported future-product table.

## Source inclusion

- Foundation: site, worker, employment, activity and dictionaries. Restricted employee PII worksheet is excluded.
- WMS: all worksheets preserved for read-only evidence; canonical operational tables are supplied by Product 1, not independently rebuilt from WMS.
- Operational Product 1: work_segment, warehouse_task and supporting evidence. Its labor_event is not added to Tier B labor_event.
- Financial Product 1: historical sources, intervals, policies, corrections and GL. Precomputed cost_event/allocation/output worksheets are retained as evidence but never summed into the computed ledger.
- Cost Intelligence Product 2: standards, one selected budget version, billing, task-to-order/customer links. Existing variance and cost-to-serve output tables are reference-only.
- Copilot: source definitions and reference evaluations retained. These are not evidence of a functioning chatbot.
- Shift Command, Workforce Development and Savings Governance: inventory only; no product behavior implemented.
- Test_Truth_NOT_FOR_PRODUCT: excluded entirely from runtime database and queries.

## Data gaps and readiness

The supplied operating site is SYN-DC100, 40 workers, six picking work types, 148,660 completed task lines, and two closed payroll periods. SYN-DC200 is a standards-only reference site, not a second financial operating warehouse.

The referenced presentation/blueprint was not attached to this build request and was not used. The two attached files are the requirements text and dataset ZIP. The workbook build scripts reference an external original generator; this application deliberately runs from the supplied workbooks.

Readiness is **recorded financial demonstration with arithmetic controls**, not an approved enterprise financial close. The app does not inherit synthetic approval labels from imported reconciliation tables. General-ledger account-level sign-off, financial standard approval, historical as-of queries, full payroll expected-pay checks and operational raw-source reconstruction remain future work.

## Customer onboarding dependencies

| Feed | Enables | Without it |
|---|---|---|
| Worker identities, employment and site | Operator attribution and scoped expense | Reject unmapped financial site; investigate worker mapping |
| Approved attendance intervals | Paid-time denominators and allocation | Cost remains unallocated; full generic missing-feed UI deferred |
| WMS work segments and labor events | Logged/paid overlap and classifications | No assumed direct productive hours |
| Payroll + pay-code map | Posted wage components | No modeled substitution in actual book |
| Employer expenses | Loaded labor totals | No default burden percentages |
| Posted agency invoices | Temporary labor cost, signed credits | Do not infer expense from staffing rates |
| GL journals and approved mapping | Ledger-to-GL checks | No claimed reconciled close |
| Completed tasks + validated standards | Output and earned hours | Unavailable rate-based benchmark |
| Approved versioned budget | Budget bridge | No budget estimate invented |
| Billing + task/order/customer mapping | Partial labor contribution | Revenue-dependent result unavailable |
| Approved comparable savings baseline | Realized benefit | No realized savings claim |

This adapter expects the bundled complete schema. For missing or differently shaped real-client feeds, implement and validate a new adapter before use; it is not a general plug-and-play client onboarding system.

## Security boundary

Two password-authenticated roles: Finance has source/worker/export access; Executive has aggregate summaries. Flask session cookies are HTTP-only and SameSite=Lax; mutations require CSRF tokens. SQL parameters are bound. Source routes use active-table whitelist existence and pagination. Exports neutralize spreadsheet formula prefixes. Immutable sources are never edited from the UI. No arbitrary SQL or filesystem query API is exposed.

Single-site local use only. The engine fails if a financial event maps outside SYN-DC100. Full tenant isolation, team-level supervisor restrictions, enterprise identity, public-network throttling, backup/restore, key management and retention enforcement are not implemented. Operating-system access to the local database grants access to its non-PII source financial records; app roles do not encrypt local files.

## Technical references checked

- Flask quickstart: https://flask.palletsprojects.com/en/stable/quickstart/
- Flask / Waitress deployment: https://flask.palletsprojects.com/en/stable/deploying/waitress/
- California overtime guidance: https://www.dir.ca.gov/dlse/faq_overtime.htm
- Gemini function-calling interface: https://ai.google.dev/gemini-api/docs/function-calling

References inform the design, not a claim of payroll compliance. The DOL regular-rate page returned an access error during research; no full expected-pay/tax engine is certified in this release. Source-effective client rules remain authoritative for future implementation.
