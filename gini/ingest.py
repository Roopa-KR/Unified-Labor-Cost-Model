"""Immutable workbook snapshots; exact file reimports are no-ops. No generator execution."""
import hashlib,json,argparse
from pathlib import Path
import openpyxl
from .db import connect,migrate,DEFAULT_DB
PREFIX={'00_':'foundation','01_':'wms','02_':'operations','03_':'finance','04_':'intelligence','08_':'copilot'}
def ingest(folder,db=DEFAULT_DB):
 Path(db).parent.mkdir(parents=True,exist_ok=True)
 c=connect(db);migrate(c)
 for p in sorted(Path(folder).rglob('*.xlsx')):
  ns=next((v for k,v in PREFIX.items() if p.name.startswith(k)),None)
  if not ns or 'Test_Truth' in str(p):continue
  sha=hashlib.sha256(p.read_bytes()).hexdigest()
  if c.execute('select 1 from batch where sha256=?',(sha,)).fetchone():
   print('Already imported:',p.name,flush=True);continue
  with c:
   bid=c.execute('insert into batch(filename,sha256) values(?,?)',(p.name,sha)).lastrowid
   w=openpyxl.load_workbook(p,read_only=True,data_only=True)
   for s in w:
    if 'RESTRICTED' in s.title:continue
    it=iter(s.values);header=next(it,());header=[str(x) if x is not None else f'column_{i}' for i,x in enumerate(header)]
    if len(set(header))!=len(header):raise ValueError(f'Duplicate columns: {p.name}/{s.title}')
    buf=[]
    for n,r in enumerate(it,2):
     if not any(v is not None for v in r):continue
     obj=dict(zip(header,r));key=str(obj.get('id') or obj.get('source_record_key') or f'row:{n}')
     buf.append((bid,ns,s.title,n,key,json.dumps(obj,default=str,separators=(',',':'))))
     if len(buf)>=2000:c.executemany('insert into raw(batch_id,namespace,sheet,row_no,record_key,payload) values(?,?,?,?,?,?)',buf);buf=[]
    c.executemany('insert into raw(batch_id,namespace,sheet,row_no,record_key,payload) values(?,?,?,?,?,?)',buf)
    print(ns,s.title,s.max_row-1,flush=True)
   w.close();c.execute('insert into active_file values(?,?) on conflict(namespace) do update set batch_id=excluded.batch_id',(ns,bid))
 c.close()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('folder');p.add_argument('--db',default=str(DEFAULT_DB));a=p.parse_args();ingest(a.folder,a.db)
