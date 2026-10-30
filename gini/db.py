import sqlite3,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DEFAULT_DB=ROOT/'data'/'gini.sqlite'
SCHEMA_VERSION=2
def connect(path=DEFAULT_DB):
 c=sqlite3.connect(path);c.row_factory=sqlite3.Row
 c.execute('PRAGMA foreign_keys=ON')
 # Each request opens its own connection over a large file: memory-map reads and keep a bigger page cache.
 c.execute('PRAGMA mmap_size=1073741824');c.execute('PRAGMA cache_size=-65536');c.execute('PRAGMA temp_store=MEMORY')
 if c.execute('PRAGMA journal_mode').fetchone()[0]=='wal':c.execute('PRAGMA synchronous=NORMAL')
 return c
SCHEMA='''
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
CREATE TABLE IF NOT EXISTS raw_count(batch_id INTEGER, namespace TEXT, sheet TEXT, records INTEGER, PRIMARY KEY(batch_id,sheet));
'''
# Columns added in schema version 2 (operator cost allocation). Older databases are migrated in place.
ADDED_COLUMNS={
 'allocation':[('bucket','TEXT'),('control','TEXT'),('tier','TEXT'),('productive','INTEGER')],
 'time_slice':[('bucket','TEXT'),('control','TEXT'),('tier','TEXT'),('start_local','TEXT'),('end_local','TEXT'),('note','TEXT')],
 'task':[('earned_seconds','REAL'),('sales_order','TEXT')],
 'time_day':[('meal','REAL')],
 'check_result':[('unit',"TEXT DEFAULT 'USD'")],
}
# Covering indexes for the reporting queries; created after the version 2 columns exist.
REPORTING_INDEXES='''
CREATE INDEX IF NOT EXISTS task_worker_cover ON task(worker,activity,day,order_code,pieces,earned_seconds);
CREATE INDEX IF NOT EXISTS task_activity_day ON task(activity,day,pieces);
CREATE INDEX IF NOT EXISTS task_period_activity_day ON task(period,activity,day,pieces);
'''
def migrate(c):
 c.executescript(SCHEMA)
 for table,cols in ADDED_COLUMNS.items():
  have={r[1] for r in c.execute(f'pragma table_info({table})')}
  for name,kind in cols:
   if name not in have:c.execute(f'alter table {table} add column {name} {kind}')
 c.executescript(REPORTING_INDEXES)
 c.execute('create table if not exists calculation_run(id integer primary key, at text default current_timestamp, version text, input_batches text, results text)')
 if 'policy' not in {r[1] for r in c.execute('pragma table_info(calculation_run)')}:c.execute('alter table calculation_run add column policy text')
 c.execute(f'PRAGMA user_version={SCHEMA_VERSION}');c.commit()
def prepare(c):
 """Startup tuning: WAL journal (cheap audit commits, reads never blocked by writes), reporting indexes, sheet counts."""
 c.execute('PRAGMA journal_mode=WAL');migrate(c);sheet_counts(c);c.execute('PRAGMA optimize')
def sheet_counts(c):
 """Record counts per sheet of the active snapshots. Snapshots are immutable, so each batch is counted once."""
 for (bid,) in c.execute('select batch_id from active_file where batch_id not in (select batch_id from raw_count)').fetchall():
  c.executemany('insert or ignore into raw_count values(?,?,?,?)',c.execute('select batch_id,namespace,sheet,count(*) from raw where batch_id=? group by namespace,sheet',(bid,)).fetchall())
 c.commit()
 return c.execute('select r.namespace,r.sheet,r.records,b.filename from raw_count r join active_file a on a.batch_id=r.batch_id join batch b on b.id=a.batch_id order by r.namespace,r.sheet')
def rows(c,namespace,sheet):
 # Active batch first, then the (batch_id,sheet,row_no) unique index returns rows already in order: no sort of payloads.
 for r in c.execute('SELECT r.id,payload FROM active_file a JOIN raw r ON r.batch_id=a.batch_id AND r.sheet=? WHERE a.namespace=? AND r.namespace=? ORDER BY r.row_no',(sheet,namespace,namespace)):
  v=json.loads(r['payload']);v['_raw_id']=r['id'];yield v
