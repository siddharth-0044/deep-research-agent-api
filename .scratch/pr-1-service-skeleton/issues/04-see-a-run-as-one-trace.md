# 04: See a Run as one trace in Logfire

**What to build:** Each Run's work shows up in Logfire as one trace under its submit request.
- A named `research run` span contains each status change.
- Every status poll is its own small trace.
- Nothing is sent when no token is configured, so the tests send nothing.

**Blocked by:** 01, 03

**Status:** ready-for-agent

- [ ] With `LOGFIRE_TOKEN` set, a submitted Run appears as one trace. The trace holds the submit request, the insert, and a `research run` span that carries the run ID and contains each status update.
- [ ] Each status poll appears as a separate trace.
- [ ] Without a token, nothing is sent and the tests still pass.
- [ ] Someone checked by eye whether the submit request's span lasts as long as the Run, and the README records the answer. The spec asked for this check.
- [ ] The README explains how to view the traces in Logfire.
- [ ] The developer was taught the Run trace shape in front of the real trace, then quizzed, and explained it back. It is ticked in the spec.
