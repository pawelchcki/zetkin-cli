"""Typed services inferred from v2 calls in the official Zetkin application."""

from __future__ import annotations

from zetkin_cli.models import (
    Area,
    AreaAssignee,
    AreaAssignment,
    AreaAssignmentStats,
    AreaStats,
    Household,
    HouseholdVisit,
    JsonValue,
    Location,
    LocationVisit,
    Metric,
    Page,
    User,
)
from zetkin_cli.transport import Params

from .base import AsyncRequester, SyncRequester, model_data, page_data


class AreasService:
    def __init__(self, client: SyncRequester) -> None:
        self._client = client

    def list(self, org_id: int, *, page: int = 0, size: int = 100) -> Page[Area]:
        return page_data(
            self._client.request(
                "GET",
                f"/orgs/{org_id}/areas",
                version=2,
                params={"page": page, "size": size},
            ),
            Area,
        )

    def create(self, org_id: int, data: dict[str, JsonValue]) -> Area:
        return model_data(
            self._client.request("POST", f"/orgs/{org_id}/areas", version=2, json=data),
            Area,
        )

    def update(self, org_id: int, area_id: int, data: dict[str, JsonValue]) -> Area:
        return model_data(
            self._client.request(
                "PATCH",
                f"/orgs/{org_id}/areas/{area_id}",
                version=2,
                json=data,
            ),
            Area,
        )

    def delete(self, org_id: int, area_id: int) -> None:
        self._client.request("DELETE", f"/orgs/{org_id}/areas/{area_id}", version=2)

    def stats(self, org_id: int, area_id: int) -> AreaStats:
        return model_data(
            self._client.request(
                "GET", f"/orgs/{org_id}/areas/{area_id}/stats", version=2
            ),
            AreaStats,
        )


