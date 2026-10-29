import pytest,json
from app import create_app,PAGES
from gini.db import connect,rows,DEFAULT_DB
from gini.services import summary,activities,customers,bridge
from gini.maths import cents
@pytest.fixture
def app():return create_app({'TESTING':True})
@pytest.fixture
def client(app):
 c=app.test_client();c.get('/login')
 with c.session_transaction() as s:token=s['csrf']
 assert c.post('/login',data={'csrf':token,'role':'finance','password':'test-finance'}).status_code==302
 return c
@pytest.mark.parametrize('page',list(PAGES))
def test_page(client,page):assert client.get('/view/'+page).status_code==200
@pytest.mark.parametrize('page',list(PAGES))
def test_period_page(client,page):assert client.get('/view/'+page+'?period=prd-2026-W37').status_code==200

def test_auth(app):
 c=app.test_client();assert c.get('/api/summary').status_code==401;assert c.get('/export/ledger.csv').status_code==302

def test_executive_restrictions(app):
 c=app.test_client();c.get('/login')
 with c.session_transaction() as s:token=s['csrf']
 c.post('/login',data={'csrf':token,'role':'executive','password':'test-executive'})
 for path in ['/view/ledger','/view/operators','/view/data','/source/finance/payroll_line','/export/ledger.csv','/event/payroll_line:pl-PL0000001']:assert c.get(path).status_code==403
 assert c.get('/api/summary').status_code==200

def test_tool_validation(client):
 for path in ['/api/summary?period=evil','/api/summary?site=other','/api/tools/cost_by_worktype?sql=select+1']:
  assert client.get(path).status_code==400
 assert client.get('/api/tools/execute_sql').status_code==404

def test_csrf(client):assert client.post('/investigate',data={'key':'anything'}).status_code==400

def test_export(client):
 r=client.get('/export/ledger.csv?worker=W0001');assert r.status_code==200;assert 'W0002' not in r.text

def test_source_detail(client):
 r=client.get('/event/payroll_line:pl-PL0000001');assert r.status_code==200;assert '1372.02' in r.text

def test_source_totals_independent():
 c=connect()
 expected=sum(cents(r['amount']) for name in ['payroll_line','employer_cost','agency_invoice_line'] for r in rows(c,'finance',name))
 assert summary(c)['total_cents']==expected
 assert c.execute('select count(*) from event').fetchone()[0]==624
 assert c.execute('select sum(cents) from allocation').fetchone()[0]==expected
 # Every source transaction independently conserved.
 assert not c.execute('select e.id from event e join allocation a on a.event_id=e.id group by e.id having sum(a.cents)!=e.cents').fetchall()
 c.close()

def test_correction_and_credit():
 c=connect();r=list(rows(c,'finance','payroll_correction_log'))[0]
 amounts=[c.execute('select cents from event where id=?',('payroll_line:'+r[k],)).fetchone()[0] for k in ['original_line_id','reversal_line_id','replacement_line_id']]
 assert amounts[0]+amounts[1]==0;assert sum(amounts)==amounts[2]
 assert c.execute("select sum(cents) from event where component='agency_credit'").fetchone()[0]==-4818
 c.close()

def test_time_invariants():
 c=connect()
 for r in c.execute('select * from time_day'):
  classified=c.execute('select coalesce(sum(seconds),0) from time_slice where worker=? and day=?',(r['worker'],r['day'])).fetchone()[0]
  assert abs(classified-r['paid'])<1e-7
  assert 0<=r['unattributed']<=r['paid'];assert abs(r['logged']-r['matched']-r['outside'])<1e-7
 c.close()

def test_dimension_conservation():
 c=connect()
 for p in ['','prd-2026-W37','prd-2026-W38']:
  total=summary(c,p)['total_cents'];assert sum(r['cents'] for r in activities(c,p))==total
  customers_,unassigned=customers(c,p);assert sum(r['labor_cents'] for r in customers_)+unassigned==total
  b=bridge(c,p);assert sum(r['cents'] for r in b['steps'][:-1])==total
 c.close()

def test_truth_and_pii_absent():
 c=connect();assert not c.execute("select 1 from raw where sheet like '%RESTRICTED%' or namespace like '%truth%'").fetchone();c.close()
