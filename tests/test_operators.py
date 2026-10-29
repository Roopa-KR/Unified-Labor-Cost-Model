"""Operator-level labor cost allocation (calculation version 2.0)."""
import sqlite3
import pytest
from app import create_app
from gini.db import connect
from gini import operators as ops, policy as pol
from gini.partition import split, tier_cuts, tiers, rest_breaks, classify_day

H = 3600.0
POLICY = {k: v[0] for k, v in pol.PARAMETERS.items()}
CA = {'daily_ot_threshold_hours': 8, 'daily_dt_threshold_hours': 12, 'weekly_ot_threshold_hours': 40, 'seventh_day_rule': True}


# ---- interval primitives -------------------------------------------------------------
def test_split_marks_inside_and_outside():
    assert split(0, 10, [(2, 4), (6, 12)]) == [(0, 2, False), (2, 4, True), (4, 6, False), (6, 10, True)]

def test_rest_breaks_california_major_fraction():
    assert [rest_breaks(h * H) for h in (3, 3.5, 6, 6.01, 10, 10.5)] == [0, 1, 1, 2, 2, 3]

def test_daily_overtime_and_double_time_positions():
    assert tier_cuts(13 * H, 0, CA, False) == (8 * H, 12 * H)
    parts = tiers([(0, 13 * H, 'x')], 8 * H, 12 * H)
    assert [(b - a) / H for a, b, _, _ in parts] == [8, 4, 1] and [t for *_, t in parts] == ['ST', 'OT', 'DT']

def test_weekly_overtime_after_forty_regular_hours():
    st, dt = tier_cuts(8 * H, 36 * H, CA, False)
    assert st == 4 * H  # only 4 regular hours left in the week

def test_seventh_day_rule():
    assert tier_cuts(9 * H, 40 * H, CA, True) == (0, 8 * H)

def test_tiers_cut_across_parts_without_losing_time():
    parts = tiers([(0, 5 * H, 'a'), (5 * H, 10 * H, 'b')], 8 * H, 12 * H)
    assert sum(b - a for a, b, *_ in parts) == 10 * H
    assert [(p, t) for _, _, p, t in parts] == [('a', 'ST'), ('b', 'ST'), ('b', 'OT')]

def _ctx(**kw):
    base = dict(no_output_annotated=[], no_output=[], equipment=[], system=[], no_work=[], idle_long=[])
    base.update(kw); return base

def test_classify_day_rest_allowance_then_excess_break():
    # 8 paid hours -> 2 rest breaks = 20 min allowance; 30 min of personal breaks -> 10 min excess.
    slices = [(0, 7.5 * H, 'act-PICK_RX', 'direct'), (7.5 * H, 8 * H, 'act-PERSONAL', 'break')]
    out = classify_day(slices, _ctx(), POLICY)
    got = {b: sum(y - x for x, y, _, _, bb, _ in out if bb == b) for b in ('direct', 'rest_break', 'break_unscheduled')}
    assert got == {'direct': 7.5 * H, 'rest_break': 1200, 'break_unscheduled': 600}

def test_classify_day_idle_is_not_operator_fault_when_explained():
    slices = [(0, 600, 'act-UNEXPLAINED_IDLE', 'unexplained'), (600, 1200, 'act-UNEXPLAINED_IDLE', 'unexplained')]
    out = classify_day(slices, _ctx(equipment=[(0, 600)], idle_long=[(600, 1200)]), POLICY)
    assert [b for *_, b, _ in out] == ['wait_equipment', 'idle_excessive']

def test_classify_day_no_output_stretch_and_supervisor_note():
    slices = [(0, 3 * H, 'act-PICK_CASES', 'direct')]
    out = classify_day(slices, _ctx(no_output_annotated=[(0, H)], no_output=[(H, 2 * H)]), POLICY)
    assert [(b, ann) for *_, b, ann in out] == [('not_performed', True), ('not_performed', False), ('direct', False)]
    assert pol.control_for('not_performed', POLICY, True) == 'operational'
    assert pol.control_for('not_performed', POLICY, False) == 'undetermined'

def test_breaks_and_slow_pace_are_never_automatically_operator_controlled():
    assert pol.control_for('rest_break', POLICY) == 'policy'
    assert pol.control_for('pace_loss', POLICY) == 'undetermined'
    assert pol.control_for('wait_material', POLICY) == 'operational'


# ---- invariants on the calculated database ---------------------------------------------
@pytest.fixture(scope='module')
def c():
    conn = connect(); yield conn; conn.close()

def test_every_operator_dollar_allocated_once(c):
    posted = dict(((r[0], r[1]), r[2]) for r in c.execute('select worker,period,sum(cents) from event where worker is not null group by 1,2'))
    alloc = dict(((r[0], r[1]), r[2]) for r in c.execute('select e.worker,e.period,sum(a.cents) from allocation a join event e on e.id=a.event_id where e.worker is not null group by 1,2'))
    assert posted and posted == alloc


def test_time_parts_partition_paid_time(c):
    rows_ = c.execute('''select d.worker,d.day,d.paid,coalesce((select sum(seconds) from time_part p where p.worker=d.worker and p.day=d.day),0)
        from time_day d''').fetchall()
    assert rows_ and all(abs(r[2] - r[3]) < 1e-6 for r in rows_)

def test_overtime_premium_only_on_overtime_hours(c):
    assert not c.execute("select 1 from allocation where method='premium_on_overtime_hours_v2' and tier not in ('OT','DT')").fetchone()

