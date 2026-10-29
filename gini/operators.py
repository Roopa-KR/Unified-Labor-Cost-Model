"""Operator-level labor cost services: one set of calculations shared by every page, export and API."""
from collections import defaultdict
import json
from .db import rows
from .policy import BUCKETS, CONTROLS, CONTROL_ORDER, BUCKET_ORDER, load as load_policy

COMPONENT_GROUPS = [
    ('base_wages', 'Base wages', {'base'}),
    ('overtime', 'Overtime premium', {'overtime_premium', 'doubletime_premium'}),
    ('premiums', 'Differentials, bonus and premiums', {'differential', 'bonus', 'meal_rest_premium'}),
    ('paid_leave', 'Paid leave', {'paid_leave'}),
    ('employer_taxes', 'Employer taxes', {'employer_social_security', 'employer_medicare', 'employer_futa', 'employer_suta'}),
    ('benefits', 'Benefits', {'employer_health', 'employer_retirement'}),
    ('insurance', "Workers' comp insurance", {'employer_workers_comp'}),
    ('agency', 'Agency billing (incl. agency burden)', {'agency_labor', 'agency_credit'}),
    ('agency_fees', 'Agency fees', {'agency_conversion_fee'}),
]
GROUP_OF = {comp: key for key, _label, comps in COMPONENT_GROUPS for comp in comps}
GROUP_LABEL = {key: label for key, label, _ in COMPONENT_GROUPS}
TIER_LABEL = {'ST': 'Straight time', 'OT': 'Overtime', 'DT': 'Double time', 'NA': 'Not time-based'}
DIRECT_BUCKETS = ('direct', 'pace_loss')


class Filters:
    """Period / date range / shift / employment-type / search filter shared by operator pages."""
    def __init__(self, c, args, period=''):
        self.period = period
        bounds = c.execute('select min(day),max(day) from time_day').fetchone()
        self.min_day, self.max_day = bounds[0], bounds[1]
        start, end = args.get('from', ''), args.get('to', '')
        if period:
            p = next(r for r in rows(c, 'finance', 'payroll_period') if r['id'] == period)
            lo, hi = p['starts_on'], _prev(p['ends_on'])
        else:
            lo, hi = self.min_day, self.max_day
        self.start = max(lo, start) if _is_day(start) else lo
        self.end = min(hi, end) if _is_day(end) else hi
        if self.start > self.end:
            self.start, self.end = lo, hi
        self.custom_dates = (self.start, self.end) != (lo, hi)
        self.shift = args.get('shift', '') if args.get('shift', '') in ('DAY', 'EVE') else ''
        self.emp = args.get('emp', '') if args.get('emp', '') in ('permanent', 'temporary_agency') else ''
        self.q = (args.get('q', '') or '').strip()[:40]
        self.flagged = args.get('flagged') == '1'

    @property
    def end_excl(self):
        return _next(self.end)

    def query(self):
        out = {}
        if self.period: out['period'] = self.period
        if self.custom_dates: out.update({'from': self.start, 'to': self.end})
        for k in ('shift', 'emp', 'q'):
            if getattr(self, k): out[k] = getattr(self, k)
        if self.flagged: out['flagged'] = '1'
        return out


def _is_day(s):
    return isinstance(s, str) and len(s) == 10 and s[4] == '-' and s[7] == '-' and s.replace('-', '').isdigit()

def _shift(day, n):
    from datetime import date, timedelta
    return (date.fromisoformat(day) + timedelta(n)).isoformat()

def _prev(day): return _shift(day, -1)
def _next(day): return _shift(day, 1)


def workers(c):
    """Latest employment record per worker (job, shift, employment type)."""
    out = {}
    for r in rows(c, 'foundation', 'employment'):
        cur = out.get(r['worker_id'])
        if not cur or r['valid_from'] >= cur['valid_from']:
            out[r['worker_id']] = r
    return {w: dict(worker=w, job=(r.get('job_code') or '').replace('_', ' ').title(), shift=r.get('shift_group'),
                    emp=r.get('employment_type'), agency=r.get('agency_id'), hire_date=r.get('hire_date'),
                    valid_from=r['valid_from']) for w, r in out.items()}


