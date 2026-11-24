# Cinematic studio acceptance

Validated locally on November 24, 2026.

## Implemented

- Cinematic landing with original artwork for animation and photorealistic modes.
- Six crew-role cards with detail dialogs.
- English, Latvian and Russian interface text and self-hosted licensed fonts.
- `/studio` workspace routing with preserved project and revision workflows.

## Executed checks

- `python3 -m unittest discover -s tests -v`: 10 tests passed.
- `node --check karmina/web/app.js` and `node --check karmina/web/i18n.js`: passed.
- `node --test tests/i18n.test.mjs`: 2 tests passed.
- `PYTHONPATH=. python3 tests/cinematic_acceptance.py`: passed artwork loading,
  mode switching, role dialog interaction, language switching, routing, saved
  project preservation, 390/768/1440 px overflow checks and no runtime/asset errors.
  Reduced-motion preference was emulated, but animation behavior was not asserted.
- `PYTHONPATH=. python3 tests/browser_acceptance.py`: passed both production modes,
  approval gates, revision persistence, JSON downloads, immutable approvals,
  three interface languages and mobile layout without page errors.

## Runtime boundary

This remains a local preproduction application. Crew roles provide editable
worksheets, not autonomous agents. ohAgent and paid providers are not connected.
No generated video, production deployment or multi-user authentication is claimed.
