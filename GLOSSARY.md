# Deep Research Agent API

A service that takes one research question, researches it on the web in the background, and returns a cited report.

## Language

**Run**:
One execution of one Architecture against one query, with its Plan, Steps, Sources and Report.
_Avoid_: job, ticket (a "ticket" is a `/to-tickets` work item)

**Architecture**:
One of the two structurally different agent designs that can carry out a Run.
_Avoid_: agent (one Architecture may use several agents)

**Plan**:
The research approach worked out from the query before gathering. It can be revised mid-Run; that revision is a re-plan.

**Step**:
One recorded unit of work in a Run: planning, a search or other tool call, a re-plan, or synthesis.

**Source**:
A web result found during a Run that the Report can cite.

**Report**:
The final structured research output of a Run, with citations to its Sources.

**Comparison**:
The same query run on both Architectures, plus a stored judgment of which produced the better research.