def activity_names(c):
    return {r['id']: r['activity_name'] for r in rows(c, 'foundation', 'activity')}


def _cost_where(f, alias='a', event='e'):
    """Cost rows: accounting period when chosen, plus explicit date range on allocation day."""
    cond, args = [], []
    if f.period:
        cond.append(f'{event}.period=?'); args.append(f.period)
    if f.custom_dates or not f.period:
        cond.append(f'{alias}.day>=? and {alias}.day<?'); args += [f.start, f.end_excl]
    return ' and '.join(cond) or '1=1', args


def _blank():
    return dict(cost=0, cost_bucket=defaultdict(int), cost_control=defaultdict(int), cost_tier=defaultdict(int),
                cost_group=defaultdict(int), cost_productive=0, hours=0.0, h_bucket=defaultdict(float),
                h_control=defaultdict(float), h_tier=defaultdict(float), h_productive=0.0, lines=0, pieces=0.0,
                orders=0, earned_h=0.0, days=0, meal_h=0.0, cost_direct=0, h_direct=0.0,
                cost_bc=defaultdict(int), h_bc=defaultdict(float),
                act=defaultdict(lambda: dict(lines=0, pieces=0.0, earned_h=0.0, h_direct=0.0, h_pace=0.0,
                                             h_not=0.0, cost_direct=0, cost_all=0, h_all=0.0)))


def metrics(c, f, only=None):
    """Per-operator loaded cost, hours, output and standard comparison for the filter."""
    out = defaultdict(_blank)
    where, args = _cost_where(f)
    wsql, wargs = (' and e.worker=?', [only]) if only else ('', [])
    for r in c.execute(f'select e.worker,e.component,a.bucket,a.control,a.tier,a.productive,a.activity,sum(a.cents) '
                       f'from allocation a join event e on e.id=a.event_id where e.worker is not null and {where}{wsql} '
                       f'group by 1,2,3,4,5,6,7', args + wargs):
        w, comp, bucket, ctrl, tier, prod, act, cents = r
        m = out[w]
        m['cost'] += cents; m['cost_bucket'][bucket] += cents; m['cost_bc'][(bucket, ctrl)] += cents; m['cost_control'][ctrl] += cents
        m['cost_tier'][tier] += cents; m['cost_group'][GROUP_OF.get(comp, 'other')] += cents
        if prod: m['cost_productive'] += cents
        if bucket in DIRECT_BUCKETS:
            m['cost_direct'] += cents; m['act'][act]['cost_direct'] += cents
        if bucket in DIRECT_BUCKETS or bucket == 'not_performed':
            m['act'][act]['cost_all'] += cents
    targs = [f.start, f.end_excl] + wargs
    tw = ' and worker=?' if only else ''
    for w, bucket, ctrl, tier, prod, act, sec in c.execute(
            f'select worker,bucket,control,tier,productive,activity,sum(seconds) from time_part where day>=? and day<?{tw} group by 1,2,3,4,5,6', targs):
        m = out[w]; h = sec / 3600
        m['hours'] += h; m['h_bucket'][bucket] += h; m['h_bc'][(bucket, ctrl)] += h; m['h_control'][ctrl] += h; m['h_tier'][tier] += h
        if prod: m['h_productive'] += h
        if bucket in DIRECT_BUCKETS:
            m['h_direct'] += h; m['act'][act]['h_direct'] += h
            if bucket == 'pace_loss': m['act'][act]['h_pace'] += h
        if bucket == 'not_performed': m['act'][act]['h_not'] += h
        if bucket in DIRECT_BUCKETS or bucket == 'not_performed': m['act'][act]['h_all'] += h
    for w, act, n, pcs, es, orders in c.execute(
            f'select worker,activity,count(*),sum(pieces),sum(coalesce(earned_seconds,0)),count(distinct order_code) from task where worker is not null and day>=? and day<?{tw} group by 1,2', targs):
        m = out[w]; m['lines'] += n; m['pieces'] += pcs or 0; m['earned_h'] += es / 3600; m['orders'] += orders
        a = m['act'][act]; a['lines'] += n; a['pieces'] += pcs or 0; a['earned_h'] += es / 3600
    for w, days, meal in c.execute(f'select worker,count(*),sum(meal) from time_day where paid>0 and day>=? and day<?{tw} group by 1', targs):
        out[w]['days'] = days; out[w]['meal_h'] = (meal or 0) / 3600
    policy = load_policy(c)
    for w, m in out.items():
        finish(m, policy)
    return out


