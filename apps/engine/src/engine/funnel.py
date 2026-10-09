"""Bounded public-data triage, not an AI verdict or personalised ranking."""
import math
from datetime import datetime, timezone, date

def screen(data, symbols):
    if data.source == 'simulated':
        return {'rows':[], 'shortlist':[], 'status':'demo_excluded', 'model_calls':0,
                'note':'Synthetic data cannot make a real research shortlist.'}
    rows=[]
    for symbol in symbols:
        try:
            h=data.history(symbol,60)
            if len(h)<21 or any(not math.isfinite(x) or x<=0 for x in h):
                raise ValueError('Need at least21 valid observed daily prices')
            quote=data.quote(symbol)
            as_of=quote.get('as_of_date',quote.get('timestamp',''))
            observed=date.fromisoformat(str(as_of)[:10])
            age=(datetime.now(timezone.utc).date()-observed).days
            if age<0 or age>7:
                rows.append({'symbol':symbol,'status':'stale_data','as_of':as_of,'reason':'Provider observation outside7-calendar-day freshness guard. Not shortlisted.'})
                continue
            change=h[-1]/h[-21]-1
            rows.append({'symbol':symbol,'status':'screened','change_20_observations':round(change,4),
                         'price':quote['price'],'as_of':quote.get('as_of_date',quote.get('timestamp')),
                         'data_source':data.source,'price_type':quote.get('price_type','provider daily observation'),
                         'criterion':abs(change), 'reason':'Largest absolute20-observation price moves. A research attention heuristic, not a buy/sell signal.'})
        except (ValueError,RuntimeError,KeyError):
            rows.append({'symbol':symbol,'status':'data_unavailable','reason':'Not enough valid provider observations. No synthetic fallback.'})
    rows.sort(key=lambda r:r.get('criterion',-1),reverse=True)
    return {'rows':rows,'shortlist':[r['symbol'] for r in rows if r['status']=='screened'][:3],
            'status':'complete','model_calls':0,'created_at':datetime.now(timezone.utc).isoformat(),
            'note':'Stage1 uses public delayed prices only and no AI calls. It is not a debate or fundamentals/news screen. Stage2 runs a normal four-role discussion only when you select a stock. Free model limits still apply.'}
