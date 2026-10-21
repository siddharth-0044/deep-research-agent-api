# PR 1: Service skeleton

Status: ready-for-agent

## Problem Statement

The developer needs a running service that accepts a research question and lets the caller follow the Run's progress. That has to exist before any AI is involved, so the plumbing (API → background work → database → trace) can be built, tested and understood on its own. The repo currently holds only the assignment brief, `SPEC.md`. The developer is a complete beginner with this stack and must be able to explain every part of it afterwards.

## Solution

A FastAPI service with two endpoints:
- A caller submits a query and immediately gets back a run ID.
- A placeholder stands in for an Architecture. In the background it moves the Run through its statuses over about 6 seconds.
- The caller polls the status endpoint to watch the Run progress.

Every Run is stored in PostgreSQL, and each Run's work appears as one trace in Logfire. The whole thing can be demoed from FastAPI's built-in `/docs` page, with no frontend.

## User Stories

1. As a caller, I want to submit a research query in a single request, so that I can start a Run without any back-and-forth.
2. As a caller, I want an immediate response containing a run ID, so that I don't have to wait minutes for the research to finish.
3. As a caller, I want that response to say the Run is `queued`, so that I know it was accepted.
4. As a caller, I want a missing or empty query rejected with a validation error that names the field, so that I know what to fix.
5. As a caller, I want a query longer than 2000 characters rejected the same way, so that oversized input never reaches the service.
6. As a caller, I want to look up a Run's status by its run ID, so that I can follow its progress.
7. As a caller, I want to see the status move through `queued`, `planning`, `running` and `done`, so that I can tell how far along the Run is.
8. As a caller, I want to see when the Run was created and when it last changed, so that I can tell whether it is still progressing.
9. As a caller, I want a clear not-found response for an unknown run ID, so that I can tell a typo from a stuck Run.
10. As a caller, I want a Run that hits an error to show `failed` together with the error message, so that I know what went wrong.
11. As a caller, I want run IDs that can't be guessed, so that nobody can stumble onto someone else's Run by counting.
12. As an operator, I want every Run stored in PostgreSQL, so that Runs survive a server restart.
13. As an operator, I want any Run cut off by a restart marked `failed` with "interrupted by restart" when the service starts, so that no Run stays stuck forever.
14. As an operator, I want the database layout created and changed only through migrations, so that any copy of the database can be brought to the same shape.
15. As an operator, I want configuration (the database URL and the Logfire token) read from environment variables or a git-ignored `.env` file, with a committed example file, so that secrets never reach the public repo.
16. As an operator, I want the service to refuse to start when required configuration is missing, so that misconfiguration shows up immediately.
17. As the developer, I want each Run's work to appear as one trace in Logfire, with a named `research run` span that contains each status change, so that I can see the flow and explain it.
18. As the developer, I want each status poll to show up as its own small trace, so that polling doesn't clutter the Run's trace.
19. As the developer, I want the placeholder to pretend slowly (about 2 seconds per status), so that I can watch the lifecycle happen in `/docs` before any AI exists.
20. As the developer, I want the placeholder to sit behind a single swap point, so that PR 2 can plug in a real Architecture without touching the endpoints.
21. As the developer, I want to try both endpoints from FastAPI's `/docs` page, so that the service is tangible without building a frontend.
22. As the developer, I want a README covering setup, environment variables, running PostgreSQL and the service locally, viewing traces in Logfire, and a decision log, so that the project can be run and its choices understood.
23. As the developer, I want a Postman collection or curl script for both endpoints, including a sample end-to-end Run, so that the spec's deliverable grows PR by PR.
24. As the developer, I want a guided wizard for creating my Logfire account, project and token, so that the one step only I can do is quick and can't go wrong.
25. As the developer, I want fast automated tests that skip the placeholder's waiting, so that the test suite runs in seconds.
26. As the developer, I want to be taught, and then quizzed on, every item in the "Must be able to explain" list before this PR counts as done, so that I can explain the flow and the traces in an interview.

## Implementation Decisions

