"""The real API with the contracts FakePipeline, for the demo and e2e test until vetting merges.

Run: uv run python -m tests.e2e.fake_service --port 8000 --data-dir DIR
The store and the last-good snapshot live in DIR, so a run never touches the default database.
"""

import argparse
from pathlib import Path

import uvicorn
from fastapi import FastAPI

from mcp_greenroom.api import main as api_main
from mcp_greenroom.api.dependencies import get_pipeline
from mcp_greenroom.config import Settings
from tests.fakes import FakePipeline


def build_app(data_dir: Path) -> FastAPI:
    settings = Settings(
        database_url=f"sqlite:///{data_dir / 'greenroom.db'}",
        snapshot_path=data_dir / "last-good.json",
    )
    app = api_main.create_app(settings)
    pipeline = FakePipeline()
    app.dependency_overrides[get_pipeline] = lambda: pipeline
    return app


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--data-dir", type=Path, required=True)
    args = parser.parse_args()
    args.data_dir.mkdir(parents=True, exist_ok=True)
    uvicorn.run(build_app(args.data_dir), host="127.0.0.1", port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
