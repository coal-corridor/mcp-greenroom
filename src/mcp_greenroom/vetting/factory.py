"""Build the pipeline from configuration. The registry's get_pipeline calls this."""

from mcp_greenroom.config import Settings
from mcp_greenroom.interfaces import ClassifierProvider
from mcp_greenroom.risk.live import LiveProvider
from mcp_greenroom.risk.replay import ReplayProvider
from mcp_greenroom.scanner.null import NullScanner
from mcp_greenroom.vetting.pipeline import Policy, VettingPipeline


def build_provider(settings: Settings) -> ClassifierProvider:
    if settings.risk_provider == "live" and settings.model_api_key is not None:
        return LiveProvider(
            settings.model_base_url,
            settings.model,
            settings.model_api_key.get_secret_value(),
        )
    return ReplayProvider(settings.recordings_dir)


def build_pipeline(settings: Settings) -> VettingPipeline:
    return VettingPipeline(build_provider(settings), NullScanner(), Policy.from_settings(settings))
