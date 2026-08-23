# zetkin-cli

Private, typed Python access to the Zetkin Platform API. The project contains:

- synchronous and asynchronous Python clients;
- complete generated coverage of the public v1 endpoint catalog;
- typed v2 services derived from the current Zetkin web application;
- OAuth 2.0 login with OS-keyring token storage;
- organizer-friendly commands plus a raw API request command.

## Install

The repository uses [uv](https://docs.astral.sh/uv/):

```console
uv sync --all-groups
uv run zetkin --help
```

After the private repository has been cloned elsewhere, the CLI can also be installed
as a tool:

```console
uv tool install git+https://github.com/pawelchcki/zetkin-cli.git
```

## Authenticate

Obtain an OAuth client pair from Zetkin and export it locally. Never commit these
values:

```console
export ZETKIN_CLIENT_ID=...
export ZETKIN_CLIENT_SECRET=...
export ZETKIN_REDIRECT_URI=http://127.0.0.1:8765/callback
zetkin profile add production --redirect-uri "$ZETKIN_REDIRECT_URI"
zetkin profile default production
zetkin auth login
zetkin auth status --verify
```

If the registered redirect URI is local, `auth login` listens for one callback. For
other redirect URIs, or if the listener cannot bind, paste the final redirected URL.
OAuth state is always checked. Tokens are stored in the operating-system keyring;
there is no plaintext fallback. Use `--no-store` for a one-off login, or set
`ZETKIN_ACCESS_TOKEN` for non-interactive use.

Profiles contain only a base URL and redirect URI. The default base URL is
`https://api.zetk.in`; use a separate profile for development instances.

## CLI examples

```console
# Friendly commands
zetkin org list
zetkin people list 1 --all --output jsonl
zetkin people show 1 123
zetkin tag add 1 123 9
zetkin smart-search matches 1 42
zetkin campaign list 1
zetkin area list 1
zetkin canvass assignments 1

# Safe mutations; JSON may be inline, @file, or @-
zetkin people create 1 --first-name Clara --last-name Zetkin
zetkin people update 1 123 --data @person-patch.json
zetkin people delete 1 123 --yes

# Any API resource, including endpoints not modeled yet
zetkin request GET /orgs/1/people --api-version 1 --param pp=20
zetkin request POST /orgs/1/search/person --data '{"q":"Clara"}'
zetkin request GET /orgs/1/areas --api-version 2

# Binary responses require an explicit destination
zetkin request GET /orgs/1/avatar --output-file avatar.png
```

Output defaults to a table on a terminal and JSON when piped. Override with global
`--output table|json|jsonl`. The request command rejects absolute URLs and prevents
overrides of authentication, host, and content-length headers.

## Python SDK

```python
from zetkin_cli import ZetkinClient

with ZetkinClient.from_env() as client:
    current_user = client.v1.current_user()
    people = client.v1.people.list(org_id=1, per_page=100)
    areas = client.v2.areas.list(org_id=1)

    org = client.for_org(1)
    person = org.people.get(123)

    # Every documented v1 method/path is also statically present under ops.
    raw = client.v1.ops.get_orgs_by_org_id_people_by_person_id(org_id=1, person_id=123)
```

Async callers use `AsyncZetkinClient` and `async with`. Known response fields are
validated with Pydantic while additive server fields are retained. Where Zetkin does
not publish a schema, operation methods deliberately return `JsonValue` rather than
guessing a structure.

## Development

```console
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest
uv run python scripts/generate_v1.py --check
uv build
```

To refresh the v1 catalog from its pinned upstream source, update the source commit in
`scripts/generate_v1.py`, then run `uv run python scripts/generate_v1.py --refresh`.
Review the catalog and generated diff together.

See [docs/api-sources.md](docs/api-sources.md) for the exact coverage boundary.

