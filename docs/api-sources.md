# API sources and coverage

## API v1

The generated v1 layer is pinned to commit
[`d013cb993187fb4e5a116b3275053602fd01ae9f`](https://github.com/zetkin/developer.zetkin.org/tree/d013cb993187fb4e5a116b3275053602fd01ae9f)
of the official developer portal. Its resource catalog contains duplicate entries;
normalizing by `(HTTP method, path)` produces 256 distinct operations.

The portal lists many operations without request or response schemas. Path parameters
and HTTP operations remain statically generated, but undocumented payloads use the
recursive `JsonValue` type. Friendly models combine fields documented by the portal
with types used by the current official application, and preserve unknown fields.

## API v2

V2 coverage is pinned to commit
[`0aef1bed2280fce70b7928fe1b87e3780e1eb453`](https://github.com/zetkin/app.zetkin.org/tree/0aef1bed2280fce70b7928fe1b87e3780e1eb453)
of `zetkin/app.zetkin.org`. It covers all `/api2/` families used there at that commit:

- areas and area statistics;
- area assignments, areas, assignees, metrics, statistics, and locations;
- canvass locations, households, and location/household visits;
- organization users and the current user's area assignments.

Zetkin does not publish a complete v2 specification. `client.request(..., version=2)`
and `zetkin request --api-version 2` provide access to additional routes without
claiming unsupported schemas.

## Authentication

The authorization and token endpoints are `/v1/oauth/authorize/` and
`/v1/oauth/token/`. Requests use bearer tokens. Refresh and authorization-code token
exchanges authenticate the OAuth client with HTTP Basic, matching the official SDK and
current web application proxy.

