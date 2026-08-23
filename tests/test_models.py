from __future__ import annotations

from zetkin_cli.models import Area, Page, Person


def test_models_preserve_additive_server_fields() -> None:
    person = Person.model_validate(
        {"id": 1, "first_name": "Clara", "future_api_field": {"value": 42}}
    )

    assert person.first_name == "Clara"
    assert person.model_dump()["future_api_field"] == {"value": 42}


def test_v2_area_model_validates_polygon() -> None:
    area = Area.model_validate(
        {
            "id": 7,
            "organization_id": 1,
            "title": "North",
            "boundary": {
                "type": "Polygon",
                "coordinates": [[[18.0, 59.0], [18.1, 59.1], [18.0, 59.0]]],
            },
        }
    )

    assert area.boundary.coordinates[0][0] == (18.0, 59.0)


def test_page_is_generic_and_keeps_metadata() -> None:
    page = Page[Person](items=[Person(id=1, first_name="Clara")], meta={"next": 2})
    assert page.items[0].id == 1
    assert page.meta == {"next": 2}
