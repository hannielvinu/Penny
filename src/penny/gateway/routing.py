from dataclasses import dataclass

from penny.config import Settings
from penny.policy import Policy


@dataclass
class Route:
    name: str
    model: str
    key: str
    fallbacks: list[str]


def select(policy: Policy, settings: Settings, name: str, tier: str) -> Route:
    if name == "local":
        model = (
            (policy.models.local_strong or policy.models.local)
            if tier == "strong"
            else policy.models.local
        )
        if not model.startswith("ollama/"):
            raise ValueError("Local route must use an ollama/ model")
        return Route(name, model, settings.bifrost_vk_local.get_secret_value(), [])
    if name != "cloud":
        raise ValueError("Invalid route")
    model = policy.models.strong if tier == "strong" else policy.models.cheap
    fallbacks = policy.models.fallbacks
    if model.startswith("ollama/") or any(
        m.startswith("ollama/") or "/" not in m for m in fallbacks
    ):
        raise ValueError("Cloud fallbacks must use cloud provider/model identifiers")
    return Route(name, model, settings.bifrost_vk_dev.get_secret_value(), fallbacks)
