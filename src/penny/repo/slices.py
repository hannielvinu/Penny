from penny.repo.repomap import RepoMap


class Slices:
    def __init__(self, repo_map: RepoMap, dedupe: bool = True):
        self.map = repo_map
        self.dedupe = dedupe
        self.seen: dict[tuple, tuple[int, str]] = {}

    def lines(self, path: str, start: int, end: int, step: int = 0) -> str:
        if start < 1 or end < start or end - start + 1 > 120:
            raise ValueError("Use 1-based ranges of at most 120 lines")
        text = self.map.read(path)
        key = (path, start, end)
        if self.dedupe and key in self.seen and self.seen[key][1] == text:
            return f"already provided in step {self.seen[key][0]}"
        self.seen[key] = (step, text)
        return "\n".join(
            f"{n}: {line}" for n, line in enumerate(text.splitlines(), 1) if start <= n <= end
        )

    def symbol(self, path: str, symbol: str, step: int = 0) -> str:
        self.map.build()
        matches = [
            s
            for f in self.map.files
            if f["path"] == path
            for s in f["symbols"]
            if s["name"] == symbol
        ]
        if len(matches) != 1:
            raise ValueError("Symbol missing or ambiguous; use read_lines")
        value = matches[0]
        return self.lines(
            path, value["start_line"], min(value["end_line"], value["start_line"] + 119), step
        )
