import math
import re
from collections import Counter


def words(text: str) -> list[str]:
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    return re.findall(r"[a-z0-9]+", text.lower())


def rank(query: str, documents: list[str]) -> list[tuple[int, float]]:
    tokens = [words(d) for d in documents]
    avg = sum(map(len, tokens)) / max(len(tokens), 1) or 1
    frequency = Counter(w for t in tokens for w in set(t))
    result = []
    for i, doc in enumerate(tokens):
        counts = Counter(doc)
        score = 0.0
        for term in set(words(query)):
            tf = counts[term]
            idf = math.log(1 + (len(tokens) - frequency[term] + 0.5) / (frequency[term] + 0.5))
            score += idf * tf * 2.5 / (tf + 1.5 * (0.25 + 0.75 * len(doc) / avg))
        result.append((i, score))
    return sorted(result, key=lambda pair: (-pair[1], pair[0]))
