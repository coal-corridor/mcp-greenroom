# Brief 10: contracts

Session: lead. Budget: minutes 10 to 20. Lands in the setup pull request. Parallel work starts only after the user says "contracts frozen".

## Goal

Three sessions can build in parallel without talking to each other, because the shared shapes and the seams between areas are written down, tested and frozen.

## Read first

`docs/specs/mcp-greenroom.md` in full, then the three area children, because the contracts serve all three: `docs/specs/vetting.md`, `docs/specs/registry.md`, `docs/specs/edge.md`. Not `delivery.md` or `stretch.md`. Then `docs/structure.md`.

## Deliver, one commit each

1. `contracts/`: the MCP registry OpenAPI document and the `server.json` schema, fetched now and pinned, with a `contracts/README.md` giving URL, date and licence for each. If either differs from what the spec assumes, say so before going on.
2. Shared modules in `src/mcp_greenroom/`: the data models (submission, tool, finding, risk result, decision, audit event), the config module with validation that stops startup on a bad value, and the logger that writes one structured line and never raw untrusted text.
3. The seams, as typed signatures with docstrings and no body:
   - the vetting entry point that the API calls;
   - the classifier provider interface, with its two failure signals (unavailable, no recording);
   - the scanner interface;
   - the fingerprint function;
   - the injection point for the pipeline, the provider and the store, so tests can swap in fakes. FastAPI's documented way is dependencies replaced through `app.dependency_overrides`. An app factory that takes them is the alternative. Propose one.
4. `sample-data/servers/`: the five synthetic samples named in the spec, plus a table of the outcome each must reach.
5. A fake pipeline and a fake provider under `tests/`, so the registry and edge areas can work before vetting is merged.
6. One test per shared module that proves the shape: config rejects a bad value, the logger never emits a description, the fingerprint is stable under key order and tool order.
7. `CLAUDE.md`: replace "One module reads environment variables. One logger." with the two real paths, in the form "Read environment variables only in `<path>`". Leave the sentence on the outbound wrapper until that module exists.

Propose the names and fields. The user decides. Keep each seam as small as it can be: nothing from the store appears in vetting, and the CLI talks to the API over HTTP only.

## Done when

- `./scripts/verify.sh quick` passes and the new tests pass.
- You have listed every seam in ten lines or fewer, and the user has answered "contracts frozen".
- The setup pull request is open, its required checks are green, and the user has merged it.

## After the merge, the user runs

```bash
git switch main && git pull
git worktree add ../mcp-greenroom-vetting -b area/vetting
git worktree add ../mcp-greenroom-registry -b area/registry
```

The edge worktree is added once the API shape has held for a while.

## Stop and ask

A criterion cannot be met without a seam the spec does not imply. An upstream document disagrees with the spec. A sample cannot be written without real data.
