# Agent studio validation evidence

Date: 2026-11-24. Journeys derived from the request to build a film studio using
specialized domain agents, following ohAgent's runtime separation.

## TDD checkpoints

- RED: `python3 -m unittest discover -s tests -v` failed with
  `ModuleNotFoundError: No module named 'karmina'` before domain implementation.
  Checkpoint `3d758d4` records the intended missing module/API tests.
- GREEN: the same command passed six domain tests plus two real HTTP tests after
  implementation, checkpoint `6ee79a9`.
- Expanded acceptance adds concurrent writes, localized artifact templates, input
  bounds, lineage, translation completeness, and real browser workflows.

## Requirement-to-check map

| Guarantee | Executed check | Observed result |
| --- | --- | --- |
| Projects persist across Studio instances | `tests/test_studio.py` | PASS |
| Tenant-scoped reads and writes reject another tenant | `tests/test_studio.py` | PASS |
| Roles require preceding approval | Domain, HTTP, and Chromium workflows | PASS |
| Immutable approved artifacts and retained draft history | Domain and Chromium workflows | PASS |
| Concurrent writes have exactly one winner | `test_concurrent_updates_have_one_winner` | PASS |
| Oversized/empty/invalid inputs fail without mutation | Domain and HTTP tests | PASS |
| Artifact input IDs preserve revision lineage | `test_artifact_limits_lineage_and_localized_worksheets` | PASS |
| No false live-runtime fallback | Domain and HTTP tests selecting `ohagent` | 503, no project mutation |
| Cross-origin and invalid Host requests fail | `tests/test_http.py` | 403 |
| Both modes complete local preproduction | Actual HTTP and Chromium workflows | PASS |
| All RU/EN/LV interface keys exist | `node --test tests/i18n.test.mjs` | PASS, 2 tests |
| Revised text survives page reload | Chromium browser acceptance | PASS |
| Production-pack download is valid JSON, not claimed video | Chromium download and JSON parse | PASS, 6 artifacts, media_generated=false |
| Mobile workspace has no horizontal overflow | Chromium at 390px viewport | PASS |
| No uncaught browser errors | Chromium pageerror listener | PASS |

## Commands

```sh
python3 -m unittest discover -s tests -v
node --check karmina/web/app.js
node --check karmina/web/i18n.js
node --test tests/i18n.test.mjs
PYTHONPATH=. python3 tests/browser_acceptance.py
git diff --check
```

The expanded Python suite passed 10 tests. Browser acceptance ran against a real
loopback HTTP server, temporary database, and headless Chromium. It created projects
in both modes and completed all six approvals, including downloaded artifact packs.
All temporary databases and test servers are cleaned up by the tests.

## Coverage

Python standard-library `trace --count --summary --missing` running the unittest
suite reported line coverage of **100% for karmina.studio** and **84% for
karmina.server**. Trace output was generated in a temporary directory and removed.
These are line-execution metrics, not branch coverage or proof of security.
JavaScript instrumentation coverage was not measured. UI behavior was checked
through Playwright, not only static HTML inspection.

## Independent check path and limits

Direct domain tests, actual HTTP requests, and actual browser interaction exercise
separate acceptance paths. No independent human creative assessment was performed.
There are no model executions, ohAgent cinema sessions, uploaded original drawings,
rendered scenes, generated audio, MP4 exports, production deployment, or multi-user
authentication in this slice. Those capabilities are not certified by these tests.
