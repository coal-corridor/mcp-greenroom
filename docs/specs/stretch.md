# Spec, child: stretch

Read the parent first: `docs/specs/mcp-greenroom.md`. Nothing in this file is
part of the committed slice. An item is built only when its own opening line
allows it, one at a time, and the user picks which. The cut order is in the
parent, section Cut order. The per-version lookup endpoints and the shadowing
rule are stretch items too: the parent names them and they have no section here.

### Stretch: tracing

Cut first. Build only when everything else is green.

- One trace per submission, with a span per stage: validate, rules, scanner,
classify (one span per tool), decide. The classify span carries the provider,
the model id, the prompt hash and the token counts. In replay these come from
the recording, so a recording stores the token counts too.
- Spans carry ids, hashes, rule ids and outcomes. Never a tool description or
any other untrusted text.
- The exporter is off by default, so the default run and the tests make no
network call. A Compose profile adds one Jaeger container and switches it on.
- One test asserts the span names of a submission, with an in-memory exporter.
- Allowed for this item only: the OpenTelemetry SDK and its OTLP exporter.

### Stretch: interactive menu

Build this only when the main path, the five safe failures and the CLI commands
are green.

Bare `mcp-greenroom` in a terminal opens a menu, moved with the arrow keys:
review queue, submit a server, submissions, approved servers, check a client
config, health, quit. When the output is not a terminal, bare `mcp-greenroom`
still prints the command list.

- The menu adds no capability. Each item calls the same function as a plain
command and prints the same view, then returns to the menu.
- It needs one new endpoint, `GET /submissions`, with a filter on status. The
caller must be authenticated. A plain `mcp-greenroom queue` command uses it too.
- The review queue lists the cases in human review. Opening one shows the same
view as `status`, offers approve, decline and back, and asks for the note. The
server still enforces separation of duties.
- Selection uses the questionary library, the one extra dependency of this
item. No key handling is written by hand.
- The menu loop takes its chooser as a parameter, so tests script the choices
with no terminal. One test walks review queue, open, approve.
- Untrusted text is printed inert here too, including in the choice labels.

### Stretch: submission by upstream reference

Build this only when the main path and the five safe failures are green.

A submission may point at a server version in another registry instead of
carrying the manifest: the official MCP registry or another subregistry, since
both speak the same API. MCP Greenroom copies the record at submission. It does
not link to it.

- The submission carries an origin (registry base URL, server name, version)
and the tool list. The upstream `server.json` has no tool definitions, so the
submitter still declares them.
- MCP Greenroom resolves the manifest from the origin and stores that copy. In
the slice it resolves from a recorded upstream response in `sample-data/`, so
the default run still makes no network call. A live fetch is an option behind
configuration.
- The origin must be on a configured list of trusted registries. An origin that
is not trusted, a version that is not found there, or a record that fails the
schema is refused with 422 and a stable rule id. With a live fetch, an
unreachable origin is refused with 503. Nothing is listed in either case.
- The decision order applies unchanged. A listing upstream is not evidence: it
skips no rule and earns no lower tier.
- The fingerprint covers the copied manifest and the tools. If upstream changes
the record under the same version, a resubmission is refused with 409.
- The published record keeps the upstream name and version. The audit record
holds the origin and the time of the copy.

### Open questions

- Do the per-version endpoints fit the timebox? First move: test a URL-encoded
name containing a slash against the framework before committing to them.
- Which sample backs the upstream reference stretch: a synthetic record under a
second fictional organisation, or a real public record captured from the
official registry with URL and date? First move: synthetic, to keep one data
rule.