class AreaAssignmentsService:
    def __init__(self, client: SyncRequester) -> None:
        self._client = client

    def list(
        self, org_id: int, *, page: int = 0, size: int = 100
    ) -> Page[AreaAssignment]:
        return page_data(
            self._client.request(
                "GET",
                f"/orgs/{org_id}/area_assignments",
                version=2,
                params={"page": page, "size": size},
            ),
            AreaAssignment,
        )

    def get(self, org_id: int, assignment_id: int) -> AreaAssignment:
        return model_data(
            self._client.request(
                "GET", f"/orgs/{org_id}/area_assignments/{assignment_id}", version=2
            ),
            AreaAssignment,
        )

    def create(
        self, org_id: int, project_id: int, data: dict[str, JsonValue]
    ) -> AreaAssignment:
        return model_data(
            self._client.request(
                "POST",
                f"/orgs/{org_id}/projects/{project_id}/area_assignments",
                version=2,
                json=data,
            ),
            AreaAssignment,
        )

    def update(
        self, org_id: int, assignment_id: int, data: dict[str, JsonValue]
    ) -> AreaAssignment:
        return model_data(
            self._client.request(
                "PATCH",
                f"/orgs/{org_id}/area_assignments/{assignment_id}",
                version=2,
                json=data,
            ),
            AreaAssignment,
        )

    def delete(self, org_id: int, assignment_id: int) -> None:
        self._client.request(
            "DELETE", f"/orgs/{org_id}/area_assignments/{assignment_id}", version=2
        )

    def assignees(self, org_id: int, assignment_id: int) -> Page[AreaAssignee]:
        return page_data(
            self._client.request(
                "GET",
                f"/orgs/{org_id}/area_assignments/{assignment_id}/assignees",
                version=2,
                params={"page": 0, "size": 100},
            ),
            AreaAssignee,
        )

    def areas(self, org_id: int, assignment_id: int) -> Page[Area]:
        return page_data(
            self._client.request(
                "GET",
                f"/orgs/{org_id}/area_assignments/{assignment_id}/areas",
                version=2,
                params={"page": 0, "size": 100},
            ),
            Area,
        )

    def locations(
        self, org_id: int, assignment_id: int, *, params: Params | None = None
    ) -> Page[Location]:
        return page_data(
            self._client.request(
                "GET",
                f"/orgs/{org_id}/area_assignments/{assignment_id}/locations",
                version=2,
                params=params,
            ),
            Location,
        )

    def location(self, org_id: int, assignment_id: int, location_id: int) -> Location:
        return model_data(
            self._client.request(
                "GET",
                f"/orgs/{org_id}/area_assignments/{assignment_id}/locations/{location_id}",
                version=2,
            ),
            Location,
        )

    def metrics(self, org_id: int, assignment_id: int) -> Page[Metric]:
        return page_data(
            self._client.request(
                "GET",
                f"/orgs/{org_id}/area_assignments/{assignment_id}/metrics",
                version=2,
            ),
            Metric,
        )

    def create_metric(
        self, org_id: int, assignment_id: int, data: dict[str, JsonValue]
    ) -> Metric:
        return model_data(
            self._client.request(
                "POST",
                f"/orgs/{org_id}/area_assignments/{assignment_id}/metrics",
                version=2,
                json=data,
            ),
            Metric,
        )

    def update_metric(
        self,
        org_id: int,
        assignment_id: int,
        metric_id: int,
        data: dict[str, JsonValue],
    ) -> Metric:
        return model_data(
            self._client.request(
                "PATCH",
                f"/orgs/{org_id}/area_assignments/{assignment_id}/metrics/{metric_id}",
                version=2,
                json=data,
            ),
            Metric,
        )

    def delete_metric(self, org_id: int, assignment_id: int, metric_id: int) -> None:
        self._client.request(
            "DELETE",
            f"/orgs/{org_id}/area_assignments/{assignment_id}/metrics/{metric_id}",
            version=2,
        )

    def assign(
        self,
        org_id: int,
        assignment_id: int,
        area_id: int,
        user_id: int,
    ) -> AreaAssignee:
        return model_data(
            self._client.request(
                "PUT",
                f"/orgs/{org_id}/area_assignments/{assignment_id}/areas/{area_id}/assignees/{user_id}",
                version=2,
            ),
            AreaAssignee,
        )

    def unassign(
        self,
        org_id: int,
        assignment_id: int,
        area_id: int,
        user_id: int,
    ) -> None:
        self._client.request(
            "DELETE",
            f"/orgs/{org_id}/area_assignments/{assignment_id}/areas/{area_id}/assignees/{user_id}",
            version=2,
        )

    def stats(self, org_id: int, assignment_id: int) -> AreaAssignmentStats:
        return model_data(
            self._client.request(
                "GET",
                f"/orgs/{org_id}/area_assignments/{assignment_id}/stats",
                version=2,
            ),
            AreaAssignmentStats,
        )


class LocationsService:
    def __init__(self, client: SyncRequester) -> None:
        self._client = client

    def list(
        self,
        org_id: int,
        *,
        page: int = 0,
        size: int = 100,
        location_type: str | None = None,
    ) -> Page[Location]:
        return page_data(
            self._client.request(
                "GET",
                f"/orgs/{org_id}/locations",
                version=2,
                params={"page": page, "size": size, "type": location_type},
            ),
            Location,
        )

    def create(self, org_id: int, data: dict[str, JsonValue]) -> Location:
        return model_data(
            self._client.request(
                "POST", f"/orgs/{org_id}/locations", version=2, json=data
            ),
            Location,
        )

    def update(
        self, org_id: int, location_id: int, data: dict[str, JsonValue]
    ) -> Location:
        return model_data(
            self._client.request(
                "PATCH",
                f"/orgs/{org_id}/locations/{location_id}",
                version=2,
                json=data,
            ),
            Location,
        )

    def households(self, org_id: int, location_id: int) -> Page[Household]:
        return page_data(
            self._client.request(
                "GET",
                f"/orgs/{org_id}/locations/{location_id}/households",
                version=2,
                params={"page": 0, "size": 100},
            ),
            Household,
        )

    def get_household(
        self, org_id: int, location_id: int, household_id: int
    ) -> Household:
        return model_data(
            self._client.request(
                "GET",
                f"/orgs/{org_id}/locations/{location_id}/households/{household_id}",
                version=2,
            ),
            Household,
        )

    def create_household(
        self, org_id: int, location_id: int, data: dict[str, JsonValue]
    ) -> Household:
        return model_data(
            self._client.request(
                "POST",
                f"/orgs/{org_id}/locations/{location_id}/households",
                version=2,
                json=data,
            ),
            Household,
        )

    def update_household(
        self,
        org_id: int,
        location_id: int,
        household_id: int,
        data: dict[str, JsonValue],
    ) -> Household:
        return model_data(
            self._client.request(
                "PATCH",
                f"/orgs/{org_id}/locations/{location_id}/households/{household_id}",
                version=2,
                json=data,
            ),
            Household,
        )

    def delete_household(
        self, org_id: int, location_id: int, household_id: int
    ) -> None:
        self._client.request(
            "DELETE",
            f"/orgs/{org_id}/locations/{location_id}/households/{household_id}",
            version=2,
        )


