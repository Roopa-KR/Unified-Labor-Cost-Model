"""Configurable cost-allocation policy (calculation version 2.0).

Every parameter that changes how paid time is classified or how cost is
distributed lives here, is stored in the `cost_policy` table and is recorded
with each calculation run. Changing a value triggers a full recalculation so
every page reads the same numbers.
"""
import json

# key: (default, type, label, help)
PARAMETERS = {
    'rest_minutes_per_4h': (10, float, 'Authorized paid rest (minutes per 4 paid hours)',
        'California rule from pay_policy: 10 minutes per 4 hours or major fraction. Rest breaks are not punched, '
        'so the allowance is applied first to personal-break reason codes, then to paid time outside any login.'),
    'idle_excess_seconds': (300, float, 'Excessive idle threshold (seconds)',
        'Unexplained device idle longer than this, with no reason entered, is excessive idle (operator-controlled). '
        'Shorter idle stays undetermined.'),
    'no_output_gap_seconds': (900, float, 'No-output gap threshold (seconds)',
        'Logged direct time in a stretch longer than this with no confirmed line is assigned work not performed. '
        'Stretches a supervisor annotated (for example, reassigned to returns) count as operational.'),
    'pace_tolerance_pct': (0, float, 'Pace tolerance (%)',
        'Direct time within this margin of standard time is not counted as slow-pace time.'),
    'indirect_is_productive': (True, bool, 'Count indirect tasks as productive',
        'QA checks, housekeeping and supervisor-directed tasks are assigned warehouse work.'),
    'training_is_productive': (False, bool, 'Count training as productive',
        'Off by default: training is planned, policy-driven time that produces no output.'),
    'use_synthesized_equipment': (True, bool, 'Use synthesized equipment downtime',
        'No equipment log was supplied. When on, a clearly labeled synthesized downtime log is used to '
        'classify matching idle time as waiting for equipment.'),
    'alert_pace_pct': (90, float, 'Flag pace below (%)', 'Operators below this pace versus standard are flagged.'),
    'alert_utilization_pct': (80, float, 'Flag utilization below (%)', 'Productive hours as a share of paid hours.'),
    'alert_operator_controlled_pct': (3, float, 'Flag operator-controlled time above (% of paid)',
        'Excess breaks and excessive idle as a share of paid hours.'),
}
RECALC_KEYS = {'rest_minutes_per_4h', 'no_output_gap_seconds', 'idle_excess_seconds', 'pace_tolerance_pct', 'indirect_is_productive',
               'training_is_productive', 'use_synthesized_equipment'}

def _cast(kind, value):
    if kind is bool:
        return value if isinstance(value, bool) else str(value).lower() in ('1', 'true', 'on', 'yes')
    v = float(value)
    if v != v or v < 0 or v > 100000:
        raise ValueError('Out of range')
    return v

def load(c):
    out = {k: v[0] for k, v in PARAMETERS.items()}
    try:
        for r in c.execute('select key,value from cost_policy'):
            if r[0] in PARAMETERS:
                out[r[0]] = _cast(PARAMETERS[r[0]][1], json.loads(r[1]))
    except Exception:
        pass
    return out

def calc_signature(policy):
    return json.dumps({k: policy[k] for k in sorted(RECALC_KEYS)}, sort_keys=True)

def save(c, values, who):
    clean = {}
    for k, (default, kind, *_rest) in PARAMETERS.items():
        if kind is bool:
            clean[k] = k in values and _cast(bool, values.get(k))
        elif k in values:
            clean[k] = _cast(kind, values[k])
    for k, v in clean.items():
        c.execute('insert into cost_policy(key,value,updated_by) values(?,?,?) on conflict(key) do update set '
                  'value=excluded.value,updated_by=excluded.updated_by,updated_at=CURRENT_TIMESTAMP',
                  (k, json.dumps(v), who))
    return clean

# Cost buckets: label, control group, productive (None = decided by policy)
BUCKETS = {
    'direct':            ('Direct work', 'productive'),
    'indirect':          ('Indirect tasks', 'productive'),
    'training':          ('Training', 'policy'),
    'rest_break':        ('Authorized rest breaks', 'policy'),
    'paid_leave':        ('Paid leave (not worked)', 'policy'),
    'wait_material':     ('Waiting: replenishment', 'operational'),
    'wait_work':         ('Waiting: no work released', 'operational'),
    'wait_system':       ('Waiting: device or system', 'operational'),
    'wait_equipment':    ('Waiting: equipment', 'operational'),
    'not_performed':     ('Assigned work not performed', 'undetermined'),
    'break_unscheduled': ('Unscheduled break time', 'operator'),
    'idle_excessive':    ('Excessive idle', 'operator'),
    'idle_short':        ('Short idle', 'undetermined'),
    'pace_loss':         ('Slow-pace time', 'undetermined'),
    'unattributed':      ('Unaccounted paid time', 'undetermined'),
    'non_time':          ('Non-time charges', 'other'),
}
CONTROLS = {
    'productive':   ('Productive', '#2a78d6'),
    'policy':       ('Planned / policy', '#1baf7a'),
    'operational':  ('Operational', '#6250d6'),
    'operator':     ('Operator-controlled', '#eb6834'),
    'undetermined': ('Cause not established', '#9a9a96'),
    'other':        ('Non-time charges', '#c3c2b7'),
}
CONTROL_ORDER = list(CONTROLS)
BUCKET_ORDER = list(BUCKETS)

def is_productive(bucket, policy):
    if bucket == 'direct':
        return True
    if bucket == 'indirect':
        return bool(policy['indirect_is_productive'])
    if bucket == 'training':
        return bool(policy['training_is_productive'])
    return False

def control_for(bucket, policy, annotated=False):
    if is_productive(bucket, policy):
        return 'productive'
    if bucket == 'indirect':
        return 'operational'
    if bucket == 'not_performed' and annotated:
        return 'operational'
    return BUCKETS[bucket][1]
