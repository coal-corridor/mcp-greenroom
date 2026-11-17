# Deploy

## What is here

- `Dockerfile`: the API in one image. Python 3.12 slim, dependencies from `uv.lock`, runs as an unprivileged user, stores its SQLite file and last-good snapshot in `/data`. Health check on `/livez`.
- `docker-compose.yml`: one service, published on `127.0.0.1:8000` only, with a named volume for `/data`.

Run it:

```sh
docker compose up --build
uv run mcp-greenroom health --api http://127.0.0.1:8000
```

The image copies `evals/recordings`, so it builds once the classifier recordings are committed. It reads no credential: the classifier replays recordings by default.

This is the slice's container, not a production deployment. The stub identities (`dev-dana`, `dev-riley`, `dev-sam`) work only in the dev environment, which is why the port is bound to localhost.

## Production shape, in words

None of this is built in the slice.

- **Identity.** The organisation's single sign-on replaces the stub tokens: the API checks a signed token from the identity provider, and reviewer is a group in that provider. The identity check still compares people, not roles.
- **Store.** A managed relational database replaces SQLite, with its own backups. The audit table stays insert-only, enforced by grants as well as by triggers.
- **Last-good copy.** The snapshot moves from a local file to durable object storage, written on every publish, so a new instance can serve the list while the database is down.
- **Two faces.** The registry list (`GET /v0.1/servers`) is read by every agent platform. It runs as a read-only service that can scale out and sit behind a cache. Submit, review and audit stay on an internal address for developers and reviewers.
- **Edge.** TLS ends at the organisation's load balancer or reverse proxy. Nothing listens in plain HTTP outside the host.
- **Classifier.** The live classifier is an option. If it is turned on, its endpoint goes on an egress allowlist, and its key comes from the secret manager, never from an image or a file.
- **Logs and health.** The JSON log lines go to the central log store. `/livez` and `/readyz` feed the orchestrator's probes, and a degraded list raises an alert.
- **Clients.** Agent platforms point their registry setting at the list endpoint. The `client-check` command shows what that check does, as a simulation.
