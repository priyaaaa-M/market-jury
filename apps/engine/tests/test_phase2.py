from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

from engine.api import create_app
from engine.data import SimulatedData, YahooData
from engine.orchestrator import Engine
from engine.regime import classify
from engine.scoreboard import evaluate
from engine.store import Store
from engine.workflow import risk_plan


def test_demo_window_is_stable():
    d=SimulatedData()
    assert d.history('TCS', 60)[-2:] == d.history('TCS', 2)
    assert d.price_on('TCS',datetime(2026,10,9)) == d.daily_bars('TCS',date(2026,10,9),date(2026,10,9))[0]['close']


def test_risk_sizing_and_errors():
    p=risk_plan(100000,1,1000,980,1040)
    assert p['quantity']==50 and p['planned_loss']==1000 and p['reward_risk']==2
    assert risk_plan(1000,5,1000,999,1002)['quantity']==1
    with pytest.raises(ValueError): risk_plan(1000,1,1000,1001,1100)
    with pytest.raises(ValueError): risk_plan(float('nan'),1,1000,980,1040)


def test_regime_fresh_context_and_stale_ignored():
    args=([100+i for i in range(60)],[12.]*30)
    ctx={'as_of':datetime.now(ZoneInfo('Asia/Kolkata')).date().isoformat(),'breadth_pct':25,'fii_net_crore':-500,'dii_net_crore':100,'source':'manual NSE'}
    assert classify(*args,ctx)['size_multiplier']==.5
    ctx['as_of']='2000-01-01'
    stale=classify(*args,ctx)
    assert stale['size_multiplier']==1 and len(stale['missing_inputs'])==3


class RealFixture:
    source='fixture_real'
    def daily_bars(self, symbol,start,end):
        days=['2026-10-05','2026-10-06','2026-10-08','2026-10-09']
        return [{'date':d,'close':(100+i*10 if symbol=='TCS' else 100+i*2)} for i,d in enumerate(days) if start <= date.fromisoformat(d) <= end]


def test_scoreboard_observed_sessions_not_calendar_days():
    v={'id':1,'timestamp':'2026-10-02T12:00:00+05:30','symbol':'TCS','verdict':'buy','confidence':.8,'audit':{'data_source':'fixture_real'}}
    d=evaluate(RealFixture(),[v],datetime(2026,10,10,tzinfo=ZoneInfo('Asia/Kolkata')))
    h=d['outcomes'][0]['horizons'][1]
    assert h['start_date']=='2026-10-05' and h['end_date']=='2026-10-06'
    assert round(h['stock_return'],2)==.1 and d['by_horizon'][5]['n']==0
    assert d['outcomes'][0]['horizons'][5]['status']=='waiting'


def test_demo_and_unknown_excluded_and_hold_tracked():
    v={'timestamp':'2026-10-02T12:00:00+05:30','symbol':'TCS','verdict':'hold','confidence':.5,'audit':{'data_source':'simulated'}}
    assert evaluate(SimulatedData(),[v])['excluded_demo']==1
    v['audit']={}
    assert evaluate(RealFixture(),[v])['outcomes'][0]['status']=='unverified_source'
    v['audit']={'data_source':'fixture_real'}
    r=evaluate(RealFixture(),[v],datetime(2026,10,10))
    assert r['scored_rows']==0 and r['outcomes'][0]['status']=='hold_tracked'


async def test_verdict_audit_persists_and_legacy_migration():
    store=Store()
    e=Engine(store=store)
    await e.debate('TCS')
    assert store.verdicts()[0]['audit']['data_source']=='simulated'
    assert e.scoreboard()['excluded_demo']==1


def test_private_journal_and_public_redaction(monkeypatch):
    e=Engine();c=TestClient(create_app(e,'k'));h={'X-API-Key':'k'}
    assert c.get('/journal').status_code==401
    assert c.post('/journal',headers=h,json={'symbol':'tcs','thesis':'demo','invalidation':'below stop'}).status_code==200
    assert c.get('/journal',headers=h).json()['entries'][0]['symbol']=='TCS'
    assert c.get('/public/scoreboard').status_code==404
    monkeypatch.setenv('PUBLIC_SCOREBOARD','true')
    pub=c.get('/public/scoreboard').json()
    assert 'outcomes' not in pub and 'journal' not in pub
    assert c.post('/risk-plan',headers=h,json={'capital':1000,'risk_pct':9,'entry':100,'stop':90,'target':120}).status_code==400


def test_config_patch_is_atomic():
    e=Engine();before=dict(e.cfg.values)
    with pytest.raises(KeyError):e.cfg.update({'AGENT_FORCE_ACTIVE':True,'BAD':1})
    assert e.cfg.values==before


def test_yahoo_errors_do_not_use_demo_prices(monkeypatch):
    import sys
    from types import SimpleNamespace
    def fail(*args, **kw):
        raise RuntimeError('provider unavailable')
    monkeypatch.setitem(sys.modules,'yfinance',SimpleNamespace(Ticker=lambda t:SimpleNamespace(history=fail)))
    d=YahooData()
    with pytest.raises(ValueError,match='no simulated fallback'):
        d.history('TCS')


async def test_failed_approval_keeps_pending():
    e=Engine()
    e.pending=[{'symbol':'TCS','action':'BUY','quantity':10**10}]
    with pytest.raises(ValueError):await e.approve(0)
    assert len(e.pending)==1
    with pytest.raises(IndexError):await e.approve(-1)


def test_new_real_call_waits_without_querying_future():
    class NoFetch(RealFixture):
        def daily_bars(self,*args):raise AssertionError('must wait')
    v={'timestamp':'2026-10-09T12:00:00+05:30','symbol':'TCS','verdict':'buy','confidence':.7,'audit':{'data_source':'fixture_real'}}
    r=evaluate(NoFetch(),[v],datetime(2026,10,9,tzinfo=ZoneInfo('Asia/Kolkata')))
    assert r['outcomes'][0]['status']=='waiting'


def test_independent_crosscheck_requires_comparable_fresh_evidence():
    from engine.crosscheck import compare
    primary={'symbol':'TCS','exchange':'NSE','as_of_date':'2026-10-09','comparison_price_type':'adjusted_daily_close','price':2156,'data_source':'yahoo_delayed'}
    secondary={**primary,'provider':'independent_fixture','observed_at':datetime.now(ZoneInfo('UTC')).isoformat(),'source_url':'https://example.test/quote'}
    assert compare(primary,secondary)['status']=='cross_checked'
    secondary['price']=2160
    assert compare(primary,secondary)['status']=='mismatch'
    secondary['comparison_price_type']='intraday_last_trade'
    assert compare(primary,secondary)['status']=='incomparable'
    assert compare(primary,None)['status']=='unavailable'
    secondary['comparison_price_type']='adjusted_daily_close'
    secondary['provider']='yahoo_delayed'
    assert compare(primary,secondary)['reason']=='not_independent'
