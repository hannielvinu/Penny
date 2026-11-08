from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)
    penny_mock: bool = False
    bifrost_base_url: str = "http://localhost:8080"
    bifrost_vk_dev: SecretStr = SecretStr("")
    bifrost_vk_local: SecretStr = SecretStr("")
    chaos_proxy_url: str = "http://localhost:8099"


def read_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} must contain a YAML mapping")
    return value


class Limits(StrictModel):
    budget_usd: float = Field(default=0.5, ge=0)
    max_steps: int = Field(default=25, ge=1, le=500)
    max_prompt_tokens: int = Field(default=12000, ge=256)
    max_output_tokens: int = Field(default=800, ge=64)
    max_wall_seconds: int = Field(default=900, ge=1)
    token_cap: int = Field(default=150000, ge=1)