def finish(m, policy):
    st_h = m['h_tier'].get('ST', 0)
    m['st_rate'] = m['cost_tier'].get('ST', 0) / st_h if st_h else None          # cents per hour
    ot_h = m['h_tier'].get('OT', 0)
    m['ot_rate'] = m['cost_tier'].get('OT', 0) / ot_h if ot_h else None
    timed = m['cost'] - m['cost_tier'].get('NA', 0)
    m['loaded_rate'] = timed / m['hours'] if m['hours'] else None
    m['h_unproductive'] = m['hours'] - m['h_productive']
    m['cost_non_time'] = m['cost_control'].get('other', 0)
    m['cost_unproductive'] = m['cost'] - m['cost_productive'] - m['cost_non_time']
    m['utilization'] = m['h_productive'] / m['hours'] if m['hours'] else None
    m['pace'] = m['earned_h'] / m['h_direct'] if m['h_direct'] and m['earned_h'] else None
    m['cost_per_line'] = m['cost'] / m['lines'] if m['lines'] else None
    m['cost_per_piece'] = m['cost'] / m['pieces'] if m['pieces'] else None
    m['cost_per_order'] = m['cost'] / m['orders'] if m['orders'] else None
    m['direct_per_line'] = m['cost_direct'] / m['lines'] if m['lines'] else None
    if m['st_rate'] is not None and m['earned_h']:
        m['std_cost'] = round(m['earned_h'] * m['st_rate'])
        m['std_var'] = m['cost_direct'] - m['std_cost']
        m['eff_var'] = round((m['h_direct'] - m['earned_h']) * m['st_rate'])
        m['rate_var'] = m['std_var'] - m['eff_var']
        m['std_per_line'] = m['std_cost'] / m['lines'] if m['lines'] else None
    else:
        m['std_cost'] = m['std_var'] = m['eff_var'] = m['rate_var'] = m['std_per_line'] = None
    for a in m['act'].values():
        a['pace'] = a['earned_h'] / a['h_direct'] if a['h_direct'] and a['earned_h'] else None
        a['std_cost'] = round(a['earned_h'] * m['st_rate']) if m['st_rate'] is not None and a['earned_h'] else None
        a['variance'] = a['cost_direct'] - a['std_cost'] if a['std_cost'] is not None else None
        a['cost_per_line'] = a['cost_direct'] / a['lines'] if a['lines'] else None
    oc = m['h_control'].get('operator', 0)
    flags = []
    if m['pace'] is not None and m['pace'] * 100 < policy['alert_pace_pct']:
        flags.append(('pace', f"Pace {m['pace'] * 100:.0f}%"))
    if m['utilization'] is not None and m['utilization'] * 100 < policy['alert_utilization_pct']:
        flags.append(('utilization', f"Utilization {m['utilization'] * 100:.0f}%"))
    if m['hours'] and oc / m['hours'] * 100 > policy['alert_operator_controlled_pct']:
        flags.append(('operator', f"Operator-controlled {oc:.1f} h"))
    m['flags'] = flags
    m['distribution'] = [dict(control=k, label=CONTROLS[k][0], color=CONTROLS[k][1], cents=m['cost_control'].get(k, 0),
                              hours=m['h_control'].get(k, 0)) for k in CONTROL_ORDER]
    return m