- **Endpoints.**
  - `POST /research/query` accepts a body with a single `query` field (text, 1 to 2000 characters). It answers 202 Accepted with the run ID and status `queued`. An invalid body gets an automatic 422 from Pydantic validation.
  - `GET /research/{run_id}/status` answers 200 with the run ID, status, error (empty unless the Run failed), created-at and updated-at. An unknown run ID gets 404.
  - Run IDs are UUIDs.
  - The spec's optional architecture field is deferred to PR 3.
- **API models vs. storage models.** Pydantic models describe the request and response shapes. Separate SQLAlchemy models describe storage. SQLModel was rejected, because it blurs that distinction and is still at 0.0.x.
- **Storage.** A single `runs` table with columns `id` (UUID), `query` (text), `status` (one of the five statuses), `error` (nullable text), `created_at` and `updated_at`. It is created by one Alembic migration. The architecture column and the tables for Plans, Steps, Sources and Reports arrive in PR 2 through a new migration.
- **Run lifecycle (state machine).** The statuses are `queued`, `planning`, `running` and `done`, and a Run only moves forward through them. Any status that isn't finished can move to `failed`, with the error recorded on the Run.
- **Background execution (open decision #2).** FastAPI `BackgroundTasks` runs the work in-process after the response is sent, through a single swap point, `start_run(run_id)`. On startup, a sweep marks every Run still `queued`, `planning` or `running` as `failed` with "interrupted by restart". A task queue, a separate worker and durability across restarts were all rejected under YAGNI.
- **Placeholder.** It waits about 2 seconds, then moves to `planning`; about 2 seconds later to `running`; about 2 seconds later to `done`. The wait is configurable so tests can set it to zero. If any error is raised, the Run is set to `failed` with the error message. PR 2 replaces the placeholder with a real Architecture behind the same swap point.
- **Tracing.**
  - Logfire is configured to send only when a token is present, so nothing is sent from tests.
  - FastAPI requests and database queries are instrumented automatically.
  - One manual span, `research run`, wraps the background work and carries the run ID.
  - Because `BackgroundTasks` runs inside the request's handling, a Run's spans nest under its `POST /research/query` trace, and each status poll is its own trace.
  - Confirm while building that the `POST` span lasts as long as the Run. A separate trace per Run was rejected for now.
- **Configuration.** pydantic-settings reads the settings from the environment or `.env`. `DATABASE_URL` is required. `LOGFIRE_TOKEN` is optional; without it, traces aren't sent. The OpenRouter and Tavily keys aren't needed until PR 2. A committed `.env.example` lists the variables.
- **Toolset.**
  - Python 3.14 (ready-made builds of the database driver and Pydantic were confirmed), managed with uv and its lockfile.
  - SQLAlchemy async with asyncpg, and Alembic.
  - pytest and ruff.
  - PostgreSQL 18 running in a single Podman container. Podman is already installed, so nothing new is needed. The agent runs every command.
- **Logfire setup.** The developer creates the Logfire account, project and write token through a `wizard`-generated walkthrough before any tracing work. This is the only human-only step.
- **Docs.**
  - The README gains a decision log recording, with reasoning:
    - open decision #2 (background execution and restart behaviour);
    - the part of #7 covering these two endpoints;
    - the part of #8 covering the `runs` table.
  - A Postman collection or curl script covers both endpoints.

## Testing Decisions

- A good test checks external behaviour only: what a caller sends and receives. It never reaches into internals, so the code can be restructured freely while the tests stay valid.
- **Main seam: the HTTP endpoints.** Tests call the two endpoints through an in-process HTTP client, against a real PostgreSQL test database whose layout comes from the Alembic migration, so the migration is tested too. The placeholder's waits are set to zero. Covered cases:
  - a valid query gets 202 and a run ID, and the status then reaches `done`;
  - a blank, missing or oversized query gets 422;
  - an unknown run ID gets 404.
- **Startup sweep, through the same seam.** Seed an unfinished Run directly in the test database, start the app, then check that the status endpoint reports `failed` with "interrupted by restart".
- **Second seam: the work behind `start_run`.** One test swaps in work that deliberately raises an error, then checks through the HTTP seam that the Run ends `failed` with that message.
- Traces are not tested in code. The developer checks them by eye in Logfire, as part of the definition of done.
- Prior art: none, since this is a greenfield repo. Tests are written first, using the `tdd` red-green loop.

## Out of Scope

- **PR 2 (first Architecture):**
  - real research with Pydantic AI, OpenRouter and Tavily;
  - tables for Plans, Steps, Sources and Reports;
  - the result and trace endpoints.

  PR 2 must settle open decisions #6 (models), the report-format part of #7, and the rest of #8 (schema). It must also choose which Architecture comes first, which is part of #1.
- **PR 3 (second Architecture):** the architecture field on requests, the architectures endpoint, and choosing a default. It settles open decisions #1 and #5.
- **PR 4 (Comparison):** the compare endpoint, the evaluation method and stored judgments. It settles open decisions #3 and #4.
- **Never planned:** a frontend, Vercel or any public hosting (demos run locally through `/docs`); a type checker (mypy); CI; a container image for the API; a durable task queue or worker; cancelling Runs.

## Further Notes

**Roadmap.** The project is four PRs, each grilled just before it is built:
1. Service skeleton (this spec).
2. First Architecture.
3. Second Architecture.
4. Comparison.

Each PR updates the README decision log and the Postman collection.

**Working agreement.** The developer is a complete beginner. Every step is explained from zero before it happens, following the "Working with the developer" section of `CLAUDE.md`. The rules on what counts as done are in `CLAUDE.md` and the "Definition of done" section of `SPEC.md`.

### Must be able to explain

Tick each item only after the developer has been taught it, quizzed on it, and has explained it back correctly.

- [ ] **Run trace shape:**
  - what a span is and what a trace is;
  - why a Run's trace hangs off its `POST /research/query` request (`BackgroundTasks` runs inside that request's handling);
  - what the single manual `research run` span is for;
  - why each status poll is its own small trace;
  - why the `POST` span appears to last as long as the whole Run, even though the caller got its response instantly;
  - what the rejected alternative, a separate trace per Run with its trace ID stored on the Run, would have changed.

  ```
  POST /research/query                ← automatic (FastAPI)
  ├─ INSERT INTO runs                 ← automatic (database)
  └─ research run  run_id=…           ← the one manual span
     ├─ UPDATE runs SET status='planning'
     ├─ (PR 2: agent run → LLM calls → web_search tool calls)
     └─ UPDATE runs SET status='done'

  GET /research/{id}/status           ← each poll is its own tiny trace
  ```