def test_unpaid_meals_carry_no_cost(c):
    assert not c.execute("select 1 from allocation where activity='act-MEAL'").fetchone()

def test_order_costs_reconcile_to_direct_cost(c):
    direct = c.execute("select coalesce(sum(a.cents),0) from allocation a where a.bucket in ('direct','pace_loss')").fetchone()[0]
    assert direct == c.execute('select sum(cents) from order_cost').fetchone()[0]

def test_controls_reconcile(c):
    for name in ('operator cost allocation', 'paid time partition', 'order cost attribution', 'allocation'):
        assert not c.execute('select 1 from check_result where name=? and difference_cents<>0', (name,)).fetchone(), name

def test_synthesized_rows_are_labeled(c):
    rows_ = c.execute("select payload from raw where namespace='supplement'").fetchall()
    assert rows_ and all('"data_origin":"gini_synthesized"' in r[0] for r in rows_)

@pytest.mark.parametrize('period', ['', 'prd-2026-W37', 'prd-2026-W38'])
def test_operator_cost_distribution_reconciles(c, period):
    f = ops.Filters(c, {}, period)
    rs = ops.operator_rows(c, f)
    t, std, eff = ops.site_totals(rs)
    total = c.execute('select sum(cents) from event where worker is not null' + (' and period=?' if period else ''), (period,) if period else ()).fetchone()[0]
    assert t['cost'] == total
    for r in rs:
        assert r['cost_productive'] + r['cost_unproductive'] + r['cost_non_time'] == r['cost']
        assert sum(b['cents'] for b in ops.bucket_rows(r)) == r['cost']
        assert abs(r['h_productive'] + r['h_unproductive'] - r['hours']) < 1e-9
        if r['std_var'] is not None:
            assert r['eff_var'] + r['rate_var'] == r['std_var']
    bridge = ops.cost_bridge(t, std, eff)
    assert sum(s['cents'] for s in bridge[:-1]) == bridge[-1]['cents'] == total

def test_payroll_overtime_hours_match_timeclock_for_most_operators(c):
    f = ops.Filters(c, {}, 'prd-2026-W38')
    diffs = [abs(ops.payroll_ot_check(c, w, f)['difference']) for w in ops.workers(c)]
    assert sum(d < 0.05 for d in diffs) >= len(diffs) - 2


# ---- routes and roles ------------------------------------------------------------------
def login(app, role):
    cl = app.test_client(); cl.get('/login')
    with cl.session_transaction() as s: tok = s['csrf']
    assert cl.post('/login', data={'csrf': tok, 'role': role, 'password': 'test-' + role}).status_code == 302
    with cl.session_transaction() as s: tok = s['csrf']
    return cl, tok

@pytest.fixture(scope='module')
def app():
    return create_app({'TESTING': True})

@pytest.mark.parametrize('path', ['/operators/W0001', '/operators/W0031?period=prd-2026-W38', '/operators/W0001/day/2026-09-12',
    '/orders/100006745269', '/activities/act-PICK_CASES', '/view/operators?sort=idle_excessive&flagged=1',
    '/view/operators?from=2026-09-08&to=2026-09-09&shift=EVE&emp=permanent', '/view/ops?from=2026-09-10&to=2026-09-10'])
def test_drilldowns(app, path):
    cl, _ = login(app, 'finance')
    assert cl.get(path).status_code == 200

def test_supervisor_scope(app):
    cl, _ = login(app, 'supervisor')
    for p in ['/view/ops', '/view/operators', '/operators/W0001', '/operators/W0001/day/2026-09-07', '/export/operators.csv']:
        assert cl.get(p).status_code == 200, p
    for p in ['/view/ledger', '/view/payroll', '/view/settings', '/export/ledger.csv', '/event/payroll_line:pl-PL0000001']:
        assert cl.get(p).status_code == 403, p
    assert b'Disputed agency invoices' not in cl.get('/view/exceptions').data

def test_operator_export(app):
    cl, _ = login(app, 'finance')
    r = cl.get('/export/operators.csv?period=prd-2026-W37')
    assert r.status_code == 200 and r.text.count('\n') == 41 and 'cost_pace_loss' in r.text

def test_bad_inputs(app):
    cl, _ = login(app, 'finance')
    assert cl.get('/operators/W9999').status_code == 404
    assert cl.get('/operators/W0001/day/not-a-day').status_code == 400
    assert cl.get('/orders/nope').status_code == 404
    assert cl.get('/view/operators?from=garbage&to=2026-13-99').status_code == 200

def test_settings_requires_finance_and_csrf(app):
    cl, tok = login(app, 'supervisor')
    assert cl.post('/settings', data={'csrf': tok}).status_code == 403
    cl, tok = login(app, 'finance')
    assert cl.post('/settings', data={'rest_minutes_per_4h': '10'}).status_code == 400

def test_policy_round_trip():
    m = sqlite3.connect(':memory:')
    m.execute('create table cost_policy(key text primary key, value text, updated_by text, updated_at text default current_timestamp)')
    pol.save(m, {'rest_minutes_per_4h': '15', 'indirect_is_productive': '1'}, 'test')
    p = pol.load(m)
    assert p['rest_minutes_per_4h'] == 15 and p['indirect_is_productive'] is True and p['training_is_productive'] is False
    with pytest.raises(ValueError):
        pol.save(m, {'idle_excess_seconds': 'nan'}, 'test')
