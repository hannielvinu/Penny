from statistics import median

from penny.cost.history import read_history
from penny.repo.repomap import RepoMap


def quote(repo_map: RepoMap, map_tokens: int, pricing, model: str) -> dict:
    history = read_history(repo_map.root, len(repo_map.files))
    if len(history) >= 3:
        average = median(v["tokens_in"] + v["tokens_out"] for v in history)
        low, high = int(average * 0.6), int(average * 1.8)
        assumptions = "estimate from median of similar-size repository runs; approx tokens"
    else:
        low, high = map_tokens + 6000, map_tokens + 42000
        assumptions = "cold-start estimate, wide range; 6–14 steps; approx characters/4 tokens"
    return dict(
        low=low,
        high=high,
        cost_low=pricing.cost(model, int(low * 0.85), int(low * 0.15)),
        cost_high=pricing.cost(model, int(high * 0.85), int(high * 0.15)),
        assumptions=assumptions,
        files=len(repo_map.files),
    )
