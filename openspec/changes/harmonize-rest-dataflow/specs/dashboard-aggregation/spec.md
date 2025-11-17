# Specification: Workspace Dashboard Aggregation

## ADDED Requirements

### Requirement: Dashboard Endpoint
The API SHALL expose `GET /api/workspace/dashboard` to return the data needed to hydrate the Unified workspace in a single request.

#### Scenario: Default payload
Given an authenticated teacher with recent sessions, drafts, and presentations
When they request `/api/workspace/dashboard`
Then the response includes:
- `sessions`: latest N (configurable, default 10) session summaries with ids, titles, timestamps, presentation status
- `drafts`: total count plus latest draft summary (id, title, updatedAt)
- `presentations`: latest presentation/job summaries including status + linked lesson id
- `stats`: quick counts such as `lessonsCreated`, `activeDrafts`
And the response body is delivered within a single JSON object with camelCase keys.

#### Scenario: Optional includes
Given a teacher only needs sessions and stats
When they call `/api/workspace/dashboard?include=sessions,stats`
Then the response only contains those requested sections to reduce payload size.

### Requirement: Authorization & Ownership
The dashboard endpoint MUST enforce the same authentication + ownership rules as existing resources.

#### Scenario: Unauthorized access
Given a request without valid credentials
When `/api/workspace/dashboard` is called
Then the API returns HTTP 401/403 consistent with other routers.

#### Scenario: Mixed-tenant data isolation
Given two different teachers with separate data
When each one calls the dashboard endpoint
Then each response contains only their respective sessions/drafts/presentations, ensuring no cross-user leakage.

### Requirement: Efficient Aggregation
The endpoint SHALL aggregate data using repository helpers that limit redundant database calls.

#### Scenario: Batched queries
Given the service needs both session list and presentation summaries
When generating the dashboard payload
Then it reuses repository methods that perform at most one query per domain (sessions, drafts, presentations, stats) and avoids per-item queries (e.g., no N+1 lookups).

#### Scenario: Response freshness metadata
Given caching could be added later
When the dashboard payload is sent
Then it includes a `generatedAt` timestamp and optional `ttl` hint so clients can decide whether they should refresh immediately or reuse cached data.

