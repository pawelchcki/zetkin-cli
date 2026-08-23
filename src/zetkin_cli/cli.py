"""Typer command-line interface for Zetkin."""

from __future__ import annotations

import json
import sys
from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import typer
from pydantic import BaseModel
from rich.console import Console
from rich.table import Table

from .auth import (
    KeyringTokenStore,
    MemoryTokenStore,
    OAuthConfig,
    OAuthFlow,
    token_debug_summary,
)
from .client import ZetkinClient
from .config import ConfigStore, Profile
from .errors import ZetkinAuthError, ZetkinConfigError, ZetkinError, ZetkinHTTPError
from .models import ApiResult, JsonValue, Page, PersonCreate

app = typer.Typer(
    no_args_is_help=True,
    help="Typed command-line access to the Zetkin API.",
)
profile_app = typer.Typer(no_args_is_help=True, help="Manage non-secret profiles.")
auth_app = typer.Typer(no_args_is_help=True, help="Authenticate with OAuth 2.0.")
org_app = typer.Typer(no_args_is_help=True, help="Organizations.")
people_app = typer.Typer(no_args_is_help=True, help="People.")
tag_app = typer.Typer(no_args_is_help=True, help="Person tags.")
search_app = typer.Typer(no_args_is_help=True, help="Smart searches and matches.")
campaign_app = typer.Typer(no_args_is_help=True, help="Campaigns.")
event_app = typer.Typer(no_args_is_help=True, help="Events/actions.")
survey_app = typer.Typer(no_args_is_help=True, help="Surveys.")
area_app = typer.Typer(no_args_is_help=True, help="API v2 areas.")
canvass_app = typer.Typer(no_args_is_help=True, help="API v2 canvassing.")

for name, subapp in (
    ("profile", profile_app),
    ("auth", auth_app),
    ("org", org_app),
    ("people", people_app),
    ("tag", tag_app),
    ("smart-search", search_app),
    ("campaign", campaign_app),
    ("event", event_app),
    ("survey", survey_app),
    ("area", area_app),
    ("canvass", canvass_app),
):
    app.add_typer(subapp, name=name)

console = Console()
error_console = Console(stderr=True)


@dataclass(slots=True)
class CLIState:
    profile: str | None
    output: str


@app.callback()
def root(
    ctx: typer.Context,
    profile: str | None = typer.Option(
        None, "--profile", "-P", help="Configuration/keyring profile."
    ),
    output: str = typer.Option(
        "auto", "--output", "-o", help="auto, table, json, or jsonl."
    ),
) -> None:
    if output not in {"auto", "table", "json", "jsonl"}:
        raise typer.BadParameter("Output must be auto, table, json, or jsonl")
    ctx.obj = CLIState(profile=profile, output=output)


def _state(ctx: typer.Context) -> CLIState:
    return ctx.ensure_object(CLIState)


def _client(ctx: typer.Context) -> ZetkinClient:
    return ZetkinClient.from_env(profile=_state(ctx).profile)


def _jsonable(value: object) -> object:
    if isinstance(value, ApiResult):
        return {
            "data": _jsonable(value.data),
            "headers": value.headers,
            "meta": value.meta,
            "status_code": value.status_code,
        }
    if isinstance(value, Page):
        return {
            "items": [_jsonable(item) for item in value.items],
            "meta": value.meta,
        }
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, bytes):
        return {"bytes": len(value)}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    return value


def _render(ctx: typer.Context, value: object) -> None:
    output = _state(ctx).output
    if output == "auto":
        output = "table" if sys.stdout.isatty() else "json"
    serial = _jsonable(value)
    if output == "json":
        console.print_json(json.dumps(serial, default=str))
        return
    if output == "jsonl":
        items = serial.get("items", []) if isinstance(serial, dict) else serial
        if not isinstance(items, list):
            items = [items]
        for item in items:
            console.print(json.dumps(item, default=str, separators=(",", ":")))
        return
    rows = serial.get("items", serial) if isinstance(serial, dict) else serial
    if not isinstance(rows, list):
        rows = [rows]
    if not rows:
        console.print("No results")
        return
    mappings = [row for row in rows if isinstance(row, dict)]
    if not mappings:
        for row in rows:
            console.print(str(row))
        return
    preferred = ["id", "title", "name", "first_name", "last_name", "email"]
    all_keys = list(dict.fromkeys(key for row in mappings for key in row))
    keys = [key for key in preferred if key in all_keys]
    keys.extend(key for key in all_keys if key not in keys)
    keys = keys[:8]
    table = Table(*keys)
    for row in mappings:
        table.add_row(*[_cell(row.get(key)) for key in keys])
    console.print(table)


