# 03: Watch a Run move through its statuses

**What to build:** After submitting, the Run moves on its own through `planning`, `running` and `done`, about 2 seconds apart, so a caller who polls the status sees it progress.
- A Run that hits an error ends `failed`, with its message.
- When the service starts, any Run cut off by a restart is marked `failed` ("interrupted by restart").
- The placeholder sits behind the single swap point that PR 2 uses for the real Architecture.

**Blocked by:** 02

**Status:** ready-for-agent

- [ ] A submitted Run reaches `done` through `planning` and `running`, with no further requests. The wait is configurable, and it is zero in the tests.
- [ ] The background work starts through `start_run(run_id)` with FastAPI `BackgroundTasks`.
- [ ] If the work raises an error, the Run ends `failed` with the error message. A test swaps in work that raises, to check this.
- [ ] On startup, Runs left `queued`, `planning` or `running` become `failed` with "interrupted by restart". A test seeds an unfinished Run, to check this.
- [ ] Polling in `/docs` shows the status change in real time.
- [ ] The README decision log records open decision #2 (background execution and restart behaviour).
- [ ] The Postman collection or curl script has a sample end-to-end Run: submit, then poll until `done`.
- [ ] The developer was taught, then quizzed, and explained back the Run lifecycle, end to end. It is ticked in the spec.
