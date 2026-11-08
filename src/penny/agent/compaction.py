from penny.agent.guard import Chunk
from penny.cost.estimate import tokens


def compact(chunks: list[Chunk], cap: int) -> list[Chunk]:
    result = list(chunks)
    for i in range(2, max(2, len(result) - 2)):
        if sum(tokens(c.text) for c in result) <= cap:
            break
        c = result[i]
        result[i] = Chunk(f"[older context {i} truncated]", c.source_path, c.sensitivity)
    if sum(tokens(c.text) for c in result) > cap:
        raise ValueError("Prompt cap exceeded; finish or increase max_prompt_tokens")
    return result
