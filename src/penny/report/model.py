from datetime import UTC, datetime
from typing import Literal

from pydantic import Field

from penny.config import StrictModel
from penny.version import __version__


class RunRecord(StrictModel):
    id: str
    version: str = __version__
    started_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    finished_at: str | None = None
    status: Literal["success", "failed", "aborted", "budget_stopped", "denied", "gateway_error"] = (
        "failed"
    )
    task: str
    repo: str
    base_commit: str = ""
    base_branch: str = ""
    branch: str = ""
    allow_dirty: bool = False
    flags: dict = Field(default_factory=dict)
    policy: dict = Field(default_factory=dict)
    quote: dict = Field(default_factory=dict)
    steps: list[dict] = Field(default_factory=list)
    approvals: list[dict] = Field(default_factory=list)
    budget_events: list[dict] = Field(default_factory=list)
    failover_events: list[dict] = Field(default_factory=list)
    withheld_files: list[str] = Field(default_factory=list)
    files_changed: list[str] = Field(default_factory=list)
    created_files: list[str] = Field(default_factory=list)
    tests: list[dict] = Field(default_factory=list)
    totals: dict = Field(default_factory=dict)
    undo_command: str = ""
    final_diff: str = ""
    error: str | None = None
    summary: str = ""