def operator_rows(c, f, sort='cost', desc=True):
    meta = workers(c)
    data = metrics(c, f)
    out = []
    for w, m in data.items():
        info = meta.get(w, dict(worker=w, job='', shift='', emp=''))
        if f.shift and info.get('shift') != f.shift: continue
        if f.emp and info.get('emp') != f.emp: continue
        if f.q and f.q.lower() not in w.lower(): continue
        if f.flagged and not m['flags']: continue
        if not m['hours'] and not m['cost']: continue
        out.append(dict(info, **m))
    keys = {'worker': lambda r: r['worker'], 'cost': lambda r: r['cost'], 'hours': lambda r: r['hours'],
            'utilization': lambda r: r['utilization'] if r['utilization'] is not None else -1,
            'pace': lambda r: r['pace'] if r['pace'] is not None else -1,
            'unproductive': lambda r: r['h_unproductive'], 'cost_per_line': lambda r: r['cost_per_line'] or 0,
            'std_var': lambda r: r['std_var'] if r['std_var'] is not None else -1e18,
            'operator': lambda r: r['h_control'].get('operator', 0), 'lines': lambda r: r['lines']}
    if sort in BUCKETS:
        keyf = lambda r: r['h_bucket'].get(sort, 0)
    else:
        keyf = keys.get(sort, keys['cost'])
    out.sort(key=keyf, reverse=desc)
    return out


def site_totals(rows_):
    t = _blank()
    for r in rows_:
        for k in ('cost', 'cost_productive', 'hours', 'h_productive', 'lines', 'pieces', 'orders', 'earned_h',
                  'cost_direct', 'h_direct', 'days', 'meal_h'):
            t[k] += r[k]
        for k in ('cost_bucket', 'cost_control', 'cost_tier', 'cost_group', 'h_bucket', 'h_control', 'h_tier', 'cost_bc', 'h_bc'):
            for kk, v in r[k].items():
                t[k][kk] += v
        for act, a in r['act'].items():
            for kk in ('lines', 'pieces', 'earned_h', 'h_direct', 'h_pace', 'h_not', 'cost_direct', 'cost_all', 'h_all'):
                t['act'][act][kk] += a[kk]
    std = sum(r['std_cost'] or 0 for r in rows_)
    eff = sum(r['eff_var'] or 0 for r in rows_)
    t['operators'] = len(rows_)
    t['flagged'] = sum(1 for r in rows_ if r['flags'])
    return t, std, eff


def bucket_rows(m):
    """Ordered (bucket, control) table: hours, cost, effective loaded rate."""
    keys = set(m['cost_bc']) | set(m['h_bc'])
    out = []
    for k in sorted(keys, key=lambda k: (CONTROL_ORDER.index(k[1]), BUCKET_ORDER.index(k[0]))):
        h, cts = m['h_bc'].get(k, 0), m['cost_bc'].get(k, 0)
        if abs(h) < 1e-9 and not cts: continue
        label = BUCKETS[k[0]][0]
        if k[0] == 'not_performed':
            label = 'Work not performed, supervisor noted' if k[1] == 'operational' else 'Work not performed, no reason'
        out.append(dict(bucket=k[0], control=k[1], label=label, control_label=CONTROLS[k[1]][0],
                        color=CONTROLS[k[1]][1], hours=h, cents=cts, rate=cts / h if h >= 0.05 else None,
                        share=cts / m['cost'] if m['cost'] else 0))
    return out


def payroll_ot_check(c, worker, f):
    """Overtime hours re-derived from paid attendance vs posted payroll / agency OT hours."""
    days = (f.start, f.end_excl)
    calc = c.execute("select coalesce(sum(seconds),0) from time_part where worker=? and tier in ('OT','DT') and day>=? and day<?", (worker,) + days).fetchone()[0] / 3600
    posted = 0.0
    for r in rows(c, 'finance', 'payroll_line'):
        if r['worker_id'] == worker and r['pay_code_id'] in ('pc-OTP', 'pc-DTP') and r['earned_from'] < days[1] and r['earned_to'] > days[0]:
            posted += float(r.get('hours') or 0)
    for r in rows(c, 'finance', 'agency_invoice_line'):
        if r['worker_id'] == worker and r['fee_type'] == 'labor' and r.get('posted_at') and r['service_from'] < days[1] and r['service_to'] > days[0]:
            posted += float(r.get('ot_hours') or 0) + float(r.get('dt_hours') or 0)
    whole_weeks = not f.custom_dates
    return dict(calculated=calc, posted=posted, difference=posted - calc, comparable=whole_weeks)


