import os,secrets,json,csv,io
from pathlib import Path
from flask import Flask,render_template,request,session,redirect,url_for,abort,jsonify,Response,g
from werkzeug.security import generate_password_hash,check_password_hash
from dotenv import load_dotenv
from gini.db import connect,DEFAULT_DB,ROOT,rows,migrate,prepare,sheet_counts,SCHEMA_VERSION
from gini.services import summary,ledger,activities,customers,bridge,query
from gini import operators as ops
from gini import policy as policy_mod
from gini.policy import BUCKETS,CONTROLS,CONTROL_ORDER
load_dotenv(ROOT/'.env')

NAV=[
 ('Operations',[('ops','Workforce'),('operators','Operators'),('activities','Work types'),('exceptions','Exceptions')]),
 ('Finance',[('overview','Labor cost'),('allocation','Cost allocation'),('variance','Budget variance'),('customers','Cost to serve'),('payroll','Payroll & agency'),('ledger','Ledger')]),
 ('Controls',[('reconciliation','Reconciliation'),('data','Data sources'),('settings','Cost policy'),('api','API access')]),
]
PAGES={k:v for _,items in NAV for k,v in items}
ROLES={'finance':'Finance','supervisor':'Supervisor','executive':'Executive'}
ACCESS={
 'finance':set(PAGES),
 'supervisor':{'ops','operators','activities','exceptions'},
 'executive':{'overview','ops','activities','variance','customers','reconciliation','api'},
}
HOME={'finance':'overview','supervisor':'ops','executive':'overview'}
LEGACY={'insights':'overview','ask':'api'}
OPERATOR_PAGES={'ops','operators','activities','exceptions'}

