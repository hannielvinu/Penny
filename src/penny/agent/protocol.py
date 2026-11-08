import json
from typing import Literal

from pydantic import Field, field_validator

from penny.config import StrictModel


class Search(StrictModel):
    query: str = Field(min_length=1, max_length=2000)
    max_results: int = Field(default=8, ge=1, le=8)


class ReadSymbol(StrictModel):
    path: str
    symbol: str


class ReadLines(StrictModel):
    path: str
    start: int = Field(ge=1)
    end: int = Field(ge=1)


class ListDir(StrictModel):
    path: str = "."


class Edit(StrictModel):
    search: str = Field(min_length=1)
    replace: str


class Patch(StrictModel):
    path: str
    edits: list[Edit] = Field(min_length=1, max_length=30)


class Create(StrictModel):
    path: str
    content: str = Field(max_length=100000)


class RunTests(StrictModel):
    target: str | None = None


class Shell(StrictModel):
    command: list[str] = Field(min_length=1, max_length=100)


class Git(StrictModel):
    op: Literal["status", "diff", "log", "add", "commit", "branch", "switch", "push"]
    args: list[str] = Field(default_factory=list)


class Escalate(StrictModel):
    reason: str


class Ask(StrictModel):
    question: str


class Finish(StrictModel):
    summary: str
    status: Literal["done", "cannot_complete"]


ARGS = {
    "search": Search,
    "read_symbol": ReadSymbol,
    "read_lines": ReadLines,
    "list_dir": ListDir,
    "apply_patch": Patch,
    "create_file": Create,
    "run_tests": RunTests,
    "run_shell": Shell,
    "git": Git,
    "escalate": Escalate,
    "ask_user": Ask,
    "finish": Finish,
}


class Action(StrictModel):
    thought: str = Field(max_length=500)
    action: str
    args: dict

    @field_validator("thought")
    @classmethod
    def short_thought(cls, value):
        if len(value.split()) > 30:
            raise ValueError("thought must be at most 30 words")
        return value

    @field_validator("action")
    @classmethod
    def known_action(cls, value):
        if value not in ARGS:
            raise ValueError("Unknown action")
        return value


def parse(text: str) -> Action:
    value = Action.model_validate_json(text, strict=True)
    value.args = ARGS[value.action].model_validate(value.args, strict=True).model_dump()
    if value.action == "read_lines" and not 0 <= value.args["end"] - value.args["start"] < 120:
        raise ValueError("Read at most 120 lines")
    return value


def schema() -> str:
    return json.dumps(
        {name: model.model_json_schema() for name, model in ARGS.items()}, separators=(",", ":")
    )
