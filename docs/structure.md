# Target structure

A starting proposal, so that three sessions do not collide. The lead session may adjust it in the contracts step, with the user's agreement. After "contracts frozen" the ownership column is binding.

```text
AGENTS.md  CLAUDE.md  README.md  ROADMAP.md
pyproject.toml  uv.lock  Makefile  .env.example
.claude/                 settings, hooks, skills, reviewer agent
.github/workflows/ci.yml pull request checks
briefs/                  one brief per phase and per area
docs/                    spec notes, references, prompts, this file
docs/specs/              mcp-greenroom.md (the parent) and five child specs
contracts/               pinned upstream documents, with sources      lead, frozen
src/mcp_greenroom/
  models.py config.py logging.py     shared                           lead, frozen
  api/                 main.py, dependencies.py, routers/              registry
  store/                                                               registry
  vetting/  risk/  scanner/                                            vetting
  cli.py  client_sim.py                                                edge
tests/
  conftest.py  structure/                                              lead
  unit/                                                                vetting
  api/  contract/  failure/                                            registry
  e2e/                                                                 edge
evals/                   dataset, recordings, thresholds, runner       vetting
sample-data/
  servers/                                                             lead
  client-configs/                                                      edge
scripts/
  verify.sh                                                            lead
  demo.sh                                                              edge
deploy/README.md         production shape, in words                    edge
evidence/                the six evidence files and the session log   lead
handoff/                 one note per session, one review report per area   each session its own
```

Rules that follow from it:

- A session edits only what its column says. Anything else is a question to the user.
- A session reads `docs/specs/mcp-greenroom.md` and one child spec: `vetting.md`, `registry.md` or `edge.md` for the area of that name, `delivery.md` and `stretch.md` for the lead.
- The registry and edge areas work against the fake pipeline in `tests/` until vetting is merged.
- The CLI reaches the service over HTTP only. Nothing under `store/` is imported by `vetting/`, `risk/` or `scanner/`.
