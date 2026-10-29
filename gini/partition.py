"""Paid-time partition for operator cost allocation (calculation version 2.0).

Each approved paid second of an operator's day receives exactly one
cost bucket, one control group and one pay tier (straight time, overtime or
double time). Inputs are source intervals; nothing is summed blindly, so the
partition always reconciles to paid hours.
"""
import math
from .maths import union

HOUR=3600.0

def split(a,b,intervals):
 """Split [a,b) by a sorted, non-overlapping interval list -> [(x,y,inside)]."""
 out=[];cur=a
 for c,d in intervals:
  if d<=cur:continue
  if c>=b:break
  if c>cur:out.append((cur,min(c,b),False))
  x,y=max(c,cur),min(d,b)
  if y>x:out.append((x,y,True))
  cur=max(cur,y)
  if cur>=b:break
 if cur<b:out.append((cur,b,False))
 return [p for p in out if p[1]>p[0]]

def subtract(left,right):
 out=[]
 for a,b in union(left):
  out+= [(x,y) for x,y,inside in split(a,b,union(right)) if not inside]
 return out

def rest_breaks(paid_seconds):
 """California-style count: one rest period per 4 hours worked or major fraction (3.5h minimum)."""
 h=paid_seconds/HOUR
 return 0 if h<3.5 else math.ceil((h-2)/4)

def tier_cuts(paid_seconds,week_regular_before,pol,seventh_day):
 """Return (straight_time_end, double_time_start) positions in seconds from the start of the day's paid time."""
 daily=pol.get('daily_ot_threshold_hours');double=pol.get('daily_dt_threshold_hours');weekly=pol.get('weekly_ot_threshold_hours') or 40
 if seventh_day:
  return 0.0,8*HOUR
 st=paid_seconds
 if daily:st=min(st,daily*HOUR)
 st=min(st,max(0.0,weekly*HOUR-week_regular_before))
 dt=double*HOUR if double else math.inf
 return st,dt

def tiers(parts,st_end,dt_start):
 """Cut chronological parts [(a,b,payload)] at cumulative paid positions."""
 out=[];pos=0.0
 for a,b,payload in parts:
  cur=a
  for cut,name in ((st_end,'ST'),(dt_start,'OT'),(math.inf,'DT')):
   if cur>=b:break
   if pos<cut:
    take=min(b,cur+(cut-pos))
    out.append((cur,take,payload,name));pos+=take-cur;cur=take
 return out

def classify_day(slices,ctx,policy):
 """slices: chronological [(a,b,activity,labor_class)] covering paid time.
 ctx: interval sets for this worker-day. Returns [(a,b,activity,labor_class,bucket,annotated)]."""
 parts=[]
 def add(a,b,act,cl,bucket,annotated=False):
  if b>a:parts.append([a,b,act,cl,bucket,annotated])
 for a,b,act,cl in slices:
  if cl=='direct':
   for x,y,ann in split(a,b,ctx['no_output_annotated']):
    if ann:add(x,y,act,cl,'not_performed',True);continue
    for p,q,plain in split(x,y,ctx['no_output']):add(p,q,act,cl,'not_performed' if plain else 'direct')
  elif cl=='indirect':add(a,b,act,cl,'indirect')
  elif cl=='training':add(a,b,act,cl,'training')
  elif cl=='break':add(a,b,act,cl,'_personal')
  elif cl=='waiting':add(a,b,act,cl,'wait_material')
  elif act=='act-UNEXPLAINED_IDLE':
   for x,y,eq in split(a,b,ctx['equipment']):
    if eq:add(x,y,act,cl,'wait_equipment');continue
    for p,q,sysd in split(x,y,ctx['system']):
     if sysd:add(p,q,act,cl,'wait_system');continue
     for r,s,empty in split(p,q,ctx['no_work']):
      if empty:add(r,s,act,cl,'wait_work');continue
      for u,v,long_ in split(r,s,ctx['idle_long']):add(u,v,act,cl,'idle_excessive' if long_ else 'idle_short')
  else:
   for x,y,sysd in split(a,b,ctx['system']):add(x,y,act,cl,'wait_system' if sysd else '_gap')
 # Authorized rest allowance: personal reason codes first, then unpunched gaps, chronologically.
 allowance=rest_breaks(sum(p[1]-p[0] for p in parts))*policy['rest_minutes_per_4h']*60
 out=[]
 for target,within,beyond in (('_personal','rest_break','break_unscheduled'),('_gap','rest_break','unattributed')):
  for p in parts:
   if p[4]!=target:continue
   d=p[1]-p[0];take=min(d,allowance);allowance-=take
   if take>0:out.append((p[0],p[0]+take,p[2],p[3],within,False))
   if d-take>0:out.append((p[0]+take,p[1],p[2],p[3],beyond,False))
 out+= [tuple(p) for p in parts if p[4] not in ('_personal','_gap')]
 return sorted(out)