def _cell(value: object) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, default=str, separators=(",", ":"))
    return "" if value is None else str(value)


def _parse_pairs(values: list[str]) -> dict[str, str]:
    output: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise typer.BadParameter(f"Expected KEY=VALUE, got {value!r}")
        key, item = value.split("=", 1)
        output[key] = item
    return output


def _read_json(value: str | None) -> JsonValue:
    if value is None:
        return None
    if value == "@-":
        source = sys.stdin.read()
    elif value.startswith("@"):
        source = Path(value[1:]).read_text()
    else:
        source = value
    try:
        return json.loads(source)
    except json.JSONDecodeError as exc:
        raise typer.BadParameter(f"Invalid JSON: {exc}") from exc


def _object_json(value: str | None) -> dict[str, JsonValue]:
    parsed = _read_json(value)
    if not isinstance(parsed, dict):
        raise typer.BadParameter("This command requires a JSON object")
    return parsed


def _confirm_delete(yes: bool, label: str) -> None:
    if yes:
        return
    if not sys.stdin.isatty() or not typer.confirm(f"Delete {label}?"):
        raise typer.Abort()


@profile_app.command("list")
def profile_list(ctx: typer.Context) -> None:
    store = ConfigStore()
    default = store.default_name()
    _render(
        ctx,
        [{"default": name == default, "name": name} for name in store.names()],
    )


@profile_app.command("show")
def profile_show(ctx: typer.Context, name: str | None = None) -> None:
    profile = ConfigStore().get(name or _state(ctx).profile)
    _render(
        ctx,
        {
            "base_url": profile.base_url,
            "name": profile.name,
            "redirect_uri": profile.redirect_uri,
        },
    )


@profile_app.command("add")
def profile_add(
    name: str,
    base_url: str = typer.Option("https://api.zetk.in", "--base-url"),
    redirect_uri: str | None = typer.Option(None, "--redirect-uri"),
) -> None:
    ConfigStore().add(Profile(name, base_url.rstrip("/"), redirect_uri))
    console.print(f"Saved non-secret profile {name!r}")


@profile_app.command("default")
def profile_default(name: str) -> None:
    ConfigStore().set_default(name)
    console.print(f"Default profile is now {name!r}")


@auth_app.command("login")
def auth_login(
    ctx: typer.Context,
    no_browser: bool = typer.Option(False, "--no-browser"),
    no_store: bool = typer.Option(False, "--no-store"),
    timeout: float = typer.Option(180, "--timeout", min=1),
) -> None:
    profile = ConfigStore().get(_state(ctx).profile)
    oauth = OAuthConfig.from_env(
        base_url=profile.base_url, redirect_uri=profile.redirect_uri
    )
    flow = OAuthFlow(oauth)
    authorization_url, state = flow.create_authorization()
    redirected: str | None = None
    if no_browser:
        console.print("Open this URL in a browser:")
        console.print(authorization_url, soft_wrap=True)
    else:
        redirected = flow.open_and_receive_loopback(authorization_url, timeout=timeout)
    if not redirected:
        redirected = typer.prompt("Paste the final redirected URL")
    assert redirected is not None
    token = flow.exchange_redirect(redirected, expected_state=state)
    store = MemoryTokenStore() if no_store else KeyringTokenStore()
    store.save(profile.name, token)
    console.print(f"Authenticated profile {profile.name!r}")


@auth_app.command("status")
def auth_status(
    ctx: typer.Context, verify: bool = typer.Option(False, "--verify")
) -> None:
    with _client(ctx) as client:
        summary = token_debug_summary(client.token_manager.token)
        if verify and summary["authenticated"]:
            user = client.v1.current_user()
            summary["user"] = user.model_dump(mode="json")
        _render(ctx, summary)


@auth_app.command("logout")
def auth_logout(ctx: typer.Context) -> None:
    profile = ConfigStore().get(_state(ctx).profile)
    KeyringTokenStore().delete(profile.name)
    console.print(f"Removed stored token for profile {profile.name!r}")


