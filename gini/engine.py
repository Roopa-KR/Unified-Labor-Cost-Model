"""Calculation version 2.0: exact source cents, conservative interval attribution,
operator-level loaded-cost allocation by pay tier and productive/unproductive bucket."""
from collections import defaultdict
from datetime import datetime,timezone,timedelta,date
from bisect import bisect_right
import json
from .db import connect,rows,migrate,DEFAULT_DB
from .maths import cents,allocate,interval,union,duration,intersect,classify,stamp
from . import policy as pol_mod, supplement
from .partition import classify_day,tiers,tier_cuts,union as _u,HOUR
SITE='site-SYN-DC100'
VERSION='2.0'
PREMIUM_CODES={'pc-OTP':{'OT':1.0},'pc-DTP':{'DT':1.0},'pc-OTR':{'OT':0.5,'DT':1.0}}

def _local(ts,offset):
 return datetime.fromtimestamp(ts,timezone(timedelta(seconds=offset))).isoformat(timespec='seconds')

def _offset(s):
 d=datetime.fromisoformat(s);return int(d.utcoffset().total_seconds())

def standard_lookup(c):
 """Validated, approved line standards (same rule as Activity Economics)."""
 standards=[s for s in rows(c,'intelligence','standard') if s['status'] in ('validated','approved') and s.get('approved_by') and s.get('units_per_hour')]
 def find(activity,day):
  ss=[s for s in standards if s['activity_id']==activity and s['valid_from']<=day and (not s['valid_to'] or day<s['valid_to'])]
  return float(ss[0]['units_per_hour']) if len(ss)==1 else None
 return find

