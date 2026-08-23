from __future__ import annotations

import json
from pathlib import Path

import pytest
import respx
from httpx import Response
from typer.testing import CliRunner

from zetkin_cli.cli import app

runner = CliRunner()


@respx.mock
def test_org_list_outputs_json_when_requested(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ZETKIN_ACCESS_TOKEN", "token")
    respx.get("https://api.zetk.in/v1/orgs").mock(
        return_value=Response(200, json={"data": [{"id": 1, "title": "Org"}]})
    )

    result = runner.invoke(app, ["--output", "json", "org", "list"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["items"][0]["title"] == "Org"


@respx.mock
def test_raw_request_sends_json_and_query(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ZETKIN_ACCESS_TOKEN", "token")
    route = respx.post("https://api.zetk.in/v1/orgs/1/search/person?q=x").mock(
        return_value=Response(200, json={"data": [{"id": 2}]})
    )

    result = runner.invoke(
        app,
        [
            "--output",
            "json",
            "request",
            "POST",
            "/orgs/1/search/person",
            "--param",
            "q=x",
            "--data",
            '{"q":"Clara"}',
        ],
    )

    assert result.exit_code == 0, result.output
    assert route.called
    assert route.calls.last.request.headers["Authorization"] == "Bearer token"
    assert json.loads(route.calls.last.request.content) == {"q": "Clara"}


def test_delete_requires_confirmation_in_noninteractive_runner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ZETKIN_ACCESS_TOKEN", "token")
    result = runner.invoke(app, ["people", "delete", "1", "2"])
    assert result.exit_code != 0


def test_profile_show_contains_no_secret(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("ZETKIN_CLIENT_SECRET", "never-print")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    result = runner.invoke(app, ["--output", "json", "profile", "show"])
    assert result.exit_code == 0
    assert "never-print" not in result.output