@app.command("request")
def raw_request(
    ctx: typer.Context,
    method: str,
    path: str,
    api_version: int = typer.Option(1, "--api-version", min=1, max=2),
    param: list[str] = typer.Option([], "--param", "-q"),
    data: str | None = typer.Option(None, "--data", "-d"),
    header: list[str] = typer.Option([], "--header", "-H"),
    form: list[str] = typer.Option([], "--form"),
    file: list[str] = typer.Option([], "--file", "-F"),
    output_file: Path | None = typer.Option(None, "--output-file"),
) -> None:
    if data is not None and (form or file):
        raise typer.BadParameter("Use either --data or multipart --form/--file")
    with ExitStack() as stack, _client(ctx) as client:
        files: dict[str, Any] = {}
        for field, filename in _parse_pairs(file).items():
            handle = stack.enter_context(Path(filename).open("rb"))
            files[field] = (Path(filename).name, handle)
        result = client.request(
            method,
            path,
            version=api_version,
            params=_parse_pairs(param),
            json=_read_json(data),
            data=_parse_pairs(form) or None,
            files=files or None,
            headers=_parse_pairs(header),
        )
        if isinstance(result.data, bytes):
            if output_file is None:
                raise typer.BadParameter("Binary responses require --output-file")
            output_file.write_bytes(result.data)
            console.print(f"Wrote {len(result.data)} bytes to {output_file}")
        else:
            _render(ctx, result)


@org_app.command("list")
def org_list(ctx: typer.Context) -> None:
    with _client(ctx) as client:
        _render(ctx, client.v1.organizations.list())


@org_app.command("show")
def org_show(ctx: typer.Context, org_id: int) -> None:
    with _client(ctx) as client:
        _render(ctx, client.v1.organizations.get(org_id))


@people_app.command("list")
def people_list(
    ctx: typer.Context,
    org_id: int,
    page: int = typer.Option(0, "--page", min=0),
    per_page: int = typer.Option(50, "--per-page", min=1),
    all_pages: bool = typer.Option(False, "--all"),
) -> None:
    with _client(ctx) as client:
        value: object = (
            list(client.v1.people.iter_all(org_id, per_page=per_page))
            if all_pages
            else client.v1.people.list(org_id, page=page, per_page=per_page)
        )
        _render(ctx, value)


@people_app.command("show")
def people_show(ctx: typer.Context, org_id: int, person_id: int) -> None:
    with _client(ctx) as client:
        _render(ctx, client.v1.people.get(org_id, person_id))


@people_app.command("create")
def people_create(
    ctx: typer.Context,
    org_id: int,
    data: str | None = typer.Option(None, "--data", "-d"),
    first_name: str | None = typer.Option(None, "--first-name"),
    last_name: str | None = typer.Option(None, "--last-name"),
    email: str | None = typer.Option(None, "--email"),
    phone: str | None = typer.Option(None, "--phone"),
) -> None:
    payload = (
        _object_json(data)
        if data
        else PersonCreate(
            first_name=first_name, last_name=last_name, email=email, phone=phone
        )
    )
    with _client(ctx) as client:
        _render(ctx, client.v1.people.create(org_id, payload))


@people_app.command("update")
def people_update(ctx: typer.Context, org_id: int, person_id: int, data: str) -> None:
    with _client(ctx) as client:
        _render(ctx, client.v1.people.update(org_id, person_id, _object_json(data)))


