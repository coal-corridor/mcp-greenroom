"""The evaluation set is the one the spec describes, and every case reaches the classifier."""

from collections import Counter

from evals.cases import UNRECORDED, case_submission, load_dataset, sample_slugs
from evals.gate import LABELS

from mcp_greenroom.vetting.rules import hidden_characters
from mcp_greenroom.vetting.validation import validate

CASES = load_dataset()


def test_about_forty_labelled_cases_with_unique_ids_and_names() -> None:
    assert 36 <= len(CASES) <= 44
    assert len({c.case_id for c in CASES}) == len(CASES)
    assert len({c.tool.name for c in CASES}) == len(CASES)
    assert set(Counter(c.label for c in CASES)) == set(LABELS)


def test_the_set_holds_what_the_spec_lists() -> None:
    traits = Counter(t for c in CASES for t in c.traits)
    assert traits["addressed_to_classifier"] >= 3
    assert traits["hidden_characters"] >= 3


def test_the_hidden_character_trait_matches_the_rule() -> None:
    for case in CASES:
        flagged = bool(hidden_characters([case.tool]))
        assert flagged == ("hidden_characters" in case.traits), case.case_id


def test_every_case_passes_step_one() -> None:
    for case in CASES:
        validate(case_submission(case))


def test_the_five_named_samples_are_there_and_one_stays_unrecorded() -> None:
    assert set(sample_slugs()) == {
        "payments-readonly",
        "invalid-unpinned",
        "poisoned-notes",
        UNRECORDED,
        "ambiguous-exporter",
    }


def test_every_case_and_sample_tool_has_a_recording_except_unrecorded_reporter() -> None:
    from pathlib import Path

    from evals.cases import load_sample
    from evals.record import targets

    from mcp_greenroom.risk.replay import ReplayProvider

    replay = ReplayProvider(Path("evals/recordings"))
    missing = []
    for tool in targets():
        try:
            replay.classify(tool)
        except Exception as exc:  # NoRecording or ClassifierUnavailable
            missing.append(f"{tool.name}: {type(exc).__name__}")
    assert missing == []
    assert {c.tool.name for c in CASES} <= {t.name for t in targets()}
    assert not {t.name for t in load_sample(UNRECORDED).tools} & {t.name for t in targets()}