class VisitsService:
    def __init__(self, client: SyncRequester) -> None:
        self._client = client

    def location_visits(
        self, org_id: int, assignment_id: int, location_id: int
    ) -> Page[LocationVisit]:
        return page_data(
            self._client.request(
                "GET",
                f"/orgs/{org_id}/area_assignments/{assignment_id}/locations/{location_id}/visits",
                version=2,
                params={"page": 0, "size": 100},
            ),
            LocationVisit,
        )

    def report_location(
        self,
        org_id: int,
        assignment_id: int,
        location_id: int,
        data: dict[str, JsonValue],
        *,
        visit_id: int | None = None,
    ) -> LocationVisit:
        suffix = f"/{visit_id}" if visit_id is not None else ""
        method = "PATCH" if visit_id is not None else "POST"
        return model_data(
            self._client.request(
                method,
                f"/orgs/{org_id}/area_assignments/{assignment_id}/locations/{location_id}/visits{suffix}",
                version=2,
                json=data,
            ),
            LocationVisit,
        )

    def household_visits(
        self, org_id: int, assignment_id: int, household_id: int
    ) -> Page[HouseholdVisit]:
        return page_data(
            self._client.request(
                "GET",
                f"/orgs/{org_id}/area_assignments/{assignment_id}/households/{household_id}/visits",
                version=2,
            ),
            HouseholdVisit,
        )

    def report_household(
        self,
        org_id: int,
        assignment_id: int,
        household_id: int,
        data: dict[str, JsonValue],
    ) -> HouseholdVisit:
        return model_data(
            self._client.request(
                "POST",
                f"/orgs/{org_id}/area_assignments/{assignment_id}/households/{household_id}/visits",
                version=2,
                json=data,
            ),
            HouseholdVisit,
        )


class OrgUsersService:
    def __init__(self, client: SyncRequester) -> None:
        self._client = client

    def list(self, org_id: int) -> Page[User]:
        return page_data(
            self._client.request(
                "GET",
                f"/orgs/{org_id}/users",
                version=2,
                params={"page": 0, "size": 100},
            ),
            User,
        )

    def get(self, org_id: int, user_id: int) -> User:
        return model_data(
            self._client.request("GET", f"/orgs/{org_id}/users/{user_id}", version=2),
            User,
        )

    def my_area_assignments(self) -> Page[AreaAssignment]:
        return page_data(
            self._client.request(
                "GET",
                "/users/me/area_assignments",
                version=2,
                params={"page": 0, "size": 100},
            ),
            AreaAssignment,
        )


class V2Namespace:
    def __init__(self, client: SyncRequester) -> None:
        self.areas = AreasService(client)
        self.area_assignments = AreaAssignmentsService(client)
        self.locations = LocationsService(client)
        self.visits = VisitsService(client)
        self.users = OrgUsersService(client)


