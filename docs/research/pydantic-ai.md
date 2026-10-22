# Research: Pydantic AI, OpenRouter and Tavily (for PR 2 onward)

These facts were checked on 2026-10-21 against the live docs and Context7. The libraries change fast, so **re-check with Context7 before writing code**. Each fact names its source.

## Pydantic AI

**Version and docs.** The current version is pydantic-ai **2.59.0**, which needs Python 3.11 or newer. The docs have moved to **https://pydantic.dev/docs/ai/**; ai.pydantic.dev is the old address. Many tutorials show the v1 API, which differs: v2 has `retries={'tools': N, 'output': N}`, `capabilities=[...]`, `result.conversation`, `cost_limit`, `CancellationToken`, and `timeout=` on runs. *(PyPI pydantic-ai; pydantic.dev/docs/ai/overview/install/)*

**Install.** The plain `pydantic-ai` package includes OpenAI, Anthropic and Google model support, and Logfire. Tavily needs an extra: `pydantic-ai[tavily]`. The slim form is `pydantic-ai-slim[openrouter,logfire,tavily]`. *(install page)*

**OpenRouter.** Use the native `OpenRouterModel` with `OpenRouterProvider`, or `Agent('openrouter:<model>')`, which reads `OPENROUTER_API_KEY`. Avoid pointing the generic OpenAI provider at OpenRouter's base URL: it assumes OpenAI model profiles, so structured output can be ignored. *(pydantic.dev/docs/ai/models/openrouter/; …/models/compatible-apis/)*

**Tools and dependencies.**
- `@agent.tool` receives a `RunContext[Deps]`. `@agent.tool_plain` receives no context.
- `deps_type=` takes a dataclass that carries things like the run ID and the HTTP client.
- Raising `ModelRetry` sends the error back to the model.
- A built-in `tavily_search_tool(api_key)` exists. A custom tool gives control over the result shape, which helps with citation IDs.

*(docs/tools.md, docs/dependencies.md, common-tools)*

**Structured output.**
- Pass `output_type=Report`, a Pydantic model; the result is in `result.output`.
- The default, Tool Output, works with almost all models.
- `NativeOutput` needs the provider to support JSON-schema output. `PromptedOutput` is the fallback.
- `@agent.output_validator` plus `ModelRetry` can check rules such as "every citation ID exists".
- Output retries default to 1. When they run out, the run raises `UnexpectedModelBehavior`.

*(core-concepts/output/)*

**Limits.**
- `UsageLimits(request_limit=…, tool_calls_limit=…, total_tokens_limit=…, cost_limit=…)` raises `UsageLimitExceeded` when a limit is hit. `request_limit` defaults to 50.
- For wall-clock time, `agent.run(..., timeout=…)` raises `RunTimedOut`.
- When several agents work on one Run, share one usage object between them (`usage=ctx.usage`).

*(core-concepts/agent/#usage-limits; guides/multi-agent-applications/)*

**Logfire.**
- Calling `logfire.configure()` and then `logfire.instrument_pydantic_ai()` emits the spans `invoke_agent <name>`, `chat …` and `execute_tool <name>`. Give each agent a `name=`.
- These spans should nest under our manual `research run` span through OpenTelemetry context, but the docs do not show it. **Verify this in PR 2**, and also verify that the context carries into tasks started with `asyncio.gather`.

*(integrations/logfire/)*

**Recording Steps in the database.** Options, simplest first:
- `result.all_messages()` after the run.
- `agent.iter()`, which yields one node per step, for a live row per Step.
- `Hooks` (before/after each model request and tool call), for a row per tool call.
- An event stream handler.

*(message-history/, agent docs, hooks/)*

**How the three Architectures map onto Pydantic AI:**

| Architecture | Shape in Pydantic AI |
|---|---|
| Single-agent loop | One agent with a search tool. Its built-in loop (model → tools → model) runs until the structured Report. Cap it with `UsageLimits` and `timeout`. |
| Planner + parallel workers | Programmatic hand-off. A planner agent returns a Plan, `asyncio.gather(worker.run(...))` runs one worker per sub-question, and a synthesizer returns the Report. Throttle with `Agent(max_concurrency=N)`. |
| Reflection / critique | A writer and critic loop, or an `output_validator` that raises `ModelRetry`. |

*(guides/multi-agent-applications/; graph docs)*

**Testing.**
- Set `models.ALLOW_MODEL_REQUESTS = False` so no real model is called.
- Use `with agent.override(model=TestModel()):` to swap in a test model.
- `FunctionModel(fn)` scripts exact responses.
- `capture_run_messages()` captures the messages for assertions.

*(guides/testing/)*

**Inside FastAPI background tasks.**
- Call `await agent.run()` from an async background task. Never call `run_sync()` inside a running event loop.
- Create the httpx client and the database pool in the app lifespan, and pass them in through `deps`.

*(agent docs)*

## OpenRouter limits (open decision #6: models)

- Free (`:free`) models allow **20 requests a minute**, and **50 requests a day** with less than $10 of purchased credit. With at least $10 of credit, the daily limit is 1,000. Status 429 means rate limited, and 402 means out of credit. *(https://openrouter.ai/docs/api/reference/limits)*
- Free models come and go. Make the model ID configurable, and check that the chosen model supports tool calling and structured output before you rely on it.

## Tavily

- The free plan has **1,000 API credits a month**. A basic search costs 1 credit and an advanced search costs 2. Development keys allow 100 requests a minute. *(https://docs.tavily.com/documentation/api-credits; https://docs.tavily.com/documentation/rate-limits)*

## Not verified

- That Pydantic AI spans nest under a manual parent span, and that the context carries into `asyncio.gather` tasks.
- Whether sharing one `RunUsage` across concurrent runs is safe. The docs show it only for sequential and delegated runs.
- The full parameter list and return shape of `tavily_search_tool`.
