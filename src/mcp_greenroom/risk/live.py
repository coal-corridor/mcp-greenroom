"""Live provider: one call to an endpoint that speaks the Anthropic Messages API, over httpx.

Used only by the recording run. Base URL, model and key come from configuration. The key
goes in a header, never in a log line or an error message. Every failure is
ClassifierUnavailable, so the tool goes to human review.
"""

from dataclasses import dataclass
from typing import Any

import httpx

from mcp_greenroom.interfaces import ClassifierUnavailable
from mcp_greenroom.models import RiskResult, Tool
from mcp_greenroom.risk.parse import ANSWER_SCHEMA, parse_answer
from mcp_greenroom.risk.prompt import Prompt, load_prompt, user_message

API_VERSION = "2026-10-21"
MAX_TOKENS = 4096


class LiveCallFailed(ClassifierUnavailable):
    """The call itself failed. status is the HTTP status, or None for a transport error."""

    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status

    @property
    def retryable(self) -> bool:
        return self.status is None or self.status in (408, 409, 429) or self.status >= 500


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

    def _post(self, body: dict[str, Any]) -> dict[str, Any]:
        """The one outbound call of the vetting area."""
        url = f"{self.base_url.rstrip('/')}/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": API_VERSION,
            "content-type": "application/json",
        }
        try:
            with httpx.Client(transport=self.transport, timeout=self.timeout) as client:
                response = client.post(url, headers=headers, json=body)
        except httpx.HTTPError as exc:
            raise LiveCallFailed(
                f"Classifier call failed: {type(exc).__name__} calling {url}. "
                "Check the endpoint and the network, then run the recording again."
            ) from None
        if response.status_code != 200:
            raise LiveCallFailed(
                f"Classifier call failed: HTTP {response.status_code} from {url}. "
                "Check the model name, the key variable and the rate limit, then run again.",
                response.status_code,
            )
        try:
            data = response.json()
        except ValueError:
            data = None
        if not isinstance(data, dict):
            raise ClassifierUnavailable(
                f"Classifier call failed: the body from {url} is not a JSON message. "
                "Check that the endpoint speaks the Messages API."
            )
        return data

    def exchange(self, tool: Tool) -> LiveAnswer:
        """Send one tool, return the raw answer as the recorder stores it."""
        data = self._post(
            {
                "model": self.model,
                "max_tokens": MAX_TOKENS,
                "system": self.prompt.text,
                "messages": [{"role": "user", "content": user_message(tool)}],
                "output_config": {"format": {"type": "json_schema", "schema": ANSWER_SCHEMA}},
            }
        )
        try:
            content = data["content"]
            text = "".join(b["text"] for b in content if b.get("type") == "text")
            usage = data.get("usage") or {}
            return LiveAnswer(
                text=text,
                model_id=str(data["model"]),
                stop_reason=str(data["stop_reason"]),
                input_tokens=int(usage.get("input_tokens", 0)),
                output_tokens=int(usage.get("output_tokens", 0)),
            )
        except (KeyError, TypeError, AttributeError, ValueError):
            raise ClassifierUnavailable(
                "Classifier call failed: the reply is not a Messages API message. "
                "Check that the endpoint speaks the Messages API."
            ) from None

    def classify(self, tool: Tool) -> RiskResult:
        answer = self.exchange(tool)
        if answer.stop_reason != "end_turn":
            raise ClassifierUnavailable(
                f"Classifier answer did not end cleanly: stop reason "
                f"{ascii(answer.stop_reason[:20])}. The tool goes to human review."
            )
        return parse_answer(answer.text, tool.name, answer.model_id, self.prompt.hash)
