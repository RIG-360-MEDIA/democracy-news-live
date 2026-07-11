# Rig Wire — API Conventions

**Status:** No live API today. This file is a forward-looking contract.

The prototype is statically rendered with content in `<feature>-data.ts`
files. The first real API will appear when we wire one of:

- live article ingest (Worldwide / All Sides)
- user accounts (auth + Pocket queue persistence)
- editor tooling (Flash story rotation)

When that day arrives, these conventions are non-negotiable.

---

## Transport

- **REST + JSON** for read paths. Cacheable, debuggable, browser-native, the
  industry knows how to operate it.
- **Server-Sent Events** for live news streams (Worldwide breaking, Flash
  refresh). *Not* WebSockets — we have no bidirectional need, and SSE
  survives every corporate proxy.
- **No GraphQL** unless we onboard three or more distinct consumers. The
  N+1 myth is real in production; REST with a smart aggregation endpoint per
  page is faster to ship, faster to debug, and lets the CDN do its job.

## Routes

App-Router conventions:

- `/api/<resource>`           — collections (`GET /api/articles`)
- `/api/<resource>/[id]`      — single  (`GET /api/articles/<slug>`)
- `/api/<feature>/<action>`   — RPC for non-CRUD (`POST /api/queue/play`)

URL slugs are kebab-case. IDs are opaque strings — never leak a DB integer.

## Response envelope

Every JSON response, success or failure, conforms to:

```ts
type ApiResponse<T> = {
  ok: boolean;
  data: T | null;
  error: { code: string; message: string; details?: unknown } | null;
  meta?: { traceId: string; cachedAt?: string; nextCursor?: string };
};
```

The HTTP status code carries the semantic. The envelope carries the *why*.

## Errors

| Code | When                                                                   |
| ---- | ---------------------------------------------------------------------- |
| 400  | Malformed input. Return validation errors in `error.details`.          |
| 401  | Not authenticated.                                                     |
| 403  | Authenticated but not authorized.                                      |
| 404  | Resource doesn't exist — or you can't see it. Do not leak existence.   |
| 422  | Well-formed but semantically invalid (publish date in the future).     |
| 429  | Rate-limited. Always include `Retry-After`.                            |
| 5xx  | Our fault. Log with `traceId`. Return the `traceId` to the client.     |

NEVER return a raw stack trace. NEVER include the user's email in
`error.message`. The traceId is how you correlate the user's bug report
to your logs.

## Auth

- Session cookies — `httpOnly`, `SameSite=Lax`, `Secure` in production.
- Bearer tokens only for service-to-service.
- No long-lived JWTs in the browser. The server rotates the session at its
  discretion.

## Caching

- `Cache-Control: public, s-maxage=60, stale-while-revalidate=300` — article
  reads.
- `Cache-Control: no-store` — anything personalised (Pocket queue, prefs,
  ranked feed).
- Personalised endpoints cached at the edge must `Vary: Cookie`.

## Rate limiting

- Anonymous: 60 req/min per IP.
- Authenticated: 600 req/min per user.
- Burst: 2× for 10 seconds, then hard cap.

## Observability (mandatory before launch)

Every API request emits a structured log line:

- `traceId`, `userId | null`, `route`, `status`, `duration_ms`, `cacheHit`
- For breaking-news endpoints: `freshness_seconds` of the data served.

A news API without per-route p99 latency dashboards is unshippable. If you
do not know your tail latency, you do not know your product.

---

## What not to do

- No `PUT`/`PATCH`/`DELETE` on a public surface without idempotency keys.
- No verbs in resource names. `GET /api/articles`, not `GET /api/getArticles`.
- No nesting beyond one level. `/api/articles/[id]/comments/[id]/replies`
  flattens to `/api/comments?article=<id>&parent=<id>`.
- No `v1` in the URL until you have a `v2` forced by a real
  backwards-incompatibility.
- No "we'll add validation later". Validation lands with the route or the
  route does not land.
