CREATE TABLE IF NOT EXISTS batch(id INTEGER PRIMARY KEY, filename TEXT, sha256 TEXT UNIQUE, imported_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS raw(id INTEGER PRIMARY KEY, batch_id INTEGER REFERENCES batch(id), namespace TEXT, sheet TEXT, row_no INTEGER, record_key TEXT, payload TEXT, UNIQUE(batch_id,sheet,row_no));
CREATE INDEX IF NOT EXISTS raw_lookup ON raw(namespace,sheet,record_key);
CREATE TABLE IF NOT EXISTS active_file(namespace TEXT PRIMARY KEY, batch_id INTEGER REFERENCES batch(id));
CREATE TABLE IF NOT EXISTS event(id TEXT PRIMARY KEY, raw_id INTEGER REFERENCES raw(id), period TEXT, worker TEXT, center TEXT, site TEXT, component TEXT, source TEXT, cents INTEGER, service_from TEXT, service_to TEXT, posted_at TEXT, status TEXT, source_basis TEXT);
CREATE TABLE IF NOT EXISTS allocation(id INTEGER PRIMARY KEY, event_id TEXT REFERENCES event(id), day TEXT, activity TEXT, labor_class TEXT, seconds REAL, cents INTEGER, method TEXT);
CREATE INDEX IF NOT EXISTS allocation_event ON allocation(event_id);
CREATE TABLE IF NOT EXISTS time_day(worker TEXT, day TEXT, paid REAL, logged REAL, matched REAL, outside REAL, unattributed REAL, conflict REAL, PRIMARY KEY(worker,day));
CREATE TABLE IF NOT EXISTS time_slice(worker TEXT, day TEXT, start TEXT, end TEXT, activity TEXT, labor_class TEXT, seconds REAL);
CREATE TABLE IF NOT EXISTS task(id TEXT PRIMARY KEY, raw_id INTEGER, worker TEXT, day TEXT, period TEXT, activity TEXT, order_code TEXT, pieces REAL, customer TEXT);
CREATE INDEX IF NOT EXISTS task_group ON task(period,activity,customer);
CREATE TABLE IF NOT EXISTS check_result(name TEXT, period TEXT, source_cents INTEGER, ledger_cents INTEGER, difference_cents INTEGER, note TEXT);
CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY, at TEXT DEFAULT CURRENT_TIMESTAMP, principal TEXT, action TEXT, detail TEXT);
CREATE TABLE IF NOT EXISTS investigation(key TEXT PRIMARY KEY, status TEXT, reviewer TEXT, note TEXT, updated_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS cost_policy(key TEXT PRIMARY KEY, value TEXT, updated_by TEXT, updated_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS time_part(worker TEXT, day TEXT, activity TEXT, labor_class TEXT, bucket TEXT, control TEXT, tier TEXT, productive INTEGER, seconds REAL);
CREATE INDEX IF NOT EXISTS time_part_worker ON time_part(worker,day);
CREATE TABLE IF NOT EXISTS order_cost(worker TEXT, day TEXT, activity TEXT, order_code TEXT, seconds REAL, lines INTEGER, cents INTEGER);
CREATE INDEX IF NOT EXISTS order_cost_worker ON order_cost(worker,day);
CREATE INDEX IF NOT EXISTS order_cost_order ON order_cost(order_code);
CREATE INDEX IF NOT EXISTS task_worker_day ON task(worker,day);
CREATE INDEX IF NOT EXISTS task_order ON task(order_code);

-- Schema version 2 columns (added in place by gini.db.migrate on older databases)
ALTER TABLE allocation ADD COLUMN bucket TEXT;
ALTER TABLE allocation ADD COLUMN control TEXT;
ALTER TABLE allocation ADD COLUMN tier TEXT;
ALTER TABLE allocation ADD COLUMN productive INTEGER;
ALTER TABLE time_slice ADD COLUMN bucket TEXT;
ALTER TABLE time_slice ADD COLUMN control TEXT;
ALTER TABLE time_slice ADD COLUMN tier TEXT;
ALTER TABLE time_slice ADD COLUMN start_local TEXT;
ALTER TABLE time_slice ADD COLUMN end_local TEXT;
ALTER TABLE time_slice ADD COLUMN note TEXT;
ALTER TABLE task ADD COLUMN earned_seconds REAL;
ALTER TABLE task ADD COLUMN sales_order TEXT;
ALTER TABLE time_day ADD COLUMN meal REAL;
ALTER TABLE check_result ADD COLUMN unit TEXT DEFAULT 'USD';

-- calculation_run is created by gini.db.migrate: version, input batch IDs, control results and cost-policy signature.
PRAGMA user_version=2;
