"""Immutable versions: the fingerprint covers the manifest and the tool definitions."""

from mcp_greenroom.fingerprint import fingerprint
from mcp_greenroom.models import Submission, Tool

SERVER = {"name": "com.examplebank/payments-readonly", "version": "1.2.0", "description": "x"}
TOOL_A = Tool(name="get_balance", description="Read a balance.", inputSchema={"type": "object"})
TOOL_B = Tool(name="list_payments", description="List payments.", inputSchema={"a": 1, "b": 2})


def test_same_content_gives_the_same_fingerprint_whatever_the_order() -> None:
    reordered_server = dict(reversed(list(SERVER.items())))
    reordered_b = Tool(
        name=TOOL_B.name, description=TOOL_B.description, inputSchema={"b": 2, "a": 1}
    )
    first = fingerprint(Submission(server=SERVER, tools=[TOOL_A, TOOL_B]))
    second = fingerprint(Submission(server=reordered_server, tools=[reordered_b, TOOL_A]))
    assert first == second
    assert first.startswith("sha256:")


def test_any_change_to_a_tool_or_the_manifest_changes_it() -> None:
    base = fingerprint(Submission(server=SERVER, tools=[TOOL_A]))
    edited_tool = Tool(
        name=TOOL_A.name, description="Read a balance. ", inputSchema={"type": "object"}
    )
    assert fingerprint(Submission(server=SERVER, tools=[edited_tool])) != base
    assert fingerprint(Submission(server={**SERVER, "description": "y"}, tools=[TOOL_A])) != base
