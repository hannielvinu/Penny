from dataclasses import dataclass, field

from penny.pricing import Pricing


class BudgetStop(Exception):
    pass


@dataclass
class Ledger:
    pricing: Pricing
    entries: list[dict] = field(default_factory=list)

    @property
    def tokens_in(self) -> int:
        return sum(e["tokens_in"] for e in self.entries)

    @property
    def tokens_out(self) -> int:
        return sum(e["tokens_out"] for e in self.entries)

    @property
    def cost(self) -> float | None:
        if not self.entries or any(e["cost_usd"] is None for e in self.entries):
            return None
        return sum(e["cost_usd"] for e in self.entries)

    def add(self, model: str, incoming: int, outgoing: int, source: str, **extra) -> dict:
        entry = dict(
            model=model,
            tokens_in=incoming,
            tokens_out=outgoing,
            tokens_source=source,
            cost_usd=self.pricing.cost(model, incoming, outgoing),
            **extra,
        )
        self.entries.append(entry)
        return entry

    def check(self, models: list[str], incoming: int, outgoing: int, budget: float, token_cap: int):
        if self.tokens_in + self.tokens_out + incoming + outgoing > token_cap:
            raise BudgetStop("Agent token cap reached (includes next-call estimate)")
        costs = [self.pricing.cost(m, incoming, outgoing) for m in models]
        if any(c is None for c in costs) or any(e["cost_usd"] is None for e in self.entries):
            return  # Token cap applies; gateway budget is independent.
        upper = max(c for c in costs if c is not None)
        spent = self.cost or 0
        if spent + upper > budget:
            raise BudgetStop(
                f"Agent budget cap reached: {spent:.6f} spent; next call estimate up to {upper:.6f}"
            )
