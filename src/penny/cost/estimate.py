import math


def tokens(text: str) -> int:
    # Offline by default: tiktoken may download an encoding on its first use.
    return math.ceil(len(text) / 4)


def estimate_label() -> str:
    return "approx (characters / 4)"
