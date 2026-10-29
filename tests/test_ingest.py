import shutil
import openpyxl
from gini.ingest import ingest
from gini.db import connect,rows
# Fixture workbooks are test inputs, not user-facing spreadsheet deliverables.
def fixture(path,amount):
 w=openpyxl.Workbook();s=w.active;s.title='payroll_line';s.append(['id','amount']);s.append(['P1',amount]);w.save(path)
def test_idempotent_and_corrected_snapshot(tmp_path):
 source=tmp_path/'inputs';source.mkdir();p=source/'03_test.xlsx';db=tmp_path/'test.sqlite'
 fixture(p,10);ingest(source,db);ingest(source,db)
 c=connect(db);assert c.execute('select count(*) from raw').fetchone()[0]==1;c.close()
 fixture(p,12);ingest(source,db);c=connect(db)
 assert c.execute('select count(*) from raw').fetchone()[0]==2
 assert list(rows(c,'finance','payroll_line'))[0]['amount']==12
 assert c.execute('select count(*) from batch').fetchone()[0]==2;c.close()