- [ ] **API endpoints and HTTP status codes:**
  - what an endpoint is (method + path);
  - what a request and a response are, including the JSON body;
  - the three status-code families: 2xx success, 4xx the caller's mistake, 5xx the server's fault;
  - what 200, 202, 404, 422 and 500 each mean, and which endpoint returns which, and why;
  - why the submit endpoint answers 202 instead of 200;
  - how a Pydantic model turns a bad request body into an automatic 422.
- [ ] **The `runs` table and migrations:**
  - what a database, a table, a row and a column are, and what "nullable" means;
  - what each of the six columns holds, and why `error` is nullable;
  - what SQLAlchemy does (tables as Python classes) and what Alembic does (numbered migration scripts that build and change tables, like git commits for the table layout);
  - why PR 1 creates only one table, and how PR 2 adds the rest with a new migration.
- [ ] **The Run lifecycle, end to end:**
  - the five statuses and the allowed moves between them (the state machine);
  - what the placeholder does and why it exists (a conveyor belt tested with empty boxes);
  - how an error ends a Run as `failed` with its message recorded, and how the startup sweep handles Runs cut off by a restart;
  - where `start_run(run_id)` sits, and how PR 2 swaps a real Architecture in without touching the endpoints;
  - the full path of one Run: submit → 202 + run ID → background work → status updates → poll → done, and where each step appears in the trace.
- [ ] **Test seams:**
  - what a test and a seam are (the vending machine: test from the slot and buttons, not by poking the motors);
  - why the HTTP endpoints are the main seam;
  - what the second seam (the work behind `start_run`) is for;
  - why traces are checked by eye instead of in code.
