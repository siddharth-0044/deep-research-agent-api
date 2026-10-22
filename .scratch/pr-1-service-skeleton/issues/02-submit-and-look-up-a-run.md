# 02: Submit a query and look up its Run

**What to build:** A caller can submit a research query and immediately get a run ID back. The caller can then look the Run up by that ID and see it `queued`. Invalid queries and unknown run IDs get clear errors.

This ticket lays the foundation: the service, its configuration, PostgreSQL 18 running locally, and the `runs` table, which one migration creates.

The spec assumed Podman is already installed (true on the original Fedora machine). On a machine without it, settle with the developer how PostgreSQL runs locally before starting.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] Submitting a valid query returns 202 with a UUID run ID and status `queued`.
- [ ] A missing or empty query, or one longer than 2000 characters, returns 422 naming the field.
- [ ] Looking up a Run returns 200 with the run ID, status, error (empty), created-at and updated-at.
- [ ] Looking up an unknown run ID returns 404.
- [ ] Runs are stored in a `runs` table that one Alembic migration creates, in a locally running PostgreSQL 18.
- [ ] The service refuses to start without `DATABASE_URL`, and `.env.example` lists the variables.
- [ ] Both endpoints work from the `/docs` page.
- [ ] The tests go through the HTTP endpoints against a real PostgreSQL test database built from the migration. They are written test-first, and ruff passes.
- [ ] The README covers setup, the environment variables, and running PostgreSQL and the service locally. Its decision log records the API shape of these endpoints (part of open decision #7) and the `runs` table (part of open decision #8).
- [ ] A Postman collection or curl script has both requests.
- [ ] The developer was taught, then quizzed, and explained back each of these: API endpoints and status codes, the `runs` table and migrations, and test seams. Each one is ticked in the spec.
