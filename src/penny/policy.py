from importlib.resources import files
from pathlib import Path
from typing import Literal

import yaml
from pydantic import Field, field_validator

from penny.config import Limits, StrictModel, read_yaml


class Models(StrictModel):
    cheap: str
    strong: str
    local: str
    local_strong: str | None = None
    fallbacks: list[str] = Field(default_factory=list)

    @field_validator("cheap", "strong", "local", "local_strong")
    @classmethod
    def provider_prefix(cls, value):
        if value is not None and ("/" not in value or not all(value.split("/", 1))):
            raise ValueError("Use provider/model format")
        return value


class AutoApprove(StrictModel):
    reads: bool = True
    commands: list[str] = Field(default_factory=lambda: ["pytest -q", "python -m pytest -q"])


class GitPolicy(StrictModel):
    branch_prefix: str = "penny/"
    allow_push: bool = False


class Policy(StrictModel):
    version: Literal[1] = 1
    confidential: bool = False
    confidential_globs: list[str] = Field(default_factory=list)
    on_confidential: Literal["go_local", "withhold", "block"] = "go_local"
    de_escalate: bool = True
    test_command: str | None = None
    auto_approve: AutoApprove = Field(default_factory=AutoApprove)
    limits: Limits = Field(default_factory=Limits)
    models: Models
    git: GitPolicy = Field(default_factory=GitPolicy)


def example_policy() -> str:
    return files("penny").joinpath("defaults/policy.yaml").read_text(encoding="utf-8")


def load_policy(repo: Path) -> Policy:
    path = repo / ".penny/policy.yaml"
    return Policy.model_validate(
        read_yaml(path) if path.exists() else yaml.safe_load(example_policy())
    )