class AsyncV2Service:
    def __init__(self, client: AsyncRequester) -> None:
        self._client = client

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Params | None = None,
        json: JsonValue = None,
    ) -> JsonValue | bytes:
        return (
            await self._client.request(
                method, path, version=2, params=params, json=json
            )
        ).data


class AsyncAreasService(AsyncV2Service):
    async def list(self, org_id: int, *, page: int = 0, size: int = 100) -> Page[Area]:
        return page_data(
            await self._client.request(
                "GET",
                f"/orgs/{org_id}/areas",
                version=2,
                params={"page": page, "size": size},
            ),
            Area,
        )

    async def create(self, org_id: int, data: dict[str, JsonValue]) -> Area:
        return model_data(
            await self._client.request(
                "POST", f"/orgs/{org_id}/areas", version=2, json=data
            ),
            Area,
        )

    async def update(
        self, org_id: int, area_id: int, data: dict[str, JsonValue]
    ) -> Area:
        return model_data(
            await self._client.request(
                "PATCH",
                f"/orgs/{org_id}/areas/{area_id}",
                version=2,
                json=data,
            ),
            Area,
        )

    async def delete(self, org_id: int, area_id: int) -> None:
        await self._client.request(
            "DELETE", f"/orgs/{org_id}/areas/{area_id}", version=2
        )

    async def stats(self, org_id: int, area_id: int) -> AreaStats:
        return model_data(
            await self._client.request(
                "GET", f"/orgs/{org_id}/areas/{area_id}/stats", version=2
            ),
            AreaStats,
        )