def rate_buildup(c, worker, f, m):
    """Loaded hourly rate by component group, per paid hour, plus source base rates."""
    base = None
    for r in rows(c, 'finance', 'worker_rate'):
        if r['worker_id'] == worker and r['pay_code_id'] == 'pc-REG' and r['valid_from'] <= f.end and (not r.get('valid_to') or f.start < r['valid_to']):
            base = float(r['rate_amount'])
    bill = None
    for r in rows(c, 'finance', 'agency_invoice_line'):
        if r['worker_id'] == worker and r['fee_type'] == 'labor':
            bill = float(r['bill_rate'])
    groups = [dict(key=k, label=label, cents=m['cost_group'].get(k, 0),
                   per_hour=m['cost_group'].get(k, 0) / m['hours'] if m['hours'] else None)
              for k, label, _ in COMPONENT_GROUPS if m['cost_group'].get(k, 0)]
    tiers = [dict(tier=t, label=TIER_LABEL[t], hours=m['h_tier'].get(t, 0), cents=m['cost_tier'].get(t, 0),
                  rate=m['cost_tier'].get(t, 0) / m['h_tier'][t] if m['h_tier'].get(t) else None)
             for t in ('ST', 'OT', 'DT', 'NA') if m['h_tier'].get(t) or m['cost_tier'].get(t)]
    return dict(base_rate=base, bill_rate=bill, groups=groups, tiers=tiers)


def daily_rows(c, worker, f):
    names = activity_names(c)
    shifts = {r['business_date']: r['shift_id'].rsplit('-', 1)[-1] for r in rows(c, 'finance', 'schedule') if r['worker_id'] == worker}
    days = defaultdict(lambda: dict(hours=0.0, h_prod=0.0, h_control=defaultdict(float), cost=0, c_control=defaultdict(int),
                                    lines=0, earned_h=0.0, h_direct=0.0, ot_h=0.0, acts=set()))
    for day, ctrl, prod, bucket, tier, act, s in c.execute('select day,control,productive,bucket,tier,activity,sum(seconds) from time_part where worker=? and day>=? and day<? group by 1,2,3,4,5,6', (worker, f.start, f.end_excl)):
        d = days[day]; h = s / 3600; d['hours'] += h; d['h_control'][ctrl] += h
        if prod: d['h_prod'] += h
        if bucket in DIRECT_BUCKETS: d['h_direct'] += h; d['acts'].add(names.get(act, act))
        if tier != 'ST': d['ot_h'] += h
    for day, ctrl, cents in c.execute("select a.day,a.control,sum(a.cents) from allocation a join event e on e.id=a.event_id where e.worker=? and a.day>=? and a.day<? and a.tier<>'NA' group by 1,2", (worker, f.start, f.end_excl)):
        days[day]['cost'] += cents; days[day]['c_control'][ctrl] += cents
    for day, n, es in c.execute('select day,count(*),sum(coalesce(earned_seconds,0)) from task where worker=? and day>=? and day<? group by 1', (worker, f.start, f.end_excl)):
        days[day]['lines'] += n; days[day]['earned_h'] += es / 3600
    out = []
    for day in sorted(days):
        d = days[day]
        if not d['hours']: continue
        out.append(dict(day=day, shift=shifts.get(day, ''), hours=d['hours'], h_prod=d['h_prod'], h_unprod=d['hours'] - d['h_prod'],
                        cost=d['cost'], lines=d['lines'], ot_h=d['ot_h'], activities=', '.join(sorted(d['acts'])),
                        pace=d['earned_h'] / d['h_direct'] if d['h_direct'] and d['earned_h'] else None,
                        utilization=d['h_prod'] / d['hours'] if d['hours'] else None,
                        distribution=[dict(control=k, label=CONTROLS[k][0], color=CONTROLS[k][1], cents=d['c_control'].get(k, 0), hours=d['h_control'].get(k, 0)) for k in CONTROL_ORDER]))
    return out


