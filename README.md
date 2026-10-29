# GiNi Labor Economics — Flask edition

A working local application for the supplied synthetic warehouse dataset. Flask serves the dashboard, authenticated JSON endpoints and CSV exports. SQLite stores immutable source snapshots, calculated financial events and exact-cent allocations. No Node.js, MongoDB, Streamlit, FastAPI, cloud database or AI key is needed.

**Version 2.0** adds operator-level labor cost allocation and a redesigned interface for warehouse supervisors and finance teams. Each operator's loaded cost (wages, overtime, employer taxes, benefits, insurance, agency billing) is distributed over productive work and unproductive time at the applicable straight-time or overtime rate. Unproductive time is split by cause and by who controls it, and pace is compared with standard. See `docs/ACCOUNTING_POLICIES.md` §16 and `docs/UI_REVIEW.md`.

**Scope:** functional Core Ledger and an initial Cost Intelligence implementation, not the complete commercial system in the master brief. See `docs/FEATURE_MATRIX.md` for implemented and deferred capabilities. All records are **Synthetic Demonstration Data**.

## Start on Windows in VS Code

1. Extract this ZIP completely. Allow about 1 GB free disk space for the source evidence database.
2. Open the extracted `GiNi_Labor_Economics` folder in VS Code. `app.py` must be directly inside the folder you open.
3. Select **Terminal → New Terminal**, then run:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

If Python 3.12 is not installed, use an installed Python 3.11+ interpreter with `python -m venv .venv`. Using the explicit virtual-environment Python path avoids PowerShell activation-policy issues.

4. Open **http://127.0.0.1:5007**.
5. Choose **Finance** or **Supervisor**. The first start generates the passwords in `data/local_login.txt` (Finance) and `data/local_login_supervisor.txt` (Supervisor). Open the file in VS Code and paste its contents into the password field. Passwords are generated locally; no shared password is shipped.
6. Keep the terminal running. Press Ctrl+C to stop.

The supplied database is already imported and calculated with version 2.0. **You do not need to initialize it to run the demonstration.** If you start the app against an older version 1.0 database, it upgrades the schema and recalculates once on startup (about 15 seconds). It contains source evidence as database records, not the test-truth workbook or restricted employee PII.

## Optional configuration

Copy `.env.example` to `.env`. Set `GINI_FINANCE_PASSWORD` to your preferred password. Set `GINI_SUPERVISOR_PASSWORD` to choose the Supervisor password. Set `GINI_EXECUTIVE_PASSWORD` to enable the summary-only Executive role. Restart the app after editing configuration. The `.env.example` file is included even if Windows Explorer hides its leading-dot filename.

`GINI_PORT=5007` controls the port. Default binding is loopback. Do not expose this local demo directly to a public network. Production authentication, tenant isolation, TLS, rate limiting, deployment controls and payroll policy approval are not supplied.

## Verify

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

The verified environment and results are recorded in `docs/test_results.txt` and `docs/TEST_REPORT.md`. Tests exercise data invariants, templates, authorization, API validation, interval arithmetic and signed corrections. The small overtime utility is unit-tested but not integrated as an independent payroll audit engine.

## Re-import the original dataset (optional)

Extract your original data ZIP into a separate directory, then:

```powershell
.\.venv\Scripts\python.exe -m gini.ingest "C:\path\to\GiNi_Synthetic_Data"
.\.venv\Scripts\python.exe -m gini.engine
```

The importer accepts the supplied workbook naming/layout. It does not run the generator. Exact file hashes are skipped; changed workbooks become new immutable snapshots and supersede the previous active snapshot. Old source rows remain. Missing rows in a replacement workbook are removed from the active snapshot, so replacements must be **complete workbook snapshots**, not delta files. Financial identifiers must be unique within a snapshot.

Reporting is blocked while active source snapshots differ from the last successful calculation. Failed recalculation rolls back canonical changes. Re-imports are administrative CLI operations; no public file upload or arbitrary SQL endpoint exists.

The version-1 schema is created idempotently by `gini/db.py` and tracked with SQLite `user_version`. No PostgreSQL/Alembic migration system is claimed.

## Roles

| Role | Home page | Sees |
|---|---|---|
| Finance | Labor cost | Everything, including ledger, payroll, source evidence, exports and Cost policy |
| Supervisor | Workforce | Workforce, Operators (with drill-down to shifts and orders), Work types, Exceptions |
| Executive | Labor cost | Site-level summaries only; no operator, payroll or source detail |

## Demo walkthrough

1. **Workforce** (Supervisor home): paid hours by day, split by control group. Select a day to see its operators. Review unproductive time by cause and the operators flagged against Cost policy thresholds.
2. **Operators**: sort by any column or any unproductive cause, filter by period, dates, shift and employment type, and export CSV. The strip in each row shows where that operator's cost went.
3. **Operator detail** (select W0028 or W0001): cost by category with loaded rates, the loaded wage build-up and overtime check against payroll, pace and standard cost by work type, then shifts.
4. **Shift page**: a timeline of every paid minute with overtime shaded, cost by category, and the orders worked. Select an order for its cost per line, operators and customers.
5. **Labor cost** (Finance home): the bridge from standard cost of completed lines to total loaded cost, cost composition, and unproductive cost by cause.
6. **Cost allocation**: each cost component by control group, plus a per-operator reconciliation where allocated equals posted.
7. **Budget variance**, **Cost to serve**, **Payroll & agency**, **Ledger** (select a reference for source evidence and where the amount went), and **Reconciliation** (operator allocation, time partition, order attribution, overtime and GL controls).
8. **Exceptions**: shifts to review by category and control, recorded WMS/device exceptions, disputed invoices with review notes.
9. **Cost policy**: change the rest allowance, thresholds or productive classification. Saving recalculates every page.
10. **Data sources**: the source inventory, with the synthesized equipment log clearly labeled.

## Project files

- `app.py`: Flask routing, access controls and application entry point (Waitress).
- `gini/ingest.py`: workbook snapshot ingestion.
- `gini/engine.py`: financial normalization, interval attribution, allocations and reconciliation.
- `gini/maths.py`: Decimal money conversion, interval and allocation primitives.
- `gini/services.py`: dashboard/API metrics, standards, variance and customer attribution.
- `gini/operators.py`: operator cost metrics, drill-downs, cost bridge (shared by pages, exports and API).
- `gini/partition.py`: paid-time partition, rest allowance and overtime tiers.
- `gini/policy.py`: configurable cost policy and category definitions.
- `gini/supplement.py`: the labeled, synthesized equipment downtime log.
- `gini/db.py`: schema and source-access layer.
- `templates/`, `static/`: responsive UI and bundled offline chart library.
- `data/gini.sqlite`: prebuilt source evidence and calculated data.
- `tests/`: automated verification.
- `docs/`: source mapping, schema, accounting policies, gaps and test evidence.

Plotly.js is distributed under its MIT license; its license header is retained in the bundled file. No remote fonts, chart CDNs or external AI services are required at runtime.
