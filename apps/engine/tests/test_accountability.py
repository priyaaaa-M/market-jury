from datetime import date,datetime,timedelta,timezone
from fastapi.testclient import TestClient
from engine.accountability import review_report
from engine.funnel import screen
from engine.orchestrator import Engine
from engine.api import create_app
from engine.store import Store

def verdict(i=1):
 return {'id':i,'symbol':'TCS','verdict':'buy','confidence':.8,'timestamp':'2026-09-01T12:00:00+00:00','reasoning':'saved thesis','audit':{'data_source':'fixture'},'positions':[{'agent_name':'debater_bull','evidence':[]}], 'regime':'risk_on'}
def outcome(i=1):
 return {'id':i,'symbol':'TCS','verdict':'buy','status':'scored','horizons':{5:{'status':'scored','stock_return':-.1,'benchmark_return':-.02}}}
def test_miss_is_not_cause_and_holds_not_wrong():
 v=verdict();o=outcome();r=review_report({'outcomes':[o]},[v],{})
 assert r['calls'][0]['scored_horizons'][0]['result']=='miss'
 assert r['calls'][0]['cause_status']=='unknown' and not r['suggestions']
 v['verdict']='hold';assert review_report({'outcomes':[o]},[v],{})['calls'][0]['scored_horizons'][0]['result']=='hold_tracked'
 o['horizons'][5]['stock_return']=0;v['verdict']='buy'
 assert review_report({'outcomes':[o]},[v],{})['calls'][0]['scored_horizons'][0]['result']=='flat'

def test_pattern_minimum_fixed_horizon_unique_role_and_no_mutation():
 vs=[verdict(i) for i in range(5)];os=[outcome(i) for i in range(5)]
 for v in vs:v['positions']*=3
 r=review_report({'outcomes':os},vs,{})
 assert len(r['suggestions'])==1 and r['suggestions'][0]['n']==5
 assert r['suggestions'][0]['status']=='suggestion_only'
 assert not review_report({'outcomes':os[:4]},vs,{})['suggestions']
 assert vs[0]['positions'][0]['agent_name']=='debater_bull'

def test_private_review_validates_and_config_unchanged():
 e=Engine(store=Store());v=verdict();v.update(bull_score=.8,bear_score=.2);i=e.store.add_verdict(v)
 c=TestClient(create_app(e,'k'));h={'X-API-Key':'k'};before=dict(e.cfg.values)
 assert c.get('/accountability').status_code==401
 assert c.post(f'/verdicts/{i}/review',json={'category':'unknown','evidence':'saved evidence'}).status_code==401
 assert c.post(f'/verdicts/{i}/review',headers=h,json={'category':'bad_data','evidence':'source reference under review'}).json()['status']=='reviewer_hypothesis'
 assert c.post('/verdicts/999/review',headers=h,json={'category':'unknown','evidence':'source reference'}).status_code==404
 assert c.post(f'/verdicts/{i}/review',headers=h,json={'category':'certain_cause','evidence':'source reference'}).status_code==400
 assert e.cfg.values==before

class Prices:
 source='public_fixture'
 def history(self,symbol,days):return [100+i for i in range(25)]
 def quote(self,symbol):return {'price':124,'as_of_date':datetime.now(timezone.utc).date().isoformat()}
def test_funnel_no_models_stale_and_demo_exclusion():
 d=Prices();r=screen(d,['TCS','INFY']);assert r['model_calls']==0 and len(r['shortlist'])==2
 d.quote=lambda s:{'price':124,'as_of_date':'2000-01-01'}
 r=screen(d,['TCS']);assert not r['shortlist'] and r['rows'][0]['status']=='stale_data'
 d.source='simulated';assert screen(d,['TCS'])['status']=='demo_excluded'
def test_funnel_api_auth_watchlist_cap_no_tasks():
 e=Engine();c=TestClient(create_app(e,'k'));h={'X-API-Key':'k'}
 assert c.post('/funnel',json={'symbols':['TCS']}).status_code==401
 assert c.post('/funnel',headers=h,json={'symbols':['UNKNOWN']}).status_code==400
 assert c.post('/funnel',headers=h,json={'symbols':['TCS']*21}).status_code==422
 assert c.post('/funnel',headers=h,json={'symbols':['TCS']}).json()['model_calls']==0
 assert not e.active_debates