def calculate(db=DEFAULT_DB):
 c=connect(db);migrate(c)
 policy=pol_mod.load(c)
 periods={r['id']:r for r in rows(c,'finance','payroll_period')}
 def period_for(day):return next((p['id'] for p in periods.values() if p['starts_on']<=day<p['ends_on']),None)
 with c:
  equipment_rows=supplement.ensure(c,policy['use_synthesized_equipment'])
  for t in ['allocation','event','time_day','time_slice','time_part','order_cost','task','check_result']:c.execute('delete from '+t)
  codes={r['id']:r for r in rows(c,'finance','pay_code')}
  employment=defaultdict(list)
  for r in rows(c,'foundation','employment'):employment[r['worker_id']].append(r)
  def site_for(worker,day):
   matches=[r for r in employment[worker] if r['valid_from']<=day and (not r['valid_to'] or day<r['valid_to'])]
   return matches[0]['site_id'] if len(matches)==1 else None
  pay_code_of={};agency_line={}
  for source in ['payroll_line','employer_cost','agency_invoice_line']:
   seen=set()
   for r in rows(c,'finance',source):
    if r['id'] in seen:raise ValueError('Duplicate financial source identifier '+r['id'])
    seen.add(r['id']);period=r.get('period_id') or period_for(r['service_from']);p=periods.get(period)
    if not p:raise ValueError('Unmapped financial period '+r['id'])
    start=r.get('earned_from') or r.get('service_from') or p['starts_on'];end=r.get('earned_to') or r.get('service_to') or p['ends_on']
    if source=='payroll_line':component=codes[r['pay_code_id']]['component'];pay_code_of[source+':'+r['id']]=r['pay_code_id']
    elif source=='employer_cost':component='employer_'+r['component_code']
    else:component='agency_'+('credit' if r['fee_type']=='credit_adjustment' else r['fee_type']);agency_line[source+':'+r['id']]=r
    status=r.get('status','posted');basis=r.get('cost_basis','actual')
    if source=='agency_invoice_line' and not r.get('posted_at'):continue
    c.execute('insert into event values(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(source+':'+r['id'],r['_raw_id'],period,r.get('worker_id'),r.get('cost_center_id'),r.get('site_id') or site_for(r.get('worker_id'),start),component,source,cents(r['amount']),start,end,r.get('posted_at') or r.get('recorded_at'),status,basis))
  if c.execute('select 1 from event where site is null or site<>?',(SITE,)).fetchone():
   raise ValueError('This local adapter supports SYN-DC100 only; isolate other clients in a separate database.')

  # Completed tasks (one task = one line) with standard time earned. Explicit links only; ambiguous customers not guessed.
  find_std=standard_lookup(c)
  headers={r['id']:r for r in rows(c,'intelligence','order_header')}
  orders={k:r['customer_id'] for k,r in headers.items()}
  line_order={r['id']:r.get('order_id') for r in rows(c,'intelligence','order_line')}
  lines={k:orders.get(v) for k,v in line_order.items()}
  links=defaultdict(set);sales=defaultdict(set)
  for r in rows(c,'intelligence','task_order_line'):
   if lines.get(r['order_line_id']):links[r['task_id']].add(lines[r['order_line_id']])
   h=headers.get(line_order.get(r['order_line_id']))
   if h:sales[r['task_id']].add(h['order_code'])
  order_activity={};queue_events=defaultdict(list)
  earned=defaultdict(float);line_count=defaultdict(int);completions=defaultdict(list)
  task_rows=[]
  for r in rows(c,'operations','warehouse_task'):
   order_activity[r['warehouse_order_code']]=r['activity_id']
   if r.get('created_at'):
    queue_events[r['activity_id']].append((stamp(r['created_at']),1))
    if r.get('completed_at'):queue_events[r['activity_id']].append((stamp(r['completed_at']),-1))
   if r['status']!='completed' or not r.get('completed_at'):continue
   day=r['completed_at'][:10];customers=links[r['id']]
   uph=find_std(r['activity_id'],day);es=3600.0/uph if uph else None
   if r.get('worker_id'):
    completions[r['worker_id']].append(stamp(r['completed_at']))
    line_count[(r['worker_id'],day,r['activity_id'])]+=1
    if es:earned[(r['worker_id'],day,r['activity_id'])]+=es
   so=sales[r['id']]
   task_rows.append((r['id'],r['_raw_id'],r.get('worker_id'),day,period_for(day),r['activity_id'],r['warehouse_order_code'],r.get('completed_qty'),next(iter(customers)) if len(customers)==1 else None,es,next(iter(so)) if len(so)==1 else None))
  c.executemany('insert into task(id,raw_id,worker,day,period,activity,order_code,pieces,customer,earned_seconds,sales_order) values(?,?,?,?,?,?,?,?,?,?,?)',task_rows)

  # Periods when an activity had no released, uncompleted work: idle then is waiting for work, not operator idle.
  no_work=defaultdict(list)
  for act,evs in queue_events.items():
   evs.sort();open_=0;empty_from=None
   for t,d in evs:
    if open_==0 and empty_from is not None and t>empty_from:no_work[act].append((empty_from,t))
    open_+=d
    empty_from=t if open_==0 else None

  # Context interval sets per worker.
  segments=defaultdict(list);no_output=defaultdict(list)
  annotated={r['entity_id'] for r in rows(c,'operations','operational_exception') if r['exception_type']=='logged_without_output' and r.get('annotation')}
  system=defaultdict(list)
  for r in rows(c,'operations','operational_exception'):
   if r['exception_type']=='device_offline_late_sync' and r.get('worker_id') and r.get('ends_at'):system[r['worker_id']].append(interval(r))
  for v in completions.values():v.sort()
  gap=policy['no_output_gap_seconds']
  for r in rows(c,'operations','work_segment'):
   if not r.get('worker_id') or not r.get('ends_at'):continue
   a,b=interval(r);segments[(r['worker_id'],r['business_date'])].append((a,b,r['activity_id']))
   ts=completions[r['worker_id']];i=bisect_right(ts,a);points=[a]
   while i<len(ts) and ts[i]<b:points.append(ts[i]);i+=1
   points.append(b);ann=r['id'] in annotated
   for x,y in zip(points,points[1:]):
    if y-x>gap:no_output[r['worker_id']].append((x,y,ann))
  equipment=defaultdict(list)
  for r in equipment_rows:equipment[r['worker_id']].append(interval(r))
  idle_long=defaultdict(list)

  paid=defaultdict(list);logged=defaultdict(list);events=defaultdict(list);offsets={}
  meals=defaultdict(list)
  for r in rows(c,'finance','attendance_interval'):
   if r['approved'] and not r['paid']:meals[(r['worker_id'],r['business_date'])].append(interval(r))
   if r['approved'] and r['paid']:
    key=(r['worker_id'],r['business_date']);paid[key].append(interval(r));offsets.setdefault(key,_offset(r['starts_at']))
  for r in rows(c,'operations','work_segment'):
   if r.get('worker_id') and r.get('ends_at'):logged[(r['worker_id'],r['business_date'])].append(interval(r))
  for r in rows(c,'finance','labor_event'):
   if r.get('worker_id') and r.get('ends_at'):
    a,b=interval(r);events[(r['worker_id'],r['business_date'])].append((a,b,r.get('activity_id') or 'unattributed',r['labor_class']))
    if r.get('activity_id')=='act-UNEXPLAINED_IDLE' and (r.get('duration_seconds') or b-a)>policy['idle_excess_seconds']:idle_long[r['worker_id']].append((a,b))

  # Pay policy per worker (effective-dated assignment) for overtime tiers.
  policies={r['id']:r for r in rows(c,'finance','pay_policy')}
  assignment=defaultdict(list)
  for r in rows(c,'finance','pay_policy_assignment'):assignment[r['worker_id']].append(r)
  def pay_policy(worker,day):
   ms=[policies[r['pay_policy_id']] for r in assignment[worker] if r['valid_from']<=day and (not r.get('valid_to') or day<r['valid_to'])]
   return ms[0] if ms else policies.get('ppol-US-CA-2026-v1') or {'daily_ot_threshold_hours':8,'daily_dt_threshold_hours':12,'weekly_ot_threshold_hours':40,'seventh_day_rule':True,'workweek_start_dow':1}
  def week_start(day,pol):
   d=date.fromisoformat(day);dow=(pol.get('workweek_start_dow') or 1)-1
   return (d-timedelta((d.weekday()-dow)%7)).isoformat()

  keys=sorted(paid.keys()|logged.keys())
  worked_days=defaultdict(set)
  for (w,d) in paid:
   if duration(union(paid[(w,d)]))>0:worked_days[(w,week_start(d,pay_policy(w,d)))].add(d)
  week_regular=defaultdict(float)
  parts=defaultdict(float)   # (worker,day,activity,labor_class,bucket,annotated,tier) -> seconds
  direct_slices=defaultdict(list)  # (worker,day,activity) -> [(a,b)]
  ot_seconds=defaultdict(float)
  day_rows=[];slice_rows=[]
  for worker,day in keys:
   key=worker,day;pp=union(paid[key]);ll=union(logged[key]);ss=classify(pp,events[key])
   un=sum(b-a for a,b,act,cl in ss if act=='unattributed' or cl in ('unexplained','unattributed','conflict'))
   conflict=sum(b-a for a,b,act,cl in ss if cl=='conflict');match=duration(intersect(pp,ll))
   day_rows.append((worker,day,duration(pp),duration(ll),match,duration(ll)-match,un,conflict,duration(union(meals[key]))))
   if not ss:continue
   pol=pay_policy(worker,day);wk=week_start(day,pol)
   no_work_ivs=[]
   for sa,sb,act in segments[key]:
    ivs=no_work.get(act,[]);i=max(0,bisect_right(ivs,(sa,))-1)
    while i<len(ivs) and ivs[i][0]<sb:
     na,nb=ivs[i]
     if nb>sa:no_work_ivs.append((max(na,sa),min(nb,sb)))
     i+=1
   ctx=dict(no_output_annotated=_u([(a,b) for a,b,ann in no_output[worker] if ann]),
            no_output=_u([(a,b) for a,b,ann in no_output[worker] if not ann]),
            equipment=_u(equipment[worker]),system=_u(system[worker]),no_work=_u(no_work_ivs),idle_long=_u(idle_long[worker]))
   day_parts=classify_day(ss,ctx,policy)
   total=sum(b-a for a,b,*_ in day_parts)
   seventh=bool(pol.get('seventh_day_rule')) and len(worked_days[(worker,wk)])==7 and day==max(worked_days[(worker,wk)])
   st_end,dt_start=tier_cuts(total,week_regular[(worker,wk)],pol,seventh)
   week_regular[(worker,wk)]+=min(st_end,total)
   off=offsets.get(key,-25200)
   for a,b,payload,tier in tiers([(a,b,p) for a,b,*p in day_parts],st_end,dt_start):
    act,cl,bucket,ann=payload
    ctrl=pol_mod.control_for(bucket,policy,ann)
    slice_rows.append((worker,day,datetime.fromtimestamp(a,timezone.utc).isoformat(),datetime.fromtimestamp(b,timezone.utc).isoformat(),act,cl,b-a,bucket,ctrl,tier,_local(a,off),_local(b,off)))
    parts[(worker,day,act,cl,bucket,ann,tier)]+=b-a
    if bucket=='direct':direct_slices[(worker,day,act)].append((a,b))
    if tier!='ST':ot_seconds[(worker,day,tier)]+=b-a
  c.executemany('insert into time_day(worker,day,paid,logged,matched,outside,unattributed,conflict,meal) values(?,?,?,?,?,?,?,?,?)',day_rows)
  c.executemany('insert into time_slice(worker,day,start,end,activity,labor_class,seconds,bucket,control,tier,start_local,end_local) values(?,?,?,?,?,?,?,?,?,?,?,?)',slice_rows)

  # Pace: direct time beyond standard time for the lines completed that day is slow-pace time (cause not established).
  direct_total=defaultdict(float)
  for (w,d,act,cl,bucket,ann,tier),s in parts.items():
   if bucket=='direct':direct_total[(w,d,act)]+=s
  tol=1+policy['pace_tolerance_pct']/100
  worker_parts=defaultdict(list);part_rows=[]
  for (w,d,act,cl,bucket,ann,tier),s in sorted(parts.items()):
   pieces=[(bucket,s)]
   if bucket=='direct':
    D=direct_total[(w,d,act)];E=earned.get((w,d,act))
    if E is not None and D>0 and find_std(act,d):
     loss=max(0.0,D-E*tol);f=loss/D
     pieces=[('direct',s*(1-f)),('pace_loss',s*f)]
   for b_,sec in pieces:
    if sec<=0:continue
    ctrl=pol_mod.control_for(b_,policy,ann);prod=int(pol_mod.is_productive(b_,policy))
    part_rows.append((w,d,act,cl,b_,ctrl,tier,prod,sec))
    worker_parts[w].append((d,act,cl,b_,ctrl,tier,prod,sec))
  c.executemany('insert into time_part values(?,?,?,?,?,?,?,?,?)',part_rows)

  # Allocation: every source event -> worker paid time parts in its service window. Integer cents, exact.
  ins='insert into allocation(event_id,day,activity,labor_class,seconds,cents,method,bucket,control,tier,productive) values(?,?,?,?,?,?,?,?,?,?,?)'
  alloc_rows=[]
  def spread(e,amount,ss,weight,method):
   groups=defaultdict(float);secs=defaultdict(float)
   for d,act,cl,b_,ctrl,tier,prod,sec in ss:
    k=(d,act,cl,b_,ctrl,tier,prod);w=sec*weight(tier)
    if w>0:groups[k]+=w;secs[k]+=sec
   keys_=sorted(groups);amounts=allocate(amount,[groups[k] for k in keys_])
   if not amounts:return False
   for k,v in zip(keys_,amounts):
    d,act,cl,b_,ctrl,tier,prod=k;alloc_rows.append((e['id'],d,act,cl,secs[k],v,method,b_,ctrl,tier,prod))
   return True
  def unallocated(e,amount,bucket,method):
   ctrl='policy' if bucket=='paid_leave' else 'other' if bucket=='non_time' else 'undetermined'
   alloc_rows.append((e['id'],e['service_from'],'unallocated','unallocated',0,amount,method,bucket,ctrl,'NA',0))
  for e in c.execute('select * from event').fetchall():
   ss=[p for p in worker_parts.get(e['worker'],[]) if e['service_from']<=p[0]<e['service_to']]
   if e['component']=='paid_leave':unallocated(e,e['cents'],'paid_leave','paid_leave_not_worked');continue
   if e['component']=='agency_conversion_fee':unallocated(e,e['cents'],'non_time','non_time_charge');continue
   if not ss:unallocated(e,e['cents'],'unattributed','unallocated_no_eligible_driver');continue
   code=pay_code_of.get(e['id'])
   if code in PREMIUM_CODES:
    m=PREMIUM_CODES[code]
    if not spread(e,e['cents'],ss,lambda t:m.get(t,0),'premium_on_overtime_hours_v2'):spread(e,e['cents'],ss,lambda t:1,'premium_fallback_paid_time_v2')
    continue
   if e['component']=='agency_labor':
    r=agency_line[e['id']];rate=float(r.get('bill_rate') or 0);ot=float(r.get('ot_hours') or 0);dt=float(r.get('dt_hours') or 0);reg=float(r.get('reg_hours') or 0)
    straight,premium=allocate(e['cents'],[(reg+ot+dt)*rate,(0.5*ot+1.0*dt)*rate]) if rate and (ot or dt) else (e['cents'],0)
    spread(e,straight,ss,lambda t:1,'loaded_time_v2')
    if premium and not spread(e,premium,ss,lambda t:{'OT':0.5,'DT':1.0}.get(t,0),'premium_on_overtime_hours_v2'):spread(e,premium,ss,lambda t:1,'premium_fallback_paid_time_v2')
    continue
   spread(e,e['cents'],ss,lambda t:1,'loaded_time_v2')
  c.executemany(ins,alloc_rows)

  # Order attribution: direct (incl. slow-pace) cost of a worker-day-activity spread over the orders worked,
  # concurrent orders share elapsed time equally, and time between orders stays as its own row (no double counting).
  direct_cost=defaultdict(int)
  for r in c.execute("select e.worker,a.day,a.activity,sum(a.cents) cents from allocation a join event e on e.id=a.event_id where a.bucket in ('direct','pace_loss') group by 1,2,3"):direct_cost[(r[0],r[1],r[2])]=r[3]
  direct_secs=defaultdict(float)
  for r in c.execute("select worker,day,activity,sum(seconds) from time_part where bucket in ('direct','pace_loss') group by 1,2,3"):direct_secs[(r[0],r[1],r[2])]=r[3]
  orders_by=defaultdict(list);order_rows=[]
  for r in rows(c,'operations','task_worker'):
   if not r.get('worker_id') or not r.get('ends_at'):continue
   act=order_activity.get(r['warehouse_order_code']);a,b=interval(r)
   orders_by[(r['worker_id'],r['starts_at'][:10],act)].append((a,b,r['warehouse_order_code'],r.get('lines_confirmed') or 0))
  for key,C in direct_cost.items():
   ds=_u(direct_slices.get(key,[]));obs=orders_by.get(key,[])
   clipped=[(code,lines,[iv for iv in intersect([(a,b)],ds)]) for a,b,code,lines in obs]
   cuts=sorted({x for _,_,ivs in clipped for iv in ivs for x in iv})
   secs=defaultdict(float);line_of=defaultdict(int)
   for code,lines,_ in clipped:line_of[code]+=lines
   for x,y in zip(cuts,cuts[1:]):
    live=[code for code,_,ivs in clipped if any(a<=x and y<=b for a,b in ivs)]
    for code in live:secs[code]+=(y-x)/len(live)
   order_codes=sorted(line_of);S=direct_secs.get(key,0.0)
   rest=max(0.0,S-sum(secs.values()))
   weights=[secs[k] for k in order_codes]+[rest]
   amounts=allocate(C,weights) or ([0]*len(order_codes)+[C])
   for k,v in zip(order_codes+[None],amounts):
    order_rows.append((key[0],key[1],key[2],k,secs[k] if k else rest,line_of[k] if k else 0,v))
  c.executemany('insert into order_cost values(?,?,?,?,?,?,?)',order_rows)

  # Controls.
  ins_check='insert into check_result(name,period,source_cents,ledger_cents,difference_cents,note,unit) values(?,?,?,?,?,?,?)'
  payroll_ot=defaultdict(float);agency_ot=defaultdict(float)
  for r in rows(c,'finance','payroll_line'):
   if r['pay_code_id'] in ('pc-OTP','pc-DTP'):payroll_ot[r['period_id']]+=float(r.get('hours') or 0)
  for r in rows(c,'finance','agency_invoice_line'):
   if r['fee_type']=='labor' and r.get('posted_at'):agency_ot[period_for(r['service_from'])]+=float(r.get('ot_hours') or 0)+float(r.get('dt_hours') or 0)
  for p in periods.values():
   pid=p['id']
   for source in ['payroll_line','employer_cost','agency_invoice_line']:
    src=sum(cents(r['amount']) for r in rows(c,'finance',source) if (r.get('period_id') or period_for(r.get('service_from','')))==pid and (source!='agency_invoice_line' or r.get('posted_at')))
    total=c.execute('select coalesce(sum(cents),0) from event where period=? and source=?',(pid,source)).fetchone()[0]
    c.execute(ins_check,(source,pid,src,total,src-total,'Arithmetic matched; not controller approval. Posted disputed invoice remains in expense.','USD'))
   total=c.execute('select sum(cents) from event where period=?',(pid,)).fetchone()[0] or 0
   alloc=c.execute('select sum(a.cents) from allocation a join event e on e.id=a.event_id where period=?',(pid,)).fetchone()[0] or 0
   c.execute(ins_check,('allocation',pid,total,alloc,total-alloc,'Allocated plus explicit unallocated; integer cents.','USD'))
   wt=c.execute('select coalesce(sum(cents),0) from event where period=? and worker is not null',(pid,)).fetchone()[0]
   wa=c.execute('select coalesce(sum(a.cents),0) from allocation a join event e on e.id=a.event_id where e.period=? and e.worker is not null',(pid,)).fetchone()[0]
   c.execute(ins_check,('operator cost allocation',pid,wt,wa,wt-wa,'Every operator-linked source amount distributed to that operator\'s productive, unproductive or non-time buckets.','USD'))
   days=(p['starts_on'],p['ends_on'])
   paid_s=c.execute('select coalesce(sum(paid),0) from time_day where day>=? and day<?',days).fetchone()[0]
   part_s=c.execute('select coalesce(sum(seconds),0) from time_part where day>=? and day<?',days).fetchone()[0]
   c.execute(ins_check,('paid time partition',pid,round(paid_s),round(part_s),round(paid_s)-round(part_s),'Approved paid seconds versus the sum of mutually exclusive productive and unproductive time parts.','seconds'))
   ot_calc=sum(s for (w,d,t),s in ot_seconds.items() if days[0]<=d<days[1])
   ot_src=(payroll_ot[pid]+agency_ot[pid])*3600
   c.execute(ins_check,('overtime hours: timeclock vs payroll',pid,round(ot_src),round(ot_calc),round(ot_src)-round(ot_calc),'Overtime tiers re-derived from paid attendance under the assigned pay policy versus posted payroll OTP/DTP and agency OT hours. Posted payroll remains authoritative; differences are payroll review items.','seconds'))
   dc=c.execute("select coalesce(sum(a.cents),0) from allocation a join event e on e.id=a.event_id where a.bucket in ('direct','pace_loss') and a.day>=? and a.day<?",days).fetchone()[0]
   oc=c.execute('select coalesce(sum(cents),0) from order_cost where day>=? and day<?',days).fetchone()[0]
   c.execute(ins_check,('order cost attribution',pid,dc,oc,dc-oc,'Direct-work cost versus cost attributed to orders plus time between orders.','USD'))
   gl=sum(cents(r['debit_amount'])-cents(r['credit_amount']) for r in rows(c,'finance','gl_entry') if r['posting_status']=='posted' and r['journal_code']=='JE-'+p['period_code'] and str(r['account_code']).startswith('6'))
   c.execute(ins_check,('GL expense accounts 6xxx',pid,gl,total,gl-total,'Journal period mapped from JE-<period_code>; expense accounts 6xxx only. Aggregate match; cost-center and timing sign-off still pending.','USD'))
  c.execute('insert into calculation_run(version,input_batches,results,policy) values(?,?,?,?)',(VERSION,json.dumps([dict(r) for r in c.execute('select * from active_file order by namespace')]),json.dumps([dict(r) for r in c.execute('select * from check_result')]),pol_mod.calc_signature(policy)))
 c.close()

if __name__=='__main__':calculate()
