"""The one module that reads environment variables.

Every setting has a safe default: the slice runs with none set. Names match
.env.example. Invalid values stop startup with a ConfigError.
"""

from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from mcp_greenroom.models import Identity, Role

ENV_PREFIX = "MCP_GREENROOM_"

# Stub identities, dev environment only. Synthetic tokens, not secrets.
# All three may submit; two are reviewers (separation of duties needs two).
DEV_IDENTITIES: dict[str, Identity] = {
    "dev-dana": Identity(id="dana", roles=frozenset({Role.SUBMITTER})),
    "dev-riley": Identity(id="riley", roles=frozenset({Role.SUBMITTER, Role.REVIEWER})),
    "dev-sam": Identity(id="sam", roles=frozenset({Role.SUBMITTER, Role.REVIEWER})),
}


class ConfigError(Exception):
    """Invalid configuration. The message says what failed, what was received, what to do."""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix=ENV_PREFIX,
        env_file=".env",
        extra="ignore",
        frozen=True,
        protected_namespaces=(),
    )

    env: Literal["dev"] = "dev"
    api: str = "http://localhost:8000"
    token: SecretStr | None = None

    database_url: str = "sqlite:///./mcp-greenroom.db"
    snapshot_path: Path = Path("snapshots/last-good.json")

    risk_provider: Literal["replay", "live"] = "replay"
    recordings_dir: Path = Path("evals/recordings")
    model_base_url: str = "https://api.anthropic.com"
    model: str = ""
    model_api_key: SecretStr | None = None

    reject_threshold: float = Field(default=0.80, gt=0.0, le=1.0)
    approve_threshold: float = Field(default=0.20, ge=0.0, lt=1.0)
    policy_version: str = "2026-11-17.1"
    require_human_for_all: bool = False

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"


def load_settings(env_file: str | None = ".env") -> Settings:
    """Read and validate the configuration. Raises ConfigError on any bad value."""
    return Settings(_env_file=env_file)  # type: ignore[call-arg]
