from datetime import date
from pathlib import Path

from pydantic import Field, model_validator

from penny.config import StrictModel, read_yaml


class Price(StrictModel):
    input_per_1m_usd: float | None = Field(default=None, ge=0)
    output_per_1m_usd: float | None = Field(default=None, ge=0)
    source_url: str = ""
    checked_on: str = ""

    @model_validator(mode="after")
    def documented(self):
        if self.input_per_1m_usd is not None or self.output_per_1m_usd is not None:
            if not self.source_url.startswith("https://"):
                raise ValueError("Configured prices require an HTTPS source_url")
            date.fromisoformat(self.checked_on)
        return self

    def cost(self, incoming: int, outgoing: int) -> float | None:
        if self.input_per_1m_usd is None or self.output_per_1m_usd is None:
            return None
        return (incoming * self.input_per_1m_usd + outgoing * self.output_per_1m_usd) / 1e6


class Pricing(StrictModel):
    models: dict[str, Price] = Field(default_factory=dict)

    def cost(self, model: str, incoming: int, outgoing: int) -> float | None:
        if model.startswith("ollama/"):
            return None
        return self.models.get(model, Price()).cost(incoming, outgoing)


def load_pricing(repo: Path) -> Pricing:
    return Pricing.model_validate(read_yaml(repo / "pricing.yaml"))
