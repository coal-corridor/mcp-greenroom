"""Build the pipeline from configuration. The registry's get_pipeline calls this."""

from mcp_greenroom.config import Settings
from mcp_greenroom.vetting.pipeline import VettingPipeline


def build_pipeline(settings: Settings) -> VettingPipeline:
    raise NotImplementedError
