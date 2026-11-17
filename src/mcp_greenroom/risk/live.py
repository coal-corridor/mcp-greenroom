"""Live provider: one call to an endpoint that speaks the Anthropic Messages API, over httpx."""

from dataclasses import dataclass

import httpx

from mcp_greenroom.models import RiskResult, Tool
from mcp_greenroom.risk.prompt import Prompt, load_prompt


@dataclass(frozen=True)
class LiveAnswer:
    text: str
    model_id: str
    stop_reason: str
    input_tokens: int
    output_tokens: int


class LiveProvider:
    """Implements interfaces.ClassifierProvider. Used only by the recording run."""

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str,
        prompt: Prompt | None = None,
        transport: httpx.BaseTransport | None = None,
        timeout: float = 120.0,
    ) -> None:
        self.base_url = base_url
        self.model = model
        self.api_key = api_key
        self.prompt = prompt or load_prompt()
        self.transport = transport
        self.timeout = timeout

    def exchange(self, tool: Tool) -> LiveAnswer:
        raise NotImplementedError

    def classify(self, tool: Tool) -> RiskResult:
        raise NotImplementedError
