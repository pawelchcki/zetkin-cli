"""Shared API envelopes and evidence-backed Zetkin resource models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

type JsonPrimitive = str | int | float | bool | None
type JsonValue = JsonPrimitive | list[JsonValue] | dict[str, JsonValue]
T = TypeVar("T")


class ZetkinModel(BaseModel):
    """Base model that remains compatible with additive API changes."""

    model_config = ConfigDict(extra="allow")


@dataclass(slots=True)
class ApiResult[T]:
    """Unmodified response information returned by low-level requests."""

    data: T
    status_code: int
    headers: dict[str, str]
    meta: dict[str, JsonValue] | None = None

    def parse(self, target: type[T]) -> T:
        return TypeAdapter(target).validate_python(self.data)


class Page[T](ZetkinModel):
    items: list[T]
    meta: dict[str, JsonValue] = Field(default_factory=dict)


class Organization(ZetkinModel):
    id: int
    title: str
    country: str | None = None
    slug: str | None = None
    is_open: bool | None = None
    is_active: bool | None = None
    is_public: bool | None = None
    email: str | None = None
    phone: str | None = None
    lang: str | None = None
    parent: dict[str, JsonValue] | None = None


class OrganizationCreate(ZetkinModel):
    title: str
    country: str | None = None
    parent_id: int | None = None


class Person(ZetkinModel):
    id: int
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    alt_phone: str | None = None
    street_address: str | None = None
    co_address: str | None = None
    city: str | None = None
    zip_code: str | None = None
    country: str | None = None
    gender: str | None = None
    ext_id: str | None = None
    is_user: bool | None = None


class PersonCreate(ZetkinModel):
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None


class Tag(ZetkinModel):
    id: int
    title: str
    description: str | None = None
    color: str | None = None


class Campaign(ZetkinModel):
    id: int
    title: str
    info_text: str | None = None
    archived: bool | None = None
    color: str | None = None


class Event(ZetkinModel):
    id: int
    start_time: str
    end_time: str
    title: str | None = None
    info_text: str | None = None
    published: str | None = None
    cancelled: str | None = None
    organization: dict[str, JsonValue] | None = None
    campaign: dict[str, JsonValue] | None = None
    activity: dict[str, JsonValue] | None = None
    location: dict[str, JsonValue] | None = None


class Survey(ZetkinModel):
    id: int
    title: str
    info_text: str | None = None
    access: str | None = None
    published: str | None = None
    expires: str | None = None


class SmartSearch(ZetkinModel):
    id: int | str
    title: str
    type: str = "standalone"
    info_text: str | None = None
    filter_spec: list[dict[str, JsonValue]] = Field(default_factory=list)


class User(ZetkinModel):
    id: int
    username: str | None = None
    first_name: str
    last_name: str
    email: str | None = None
    phone: str | None = None
    lang: str | None = None
    is_verified: bool | None = None
    email_is_verified: bool | None = None
    phone_is_verified: bool | None = None
    is_superuser: bool | None = None


class AreaBoundary(ZetkinModel):
    type: str = "Polygon"
    coordinates: list[list[tuple[float, float]]]


class Area(ZetkinModel):
    id: int
    organization_id: int
    title: str
    description: str = ""
    boundary: AreaBoundary


class AreaStats(ZetkinModel):
    id: int
    area_id: int
    count_households: int
    count_locations: int
    count_unique_households_visited: int
    count_unique_locations_visited: int
    sum_successful_visits: int
    sum_visits: int


class AreaAssignment(ZetkinModel):
    id: int
    organization_id: int
    project_id: int
    title: str
    instructions: str = ""
    reporting_level: str
    start_date: str | None = None
    end_date: str | None = None


class AreaAssignee(ZetkinModel):
    area_id: int
    assignment_id: int
    user_id: int


class Metric(ZetkinModel):
    id: int
    area_assignment_id: int
    created: str
    defines_success: bool
    question: str
    type: str
    description: str | None = None


class MetricBulkResponse(ZetkinModel):
    metric_id: int
    num_no: int | None = None
    num_yes: int | None = None
    num_values: tuple[int, int, int, int, int] | None = None


class AreaAssignmentStats(ZetkinModel):
    metrics: list[MetricBulkResponse]
    num_households: int
    num_households_successfully_visited: int | None = None
    num_households_visited: int | None = None
    num_locations: int
    num_locations_visited: int
    num_successful_visits: int
    num_visits: int


class Location(ZetkinModel):
    id: int
    organization_id: int
    title: str
    description: str = ""
    latitude: float
    longitude: float
    type: str
    created: str | None = None
    created_by_user_id: int | None = None
    num_estimated_households: int = 0
    num_known_households: int = 0


class Household(ZetkinModel):
    id: int
    location_id: int
    title: str
    level: int
    color: str | None = None


class MetricResponse(ZetkinModel):
    metric_id: int
    response: str | int


class LocationVisit(ZetkinModel):
    id: int
    assignment_id: int
    location_id: int
    created: str
    created_by_user_id: int
    metrics: list[MetricResponse] = Field(default_factory=list)
    num_households_visited: int = 0


class HouseholdVisit(ZetkinModel):
    id: int
    assignment_id: int
    household_id: int
    created: str
    created_by_user_id: int
    metrics: list[MetricResponse] = Field(default_factory=list)
