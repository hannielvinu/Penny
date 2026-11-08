import re


def trim(output: str, max_chars: int = 4800) -> str:
    if len(output) <= max_chars:
        return output
    lines = output.splitlines()
    important = [
        line
        for line in lines
        if re.search(r"FAILED |ERROR |AssertionError|^E\s|=+.*(?:failed|passed|error)", line)
    ]
    tail = "\n".join(lines[-90:])
    combined = "\n".join(important[:30]) + "\n[output trimmed; full output stored locally]\n" + tail
    return combined[: max_chars // 3] + "\n…\n" + combined[-(max_chars * 2 // 3 - 5) :]
