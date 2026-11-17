"""Live provider over httpx, against a mock transport: no socket is ever opened."""

import json
from collections.abc import Callable

import httpx
import pytest

from mcp_greenroom.interfaces import ClassifierUnavailable
from mcp_greenroom.models import Capability, Tool
from mcp_greenroom.risk.live import LiveProvider
from mcp_greenroom.risk.prompt import load_prompt, user_message

PROMPT = load_prompt()
TOOL = Tool(name="export_report", description="Send a report to a URL you choose.")
KEY = "test-key-not-a-secret"
ANSWER = {"score": 0.1, "capabilities": ["network_egress"], "evidence": "", "rationale": "Sends."}


def reply(
    text: str = json.dumps(ANSWER), stop_reason: str = "end_turn", status: int = 200
) -> Callable[[httpx.Request], httpx.Response]:
    body = {
        "id": "msg_1",
        "type": "message",
        "role": "assistant",
        "model": "claude-test-model",
        "content": [{"type": "thinking", "thinking": ""}, {"type": "text", "text": text}],
        "stop_reason": stop_reason,
        "usage": {"input_tokens": 812, "output_tokens": 57},
    }

    def handler(request: httpx.Request) -> httpx.Response:
        handler.seen = request  # type: ignore[attr-defined]
        return httpx.Response(status, json=body)

    return handler


def provider(handler: Callable[[httpx.Request], httpx.Response]) -> LiveProvider:
    return LiveProvider(
        "https://models.example.test/",
        "claude-test-model",
        KEY,
        PROMPT,
        transport=httpx.MockTransport(handler),
    )


def test_the_request_speaks_the_messages_api() -> None:
    handler = reply()
    provider(handler).classify(TOOL)
    request: httpx.Request = handler.seen  # type: ignore[attr-defined]
    assert request.method == "POST"
    assert str(request.url) == "https://models.example.test/v1/messages"
    assert request.headers["x-api-key"] == KEY
    assert request.headers["anthropic-version"] == "2026-10-21"
    body = json.loads(request.content)
    assert body["model"] == "claude-test-model"
    assert body["system"] == PROMPT.text
    assert body["messages"] == [{"role": "user", "content": user_message(TOOL)}]
    assert body["output_config"]["format"]["type"] == "json_schema"
    assert KEY not in request.content.decode()


def test_the_answer_becomes_a_risk_result_with_the_served_model_id() -> None:
    result = provider(reply()).classify(TOOL)
    assert result.score == 0.1
    assert result.capabilities == {Capability.NETWORK_EGRESS}
    assert result.model_id == "claude-test-model"
    assert result.prompt_hash == PROMPT.hash


def test_the_exchange_keeps_what_the_recorder_needs() -> None:
    answer = provider(reply()).exchange(TOOL)
    assert (answer.model_id, answer.stop_reason) == ("claude-test-model", "end_turn")
    assert (answer.input_tokens, answer.output_tokens) == (812, 57)
    assert json.loads(answer.text) == ANSWER


@pytest.mark.parametrize("stop_reason", ["refusal", "max_tokens"])
def test_an_answer_that_did_not_end_cleanly_is_unavailable(stop_reason: str) -> None:
    with pytest.raises(ClassifierUnavailable):
        provider(reply(stop_reason=stop_reason)).classify(TOOL)


@pytest.mark.parametrize("status", [400, 401, 429, 500, 529])
def test_an_error_status_is_unavailable_and_never_shows_the_key(status: int) -> None:
    with pytest.raises(ClassifierUnavailable) as caught:
        provider(reply(status=status)).classify(TOOL)
    assert str(status) in str(caught.value)
    assert KEY not in str(caught.value)


def test_a_transport_failure_is_unavailable() -> None:
    def down(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("timed out", request=request)

    with pytest.raises(ClassifierUnavailable):
        provider(down).classify(TOOL)


def test_a_body_that_is_not_a_message_is_unavailable() -> None:
    def junk(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html>proxy error</html>")

    with pytest.raises(ClassifierUnavailable):
        provider(junk).classify(TOOL)
