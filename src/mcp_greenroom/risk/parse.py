"""Parse the classifier's answer into a RiskResult. Anything off is ClassifierUnavailable."""

from mcp_greenroom.models import RiskResult


def parse_answer(text: str, tool_name: str, model_id: str, prompt_hash: str) -> RiskResult:
    raise NotImplementedError
