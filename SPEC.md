# Deep Research Agent API — Specification

A Python/FastAPI backend, backed by PostgreSQL, that exposes a deep research agent as an API service. From a single natural-language query, the agent plans and executes a multi-step research process on its own, gathers information from the web, and synthesizes it into a cited report. The research runs in the background, and every run is persisted so it can be inspected afterwards. There is no frontend: the whole system is exercised through documented API endpoints with curl or Postman.

Choices this spec leaves open are collected under [Open decisions](#open-decisions).

## Stack

| Concern | Choice |
|---|---|
| Language / framework | Python, FastAPI |
| Database | PostgreSQL for all persistence, with schema migrations |
| LLM | OpenRouter (OpenAI-compatible API, base URL `https://openrouter.ai/api/v1`) |
| Web search | Tavily |
| Tracing | Logfire |
| Interface | REST API only, exercised with curl / Postman |

Secrets come from environment variables, stay out of the repository, and are documented in the README:

| Variable | Used for |
|---|---|
| `DATABASE_URL` | PostgreSQL connection |
| `OPENROUTER_API_KEY` | LLM calls |
| `TAVILY_API_KEY` | Web search |
| `LOGFIRE_TOKEN` | Sending traces to Logfire |

## Glossary

Domain terms (Run, Architecture, Plan, Step, Source, Report, Comparison) are defined in [GLOSSARY.md](GLOSSARY.md).

## Core behaviour

- **Single-shot kickoff.** A run starts from one query in one request. The agent plans its research approach on its own and goes straight from the query to planning, with no clarification exchange with the caller.
- **Background execution.** The request that submits the query returns quickly with a run ID. The research itself runs asynchronously in the background (FastAPI `BackgroundTasks`, a task queue, or another worker pattern).
- **Research loop.** The agent reasons in steps: plan → gather → re-plan (optional) → synthesize → final report. How explicit this loop is depends on the architecture.
- **Web search.** Every run gathers information from the web through Tavily.
- **Report.** Every run ends in a structured research report whose claims are grounded in cited sources, stored against the run.
- **Persistence.** Every run (query, architecture, status, timestamps, plan, intermediate steps, sources, and final report) is stored in PostgreSQL and retrievable after the fact.
- **Failures.** A run that hits an error ends in status `failed`, with the error recorded on the run.

## Execution flow

1. The caller sends a request carrying only the query (and optionally the architecture to use).
2. The API validates and persists the query, starts the selected architecture, and immediately returns a run ID.
3. The research executes in the background, and the run's status advances as it goes.
4. The caller polls for status (or is notified later) and, once the run is complete, fetches the full result and trace.

Run status values: `queued` → `planning` → `running` → `done`, or `failed`.

## API

The API must expose the capabilities below. Route names and payload shapes are open (see [Open decisions](#open-decisions)); the table is a guide to the required capabilities.

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/research/query` | Submit one query; kicks off planning and background execution; returns a run ID |
| GET | `/research/{id}/status` | Poll run progress (`queued` / `planning` / `running` / `done` / `failed`) |
| GET | `/research/{id}/result` | Retrieve the final report, the sources, and which architecture produced it |
| GET | `/research/architectures` | List the two implemented architectures |
| POST | `/research/compare` | Run the same query on both architectures and return an evaluation/comparison |
| GET | `/research/{id}/trace` | Return the recorded planning / search / synthesis trace for the run |

## Database

PostgreSQL holds all persistence, managed through migrations. The schema is designed deliberately and captures:

- the query
- the chosen architecture
- run status and timestamps
- the plan, including any re-plans
- each research step / tool call
- the sources found
- the final synthesized report
- comparison judgments (see [Evaluation](#evaluation))

## Agent architectures

Implement **two** agent architectures for performing the research. They are structurally different approaches to the same research problem: they differ in control flow and orchestration, beyond their prompts.

Options (choose two):

- **Single-agent iterative loop**: one agent repeatedly decides its next search from what it has found so far.
- **Planner + parallel sub-agent workers**: a planner splits the query into sub-tasks that workers research in parallel, and the results are merged.
- **Reflection / critique-driven**: drafts are critiqued for gaps and weak claims, then improved through further research.

Requirements:

- **Selectable at request time.** The caller specifies which architecture to use, or calls the compare endpoint to run both against the same query.
- **Documented tradeoffs.** For each architecture, document its design, its rationale, and its cost / latency / quality tradeoffs versus the other.

## Evaluation

Comparing the architectures uses a concrete, implemented method that judges which one produced better research for a given query, for example scoring on source coverage, factual grounding, and depth, or an LLM-as-judge step. The judgment is stored in PostgreSQL alongside the runs it compares and exposed through the API.

## Observability

The research is multi-step and runs in the background, so it is observable end to end through Logfire traces, beyond stdout logging.

- Instrument the planning, search, and synthesis steps as traced spans.
- A run's spans connect into one trace (parent → child), so the trace shows what the agent planned, which tools and searches it called, what came back, and how the final report was derived.
- The README explains how to view the traces in the Logfire dashboard.

## Deliverables

- **Repository** with the FastAPI service, database migrations/schema, and both architecture implementations.
- **README** covering setup, environment variables, running the service and database locally, and viewing traces.
- **Postman collection** (or an equivalent curl script) covering every endpoint, including a sample end-to-end run.
- **Architecture note** (in the README or a separate file) explaining each architecture, its design rationale and tradeoffs, and the evaluation method used to compare them.

## Open decisions

These are open. Settle each one before building the part it affects, and record the decision and its reasoning in the README.

1. **Architectures**: which two of the options above.
2. **Background execution**: `BackgroundTasks`, a task queue, or another worker pattern; and what happens to in-progress runs when the server restarts.
3. **Comparison delivery**: whether `POST /research/compare` waits for both runs and the judgment, or returns an ID the caller polls.
4. **Evaluation method**: which signals are scored, how the winner is decided, and which model does the judging.
5. **Default architecture**: which one runs when the request names none.
6. **Models**: which OpenRouter models the agents and the judge use. Free (`:free`) models have per-minute and per-day request caps, which limit how many LLM calls a run can make.
7. **API shape**: exact routes, request/response payloads, and the report format (sections, citation style).
8. **Schema**: tables and relationships for runs, plans, steps, sources, reports, and comparisons.

## Definition of done

A PR, and the project as a whole, is done only when the developer can explain what was built **without notes**, especially the request flow and the Logfire traces. Working code that the developer cannot explain does not count as done, and neither does broken or partial understanding.

Getting there works like tuition, not an exam:

1. **Explain.** The developer is taught each item first, in plain words, against the actual code and the actual Logfire trace.
2. **Quiz.** Then the developer is quizzed on what was just taught, interview-style.
3. **Re-explain.** Anything answered shakily is explained again and quizzed again.

Each PR's spec under `.scratch/` lists what the developer must be able to explain for that PR.
