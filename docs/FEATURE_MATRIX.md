# Feature completion and limits

This is a working local first release, following the brief's instruction to prioritize an end-to-end Core Ledger when the full commercial scope cannot fit in one pass. It must not be described as all 49 sections fully implemented.

| Capability | Status | Evidence / page | Limit |
|---|---|---|---|
| Workbook/worksheet inventory and dictionaries | Implemented | DATA_INVENTORY.json, SOURCE_DICTIONARIES.json | Actual supplied schemas; other products inventoried, not imported |
| Immutable raw rows, hashes and workbook versions | Implemented | Data Quality & Sources | Whole workbook replacements; no incremental connector/CDC |
| Idempotent and corrected imports | Tested | test_ingest.py | CLI ingestion, supplied naming/layout only |
| Source financial normalization | Implemented and tested | Core Ledger | USD, one configured demo site; missing site mapping fails |
| Exact-cent signed money and allocation | Implemented and tested | Transaction evidence | Paid-time share only; not direct observed task cost |
| Payroll and employer expense | Implemented | Payroll & Agency, Ledger | Official supplied amounts remain authoritative |
| Agency costs, dispute and credit | Implemented and tested | Exceptions, Ledger | Disputed posted amount included as recorded expense, not approved expense |
| Payroll reversal/replacement lineage | Implemented and tested | Correction source table and event evidence | No new financial adjustments posted from UI |
| Paid/WMS union, intersection, overlap classification | Implemented and tested | Operator Economics | Uses supplied canonical work segments and approved attendance |
| Raw WMS-to-canonical identity engine | Deferred | Raw WMS retained for inspection | Does not independently rebuild the supplied operational model |
| Overnight and DST elapsed-time primitives | Tested | test_finance.py | Already timezone-aware ISO input; business dates supplied by source |
| Timeline and daily time metrics | Implemented | Operator Economics | Timeline in UTC; no daily payroll expense claim |
| Worker and component ledger filters/export | Implemented and tested | Core Ledger | No all-dimension grouping or pivot UI |
| Financial books | Partial | Actual recorded ledger | Accrued, modeled, forecast books not implemented; supplied estimated events are reference-only |
| Source/allocated/unallocated conservation | Implemented and tested | Reconciliation Center | Exact cents |
| GL aggregate reconciliation | Implemented and tested | Reconciliation Center | Dataset-specific journal period mapping and 6xxx accounts; no controller sign-off or account-level matching workflow |
| Full expected payroll, tax caps, bonuses, exemptions | Deferred | Source policies retained | Ordinary-week overtime helper is unit-tested only; do not use as payroll compliance engine |
| Earned hours | Implemented | Activity Economics | Simple retrospectively validated line/hour standards; no multi-component model or finance-approved standard cost |
| Unit costs | Implemented | Overview, Activities | Whole-site cost/line and activity allocated cost/line; null for missing denominator |
| Budget version selection and bridge | Partial, arithmetic tested | Variance Analysis | Volume, standard change, explicit remaining residual; no claimed rate/efficiency/agency decomposition |
| Customer attribution and billed contribution | Partial, conservation tested | Cost-to-Serve | Activity completed-line share; remaining costs stay unassigned; not net profit |
| Billing leakage, SLA penalties, quality cost engine | Deferred | Relevant input tables retained | Supplied precomputed outputs are not presented as independently verified results |
| Operator loaded-cost allocation | Implemented and tested (v2.0) | Operators, operator detail, Cost allocation | Uses posted source amounts; tiers re-derived from attendance under assigned pay policy |
| Pay-tier (straight / overtime / double-time) loaded rates | Implemented and tested | Operator detail, evidence page | Overtime premium placed on overtime hours; burden spread per paid hour |
| Productive / unproductive time partition with control attribution | Implemented and tested | Workforce, Operators, shift timeline | Rest breaks are not punched in the source; allowance policy used |
| Pace vs standard and standard vs actual cost | Implemented and tested | Operators, Work types, Labor cost bridge | Retrospectively validated line standards only |
| Shift timeline, order-level cost drill-down | Implemented | Operator shift page, order page | Order cost covers direct work; concurrent orders share time |
| Configurable cost policy with recalculation | Implemented and tested | Cost policy | Finance only; full recalculation on change |
| Supervisor role | Implemented and tested | Workforce, Operators, Work types, Exceptions | No payroll ledger, source evidence or policy access |
| Equipment downtime feed | Synthesized | Data sources (labeled) | Generated from source idle events; replace with a real log |
| Operator / shift CSV exports | Implemented and tested | Operators, operator detail | Same calculations as dashboards |
| Investigation notes | Implemented | Financial Exceptions | Disputed-invoice notes/status only; no accounting changes |
| Deterministic insights | Implemented | Labor cost "Needs review" (Insights page merged) | Descriptive totals and caveats; no realized savings claims |
| Role enforcement and audit | Implemented and tested | Finance, Supervisor, Executive | Three local roles, session auth; not full enterprise IAM/HR/Supervisor policy set |
| Restricted PII and test-truth exclusion | Tested | Database check | Neither is imported |
| Multi-client commercial deployment | Deferred / blocked | Engine rejects other event sites | Separate DB per installation; no shared multi-tenant architecture |
| Approved semantic API | Partial, tested | Ask GiNi | Summary, activities, variance, reconciliation; no free-form SQL |
| Gemini chat, numeric/citation verification | Deferred | Ask GiNi labels it future | No SDK integration or AI calls |
| Windows local runtime | Documented | README | Python/Flask/Waitress; tests executed on Linux Python 3.12 |
| Production infrastructure | Deferred | Architecture notes | No PostgreSQL, DuckDB, SSO, backups, distributed jobs or formal retention enforcement |

The supplied master prompt is retained in REQUIREMENTS.md for the full requested scope. All unimplemented calculations remain unavailable rather than being replaced by fabricated results.
