import math

# Update Exponential Moving Average of term frequencies
def update_ema(baseline: dict, counts_now: dict, alpha: float = 0.3):
    updated = baseline.copy()
    for term, c in counts_now.items():
        prev = float(updated.get(term, {}).get("ema", 0.0))
        ema = alpha * float(c) + (1 - alpha) * prev
        updated[term] = {"ema": ema}
    for term, val in baseline.items():
        if term not in counts_now:
            prev = float(val.get("ema", 0.0))
            ema = (1 - alpha) * prev
            updated[term] = {"ema": ema}
    return updated

# Compute spike scores vs EMA
def spike_scores(baseline: dict, counts_now: dict):
    scores = {}
    for term, c in counts_now.items():
        ema = float(baseline.get(term, {}).get("ema", 0.0))
        score = (float(c) - ema) / max(1.0, math.sqrt(ema)) if ema >= 0 else 0.0
        scores[term] = round(score, 2)
    return scores