class AsyncAreaAssignmentsService(AsyncV2Service):
    async def list(
        self, org_id: int, *, page: int = 0, size: int = 100
    ) -> Page[AreaAssignment]:
        return page_data(
            await self._client.request(
                "GET",
                f"/orgs/{org_id}/area_assignments",
                version=2,
                params={"page": page, "size": size},
            ),
            AreaAssignment,
        )

    async def get(self, org_id: int, assignment_id: int) -> AreaAssignment:
        return model_data(
            await self._client.request(
                "GET", f"/orgs/{org_id}/area_assignments/{assignment_id}", version=2
            ),
            AreaAssignment,
        )

    async def create(
        self, org_id: int, project_id: int, data: dict[str, JsonValue]
    ) -> AreaAssignment:
        return model_data(
            await self._client.request(
                "POST",
                f"/orgs/{org_id}/projects/{project_id}/area_assignments",
                version=2,
                json=data,
            ),
            AreaAssignment,
        )

    async def update(
        self, org_id: int, assignment_id: int, data: dict[str, JsonValue]
    ) -> AreaAssignment:
        return model_data(
            await self._client.request(
                "PATCH",
                f"/orgs/{org_id}/area_assignments/{assignment_id}",
                version=2,
                json=data,
            ),
            AreaAssignment,
        )

    async def delete(self, org_id: int, assignment_id: int) -> None:
        await self._client.request(
            "DELETE", f"/orgs/{org_id}/area_assignments/{assignment_id}", version=2
        )

    async def assignees(self, org_id: int, assignment_id: int) -> Page[AreaAssignee]:
        return page_data(
            await self._client.request(
                "GET",
                f"/orgs/{org_id}/area_assignments/{assignment_id}/assignees",
                version=2,
                params={"page": 0, "size": 100},
            ),
            AreaAssignee,
        )

    async def areas(self, org_id: int, assignment_id: int) -> Page[Area]:
        return page_data(
            await self._client.request(
                "GET",
                f"/orgs/{org_id}/area_assignments/{assignment_id}/areas",
                version=2,
                params={"page": 0, "size": 100},
            ),
            Area,
        )

    async def locations(
        self, org_id: int, assignment_id: int, *, params: Params | None = None
    ) -> Page[Location]:
        return page_data(
            await self._client.request(
                "GET",
                f"/orgs/{org_id}/area_assignments/{assignment_id}/locations",
                version=2,
                params=params,
            ),
            Location,
        )

    async def location(
        self, org_id: int, assignment_id: int, location_id: int
    ) -> Location:
        return model_data(
            await self._client.request(
                "GET",
                f"/orgs/{org_id}/area_assignments/{assignment_id}/locations/{location_id}",
                version=2,
            ),
            Location,
        )

    async def metrics(self, org_id: int, assignment_id: int) -> Page[Metric]:
        return page_data(
            await self._client.request(
                "GET",
                f"/orgs/{org_id}/area_assignments/{assignment_id}/metrics",
                version=2,
            ),
            Metric,
        )

    async def create_metric(
        self, org_id: int, assignment_id: int, data: dict[str, JsonValue]
    ) -> Metric:
        return model_data(
            await self._client.request(
                "POST",
                f"/orgs/{org_id}/area_assignments/{assignment_id}/metrics",
                version=2,
                json=data,
            ),
            Metric,
        )

    async def update_metric(
        self,
        org_id: int,
        assignment_id: int,
        metric_id: int,
        data: dict[str, JsonValue],
    ) -> Metric:
        return model_data(
            await self._client.request(
                "PATCH",
                f"/orgs/{org_id}/area_assignments/{assignment_id}/metrics/{metric_id}",
                version=2,
                json=data,
            ),
            Metric,
        )

    async def delete_metric(
        self, org_id: int, assignment_id: int, metric_id: int
    ) -> None:
        await self._client.request(
            "DELETE",
            f"/orgs/{org_id}/area_assignments/{assignment_id}/metrics/{metric_id}",
            version=2,
        )

    async def assign(
        self,
        org_id: int,
        assignment_id: int,
        area_id: int,
        user_id: int,
    ) -> AreaAssignee:
        return model_data(
            await self._client.request(
                "PUT",
                f"/orgs/{org_id}/area_assignments/{assignment_id}/areas/{area_id}/assignees/{user_id}",
                version=2,
            ),
            AreaAssignee,
        )

    async def unassign(
        self,
        org_id: int,
        assignment_id: int,
        area_id: int,
        user_id: int,
    ) -> None:
        await self._client.request(
            "DELETE",
            f"/orgs/{org_id}/area_assignments/{assignment_id}/areas/{area_id}/assignees/{user_id}",
            version=2,
        )

    async def stats(self, org_id: int, assignment_id: int) -> AreaAssignmentStats:
        return model_data(
            await self._client.request(
                "GET",
                f"/orgs/{org_id}/area_assignments/{assignment_id}/stats",
                version=2,
            ),
            AreaAssignmentStats,
        )


class AsyncLocationsService(AsyncV2Service):
    async def list(
        self,
        org_id: int,
        *,
        page: int = 0,
        size: int = 100,
        location_type: str | None = None,
    ) -> Page[Location]:
        return page_data(
            await self._client.request(
                "GET",
                f"/orgs/{org_id}/locations",
                version=2,
                params={"page": page, "size": size, "type": location_type},
            ),
            Location,
        )

    async def create(self, org_id: int, data: dict[str, JsonValue]) -> Location:
        return model_data(
            await self._client.request(
                "POST", f"/orgs/{org_id}/locations", version=2, json=data
            ),
            Location,
        )

    async def update(
        self, org_id: int, location_id: int, data: dict[str, JsonValue]
    ) -> Location:
        return model_data(
            await self._client.request(
                "PATCH",
                f"/orgs/{org_id}/locations/{location_id}",
                version=2,
                json=data,
            ),
            Location,
        )

    async def households(self, org_id: int, location_id: int) -> Page[Household]:
        return page_data(
            await self._client.request(
                "GET",
                f"/orgs/{org_id}/locations/{location_id}/households",
                version=2,
                params={"page": 0, "size": 100},
            ),
            Household,
        )

    async def get_household(
        self, org_id: int, location_id: int, household_id: int
    ) -> Household:
        return model_data(
            await self._client.request(
                "GET",
                f"/orgs/{org_id}/locations/{location_id}/households/{household_id}",
                version=2,
            ),
            Household,
        )

    async def create_household(
        self, org_id: int, location_id: int, data: dict[str, JsonValue]
    ) -> Household:
        return model_data(
            await self._client.request(
                "POST",
                f"/orgs/{org_id}/locations/{location_id}/households",
                version=2,
                json=data,
            ),
            Household,
        )

    async def update_household(
        self,
        org_id: int,
        location_id: int,
        household_id: int,
        data: dict[str, JsonValue],
    ) -> Household:
        return model_data(
            await self._client.request(
                "PATCH",
                f"/orgs/{org_id}/locations/{location_id}/households/{household_id}",
                version=2,
                json=data,
            ),
            Household,
        )

    async def delete_household(
        self, org_id: int, location_id: int, household_id: int
    ) -> None:
        await self._client.request(
            "DELETE",
            f"/orgs/{org_id}/locations/{location_id}/households/{household_id}",
            version=2,
        )


