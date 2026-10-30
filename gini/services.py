from collections import defaultdict
from decimal import Decimal
from .db import rows
from .maths import cents,allocate

def query(c,sql,args=()):return [dict(r) for r in c.execute(sql,args)]
def summary(c,period=''):
 where=' WHERE period=?' if period else '';args=(period,) if period else ()
 components=query(c,'SELECT component,sum(cents) cents FROM event'+where+' GROUP BY component ORDER BY cents DESC',args)
 trend=query(c,'SELECT period,sum(cents) cents FROM event'+where+' GROUP BY period',args)
 classes=query(c,'SELECT a.labor_class,sum(a.cents) cents FROM allocation a JOIN event e ON e.id=a.event_id'+(' WHERE e.period=?' if period else '')+' GROUP BY a.labor_class ORDER BY cents DESC',args)
 sources=query(c,'SELECT source,sum(cents) cents FROM event'+where+' GROUP BY source',args)
 total=sum(r['cents'] for r in components)
 tasks=c.execute('SELECT count(*) FROM task'+where,args).fetchone()[0]
 un=sum(r['cents'] for r in classes if r['labor_class'] in ('unallocated','unattributed','unexplained','conflict'))
 return dict(total_cents=total,components=components,trend=trend,classes=classes,sources=sources,completed_lines=tasks,cost_per_line=total/100/tasks if tasks else None,unattributed_cents=un,cost_basis='Recorded actual • includes posted disputed invoices and allocated employer expenses',calculation_version='1.0')
def ledger(c,period='',worker='',component='',search='',limit=None,offset=0):
 conditions=[];args=[]
 for k,v in [('period',period),('worker',worker),('component',component)]:
  if v:conditions.append(k+'=?');args.append(v)
 if search:conditions.append('(id LIKE ? OR component LIKE ?)');args.extend(['%'+search+'%']*2)
 where=' WHERE '+' AND '.join(conditions) if conditions else ''
 total=c.execute('SELECT count(*),coalesce(sum(cents),0) FROM event'+where,args).fetchone()
 sql='SELECT * FROM event'+where+' ORDER BY period,worker,component,id'
 if limit:sql+=' LIMIT ? OFFSET ?';args.extend([limit,offset])
 return query(c,sql,args),total[0],total[1]
def activities(c,period=''):
 args=(period,) if period else ();where=' WHERE e.period=?' if period else ''
 money=query(c,'SELECT a.activity,sum(a.cents) cents FROM allocation a JOIN event e ON e.id=a.event_id'+where+' GROUP BY a.activity',args)
 qty={r['activity']:r for r in query(c,'SELECT activity,count(*) lines,sum(pieces) pieces FROM task'+(' WHERE period=?' if period else '')+' GROUP BY activity',args)}
 names={r['id']:r['activity_name'] for r in rows(c,'foundation','activity')}
 standards=list(rows(c,'intelligence','standard'));earned=defaultdict(Decimal)
 for t in query(c,'SELECT activity,day,count(*) lines FROM task'+(' WHERE period=?' if period else '')+' GROUP BY activity,day',args):
  ss=[s for s in standards if s['activity_id']==t['activity'] and s['status'] in ('validated','approved') and s.get('approved_by') and s['valid_from']<=t['day'] and (not s['valid_to'] or t['day']<s['valid_to']) and s.get('units_per_hour')]
  if len(ss)==1:earned[t['activity']]+=Decimal(t['lines'])/Decimal(str(ss[0]['units_per_hour']))
 out=[]
 for r in money:
  aid=r['activity'];q=qty.get(aid,{});out.append(dict(activity=aid,name=names.get(aid,aid),cents=r['cents'],lines=q.get('lines',0),pieces=q.get('pieces',0),cost_per_line=r['cents']/100/q['lines'] if q.get('lines') else None,earned_hours=float(earned[aid]) if aid in earned else None))
 return sorted(out,key=lambda r:r['cents'],reverse=True)
def customers(c,period=''):
 # Only activity-attributable allocations are assigned. Remaining site costs stay unassigned.
 acts=activities(c,period);args=(period,) if period else ()
 money=defaultdict(int);qty=defaultdict(int);by_activity=defaultdict(list)
 for r in query(c,'SELECT activity,customer,count(*) n FROM task'+(' WHERE period=?' if period else '')+' GROUP BY activity,customer ORDER BY activity,customer',args):by_activity[r['activity']].append(r)
 for a in acts:
  qq=by_activity.get(a['activity'])
  if not qq:continue
  allocations=allocate(a['cents'],[r['n'] for r in qq])
  for r,amount in zip(qq,allocations):money[r['customer']]+=amount;qty[r['customer']]+=r['n']
 billed=defaultdict(int)
 for r in rows(c,'intelligence','billing_line'):
  if not period or r['period_id']==period:billed[r['customer_id']]+=cents(r['amount'])
 out=[]
 for r in rows(c,'intelligence','customer'):
  k=r['id'];out.append(dict(customer=k,name=r['customer_name'],lines=qty[k],labor_cents=money[k],billed_cents=billed[k],contribution_cents=billed[k]-money[k]))
 return out,summary(c,period)['total_cents']-sum(r['labor_cents'] for r in out)
def bridge(c,period='',version=''):
 budgets=[r for r in rows(c,'intelligence','budget') if (not period or r['period_id']==period)]
 versions=sorted({r['budget_version'] for r in budgets});version=version or (versions[-1] if versions else '')
 budgets=[r for r in budgets if r['budget_version']==version]
 baseline=sum(cents(r['budget_amount']) for r in budgets);vol=Decimal(0);mix=Decimal(0)
 counts={(r[0],r[1]):r[2] for r in c.execute('SELECT period,activity,count(*) FROM task GROUP BY period,activity')}
 by_period={}  # activities() is the expensive part; compute it once per period, not once per budget line
 for b in budgets:
  actual=counts.get((b['period_id'],b['activity_id']),0)
  rate=Decimal(str(b['base_hourly_rate']));h=Decimal(str(b['standard_hours_per_unit']))
  vol+=(Decimal(actual)-Decimal(str(b['volume'])))*h*rate
  if b['period_id'] not in by_period:by_period[b['period_id']]={r['activity']:r for r in activities(c,b['period_id'])}
  activity=by_period[b['period_id']].get(b['activity_id'])
  if activity and activity['earned_hours'] is not None:mix+=(Decimal(str(activity['earned_hours']))-Decimal(actual)*h)*rate
 actual=summary(c,period)['total_cents'];v=cents(vol);m=cents(mix)
 return dict(version=version,versions=versions,budget_cents=baseline,actual_cents=actual,steps=[dict(label='Budget',cents=baseline),dict(label='Volume',cents=v),dict(label='Standard change',cents=m),dict(label='Other / unexplained',cents=actual-baseline-v-m),dict(label='Actual',cents=actual)],note='Other / unexplained includes rate, efficiency, indirect time, non-comparable expense scope and all interactions. It is not a diagnosed cause or a saving. Standards are retrospectively validated; this is not an as-known-at-the-time benchmark.')
