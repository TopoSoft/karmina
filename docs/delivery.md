# Delivery and acceptance

A local preproduction vertical slice is implemented: persistent projects, six
specialist role worksheets, revision history, approval gates, and JSON production
packs. See README.md and agents.md for executable scope and runtime limitations.
The milestones below remain the broader film-production roadmap. Asset upload,
live agents, rendering, and SaaS readiness are not complete.

## 1. Local studio skeleton

Choose and document a maintainable stack. Implement project creation, production
mode, localized workspace, reference assets, character sheets, and ordered shots.
Use explicitly labelled fixtures before a provider is connected.

Acceptance: browser checks create and reopen projects in both modes, preserve shot
ordering, and verify English, Latvian, and Russian UI. Authorization tests prove
that one tenant cannot access another tenant's records or media.

## 2. Controlled generation

Evaluate providers, obtain explicit paid-service approval where needed, agree on
secret storage, and implement one adapter with durable asynchronous jobs.

Acceptance: unit/integration tests cover duplicate submissions, concurrent budget
reservations, timeouts, reconciliation, failures, cancellation, and callbacks.
Run a real generation separately from fixture tests and report its actual cost.

## 3. Complete short-film workflow

Implement take selection, a basic timeline, audio, captions, review, and export.

Acceptance: produce a 15–30 second MP4 with at least three shots and a recurring
character for each production mode. Probe output duration and codecs, play the
export, and replace one shot while verifying other selected takes are unchanged.
Have the artist-director assess style fidelity and continuity independently of
technical test results. Record quality limitations rather than hiding them.

## 4. External customer readiness

Implement and test workspace invitations, permission boundaries, billing controls,
retention/deletion, operational monitoring, backups, and restore procedures.
Review provider rights and data handling before real client assets are uploaded.

Acceptance: independent security checks, cross-tenant tests, restore exercise,
usage reconciliation, and a complete client review/export workflow. Production
deployment remains subject to explicit authorization.

## Evidence discipline

Record executed commands and results for each implementation milestone. A mock
test does not prove provider compatibility. A successful render does not prove
creative quality. A committed branch does not mean a deployed platform.
