# Karmina

An author-led production platform for animated films, photorealistic cinematic
stories, and video advertising. Artists remain authors and directors, with AI
assisting production rather than replacing creative control.

## Status

A working local preproduction application is available: persistent projects,
six specialized role definitions, editable versioned artifacts, director approval
gates, and production-pack export. The execution mode is explicitly **local
worksheets**, not autonomous AI. ohAgent is not connected and no media is generated.

## Run locally

Requires Python 3.12 or later. No runtime packages or credentials are needed.

```sh
python3 -m karmina.server
```

Open `http://127.0.0.1:8787`. Project data is stored in ignored
`data/studio.sqlite3`. Override with `--database PATH` and `--port PORT`.
The server binds to loopback only and serves a single local director workspace.
It is not a production server or a multi-user authentication system. Do not expose
it through a reverse proxy or upload sensitive client materials yet.

Create a project, open each role's worksheet, write or edit its content, save a
revision, and approve it to unlock the next role. All six approvals unlock a JSON
production pack, not a video export. Approved artifacts are immutable in this
iteration. New projects are required for changes to already approved stages.

## Validate

```sh
python3 -m unittest discover -s tests -v
node --check karmina/web/app.js
node --check karmina/web/i18n.js
node --test tests/i18n.test.mjs
# Optional: requires Playwright Python package and Chromium installed separately
PYTHONPATH=. python3 tests/browser_acceptance.py
PYTHONPATH=. python3 tests/cinematic_acceptance.py
```

See [agent runtime boundary](docs/agents.md) and
[validation evidence](docs/testing/agent-studio.md), and
[cinematic redesign acceptance](docs/testing/cinematic-studio.md).

## Production modes

- **Animation:** use original drawings, character references, and style guides.
- **Photorealistic cinema:** direct fictional characters, locations, lighting,
  performances, and continuity across shots.

Both modes share a production workflow:

Brief → story → script → storyboards → shots → sound → edit → review → export.

## Foundation documents

- [Product scope and first release](docs/product.md)
- [Architecture and domain boundaries](docs/architecture.md)
- [Delivery milestones and acceptance](docs/delivery.md)

## Development principles

Tenant isolation, private assets, explicit generation spending approval, immutable
creative revisions, and provider independence are baseline requirements. Interface
languages are English, Latvian, and Russian. Infrastructure and provider choices
remain proposals until evaluated. No paid activation or production deployment is
authorized by this repository.
