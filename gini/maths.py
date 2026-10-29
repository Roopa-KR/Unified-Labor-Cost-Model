from decimal import Decimal,ROUND_HALF_UP
from datetime import datetime,timezone

def cents(v):
 if v is None:raise ValueError('Missing financial amount')
 d=Decimal(str(v))
 if not d.is_finite():raise ValueError('Non-finite financial amount')
 return int((d*100).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
def allocate(amount,weights):
 """Largest remainder in integer cents, including signed corrections."""
 ws=[Decimal(str(w)) for w in weights]
 if any(w<0 for w in ws):raise ValueError('Negative weight')
 total=sum(ws)
 if not total:return []
 exact=[abs(amount)*w/total for w in ws];out=[int(x) for x in exact]
 for i in sorted(range(len(ws)),key=lambda i:exact[i]-out[i],reverse=True)[:abs(amount)-sum(out)]:out[i]+=1
 return [x*(-1 if amount<0 else 1) for x in out]
def stamp(s):
 d=datetime.fromisoformat(s)
 if d.tzinfo is None:raise ValueError('Timezone offset required')
 return d.astimezone(timezone.utc).timestamp()
def interval(r):
 a,b=stamp(r['starts_at']),stamp(r['ends_at'])
 if b<a:raise ValueError('Negative duration')
 return a,b

def union(parts):
 out=[]
 for a,b in sorted(parts):
  if b<a:raise ValueError('Negative interval')
  if out and a<=out[-1][1]:out[-1]=(out[-1][0],max(b,out[-1][1]))
  else:out.append((a,b))
 return out

def duration(parts):return sum(b-a for a,b in union(parts))
def intersect(left,right):
 return union([(max(a,c),min(b,d)) for a,b in union(left) for c,d in union(right) if max(a,c)<min(b,d)])
def classify(paid,events):
 """Partition paid intervals. Conflicting classifications remain unattributed."""
 out=[]
 for pa,pb in union(paid):
  cuts=sorted({pa,pb}|{max(pa,a) for a,b,_,_ in events if a<pb and b>pa}|{min(pb,b) for a,b,_,_ in events if a<pb and b>pa})
  for a,b in zip(cuts,cuts[1:]):
   labels={(act,cl) for x,y,act,cl in events if x<b and y>a}
   act,cl=next(iter(labels)) if len(labels)==1 else ('unattributed','conflict' if len(labels)>1 else 'unattributed')
   out.append((a,b,act,cl))
 return out

def overtime(hours,daily=8,double=12,weekly=40,seventh=True,exempt=False):
 """Illustrative non-exempt ordinary workweek check, not a payroll replacement."""
 if len(hours)!=7 or any(h<0 for h in hours):raise ValueError('Seven nonnegative workdays required')
 if exempt:return sum(hours),0,0
 reg=ot=dt=0
 for i,h in enumerate(hours):
  if seventh and i==6 and all(x>0 for x in hours):r=0;o=min(h,8);d=max(0,h-8)
  else:
   r=min(h,daily) if daily is not None else h
   d=max(0,h-double) if double is not None else 0
   o=h-r-d
  reg+=r;ot+=o;dt+=d
 extra=max(0,reg-weekly);return reg-extra,ot+extra,dt
