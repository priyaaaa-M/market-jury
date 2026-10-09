import httpx
import pytest

from engine.twelvedata import DataUnavailable, TwelveData


def response():
    return {'meta':{'symbol':'TCS','exchange':'NSE','currency':'INR'},'values':[{'datetime':'2026-10-09','close':'2156'}]}

def test_cache_expiry_and_no_click_refetch():
    ticks=[0];calls=[]
    def handle(req):calls.append(req);return httpx.Response(200,json=response())
    p=TwelveData('test',transport=httpx.MockTransport(handle),clock=lambda:ticks[0])
    a=p.quote('TCS')
    for _ in range(20):assert p.quote('TCS')['retrieved_at']==a['retrieved_at']
    assert len(calls)==1
    ticks[0]=301;p.quote('TCS');assert len(calls)==2
    assert 'apikey=' not in str(calls[0].url)

def test_http_and_json_limit_backoff():
    for http_code in (200,429):
        ticks=[0];calls=[]
        def handle(req):calls.append(req);return httpx.Response(http_code,json={'code':429,'status':'error'})
        p=TwelveData('test',transport=httpx.MockTransport(handle),clock=lambda:ticks[0])
        for _ in range(10):
            with pytest.raises(DataUnavailable):p.quote('TCS')
        assert len(calls)==1
        ticks[0]=61
        with pytest.raises(DataUnavailable):p.quote('TCS')
        assert len(calls)==2

def test_shared_8_minute_budget():
    calls=[];ticks=[0]
    def handle(req):calls.append(req);return httpx.Response(200,json={'ok':True})
    p=TwelveData('test',transport=httpx.MockTransport(handle),clock=lambda:ticks[0])
    for i in range(8):p._request('/x',{'symbol':str(i)})
    with pytest.raises(DataUnavailable):p._request('/x',{'symbol':'9'})
    assert len(calls)==8
    ticks[0]=62;p._request('/x',{'symbol':'9'});assert len(calls)==9

def test_intraday_metadata_and_mismatch():
    def handle(req):return httpx.Response(200,json={'symbol':'TCS','exchange':'NSE','currency':'INR','close':'2156','timestamp':1791540000,'last_quote_at':1791541000})
    p=TwelveData('test',transport=httpx.MockTransport(handle))
    q=p.quote('TCS',intraday=True)
    assert q['comparison_price_type']=='intraday_last_trade' and q['price']==2156
    with pytest.raises(DataUnavailable):p.quote('WRONG',intraday=True)

def test_missing_key_never_calls_provider():
    p=TwelveData('',transport=httpx.MockTransport(lambda r:pytest.fail('unexpected request')))
    with pytest.raises(DataUnavailable):p.quote('TCS')
