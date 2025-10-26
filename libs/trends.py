from typing import List, Dict
from pytrends.request import TrendReq

def rising_queries(seed_terms: List[str], geo: str = "JO") -> Dict[str, List[str]]:
    pytrends = TrendReq(hl='ar', tz=180)
    suggestions = {}
    for term in seed_terms:
        try:
            pytrends.build_payload([term], timeframe='now 1-d', geo=geo)
            rq = pytrends.related_queries()
            rising = rq.get(term, {}).get('rising', None)
            if rising is not None:
                suggestions[term] = [str(x) for x in rising['query'].head(10).tolist()]
        except Exception:
            suggestions[term] = []
    return suggestions