def day_detail(c, worker, day):
    names = activity_names(c)
    slices = [dict(r) for r in c.execute('select * from time_slice where worker=? and day=? order by start', (worker, day))]
    for s in slices:
        s['name'] = names.get(s['activity'], s['activity']); s['bucket_label'] = BUCKETS.get(s['bucket'], (s['bucket'],))[0]
        s['control_label'] = CONTROLS.get(s['control'], (s['control'],))[0]
    meals = [dict(start_local=r['starts_at'], end_local=r['ends_at'], seconds=r['duration_seconds'])
             for r in rows(c, 'finance', 'attendance_interval') if r['worker_id'] == worker and r['business_date'] == day and not r['paid']]
    time_by = defaultdict(float)
    keep = lambda act, bucket: act if bucket in DIRECT_BUCKETS + ('not_performed',) else ''
    for act, bucket, ctrl, s in c.execute('select activity,bucket,control,sum(seconds) from time_part where worker=? and day=? group by 1,2,3', (worker, day)):
        time_by[(keep(act, bucket), bucket, ctrl)] += s
    cost_by = defaultdict(int); rate = {}
    for act, bucket, ctrl, cents in c.execute("select a.activity,a.bucket,a.control,sum(a.cents) from allocation a join event e on e.id=a.event_id where e.worker=? and a.day=? and a.tier<>'NA' group by 1,2,3", (worker, day)):
        cost_by[(keep(act, bucket), bucket, ctrl)] += cents
    tasks = {r[0]: r[1:] for r in c.execute('select activity,count(*),sum(pieces),sum(coalesce(earned_seconds,0)) from task where worker=? and day=? group by 1', (worker, day))}
    activities = []
    for key in sorted(set(time_by) | set(cost_by), key=lambda k: (BUCKET_ORDER.index(k[1]) if k[1] in BUCKET_ORDER else 99, k[0])):
        act, bucket, ctrl = key
        h = time_by.get(key, 0) / 3600; cts = cost_by.get(key, 0)
        activities.append(dict(activity=act, name=names.get(act, act) if act else '', bucket=bucket, bucket_label=BUCKETS[bucket][0], control=ctrl,
                               control_label=CONTROLS[ctrl][0], hours=h, cents=cts, rate=cts / h if h >= 0.05 else None))
    tiers = {t: (s, cts) for t, s, cts in c.execute("""select tier,(select sum(seconds) from time_part p where p.worker=? and p.day=? and p.tier=a.tier),sum(a.cents)
        from allocation a join event e on e.id=a.event_id where e.worker=? and a.day=? and a.tier<>'NA' group by 1""", (worker, day, worker, day))}
    orders = [dict(r) for r in c.execute("""select o.order_code,o.activity,o.seconds,o.lines,o.cents,
        (select sum(coalesce(earned_seconds,0)) from task t where t.order_code=o.order_code and t.worker=o.worker) earned,
        (select group_concat(distinct t.customer) from task t where t.order_code=o.order_code) customers
        from order_cost o where o.worker=? and o.day=? order by o.order_code is null, o.cents desc""", (worker, day))]
    custs = {r['id']: r['customer_name'].replace(' (fictional)', '') for r in rows(c, 'intelligence', 'customer')}
    for o in orders:
        o['name'] = names.get(o['activity'], o['activity'])
        o['customers'] = ', '.join(custs.get(x, x) for x in (o['customers'] or '').split(',') if x)
        o['pace'] = o['earned'] / o['seconds'] if o['seconds'] and o['earned'] else None
    ot_start = next((s['start_local'] for s in slices if s['tier'] != 'ST'), None)
    td = c.execute('select * from time_day where worker=? and day=?', (worker, day)).fetchone()
    return dict(slices=slices, meals=meals, activities=activities, orders=orders, tasks=tasks, ot_start=ot_start,
                time_day=dict(td) if td else None,
                tiers={t: dict(hours=(s or 0) / 3600, cents=cts, rate=cts / ((s or 0) / 3600) if s else None) for t, (s, cts) in tiers.items()})


