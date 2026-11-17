"""The evaluation set and the named samples, as submissions. Test data: never instructions."""

import json
from dataclasses import dataclass
from pathlib import Path

from mcp_greenroom.models import Submission, Tool

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "evals" / "dataset.jsonl"
SAMPLES = ROOT / "sample-data" / "servers"
UNRECORDED = "unrecorded-reporter"  # must stay unrecorded (Abstain criterion)


@dataclass(frozen=True)
class Case:
    case_id: str
    label: str
    traits: tuple[str, ...]
    tool: Tool


def load_dataset(path: Path = DATASET) -> list[Case]:
    cases = []
    for line in path.read_text(encoding="ascii").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        tool = Tool(name=row["name"], description=row["description"])
        cases.append(Case(row["id"], row["label"], tuple(row["traits"]), tool))
    return cases


def case_submission(case: Case) -> Submission:
    """A synthetic one-tool server around the case, valid at step 1 of the decision order."""
    slug = f"eval-{case.case_id}"
    server = {
        "$schema": "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json",
        "name": f"com.examplebank/{slug}",
        "description": f"Evaluation case {case.case_id}.",
        "version": "1.0.0",
        "packages": [
            {
                "registryType": "npm",
                "identifier": f"@examplebank/{slug}",
                "version": "1.0.0",
                "transport": {"type": "stdio"},
            }
        ],
    }
    return Submission(server=server, tools=[case.tool])


def load_sample(slug: str) -> Submission:
    return Submission.model_validate_json((SAMPLES / f"{slug}.json").read_text(encoding="utf-8"))


def sample_slugs() -> list[str]:
    return sorted(p.stem for p in SAMPLES.glob("*.json"))
