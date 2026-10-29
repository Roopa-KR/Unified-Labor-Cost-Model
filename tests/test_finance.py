from decimal import Decimal
import pytest
from gini.maths import cents,allocate,union,duration,intersect,classify,stamp,overtime

def test_decimal_rounding():assert cents('10.125')==1013 and cents('-10.125')==-1013
@pytest.mark.parametrize('v',[None,'NaN','Infinity'])
def test_bad_money(v):
 with pytest.raises(ValueError):cents(v)
@pytest.mark.parametrize('amount',[1,2,100,10001,-1,-10001,0])
def test_allocation_conserves_cents(amount):
 parts=allocate(amount,[1,2,7]);assert sum(parts)==amount;assert all((x>=0 if amount>=0 else x<=0) for x in parts)
def test_known_rounding():assert allocate(100,[1,1,1])==[34,33,33]
def test_missing_driver():assert allocate(100,[0,0])==[]
def test_normal_day():
 slices=classify([(0,28800)],[(0,25200,'pick','direct'),(25200,27000,'clean','indirect'),(27000,28800,'break','break')]);assert sum(b-a for a,b,_,_ in slices)==28800
 assert allocate(cents('160'),[25200,1800,1800])==[14000,1000,1000]
def test_unattributed():assert classify([(0,100)],[(0,60,'pick','direct')])[-1]==(60,100,'unattributed','unattributed')
def test_overlap_and_outside():
 paid=[(0,100)];logged=[(-10,60),(50,110)];assert duration(logged)==120;assert duration(intersect(paid,logged))==100
def test_conflicting_activity():assert classify([(0,10)],[(0,10,'A','direct'),(0,10,'B','direct')])==[(0,10,'unattributed','conflict')]
def test_duplicate_activity_not_double_counted():assert classify([(0,10)],[(0,10,'A','direct')]*2)==[(0,10,'A','direct')]
def test_cross_midnight():assert stamp('2026-09-08T02:00:00-07:00')-stamp('2026-09-07T22:00:00-07:00')==14400
def test_dst_fall():assert stamp('2026-11-01T02:30:00-08:00')-stamp('2026-11-01T00:30:00-07:00')==10800
def test_dst_spring():assert stamp('2026-03-08T03:30:00-07:00')-stamp('2026-03-08T00:30:00-08:00')==7200
def test_naive_timestamp():
 with pytest.raises(ValueError):stamp('2026-09-07T00:00:00')
def test_daily_weekly_no_pyramiding():assert overtime([10,10,10,10,10,0,0])==(40,10,0)
def test_double_time():assert overtime([13,0,0,0,0,0,0])==(8,4,1)
def test_seventh_day():assert overtime([8,8,8,8,8,8,10])==(40,16,2)
def test_federal():assert overtime([10,10,10,0,0,0,0],daily=None,double=None,seventh=False)==(30,0,0)
def test_exempt():assert overtime([10]*7,exempt=True)==(70,0,0)