def order_detail(c, code):
    names = activity_names(c)
    tasks = [dict(r) for r in c.execute('select * from task where order_code=? order by worker,day', (code,))]
    if not tasks:
        return None
    custs = {r['id']: r['customer_name'] for r in rows(c, 'intelligence', 'customer')}
    costs = [dict(r) for r in c.execute('select * from order_cost where order_code=? order by day,worker', (code,))]
    by_worker = defaultdict(lambda: dict(lines=0, pieces=0.0, earned=0.0))
    for t in tasks:
        b = by_worker[t['worker']]; b['lines'] += 1; b['pieces'] += t['pieces'] or 0; b['earned'] += t['earned_seconds'] or 0
    for o in costs:
        o.update(by_worker.get(o['worker'], {}))
        o['pace'] = o['earned'] / o['seconds'] if o.get('earned') and o['seconds'] else None
    sales = sorted({t['sales_order'] for t in tasks if t['sales_order']})
    total = sum(o['cents'] for o in costs)
    earned = sum(t['earned_seconds'] or 0 for t in tasks)
    worked = sum(o['seconds'] for o in costs)
    return dict(code=code, activity=tasks[0]['activity'], activity_name=names.get(tasks[0]['activity'], tasks[0]['activity']),
                lines=len(tasks), pieces=sum(t['pieces'] or 0 for t in tasks), customers=sorted({custs.get(t['customer'], t['customer']) for t in tasks if t['customer']}),
                sales_orders=sales, costs=costs, cents=total, seconds=worked, earned=earned,
                pace=earned / worked if worked and earned else None, cost_per_line=total / len(tasks) if tasks else None,
                days=sorted({t['day'] for t in tasks}))


def site_daily(c, f):
    """Paid hours by control group by day (supervisor trend)."""
    out = defaultdict(lambda: defaultdict(float))
    for day, ctrl, s in c.execute('select day,control,sum(seconds) from time_part where day>=? and day<? group by 1,2', (f.start, f.end_excl)):
        out[day][ctrl] += s / 3600
    return [dict(day=d, **{k: out[d].get(k, 0) for k in CONTROL_ORDER}) for d in sorted(out)]


def activity_rows(c, f, total):
    names = activity_names(c)
    out = []
    for act, a in total['act'].items():
        if not a['lines'] and not a['h_direct']: continue
        r = dict(a, activity=act, name=names.get(act, act))
        r['pace'] = a['earned_h'] / a['h_direct'] if a['h_direct'] and a['earned_h'] else None
        r['cost_per_line'] = a['cost_direct'] / a['lines'] if a['lines'] else None
        out.append(r)
    return sorted(out, key=lambda r: -r['cost_direct'])


def activity_operators(c, f, activity):
    data = metrics(c, f)
    meta = workers(c)
    out = []
    for w, m in data.items():
        a = m['act'].get(activity)
        if not a or (not a['lines'] and not a['h_direct']): continue
        r = dict(meta.get(w, {'worker': w})); r.update(a); r.update(worker=w, st_rate=m['st_rate']); out.append(r)
    return sorted(out, key=lambda r: -(r['cost_direct']))


def cost_bridge(t, std, eff):
    """Standard cost of completed work -> total loaded labor cost. Every cent lands in exactly one step."""
    b, ctrl = t['cost_bucket'], t['cost_control']
    direct = t['cost_direct']
    steps = [('Standard cost of completed lines', std, 'absolute'),
             ('Pace vs standard (net)', eff, 'relative'),
             ('Overtime and rate mix', direct - std - eff, 'relative'),
             ('Indirect and other productive work', ctrl.get('productive', 0) - b.get('direct', 0), 'relative'),
             ('Planned / policy time', ctrl.get('policy', 0), 'relative'),
             ('Operational delays', ctrl.get('operational', 0), 'relative'),
             ('Operator-controlled', ctrl.get('operator', 0), 'relative'),
             ('Cause not established', ctrl.get('undetermined', 0) - b.get('pace_loss', 0), 'relative'),
             ('Non-time charges', ctrl.get('other', 0), 'relative'),
             ('Total loaded labor cost', t['cost'], 'total')]
    return [dict(label=l, cents=v, measure=m) for l, v, m in steps]
