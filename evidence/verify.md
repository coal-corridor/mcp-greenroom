# Verification: MCP Greenroom

Status: headings only, prepared before the timed build. Every table and block below is pasted from a command run during the build. One page.

## Check script

`TODO(build)`: the summary table of `./scripts/verify.sh` from a fresh clone, with the date and the commit.

## Tests

`TODO(build)`: counts per folder. List structural checks separately from behaviour tests. Name the test behind each acceptance criterion of the spec.

## Classifier evaluation

`TODO(build)`: the evaluation report, with the model id, the prompt version, the thresholds in force, and the scanner column per label.

## Demo

`TODO(build)`: the real output of `./scripts/demo.sh`: the main path and the five safe failures.

## Hands-on and break tests

`TODO(build)`: commands and output from the hands-on test and from the break test on a fresh clone. What was fixed, what was left.

## Pull request checks

`TODO(build)`: link to the run on the last commit of `main`. The dependency audit result, and what was done about each finding.

## Independent review

`TODO(build)`: the reviewer's criteria, its findings, and the decision on each. Where it was wrong.

## Local, pull request, pipeline

`TODO(build)`: confirm against what was built.

| Check | Local | Pull request | Later pipeline |
| --- | --- | --- | --- |
| Lint and types | | | |
| Tests, including structure and no-network guard | | | |
| Classifier evaluation gate | | | |
| Secret scan | | | |
| Dependency audit | | | |
| Image scan, second reviewer, promotion gates | | | |

## Known gaps

`TODO(build)`: what is not verified, including the limits of agent review and of an evaluation that replays recordings.
