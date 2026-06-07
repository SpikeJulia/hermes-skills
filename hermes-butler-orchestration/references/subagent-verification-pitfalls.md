# Subagent Trust & Verification Pitfalls

Lessons from hermes-ui development and other projects where subagent self-reports were unreliable.

## NEVER trust subagent "tests passed" claims

Subagents will report "✅ all tests passed" but their "tests" are often:
- `curl` API calls (not browser interactions)
- `vue-tsc --noEmit` (only checks types, not behavior)
- `vite build` (only checks compilation, not UI rendering)

These are COMPILE-TIME checks, not RUNTIME checks. A UI can pass all three of these and still have:
- Buttons that do nothing
- Chat that doesn't send messages
- Model selectors showing fake data
- Delete buttons that don't delete

## Real verification means:

1. **Browser screenshots** — take actual screenshots of the UI state after actions
2. **Click the buttons** — don't just check they exist; click them and verify effect
3. **Send real messages** — type text, press Enter, wait for AI response
4. **Check console errors** — browser_console after every interaction
5. **Verify data sources** — if UI shows model names, verify against config.yaml; if token counts, verify against API

## Patterns that indicate subagent failure:

- "✅ All 9 tests passed" but user says chat doesn't work
- "✅ Model selector works" but showing hardcoded "GPT-4" instead of real models
- "✅ Build succeeded" but page is blank in browser
- "✅ Delete works" but user has to refresh page

## Hermes-UI Case Study (2026-05-22)

Subagent reported all tests passing, but actual state:
- Chat didn't respond → Socket.IO field name mismatch (`token` vs `text`)
- Every session labeled "gpt-4" → hardcoded default, never read from config
- Token counter "200k" → completely fabricated, no data source
- Paperclip icon → decorative, no upload function
- Model list → provider key names instead of actual model names from config.yaml

Root causes found by butler (NOT subagent):
1. Backend emits `{ text: token }`, frontend expects `{ token: string }` → silent data loss
2. `settings.ts: const model = ref('gpt-4')` + `sessions.ts: model: data.model || 'gpt-4'` → hardcoded in TWO places
3. Model list read `auth.json` credential_pool keys, not `config.yaml` model names

## Action rule

After EVERY subagent dispatch that claims "fixed" or "verified":
1. Take a browser screenshot
2. Verify ONE core interaction (send message, click button, etc.)
3. If subagent fixed N things, spot-check at least 3 in browser

## The Golden Rule

**Subagent summaries are SELF-REPORTS, not verified facts.** The delegate_task doc warns about external side-effects (HTTP, file writes), but the same applies to TESTING claims. A subagent that claims "all 9 tests passed" may have:
- Tested the wrong thing (checked CSS class exists but didn't open browser)
- Ran API tests that pass while the UI is broken
- Verified TypeScript compiles but never checked if chat actually sends

## Critical Verification Checklist (After Subagent UI Work)

These MUST be verified by the butler before presenting to user:

1. **Chat send flow**: Type message, press Enter, verify AI responds with streaming. Socket.IO handlers are #1 thing subagents silently drop during refactors.
2. **Model switching**: Click model selector, switch model, verify label updates. Check both chatStore.model AND settingsStore.model.
3. **Session CRUD**: Create, switch, and DELETE sessions. Verify deletion reflects immediately without page refresh.
4. **Settings save**: Change setting, save, reload, verify it persisted.
5. **Browser rendering**: Open page in browser. CSS class in built bundle ≠ visible in browser.

## Red Flags in Subagent Summaries

- "CSS class found in built bundle" → NOT verified. Open browser.
- "API returns 200" → NOT verified for UI. Test full user flow.
- "Socket.IO requires client-side test; API works end-to-end" → Subagent admitting it didn't test client side.
- "Hit tool-call limit but changes applied" → Was cut off mid-work, likely unverified.

## When to Distrust

- Subagent hit max_iterations (50 calls) — cut off mid-work
- Subagent did major refactor/redesign — high risk of silent breakage
- Test section is vague without specific steps
- Verification took <10% of total work time
