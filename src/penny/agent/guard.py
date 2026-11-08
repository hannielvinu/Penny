import fnmatch
from dataclasses import dataclass
from typing import Literal

from penny.policy import Policy
from penny.repo.secrets import mask


@dataclass
class Chunk:
    text: str
    source_path: str | None = None
    sensitivity: Literal["public", "confidential"] = "public"


def sanitize(chunk: Chunk, policy: Policy) -> Chunk:
    clean, found = mask(chunk.text)
    private = policy.confidential or found or chunk.sensitivity == "confidential"
    if chunk.source_path:
        private |= any(fnmatch.fnmatch(chunk.source_path, p) for p in policy.confidential_globs)
    return Chunk(clean, chunk.source_path, "confidential" if private else "public")


class RouteGuard:
    @staticmethod
    def assert_allowed(chunks: list[Chunk], route: str) -> None:
        if route not in {"local", "cloud"}:
            raise ValueError("Unknown route")
        if route == "cloud" and any(c.sensitivity == "confidential" for c in chunks):
            raise ValueError("Confidential context refused on cloud route")


def prepare(chunks: list[Chunk], policy: Policy) -> tuple[list[Chunk], str, list[str]]:
    cleaned = [sanitize(c, policy) for c in chunks]
    private = any(c.sensitivity == "confidential" for c in cleaned)
    withheld = []
    if private and not policy.confidential:
        if policy.on_confidential == "block":
            raise ValueError("Policy blocks confidential context")
        if policy.on_confidential == "withhold":
            withheld = [
                c.source_path or "context" for c in cleaned if c.sensitivity == "confidential"
            ]
            cleaned = [
                Chunk("[file withheld]", c.source_path) if c.sensitivity == "confidential" else c
                for c in cleaned
            ]
            private = False
    route = "local" if private or policy.confidential else "cloud"
    RouteGuard.assert_allowed(cleaned, route)
    return cleaned, route, withheld
