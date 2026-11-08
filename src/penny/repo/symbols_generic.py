import re

PATTERN = re.compile(
    r"^\s*(?:(?:export|public|private|static|async|pub)\s+)*(?:(?:function|class|interface|func|fn|struct|enum)\s+([\w]+)|(?:const|let)\s+(\w+)\s*=)"
)


def extract(text: str) -> list[dict]:
    lines = text.splitlines()
    starts = [(i, m) for i, line in enumerate(lines, 1) if (m := PATTERN.match(line))]
    return [
        dict(
            name=m.group(1) or m.group(2),
            kind="symbol",
            signature=lines[i - 1].strip()[:180],
            start_line=i,
            end_line=starts[n + 1][0] - 1 if n + 1 < len(starts) else len(lines),
            docstring_first_line="",
        )
        for n, (i, m) in enumerate(starts)
    ]
