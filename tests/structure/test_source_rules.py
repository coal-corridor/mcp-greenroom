"""Structural rules for src/: file size, and one module that reads the environment."""

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src" / "mcp_greenroom"
CONFIG_MODULE = SRC / "config.py"
MAX_LINES = 350

_ENV_NAMES = {"environ", "environb", "getenv", "getenvb", "putenv", "unsetenv"}


def _source_files() -> list[Path]:
    return sorted(SRC.rglob("*.py"))


def env_reads(source: str) -> list[int]:
    """Line numbers where the code reads the environment, directly or via pydantic-settings."""
    lines: list[int] = []
    for node in ast.walk(ast.parse(source)):
        if (
            isinstance(node, ast.Attribute)
            and node.attr in _ENV_NAMES
            and isinstance(node.value, ast.Name)
            and node.value.id == "os"
        ):
            lines.append(node.lineno)
        elif isinstance(node, ast.ImportFrom) and node.module == "os":
            if any(alias.name in _ENV_NAMES for alias in node.names):
                lines.append(node.lineno)
        elif isinstance(node, ast.ImportFrom) and (node.module or "").startswith(
            "pydantic_settings"
        ):
            lines.append(node.lineno)
        elif isinstance(node, ast.Import) and any(
            alias.name.startswith("pydantic_settings") for alias in node.names
        ):
            lines.append(node.lineno)
    return sorted(lines)


def test_source_tree_exists() -> None:
    assert _source_files(), f"No Python files under {SRC}: the rules below would pass vacuously."


def test_no_source_file_over_the_line_limit() -> None:
    too_long = {
        str(path.relative_to(ROOT)): count
        for path in _source_files()
        if (count := len(path.read_text(encoding="utf-8").splitlines())) > MAX_LINES
    }
    assert not too_long, (
        f"Source files over {MAX_LINES} lines: {too_long}. Split each into smaller modules."
    )


def test_only_the_config_module_reads_the_environment() -> None:
    offenders = {
        str(path.relative_to(ROOT)): found
        for path in _source_files()
        if path != CONFIG_MODULE and (found := env_reads(path.read_text(encoding="utf-8")))
    }
    assert not offenders, (
        f"Environment read outside {CONFIG_MODULE.relative_to(ROOT)}, at lines {offenders}. "
        "Add the setting to the config module and pass it in."
    )


@pytest.mark.parametrize(
    "snippet",
    [
        "import os\nx = os.environ['A']",
        "import os\nx = os.getenv('A')",
        "from os import environ",
        "from os import getenv as g",
        "from pydantic_settings import BaseSettings",
        "import pydantic_settings",
    ],
)
def test_env_detector_catches(snippet: str) -> None:
    assert env_reads(snippet), f"Detector missed an environment read in: {snippet!r}"


@pytest.mark.parametrize(
    "snippet",
    ["import os\nos.path.join('a', 'b')", "from os import path", "environ = {}"],
)
def test_env_detector_ignores(snippet: str) -> None:
    assert not env_reads(snippet)
