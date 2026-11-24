# Karmina engineering instructions

Read README.md and docs/ before implementation. Keep documentation aligned with
working behavior and distinguish implemented features from proposals.

- Work on task branches, never directly on main.
- Preserve animation and photorealistic workflows as first-class production modes.
- Scope tenant-owned records, jobs, assets, and review access by tenant_id.
- Never expose provider credentials to browsers or commit real credentials.
- Ask for the preferred secret storage before introducing secrets.
- Keep all user-facing text localizable in English, Latvian, and Russian.
- Paid generation requires a server-side approved spending limit.
- Do not claim generated video is working when only mocks or fixtures exist.
- Require tests for authorization, generation retries, cost accounting, and revision
  lineage before connecting a paid provider.
- No production deployments or paid service activation without explicit approval.
- Include `AI-assisted: Jcode` in each AI-assisted commit.
