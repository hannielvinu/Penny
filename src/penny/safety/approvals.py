from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from tempfile import gettempdir
from typing import Protocol

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from penny.safety.risk import Risk


class UserQuit(Exception):
    pass


@dataclass
class Approval:
    kind: str
    risk: Risk
    content: str
    cost_usd: float | None = None
    decision: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self):
        return asdict(self)


class Approver(Protocol):
    def approve(self, request: Approval) -> bool: ...


class DenyAllApprover:
    def approve(self, request: Approval) -> bool:
        return False


class ScriptedApprover:
    def __init__(self, decisions: list[bool]):
        self.decisions = iter(decisions)

    def approve(self, request: Approval) -> bool:
        return request.risk != Risk.BLOCKED and next(self.decisions, False)


class InteractiveApprover:
    def __init__(self, console: Console | None = None):
        self.console = console or Console()
        self.writes = False

    def approve(self, request: Approval) -> bool:
        if request.risk == Risk.BLOCKED:
            return False
        if self.writes and request.kind == "write" and request.risk == Risk.MEDIUM:
            return True
        self.console.print(
            Panel(
                Text(request.content),
                title=f"[{request.risk}] {request.kind}",
                subtitle=f"Cost so far: {request.cost_usd if request.cost_usd is not None else 'price not configured'}",
            )
        )
        while True:
            answer = (
                self.console.input("[y]es / [n]o / [a]ll writes / [d]iff / [q]uit: ")
                .lower()
                .strip()
            )
            if answer == "q":
                raise UserQuit()
            if answer == "d":
                self.console.print(request.content, markup=False)
                continue
            if answer == "a" and request.kind == "write" and request.risk == Risk.MEDIUM:
                self.writes = True
                return True
            return answer == "y"


class SandboxAutoApprover:
    """Only benchmark copies explicitly registered under an owned temporary directory."""

    def __init__(self, root: Path):
        root = root.resolve()
        if (
            not root.is_relative_to(Path(gettempdir()).resolve())
            or not (root / ".penny-benchmark-sandbox").is_file()
        ):
            raise ValueError("Auto approval requires a marked temporary benchmark sandbox")
        self.root = root

    def approve(self, request: Approval) -> bool:
        return request.risk in {Risk.LOW, Risk.MEDIUM} and request.kind != "budget"