@people_app.command("delete")
def people_delete(
    ctx: typer.Context,
    org_id: int,
    person_id: int,
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    _confirm_delete(yes, f"person {person_id}")
    with _client(ctx) as client:
        client.v1.people.delete(org_id, person_id)


@tag_app.command("list")
def tag_list(ctx: typer.Context, org_id: int) -> None:
    with _client(ctx) as client:
        _render(ctx, client.v1.tags.list(org_id))


@tag_app.command("add")
def tag_add(ctx: typer.Context, org_id: int, person_id: int, tag_id: int) -> None:
    with _client(ctx) as client:
        client.v1.tags.add_to_person(org_id, person_id, tag_id)


@tag_app.command("remove")
def tag_remove(ctx: typer.Context, org_id: int, person_id: int, tag_id: int) -> None:
    with _client(ctx) as client:
        client.v1.tags.remove_from_person(org_id, person_id, tag_id)


@search_app.command("list")
def search_list(ctx: typer.Context, org_id: int) -> None:
    with _client(ctx) as client:
        _render(ctx, client.v1.smart_searches.list(org_id))


@search_app.command("matches")
def search_matches(ctx: typer.Context, org_id: int, query_id: int) -> None:
    with _client(ctx) as client:
        _render(ctx, client.v1.smart_searches.matches(org_id, query_id))


@search_app.command("run")
def search_run(ctx: typer.Context, org_id: int, data_type: str, query: str) -> None:
    with _client(ctx) as client:
        _render(ctx, client.v1.smart_searches.search(org_id, data_type, query))


def _register_v1_collection_commands(subapp: typer.Typer, service_name: str) -> None:
    @subapp.command("list")
    def list_items(ctx: typer.Context, org_id: int) -> None:
        with _client(ctx) as client:
            service = getattr(client.v1, service_name)
            _render(ctx, service.list(org_id))

    @subapp.command("show")
    def show_item(ctx: typer.Context, org_id: int, item_id: int) -> None:
        with _client(ctx) as client:
            service = getattr(client.v1, service_name)
            _render(ctx, service.get(org_id, item_id))

    @subapp.command("create")
    def create_item(ctx: typer.Context, org_id: int, data: str) -> None:
        with _client(ctx) as client:
            service = getattr(client.v1, service_name)
            _render(ctx, service.create(org_id, _object_json(data)))

    @subapp.command("update")
    def update_item(ctx: typer.Context, org_id: int, item_id: int, data: str) -> None:
        with _client(ctx) as client:
            service = getattr(client.v1, service_name)
            _render(ctx, service.update(org_id, item_id, _object_json(data)))

    @subapp.command("delete")
    def delete_item(
        ctx: typer.Context,
        org_id: int,
        item_id: int,
        yes: bool = typer.Option(False, "--yes", "-y"),
    ) -> None:
        _confirm_delete(yes, f"{service_name} item {item_id}")
        with _client(ctx) as client:
            service = getattr(client.v1, service_name)
            service.delete(org_id, item_id)


for target_app, target_service in (
    (campaign_app, "campaigns"),
    (event_app, "events"),
    (survey_app, "surveys"),
):
    _register_v1_collection_commands(target_app, target_service)


@area_app.command("list")
def area_list(ctx: typer.Context, org_id: int) -> None:
    with _client(ctx) as client:
        _render(ctx, client.v2.areas.list(org_id))


@area_app.command("create")
def area_create(ctx: typer.Context, org_id: int, data: str) -> None:
    with _client(ctx) as client:
        _render(ctx, client.v2.areas.create(org_id, _object_json(data)))


@area_app.command("update")
def area_update(ctx: typer.Context, org_id: int, area_id: int, data: str) -> None:
    with _client(ctx) as client:
        _render(ctx, client.v2.areas.update(org_id, area_id, _object_json(data)))


@area_app.command("delete")
def area_delete(
    ctx: typer.Context,
    org_id: int,
    area_id: int,
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    _confirm_delete(yes, f"area {area_id}")
    with _client(ctx) as client:
        client.v2.areas.delete(org_id, area_id)


@canvass_app.command("assignments")
def canvass_assignments(ctx: typer.Context, org_id: int) -> None:
    with _client(ctx) as client:
        _render(ctx, client.v2.area_assignments.list(org_id))


@canvass_app.command("locations")
def canvass_locations(ctx: typer.Context, org_id: int) -> None:
    with _client(ctx) as client:
        _render(ctx, client.v2.locations.list(org_id))


@canvass_app.command("households")
def canvass_households(ctx: typer.Context, org_id: int, location_id: int) -> None:
    with _client(ctx) as client:
        _render(ctx, client.v2.locations.households(org_id, location_id))


def main() -> None:
    try:
        app()
    except ZetkinHTTPError as exc:
        error_console.print(str(exc))
        raise typer.Exit(4) from None
    except (ZetkinAuthError, ZetkinConfigError) as exc:
        error_console.print(str(exc))
        raise typer.Exit(3) from None
    except ZetkinError as exc:
        error_console.print(str(exc))
        raise typer.Exit(5) from None
    except (OSError, ValueError) as exc:
        error_console.print(str(exc))
        raise typer.Exit(2) from None


if __name__ == "__main__":
    main()