class AsyncVisitsService(AsyncV2Service):
    async def location_visits(
        self, org_id: int, assignment_id: int, location_id: int
    ) -> Page[LocationVisit]:
        return page_data(
            await self._client.request(
                "GET",
                f"/orgs/{org_id}/area_assignments/{assignment_id}/locations/{location_id}/visits",
                version=2,
                params={"page": 0, "size": 100},
            ),
            LocationVisit,
        )

    async def report_location(
        self,
        org_id: int,
        assignment_id: int,
        location_id: int,
        data: dict[str, JsonValue],
        *,
        visit_id: int | None = None,
    ) -> LocationVisit:
        suffix = f"/{visit_id}" if visit_id is not None else ""
        method = "PATCH" if visit_id is not None else "POST"
        return model_data(
            await self._client.request(
                method,
                f"/orgs/{org_id}/area_assignments/{assignment_id}/locations/{location_id}/visits{suffix}",
                version=2,
                json=data,
            ),
            LocationVisit,
        )

    async def household_visits(
        self, org_id: int, assignment_id: int, household_id: int
    ) -> Page[HouseholdVisit]:
        return page_data(
            await self._client.request(
                "GET",
                f"/orgs/{org_id}/area_assignments/{assignment_id}/households/{household_id}/visits",
                version=2,
            ),
            HouseholdVisit,
        )

    async def report_household(
        self,
        org_id: int,
        assignment_id: int,
        household_id: int,
        data: dict[str, JsonValue],
    ) -> HouseholdVisit:
        return model_data(
            await self._client.request(
                "POST",
                f"/orgs/{org_id}/area_assignments/{assignment_id}/households/{household_id}/visits",
                version=2,
                json=data,
            ),
            HouseholdVisit,
        )


class AsyncOrgUsersService(AsyncV2Service):
    async def list(self, org_id: int) -> Page[User]:
        return page_data(
            await self._client.request(
                "GET",
                f"/orgs/{org_id}/users",
                version=2,
                params={"page": 0, "size": 100},
            ),
            User,
        )

    async def get(self, org_id: int, user_id: int) -> User:
        return model_data(
            await self._client.request(
                "GET", f"/orgs/{org_id}/users/{user_id}", version=2
            ),
            User,
        )

    async def my_area_assignments(self) -> Page[AreaAssignment]:
        return page_data(
            await self._client.request(
                "GET",
                "/users/me/area_assignments",
                version=2,
                params={"page": 0, "size": 100},
            ),
            AreaAssignment,
        )


class AsyncV2Namespace:
    def __init__(self, client: AsyncRequester) -> None:
        self.areas = AsyncAreasService(client)
        self.area_assignments = AsyncAreaAssignmentsService(client)
        self.locations = AsyncLocationsService(client)
        self.visits = AsyncVisitsService(client)
        self.users = AsyncOrgUsersService(client)