def create_app(test_config=None):
 app=Flask(__name__);app.config.update(SECRET_KEY=os.getenv('GINI_SECRET_KEY') or secrets.token_hex(32),DATABASE=os.getenv('GINI_DB') or str(DEFAULT_DB),SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE='Lax',MAX_CONTENT_LENGTH=1024*1024)
 if test_config:app.config.update(test_config)
 passwords={role:os.getenv('GINI_'+role.upper()+'_PASSWORD') for role in ROLES}
 if app.config.get('TESTING'):passwords={'finance':'test-finance','executive':'test-executive','supervisor':'test-supervisor'}
 # First-run credentials generated on the user's machine, not shipped in the ZIP.
 for role,filename in (('finance','local_login.txt'),('supervisor','local_login_supervisor.txt')):
  if not passwords[role]:
   credential=ROOT/'data'/filename
   if not credential.exists():credential.write_text(secrets.token_urlsafe(16),encoding='utf8');credential.chmod(0o600)
   passwords[role]=credential.read_text().strip()
 app.config['PASSWORDS']={r:generate_password_hash(p) for r,p in passwords.items() if p}
 # Upgrade an older database in place and run the version 2 calculation once.
 c=connect(app.config['DATABASE'])
 try:
  old=c.execute('pragma user_version').fetchone()[0]<SCHEMA_VERSION or not c.execute("select 1 from sqlite_master where name='calculation_run'").fetchone() or not c.execute("select 1 from calculation_run where version='2.0'").fetchone()
 finally:c.close()
 if old:
  from gini.engine import calculate
  print('GiNi: upgrading database to calculation version 2.0 …',flush=True);calculate(app.config['DATABASE'])
 c=connect(app.config['DATABASE'])
 try:prepare(c)
 finally:c.close()

 def db():
  if 'db' not in g:g.db=connect(app.config['DATABASE'])
  return g.db
 @app.teardown_appcontext
 def close(error):
  if 'db' in g:g.db.close()
 def audit(action,detail):
  c=db();c.execute('insert into audit(principal,action,detail) values(?,?,?)',(session.get('role','anonymous'),action,detail));c.commit()
 def stale(c):
  last=c.execute('select input_batches,policy from calculation_run order by id desc limit 1').fetchone()
  active=[dict(r) for r in c.execute('select * from active_file order by namespace')]
  return not last or json.loads(last[0])!=active or last[1]!=policy_mod.calc_signature(policy_mod.load(c))
 @app.before_request
 def guard():
  if request.endpoint=='static':return
  session.setdefault('csrf',secrets.token_urlsafe(24))
  if request.method=='POST' and not secrets.compare_digest(session['csrf'],request.form.get('csrf') or request.headers.get('X-CSRF-Token','')):abort(400,'Invalid request token')
  if request.endpoint not in ('login','health') and not session.get('role'):
   if request.path.startswith('/api/'):abort(401)
   return redirect(url_for('login'))
  if session.get('role') and request.endpoint not in ('login','health','logout','save_settings') and stale(db()):
   abort(503,'Source snapshots or cost policy changed. Run python -m gini.engine before reporting.')
 @app.after_request
 def headers(response):
  response.headers['X-Content-Type-Options']='nosniff';response.headers['X-Frame-Options']='DENY'
  # Versioned static files never change under the same URL; reports and data stay uncached.
  if request.endpoint=='static':response.headers['Cache-Control']='public, max-age=31536000, immutable' if request.args.get('v') else 'no-cache'
  else:response.headers['Cache-Control']='no-store'
  return response
 static_versions={}
 @app.url_defaults
 def static_version(endpoint,values):
  if endpoint=='static' and 'filename' in values:
   f=values['filename']
   if f not in static_versions:
    p=Path(app.static_folder)/f;static_versions[f]=int(p.stat().st_mtime) if p.is_file() else None
   if static_versions[f]:values['v']=static_versions[f]
 def role():return session.get('role')
 def allow(page):
  if page not in ACCESS.get(role(),set()):abort(403)
 def finance():
  if role()!='finance':abort(403)
 def operator_access():
  if role() not in ('finance','supervisor'):abort(403)
 def selected_period():
  p=request.args.get('period','');ids={r['id'] for r in rows(db(),'finance','payroll_period')}
  if p and p not in ids:abort(400,'Unknown period')
  return p
 def periods():return list(rows(db(),'finance','payroll_period'))

 @app.template_filter('usd')
 def usd(v):return '—' if v is None else ('−' if v<0 else '')+f'${abs(v)/100:,.2f}'
 @app.template_filter('usd0')
 def usd0(v):return '—' if v is None else ('−' if v<0 else '')+f'${abs(v)/100:,.0f}'
 @app.template_filter('signed')
 def signed(v):return '—' if v is None else ('+' if v>0 else '−' if v<0 else '')+f'${abs(v)/100:,.0f}'
 @app.template_filter('rate')
 def rate(v):return '—' if v is None else f'${v/100:,.2f}/h'
 @app.template_filter('hours')
 def hours(v):return '—' if v is None else f'{v:,.1f} h'
 @app.template_filter('pct')
 def pct(v):return '—' if v is None else f'{v*100:,.0f}%'
 @app.template_filter('number')
 def number(v):return '—' if v is None else f'{v:,.2f}'
 @app.template_filter('int')
 def integer(v):return '—' if v is None else f'{v:,.0f}'
 @app.template_filter('hm')
 def hm(v):return v[11:16] if v else ''
 @app.template_filter('label')
 def label(v):return (v or '').replace('act-','').replace('_',' ').capitalize()
 @app.context_processor
 def inject():
  def url_with(**kw):
   args={k:v for k,v in request.args.items()}
   for k,v in kw.items():
    if v in (None,''):args.pop(k,None)
    else:args[k]=v
   return request.path+('?'+'&'.join(f'{k}={v}' for k,v in args.items()) if args else '')
  return dict(nav=NAV,access=ACCESS.get(role(),set()),can_drill=role() in ('finance','supervisor'),is_finance=role()=='finance',roles=ROLES,url_with=url_with,BUCKETS=BUCKETS,CONTROLS=CONTROLS,CONTROL_ORDER=CONTROL_ORDER)

 @app.route('/health')
 def health():return jsonify(status='ok',application='GiNi Flask',version='2.0')
 @app.route('/login',methods=['GET','POST'])
 def login():
  error=None
  if request.method=='POST':
   r=request.form.get('role');password=request.form.get('password','')
   if check_password_hash(app.config['PASSWORDS'].get(r,generate_password_hash('disabled')),password) and r in app.config['PASSWORDS']:
    session.clear();session.update(role=r,csrf=secrets.token_urlsafe(24));audit('login',r);return redirect('/')
   error='Incorrect role or password.'
  return render_template('login.html',error=error,roles=ROLES,enabled=set(app.config['PASSWORDS']))
 @app.route('/logout',methods=['POST'])
 def logout():session.clear();return redirect('/login')
 @app.route('/')
 def home():return redirect('/view/'+HOME.get(role(),'overview'))

 def render(page,template=None,**ctx):
  return render_template(template or f'pages/{page}.html',page=page,title=ctx.pop('title',PAGES.get(page,'')),period=ctx.pop('period',request.args.get('period','')),periods=periods(),**ctx)

 @app.route('/view/<page>')
 def view(page):
  if page in LEGACY:return redirect(url_for('view',page=LEGACY[page],**request.args))
  if page not in PAGES:abort(404)
  allow(page)
  c=db();period=selected_period();ctx={}
  if page in ('overview','allocation','ops','operators','activities','exceptions'):
   f=ops.Filters(c,request.args,period);ctx['f']=f
   rows_=ops.operator_rows(c,f,request.args.get('sort','cost'),request.args.get('dir','desc')!='asc')
   t,std,eff=ops.site_totals(rows_);ops.finish(t,policy_mod.load(c))
   ctx.update(operators=rows_,t=t,std=std,eff=eff)
  if page=='overview':
   s=summary(c,period);b=bridge(c,period)
   ctx.update(s=s,cost_bridge=ops.cost_bridge(ctx['t'],ctx['std'],ctx['eff']),budget=b,buckets=ops.bucket_rows(ctx['t']),
    groups=[dict(label=label,cents=ctx['t']['cost_group'].get(k,0)) for k,label,_ in ops.COMPONENT_GROUPS if ctx['t']['cost_group'].get(k)],
    disputes=query(c,"select * from event where status='disputed'"+(' and period=?' if period else ''),(period,) if period else ()),
    checks=query(c,'select * from check_result'+(' where period=?' if period else ''),(period,) if period else ()),
    site_only=s['total_cents']-ctx['t']['cost'])
  if page=='allocation':
   ctx['posted']={r[0]:r[1] for r in c.execute('select worker,sum(cents) from event where worker is not null'+(' and period=?' if period else '')+' group by 1',(period,) if period else ())}
   ctx.update(buckets=ops.bucket_rows(ctx['t']),groups=ops.COMPONENT_GROUPS,matrix=allocation_matrix(c,ctx['f']),
    checks=query(c,"select * from check_result where name in ('operator cost allocation','paid time partition','order cost attribution','allocation')"+(' and period=?' if period else ''),(period,) if period else ()))
  if page=='ops':
   ctx.update(daily=ops.site_daily(c,ctx['f']),buckets=ops.bucket_rows(ctx['t']),work=ops.activity_rows(c,ctx['f'],ctx['t']),
    attention=sorted([r for r in ctx['operators'] if r['flags']],key=lambda r:(-len(r['flags']),r['utilization'] or 0))[:8] if role()!='executive' else [])
  if page=='operators':ctx['sort']=request.args.get('sort','cost');ctx['dir']=request.args.get('dir','desc')
  if page=='activities':
   ctx.update(activity_rows=activities(c,period),work={r['activity']:r for r in ops.activity_rows(c,ctx['f'],ctx['t'])})
  if page=='payroll':
   ctx['corrections']=list(rows(c,'finance','payroll_correction_log'));ctx['invoices']=list(rows(c,'finance','agency_invoice_line'))
   ctx['pay_codes']=list(rows(c,'finance','pay_code'));ctx['rates']=list(rows(c,'finance','labor_rate_assumption'))
  if page=='variance':ctx['bridge']=bridge(c,period,request.args.get('budget',''))
  if page=='customers':ctx['customer_rows'],ctx['unassigned']=customers(c,period);ctx['s']=summary(c,period)
  if page=='reconciliation':ctx['checks']=query(c,'select * from check_result'+(' where period=?' if period else '')+' order by period,rowid',(period,) if period else ())
  if page=='exceptions':
   f=ctx['f']
   ctx['issues']=query(c,"""select p.worker,p.day,p.bucket,p.control,sum(p.seconds) seconds from time_part p
     where p.control in ('operator','operational','undetermined') and p.bucket not in ('pace_loss') and p.day>=? and p.day<?
     group by 1,2,3,4 having sum(p.seconds)>=600 order by sum(p.seconds) desc limit 60""",(f.start,f.end_excl))
   ctx['source_exceptions']=query(c,"""select json_extract(payload,'$.exception_type') type,count(*) n,
     sum(json_extract(payload,'$.status')='open') open,sum(json_extract(payload,'$.duration_seconds')) seconds
     from raw r join active_file a on a.batch_id=r.batch_id where r.namespace='operations' and sheet='operational_exception' group by 1 order by n desc""")
   if role()=='finance':
    ctx['disputes']=query(c,"select * from event where status='disputed'"+(' and period=?' if period else ''),(period,) if period else ())
    ctx['gaps']=query(c,'select * from time_day where unattributed>0 or outside>0 order by unattributed desc limit 25');ctx['cases']={r['key']:dict(r) for r in c.execute('select * from investigation')}
  if page=='ledger':
   page_no=max(1,request.args.get('p',1,type=int));rs,count,total=ledger(c,period,request.args.get('worker',''),request.args.get('component',''),request.args.get('q',''),100,(page_no-1)*100)
   ctx.update(records=rs,count=count,filtered_total=total,page_no=page_no,components=[r[0] for r in c.execute('select distinct component from event order by 1')],
    workers=[r[0] for r in c.execute('select distinct worker from event where worker is not null order by 1')])
  if page=='data':ctx.update(inventory=[dict(r) for r in sheet_counts(c)],batches=query(c,'select * from batch order by id'),issues=list(rows(c,'foundation','data_quality_issue'))[:100])
  if page=='settings':ctx.update(params=policy_mod.PARAMETERS,values=policy_mod.load(c),last=c.execute('select * from calculation_run order by id desc limit 1').fetchone(),saved=request.args.get('saved'))
  audit('view',page+':'+period)
  return render(page,period=period,**ctx)

 def allocation_matrix(c,f):
  where,args=ops._cost_where(f)
  m={}
  for comp,ctrl,cents in c.execute(f'select e.component,a.control,sum(a.cents) from allocation a join event e on e.id=a.event_id where e.worker is not null and {where} group by 1,2',args):
   g_=ops.GROUP_OF.get(comp,'other');m.setdefault(g_,{});m[g_][ctrl]=m[g_].get(ctrl,0)+cents
  return m

 def worker_or_404(c,worker):
  if not c.execute('select 1 from time_day where worker=? union select 1 from event where worker=?',(worker,worker)).fetchone():abort(404)

 @app.route('/operators/<worker>')
 def operator(worker):
  operator_access();c=db();worker_or_404(c,worker);period=selected_period();f=ops.Filters(c,request.args,period)
  m=ops.metrics(c,f,worker).get(worker) or ops.finish(ops._blank(),policy_mod.load(c))
  info=ops.workers(c).get(worker,{'worker':worker})
  audit('operator',worker+':'+period)
  return render('operators','operator.html',title=worker,f=f,worker=worker,info=info,m=m,buckets=ops.bucket_rows(m),
   build=ops.rate_buildup(c,worker,f,m),ot=ops.payroll_ot_check(c,worker,f),days=ops.daily_rows(c,worker,f),
   acts=sorted(((k,v) for k,v in m['act'].items() if v['lines'] or v['h_all']),key=lambda kv:-kv[1]['cost_all']),names=ops.activity_names(c),
   events=ledger(c,period,worker)[0] if role()=='finance' else [])

 @app.route('/operators/<worker>/day/<day>')
 def operator_day(worker,day):
  operator_access();c=db();worker_or_404(c,worker)
  if not ops._is_day(day):abort(400)
  d=ops.day_detail(c,worker,day)
  days=[r[0] for r in c.execute('select day from time_day where worker=? and paid>0 order by day',(worker,))]
  i=days.index(day) if day in days else -1
  audit('operator_day',worker+':'+day)
  return render('operators','operator_day.html',title=worker+' · '+day,worker=worker,day=day,d=d,info=ops.workers(c).get(worker,{'worker':worker}),
   prev=days[i-1] if i>0 else None,next=days[i+1] if 0<=i<len(days)-1 else None,
   total_cents=sum(a['cents'] for a in d['activities']),total_hours=sum(a['hours'] for a in d['activities']),
   prod_hours=sum(a['hours'] for a in d['activities'] if a['control']=='productive'),prod_cents=sum(a['cents'] for a in d['activities'] if a['control']=='productive'))

 @app.route('/orders/<code>')
 def order(code):
  operator_access();c=db();o=ops.order_detail(c,code)
  if not o:abort(404)
  audit('order',code)
  return render('activities','order.html',title='Order '+code,o=o)

 @app.route('/activities/<activity>')
 def activity(activity):
  allow('activities');c=db();names=ops.activity_names(c)
  if activity not in names:abort(404)
  period=selected_period();f=ops.Filters(c,request.args,period)
  rows_=ops.activity_operators(c,f,activity) if role()!='executive' else []
  return render('activities','activity.html',title=names[activity],activity=activity,f=f,rows=rows_,
   standard=next((s for s in rows(c,'intelligence','standard') if s['activity_id']==activity and s['status'] in ('validated','approved')),None))

 @app.route('/event/<path:event_id>')
 def event(event_id):
  finance();c=db();e=c.execute('select * from event where id=?',(event_id,)).fetchone()
  if not e:abort(404)
  raw=c.execute('select r.*,b.filename,b.sha256 from raw r join batch b on b.id=r.batch_id where r.id=?',(e['raw_id'],)).fetchone()
  audit('source_evidence',event_id)
  allocs=query(c,'select * from allocation where event_id=? order by day,tier,bucket',(event_id,))
  return render('ledger','evidence.html',title='Transaction evidence',event=dict(e),raw=dict(raw),payload=json.loads(raw['payload']),allocations=allocs,
   by_bucket=query(c,'select bucket,control,tier,sum(cents) cents from allocation where event_id=? group by 1,2,3 order by 4 desc',(event_id,)))

 def csv_response(name,records,fields):
  out=io.StringIO();w=csv.DictWriter(out,fieldnames=fields,extrasaction='ignore');w.writeheader()
  for r in records:w.writerow({k:("'"+v if isinstance(v,str) and v.startswith(('=','+','-','@')) else v) for k,v in r.items() if k in fields})
  return Response(out.getvalue(),mimetype='text/csv',headers={'Content-Disposition':f'attachment; filename={name}'})
 @app.route('/export/ledger.csv')
 def export():
  finance();p=selected_period();rs,_,_=ledger(db(),p,request.args.get('worker',''),request.args.get('component',''),request.args.get('q',''))
  audit('export',f'ledger {p} {len(rs)} rows');return csv_response('GiNi_Ledger.csv',rs,list(rs[0]) if rs else ['id','cents'])
 @app.route('/export/operators.csv')
 def export_operators():
  operator_access();c=db();f=ops.Filters(c,request.args,selected_period());rs=ops.operator_rows(c,f)
  out=[]
  for r in rs:
   d=dict(operator=r['worker'],job=r['job'],shift=r['shift'],employment=r['emp'],date_from=f.start,date_to=f.end,paid_hours=round(r['hours'],2),
    productive_hours=round(r['h_productive'],2),unproductive_hours=round(r['h_unproductive'],2),utilization_pct=round(r['utilization']*100,1) if r['utilization'] is not None else '',
    pace_pct=round(r['pace']*100,1) if r['pace'] is not None else '',lines=r['lines'],pieces=r['pieces'],orders=r['orders'],earned_hours=round(r['earned_h'],2),
    loaded_cost=r['cost']/100,productive_cost=r['cost_productive']/100,unproductive_cost=r['cost_unproductive']/100,
    straight_time_loaded_rate=round(r['st_rate']/100,2) if r['st_rate'] else '',overtime_loaded_rate=round(r['ot_rate']/100,2) if r['ot_rate'] else '',
    cost_per_line=round(r['cost_per_line']/100,4) if r['cost_per_line'] else '',standard_cost=r['std_cost']/100 if r['std_cost'] is not None else '',
    actual_direct_cost=r['cost_direct']/100,actual_vs_standard=r['std_var']/100 if r['std_var'] is not None else '',flags='; '.join(x[1] for x in r['flags']))
   for b in BUCKETS:d['hours_'+b]=round(r['h_bucket'].get(b,0),3);d['cost_'+b]=r['cost_bucket'].get(b,0)/100
   out.append(d)
  audit('export',f'operators {len(out)} rows');return csv_response('GiNi_Operator_Costs.csv',out,list(out[0]) if out else ['operator'])
 @app.route('/export/operator/<worker>.csv')
 def export_operator(worker):
  operator_access();c=db();worker_or_404(c,worker);f=ops.Filters(c,request.args,selected_period())
  out=[dict(operator=worker,date=r['day'],shift=r['shift'],paid_hours=round(r['hours'],3),productive_hours=round(r['h_prod'],3),unproductive_hours=round(r['h_unprod'],3),
   overtime_hours=round(r['ot_h'],3),lines=r['lines'],pace_pct=round(r['pace']*100,1) if r['pace'] else '',loaded_cost=r['cost']/100,
   **{'cost_'+x['control']:x['cents']/100 for x in r['distribution']}) for r in ops.daily_rows(c,worker,f)]
  audit('export',f'operator {worker}');return csv_response(f'GiNi_{worker}_shifts.csv',out,list(out[0]) if out else ['operator'])

 @app.route('/api/summary')
 def api_summary():
  if set(request.args)-{'period'}:abort(400,'Unsupported filters')
  p=selected_period();audit('semantic_query','summary:'+p);return jsonify(summary(db(),p))
 @app.route('/api/tools/<name>')
 def tool(name):
  if set(request.args)-{'period'}:abort(400,'Unsupported filters')
  p=selected_period();c=db()
  if name=='cost_by_worktype':result=activities(c,p)
  elif name=='reconciliation':result=query(c,'select * from check_result'+(' where period=?' if p else ''),(p,) if p else ())
  elif name=='budget_variance':result=bridge(c,p)
  elif name=='operator_cost_distribution':
   if role() not in ('finance','supervisor'):abort(403)
   f=ops.Filters(c,{},p);rs=ops.operator_rows(c,f)
   result=[dict(operator=r['worker'],loaded_cents=r['cost'],productive_cents=r['cost_productive'],unproductive_cents=r['cost_unproductive'],
    paid_hours=r['hours'],productive_hours=r['h_productive'],pace=r['pace'],utilization=r['utilization'],
    cents_by_control=dict(r['cost_control']),hours_by_bucket=dict(r['h_bucket'])) for r in rs]
  else:abort(404)
  audit('semantic_query',name+':'+p);return jsonify(result=result,scope='SYN-DC100',period=p or 'all',calculation_version='2.0',synthetic=True)
 @app.route('/source/<namespace>/<sheet>')
 def source(namespace,sheet):
  finance();c=db()
  # Only active known sources; no unrestricted SQL, filesystem or test truth route.
  if not c.execute('select 1 from raw r join active_file a on a.batch_id=r.batch_id where r.namespace=? and sheet=?',(namespace,sheet)).fetchone():abort(404)
  page=max(1,request.args.get('p',1,type=int));rs=query(c,'select r.id,row_no,record_key,payload from active_file a join raw r on r.batch_id=a.batch_id and r.sheet=? where a.namespace=? and r.namespace=? order by r.row_no limit 100 offset ?',(sheet,namespace,namespace,(page-1)*100))
  records=[dict(r,data=json.loads(r['payload'])) for r in rs]
  cols=[k for k in (records[0]['data'] if records else {}) if k not in ('source_system_id','source_record_key','record_version','raw_record_id','recorded_at')]
  total=c.execute('select count(*) from active_file a join raw r on r.batch_id=a.batch_id and r.sheet=? where a.namespace=? and r.namespace=?',(sheet,namespace,namespace)).fetchone()[0]
  audit('source_read',namespace+'/'+sheet);return render('data','source.html',title=sheet.replace('_',' ').capitalize(),namespace=namespace,sheet=sheet,records=records,cols=cols,page_no=page,total=total)
 @app.route('/investigate',methods=['POST'])
 def investigate():
  finance();key=request.form.get('key','');status=request.form.get('status');note=request.form.get('note','')[:2000]
  if status not in ('Open','In review','Resolved') or not db().execute('select 1 from event where id=?',(key,)).fetchone():abort(400)
  db().execute('insert into investigation(key,status,reviewer,note) values(?,?,?,?) on conflict(key) do update set status=excluded.status,reviewer=excluded.reviewer,note=excluded.note,updated_at=CURRENT_TIMESTAMP',(key,status,'finance',note));db().commit();audit('investigation_update',key+':'+status);return redirect('/view/exceptions#disputes')
 @app.route('/settings',methods=['POST'])
 def save_settings():
  finance();c=db()
  try:
   before=policy_mod.load(c);policy_mod.save(c,request.form,'finance');c.commit()
  except ValueError:abort(400,'Invalid policy value')
  after=policy_mod.load(c);changed=policy_mod.calc_signature(before)!=policy_mod.calc_signature(after)
  if changed or stale(c):
   from gini.engine import calculate
   try:calculate(app.config['DATABASE'])
   except Exception:
    for k,v in before.items():c.execute('update cost_policy set value=? where key=?',(json.dumps(v),k))
    c.commit();raise
  audit('policy_update',json.dumps(after));return redirect('/view/settings?saved='+('recalculated' if changed else 'saved'))
 @app.errorhandler(403)
 def forbidden(e):return render_template('error.html',code=403,message='Your role does not have access to this page.',title='No access'),403
 @app.errorhandler(404)
 def notfound(e):return render_template('error.html',code=404,message='This page or record does not exist.',title='Not found'),404
 @app.errorhandler(503)
 def unavailable(e):return render_template('error.html',code=503,message=getattr(e,'description','Recalculation required.'),title='Recalculation required'),503
 return app
if __name__=='__main__':
 from waitress import serve
 app=create_app();print('GiNi: http://127.0.0.1:'+os.getenv('GINI_PORT','5007'),flush=True)
 print('Login: finance (data/local_login.txt) or supervisor (data/local_login_supervisor.txt), or use your .env settings.',flush=True)
 serve(app,host=os.getenv('GINI_HOST','127.0.0.1'),port=int(os.getenv('GINI_PORT','5007')))
