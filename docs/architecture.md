# Proposed architecture

This is a design baseline, not an implemented or deployed system. Technology and
model providers have not been selected. Evaluate current APIs, commercial rights,
data retention, regional availability, and pricing before selection.

## Components

- **Web studio:** localized project workspace, storyboard editor, take comparison,
  review, and basic timeline.
- **Application API:** identity integration, tenant authorization, projects,
  revisions, signed asset access, and budget approvals.
- **Relational database:** authoritative project metadata, immutable revisions,
  job state, permissions, approvals, and usage ledger.
- **Private object storage:** original drawings, reference images, generated
  media, audio, and exports. Never store binary media in database rows.
- **Job queue and workers:** provider submissions, reconciliation, media probing,
  transcoding, and export rendering outside request lifetimes.
- **Provider adapters:** separate text, image, video, speech, and music capabilities.
  Do not assume providers support identical controls or output formats.

Start as a modular application with separate worker processes, not a fleet of
microservices. Keep rendering workloads independent from interactive API latency.

## Core records

Every tenant-owned record includes tenant_id, an opaque identifier, timestamps,
and a creator where applicable. Parent-child references must preserve tenant scope.

| Record | Responsibility |
| --- | --- |
| Tenant / Membership | Workspace and owner, editor, or reviewer role |
| Project | Production mode, brief, settings, and lifecycle |
| Asset / RightsDeclaration | Private object metadata, source, and permission record |
| Character / CharacterRevision | Identity, style, voice, and reference assets |
| ScriptRevision | Immutable script snapshot with parent revision |
| Scene / Shot / ShotRevision | Ordering, duration, camera, references, and instructions |
| GenerationJob / Take | Execution state and candidate media for a shot revision |
| BudgetApproval / UsageEntry | Authorized limit, reserved spend, and reconciled usage |
| CutRevision | Ordered selected takes, audio tracks, and captions |
| Review / Comment / Approval | Feedback attached to an exact revision |
| ExportJob / Export | Versioned render and downloadable output |

Changing a shot creates a new revision. It does not mutate already approved cuts.
An export references an immutable cut and pinned media versions.

## Generation lifecycle

queued → submitting → running → succeeded | failed | cancelled

Submission timeouts with unknown provider outcome enter reconciliation rather
than automatic resubmission. Cancellation may stop local work without reversing
provider charges. Preserve provider job IDs and usage evidence.

Before enqueueing, atomically reserve against an approved tenant/project budget.
Require idempotency keys, worker leases, bounded retries, and duplicate webhook
handling. Reconcile reservations and actual costs without double charging.
Changing prompts, references, or provider parameters requires a new request.

## Security and media boundaries

- Derive tenant scope from authenticated membership, not trusted request fields.
- Authorize every asset read, job lookup, export, and review action.
- Use short-lived signed media access and private storage objects.
- Verify provider callbacks and bind them to the stored job and tenant.
- Validate upload size, signatures, dimensions, and duration. Treat originals as
  untrusted. Sandbox media processing with resource limits.
- Redact credentials and private media URLs from logs.
- Keep provider secrets server-side. Secret storage is an explicit user decision.
- Deletion must cover derivatives and document any provider retention limitation.

## Provider selection gate

Use the same original character references and three-shot scripts to evaluate
animation and photorealistic candidates. Measure identity drift, editability,
latency, failed-job charges, cost per accepted second, and export compatibility.
No provider integration should imply guaranteed cinematic quality or zero drift.
