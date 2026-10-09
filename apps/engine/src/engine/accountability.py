"""Evidence-led reviews. Return changes never establish a cause or agent accuracy."""
from collections import defaultdict

CATEGORIES = {'bad_data', 'weak_debate', 'wrong_assumption', 'market_change', 'unknown'}

def review_report(scoreboard, verdicts, reviews):
    saved = {str(v['id']): v for v in verdicts if v.get('id') is not None}
    calls, groups = [], defaultdict(list)
    for o in scoreboard['outcomes']:
        v = saved.get(str(o['id']), {})
        review = reviews.get(str(o['id']), {})
        horizons = []
        for h, f in o['horizons'].items():
            if f.get('status') != 'scored':
                continue
            sign = 1 if v.get('verdict') in {'buy','strong_buy'} else -1
            directional = None if v.get('verdict') == 'hold' else f['stock_return'] * sign
            result = 'hold_tracked' if directional is None else 'hit' if directional > 0 else 'flat' if directional == 0 else 'miss'
            horizons.append({**f, 'horizon': int(h), 'result': result})
        positions = v.get('positions', [])
        gaps = []
        if not v.get('audit', {}).get('input_snapshot'):
            gaps.append('No saved input snapshot: original quote freshness cannot be reconstructed.')
        empty = sorted({p.get('agent_name','unknown') for p in positions if not p.get('evidence')})
        if empty:
            gaps.append('No cited evidence stored for: ' + ', '.join(empty) + '. Citations alone do not prove correctness.')
        if not positions:
            gaps.append('No saved role turns; debate quality cannot be assessed.')
        if horizons and any(h['result']=='miss' for h in horizons):
            gaps.append('A directional miss is observed. Its cause remains unknown unless reviewed against evidence.')
        calls.append({**o, 'timestamp':v.get('timestamp'), 'confidence':v.get('confidence'),
                      'reasoning':v.get('reasoning',''), 'positions':positions, 'audit':v.get('audit',{}),
                      'scored_horizons':horizons, 'evidence_gaps':gaps, 'review':review,
                      'cause_status':'reviewer_hypothesis' if review else 'unknown'})
        five = next((h for h in horizons if h['horizon']==5 and h['result']!='hold_tracked'),None)
        if five:
            roles={p.get('agent_name') for p in positions if p.get('agent_name')}
            for role in roles:
                groups[(role, v.get('regime','unknown'))].append((v, five, review))
    suggestions=[]
    for (role, regime), items in groups.items():
        # One row per verdict and fixed horizon. This measures participation, not isolated responsibility.
        misses=[x for x in items if x[1]['result']=='miss']
        if len(items)<5 or len(misses)<3 or len(misses)/len(items)<.6:
            continue
        categories={c:sum(x[2].get('category')==c for x in misses) for c in CATEGORIES}
        category=max(categories,key=categories.get)
        proposal = ('Require each role to cite supplied facts and explicitly state missing evidence.' if category=='weak_debate' else
                    'Add an explicit invalidation condition and opposing scenario to each role prompt.' if category=='wrong_assumption' else
                    'Review input freshness/source checks before altering prompts or confidence thresholds.' if category=='bad_data' else
                    'Review these saved five-session misses before choosing a prompt or threshold experiment.')
        suggestions.append({'id':role+':'+regime, 'role':role, 'regime':regime, 'n':len(items), 'misses':len(misses),
                            'verdict_ids':[x[0]['id'] for x in misses], 'proposal':proposal,
                            'status':'suggestion_only', 'note':'Participated in these jury outcomes; not standalone agent accuracy, causation or a statistically validated fix. No configuration is changed.'})
    return {'calls':calls, 'suggestions':suggestions,
            'note':'Directional outcomes and benchmark-relative returns answer different questions. Causes are reviewer hypotheses, never inferred from price alone. Free Render storage remains ephemeral.'}
