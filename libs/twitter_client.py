# Twitter (X) client with two modes:
# 1) snscrape (no API keys)
# 2) Tweepy (X API v2)

import datetime as dt
from typing import List, Dict

def _normalize(text: str) -> str:
    return " ".join(text.split())

def search_with_snscrape(query: str, lang: str = "ar", minutes: int = 15, limit: int = 300) -> List[Dict]:
    try:
        import snscrape.modules.twitter as sntwitter
    except Exception as e:
        raise RuntimeError("snscrape is not installed. Please `pip install snscrape`.") from e

    since_time = dt.datetime.utcnow() - dt.timedelta(minutes=minutes)
    q = f'{query} lang:{lang}'
    results = []
    for i, tweet in enumerate(sntwitter.TwitterSearchScraper(q).get_items()):
        if i >= limit:
            break
        created = tweet.date
        if created < since_time.replace(tzinfo=created.tzinfo):
            break
        results.append({
            "id": str(tweet.id),
            "date": created.isoformat(),
            "content": _normalize(tweet.content or ""),
            "user": getattr(tweet.user, "username", ""),
            "likeCount": getattr(tweet, "likeCount", 0),
            "replyCount": getattr(tweet, "replyCount", 0),
            "retweetCount": getattr(tweet, "retweetCount", 0),
        })
    return results

def search_with_tweepy(query: str, bearer_token: str, lang: str = "ar", minutes: int = 15, max_results: int = 100) -> List[Dict]:
    import tweepy
    client = tweepy.Client(bearer_token=bearer_token, wait_on_rate_limit=True)
    end_time = dt.datetime.utcnow()
    start_time = end_time - dt.timedelta(minutes=minutes)
    resp = client.search_recent_tweets(
        query=f"{query} lang:{lang} -is:retweet",
        start_time=start_time.isoformat("T") + "Z",
        end_time=end_time.isoformat("T") + "Z",
        max_results=min(max_results, 100),
        tweet_fields=["created_at", "public_metrics", "lang"]
    )
    out = []
    if resp.data:
        for t in resp.data:
            m = t.data.get("public_metrics", {})
            out.append({
                "id": str(t.id),
                "date": t.created_at.isoformat(),
                "content": _normalize(t.text or ""),
                "user": "",
                "likeCount": m.get("like_count", 0),
                "replyCount": m.get("reply_count", 0),
                "retweetCount": m.get("retweet_count", 0),
            })
    return out
