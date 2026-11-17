"""The table of sample-data/servers/README.md, on the real recordings in evals/recordings/."""

import pytest
from evals.run_eval import SAMPLES, run_samples

from mcp_greenroom.config import Settings
from mcp_greenroom.vetting.factory import build_pipeline


def test_every_named_sample_lands_where_the_table_says() -> None:
    pipeline = build_pipeline(Settings(_env_file=None))  # type: ignore[call-arg]
    rows, failures = run_samples(pipeline)
    assert failures == []
    assert [row[0] for row in rows] == list(SAMPLES)


@pytest.mark.parametrize("slug", ["payments-readonly"])
def test_the_main_path_decides_well_inside_five_seconds(slug: str) -> None:
    pipeline = build_pipeline(Settings(_env_file=None))  # type: ignore[call-arg]
    rows, _ = run_samples(pipeline)
    elapsed_ms = {row[0]: float(row[4]) for row in rows}
    assert elapsed_ms[slug] < 5000
