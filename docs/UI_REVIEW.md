# UI review and redesign (version 2.0)

## Issues found in version 1.0

| Area | Issue |
|---|---|
| Navigation | Twelve pages in one flat list, with no grouping by audience. Supervisors and finance users had to scan everything. |
| Roles | Only Finance and Executive. No supervisor view, and the operator page was Finance-only. |
| Header | Every page repeated a site eyebrow, a "Synthetic Demonstration Data" badge, a period selector with a long label, and a "USD · Actual recorded · Calculation v1.0" line. |
| Copy | Intro sentences and caveat banners on almost every page ("Know what labor cost…", repeated "not controller approval" notes). |
| Overview | A donut of three sources, a two-bar period chart, a components table and a class chart overlapped. No productive vs unproductive view and no link from a figure to its detail. |
| Insights Center | Four cards that repeated the overview metrics in prose. |
| Operator Economics | Required picking an operator ID from a dropdown and typing a date. KPIs were in seconds-derived hours with no cost, no comparison across operators and no drill-down. |
| Payroll & Agency | Raw source tables with every column, including system fields. |
| Exceptions | Seconds shown as raw numbers. Gaps listed without links to the operator day. |
| Tables | No sorting. Free-text component filter needing the exact internal code. Previous/next only. No clickable rows. |
| Charts | Mixed palettes, rotated labels, no drill-through, and hover text in raw seconds. |
| Accessibility | Low-contrast uppercase labels and no visible focus on table rows. A 700 px layout collapsed the navigation. |

## What changed

- **Grouped navigation**: Operations (Workforce, Operators, Work types, Exceptions), Finance (Labor cost, Cost allocation, Budget variance, Cost to serve, Payroll & agency, Ledger) and Controls (Reconciliation, Data sources, Cost policy, API access). Each role sees only its pages and lands on its own home.
- **Role dashboards**: Workforce for supervisors covers hours by control group, causes, flagged operators and work-type pace. Labor cost for finance covers the standard-to-actual cost bridge, composition, unproductive cost by cause, and items needing review. Insights merged into Labor cost; old URLs redirect.
- **One design system**: a quiet, light shell with one interactive blue. KPIs sit in a single divided strip. Headings are sentence case, tables are compact with tabular numerals, and the same five control-group colors are used everywhere. Status chips always carry an icon and text.
- **Signature element**: a cost distribution strip on each operator row, shift row and detail page shows where every labor dollar went.
- **Drill-downs**: Operators → operator → shift timeline → order → work type → operators. Ledger → source evidence and where the amount went. KPIs, chart bars and table rows link to their detail. Breadcrumbs and previous/next shift navigation provide the way back.
- **Tables and filters**: sortable columns (including sorting by any unproductive cause), period, date range, shift, employment type, operator search, a flagged-only tab, dropdowns for ledger component and operator, and CSV export for operators, operator shifts and the ledger.
- **Less copy**: caveats kept only where they change how a number is read, mostly as short panel footers.
- **Responsive**: navigation becomes a horizontal strip on small screens, and tables scroll within their panel.

All version 1.0 business logic, routes, roles, exports, source evidence, investigation notes, controls and API endpoints are preserved.
