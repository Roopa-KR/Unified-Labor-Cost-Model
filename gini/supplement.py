"""Synthesized supplement for feeds the supplied dataset does not contain.

The dataset has no equipment downtime / maintenance log, so waiting-for-equipment
time cannot be observed. To demonstrate (and test) that classification path, a
small deterministic log is generated from the source idle events of
equipment-dependent work types. Every row carries data_origin='gini_synthesized'
and is stored as its own immutable snapshot in namespace 'supplement', separate
from client source data. Replace it with a real equipment log before production
use, or switch it off in Cost policy.
"""
import hashlib,json
from .db import rows

NAMESPACE='supplement'
SHEET='equipment_downtime'
FILENAME='GINI_SYNTHESIZED_equipment_downtime (generated in-app, not client data)'

def _pick(key,mod):
 return int(hashlib.sha256(key.encode()).hexdigest()[:8],16)%mod

def build(c):
 segments={r['id']:r for r in rows(c,'operations','work_segment')}
 out=[]
 for r in rows(c,'finance','labor_event'):
  if r['activity_id']!='act-UNEXPLAINED_IDLE' or not r.get('worker_id'):continue
  seg=segments.get(r.get('work_segment_id')) or {}
  act=seg.get('activity_id')
  if act=='act-PICK_CASES' and _pick(r['id'],3)==0:equipment,reason='Pallet jack','Battery swap'
  elif act=='act-PICK_COOLER' and _pick(r['id'],3)==0:equipment,reason='Cooler door','Door interlock fault'
  elif _pick(r['id'],12)==0:equipment,reason='RF scanner','Scanner fault / reboot'
  else:continue
  out.append(dict(id='eqd-'+r['id'],data_origin='gini_synthesized',worker_id=r['worker_id'],activity_id=act,
   equipment_type=equipment,reason=reason,starts_at=r['starts_at'],ends_at=r['ends_at'],business_date=r['business_date'],
   basis='Synthesized from source idle event '+r['id']+'; no equipment log supplied'))
 return out

def ensure(c,enabled=True):
 """Create (or reactivate) the synthesized snapshot. Returns rows used by the engine."""
 if not enabled:
  c.execute('delete from active_file where namespace=?',(NAMESPACE,));return []
 data=build(c);payload=json.dumps(data,sort_keys=True).encode();sha=hashlib.sha256(payload).hexdigest()
 b=c.execute('select id from batch where sha256=?',(sha,)).fetchone()
 if b:bid=b[0]
 else:
  bid=c.execute('insert into batch(filename,sha256) values(?,?)',(FILENAME,sha)).lastrowid
  c.executemany('insert into raw(batch_id,namespace,sheet,row_no,record_key,payload) values(?,?,?,?,?,?)',
   [(bid,NAMESPACE,SHEET,i+2,r['id'],json.dumps(r,separators=(',',':'))) for i,r in enumerate(data)])
 c.execute('insert into active_file values(?,?) on conflict(namespace) do update set batch_id=excluded.batch_id',(NAMESPACE,bid))
 return data
