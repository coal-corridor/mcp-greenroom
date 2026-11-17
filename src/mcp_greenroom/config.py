"""The one module that reads environment variables.

Every setting has a safe default: the slice runs with none set. Names match
.env.example. Invalid values stop startup with a ConfigError.
"""

import os
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, ValidationError, model_validator
from pydantic_core import ErrorDetails
from pydantic_settings import BaseSettings, SettingsConfigDict

from mcp_greenroom.models import Identity, Role

ENV_PREFIX = "MCP_GREENROOM_"

# The scanner package imports litellm, which fetches a remote cost map on import unless this
# is set. Tests, the check command and the default run make no network call (user-approved
# change to this frozen module, vetting branch).
os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")

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

    @model_validator(mode="after")
    def _check_cross_field(self) -> "Settings":
        if self.approve_threshold >= self.reject_threshold:
            raise ValueError(
                f"{ENV_PREFIX}APPROVE_THRESHOLD ({self.approve_threshold}) must be below "
                f"{ENV_PREFIX}REJECT_THRESHOLD ({self.reject_threshold})"
            )
        if self.risk_provider == "live" and (not self.model or self.model_api_key is None):
            raise ValueError(
                f"{ENV_PREFIX}RISK_PROVIDER=live needs {ENV_PREFIX}MODEL and "
                f"{ENV_PREFIX}MODEL_API_KEY set"
            )
        return self


_SECRET_FIELDS = {"token", "model_api_key"}


def _describe(error: ErrorDetails) -> str:
    field = str(error["loc"][0]) if error["loc"] else ""
    if not field:  # cross-field rule: the message names the variables
        return error["msg"].removeprefix("Value error, ")
    received = "<hidden>" if field in _SECRET_FIELDS else repr(error["input"])
    return f"{ENV_PREFIX}{field.upper()}: {error['msg']}. Received {received}"


def load_settings(env_file: str | None = ".env") -> Settings:
    """Read and validate the configuration. Raises ConfigError on any bad value."""
    try:
        return Settings(_env_file=env_file)  # type: ignore[call-arg]
    except ValidationError as exc:
        problems = "; ".join(_describe(error) for error in exc.errors())
        raise ConfigError(
            f"Invalid configuration: {problems}. "
            "Fix the variable in the environment or in .env (see .env.example), then start again."
        ) from None
