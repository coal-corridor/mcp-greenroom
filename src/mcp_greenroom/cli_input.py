"""Reading a submission file for the CLI. Each failure says what failed, what was received
and what to do, never just the exception class."""

import json
from pathlib import Path
from typing import Any


class InputError(Exception):
    def __init__(self, what: str, received: str, next_step: str) -> None:
        super().__init__(what)
        self.what, self.received, self.next_step = what, received, next_step


def read_submission(file: Path) -> Any:
    try:
        return json.loads(file.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise InputError(
            "Submission file not found.", str(file), "Check the path, then run submit again."
        ) from None
    except json.JSONDecodeError as exc:
        raise InputError(
            "Submission file is not valid JSON.",
            f"{file}: {exc.msg} at line {exc.lineno}, column {exc.colno}",
            "Fix the JSON at that line, then run submit again.",
        ) from None
    except UnicodeDecodeError:
        raise InputError(
            "Submission file is not UTF-8 text.", str(file), "Save it as UTF-8 JSON."
        ) from None
    except OSError as exc:
        raise InputError(
            "Could not read the submission file.",
            f"{file}: {exc.strerror or type(exc).__name__}",
            "Check that the path is a readable file, then run submit again.",
        ) from None
