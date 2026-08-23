from __future__ import annotations

import inspect
import json
from pathlib import Path

from zetkin_cli.generated import AsyncV1Operations, V1Operations


def test_catalog_has_all_distinct_documented_operations() -> None:
    payload = json.loads(Path("specs/v1_endpoints.json").read_text())
    operations = payload["operations"]
    pairs = {(item["method"], item["path"]) for item in operations}
    operation_ids = {item["operation_id"] for item in operations}

    assert len(operations) == 256
    assert len(pairs) == 256
    assert len(operation_ids) == 256
    assert payload["source_commit"] == "d013cb993187fb4e5a116b3275053602fd01ae9f"


def test_every_catalog_operation_exists_in_sync_and_async_clients() -> None:
    operations = json.loads(Path("specs/v1_endpoints.json").read_text())["operations"]

    for operation in operations:
        sync_method = getattr(V1Operations, operation["operation_id"])
        async_method = getattr(AsyncV1Operations, operation["operation_id"])
        assert callable(sync_method)
        assert inspect.iscoroutinefunction(async_method)
        for path_parameter in _path_parameters(operation["path"]):
            assert path_parameter in inspect.signature(sync_method).parameters


def test_v2_inventory_is_unique_and_pinned_to_current_app() -> None:
    payload = json.loads(Path("specs/v2_endpoints.json").read_text())
    operations = [tuple(item) for item in payload["operations"]]

    assert payload["source_commit"] == "0aef1bed2280fce70b7928fe1b87e3780e1eb453"
    assert len(operations) == 37
    assert len(set(operations)) == 37


def _path_parameters(path: str) -> list[str]:
    return [
        segment[1:-1]
        for segment in path.split("/")
        if segment.startswith("{") and segment.endswith("}")
    ]
