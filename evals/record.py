"""The recording run: one live call per tool, one recording per tool. Only the user starts it,
through /record-classifier (`make record`). It needs MCP_GREENROOM_MODEL and
MCP_GREENROOM_MODEL_API_KEY in the shell, and the network.
"""

import argparse
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from evals.cases import UNRECORDED, load_dataset, load_sample, sample_slugs
from mcp_greenroom.config import ENV_PREFIX, ConfigError, load_settings
from mcp_greenroom.interfaces import ClassifierUnavailable
from mcp_greenroom.models import Tool
from mcp_greenroom.risk.live import LiveAnswer, LiveProvider
from mcp_greenroom.risk.prompt import Prompt, load_prompt, recording_key
from mcp_greenroom.risk.recording import (
    Recording,
    Usage,
    description_digest,
    recording_path,
    write_recording,
)

ATTEMPTS = 3


@dataclass
class Summary:
    recorded: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)
    orphans: list[str] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    model_ids: set[str] = field(default_factory=set)


def targets() -> list[Tool]:
    """Every evaluation case and every sample tool, except unrecorded-reporter's."""
    tools = [case.tool for case in load_dataset()]
    for slug in sample_slugs():
        if slug != UNRECORDED:
            tools += load_sample(slug).tools
    return tools


def _now() -> datetime:
    return datetime.now(UTC)


def _ask(provider: LiveProvider, tool: Tool, sleep: Callable[[float], None]) -> LiveAnswer:
    for attempt in range(ATTEMPTS):
        try:
            return provider.exchange(tool)
        except ClassifierUnavailable:
            if attempt == ATTEMPTS - 1:
                raise
            sleep(2.0 * 2**attempt)
    raise AssertionError("unreachable")


def record_all(
    provider: LiveProvider,
    prompt: Prompt,
    directory: Path,
    tools: list[Tool],
    *,
    force: bool = False,
    prune: bool = False,
    clock: Callable[[], datetime] | None = None,
    sleep: Callable[[float], None] | None = None,
) -> Summary:
    """Record each tool once. Keeps existing recordings unless forced. A failed call writes
    nothing, so replay misses and the tool goes to human review."""
    clock = clock or _now
    sleep = sleep or time.sleep
    summary = Summary()
    wanted: dict[str, Tool] = {recording_key(prompt, tool): tool for tool in tools}
    for key, tool in wanted.items():
        label = ascii(tool.name)
        if recording_path(directory, key).exists() and not force:
            summary.skipped.append(label)
            continue
        try:
            answer = _ask(provider, tool, sleep)
        except ClassifierUnavailable:
            summary.failed.append(label)
            continue
        write_recording(
            directory,
            Recording(
                key=key,
                prompt_version=prompt.version,
                prompt_hash=prompt.hash,
                model_id=answer.model_id,
                recorded_at=clock(),
                tool_name=tool.name,
                description_sha256=description_digest(tool.description),
                stop_reason=answer.stop_reason,
                usage=Usage(input_tokens=answer.input_tokens, output_tokens=answer.output_tokens),
                answer=answer.text,
            ),
        )
        summary.recorded.append(label)
        summary.model_ids.add(answer.model_id)
        summary.input_tokens += answer.input_tokens
        summary.output_tokens += answer.output_tokens
    for path in sorted(directory.glob("*.json")):
        if path.stem not in wanted:
            summary.orphans.append(path.name)
            if prune:
                path.unlink()
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Record the classifier, one live call per tool.")
    parser.add_argument("--force", action="store_true", help="record again even when present")
    parser.add_argument("--prune", action="store_true", help="delete recordings nothing needs")
    parser.add_argument("--env-file", default=".env", help="settings file; empty for none")
    args = parser.parse_args(argv)
    try:
        settings = load_settings(env_file=args.env_file or None)
    except ConfigError as exc:
        sys.stderr.write(f"{exc}\n")
        return 2
    if not settings.model or settings.model_api_key is None:
        sys.stderr.write(
            f"Recording not started: {ENV_PREFIX}MODEL and {ENV_PREFIX}MODEL_API_KEY must be "
            f"set. Received model {settings.model!r} and "
            f"{'a key' if settings.model_api_key else 'no key'}. "
            "Export both in the shell (the key never goes in a file), then run make record.\n"
        )
        return 2
    prompt = load_prompt()
    provider = LiveProvider(
        settings.model_base_url, settings.model, settings.model_api_key.get_secret_value(), prompt
    )
    summary = record_all(
        provider, prompt, settings.recordings_dir, targets(), force=args.force, prune=args.prune
    )
    print(f"prompt {prompt.version} ({prompt.hash[:19]}), model {settings.model}")
    print(f"served by: {', '.join(sorted(summary.model_ids)) or '-'}")
    print(
        f"recorded {len(summary.recorded)}, kept {len(summary.skipped)}, "
        f"failed {len(summary.failed)}, orphans {len(summary.orphans)}"
        f"{' (pruned)' if args.prune and summary.orphans else ''}"
    )
    print(f"tokens: {summary.input_tokens} in, {summary.output_tokens} out")
    for name in summary.failed:
        print(f"FAILED {name}: no recording written; replay will send it to human review")
    return 1 if summary.failed else 0


if __name__ == "__main__":
    sys.exit(main())
