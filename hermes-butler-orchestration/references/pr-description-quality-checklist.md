# PR Description Quality Checklist

When preparing a PR for the hermes-web-ui upstream (EKKOLearnAI/hermes-web-ui),
the PR description body should include these sections. A well-structured PR
description reduces back-and-forth with the maintainer (ekko) and increases the
chance of a clean merge.

## Sections

### Problem
One paragraph describing the user-visible symptom. Keep it concrete — what did
the user type, what did they see, what did they expect?

### Root Cause
Trace the bug to its origin — include a `git blame` reference (commit SHA,
author, date) showing when and why the problematic code was introduced. If the
code was a reasonable design at the time (e.g. written before a feature existed
that later conflicted with it), say so explicitly. This signals to the
maintainer "I understand your original intent; the landscape changed."

Example format:
```
`parseSessionCommand()` (introduced in `48dcaee6` #743, 2026-05-15) falls back
to `{ name: 'status', ... }` when a slash command is not in `COMMAND_ALIASES`.
This was a reasonable design at the time — the initial alias table had only 9
bridge commands, and CLI-side skill triggers like `/neat` did not exist yet.
```

### Fix
Explain the change at the *mechanism* level, not just "changed line X to Y."
Include:
- What the new behavior is
- How each caller is affected (line references)
- What explicitly does NOT change (preserved behavior)

### Dead Code Notes
If the fix makes a branch unreachable, note it. Say whether it's kept for
defense-in-depth (and can be removed in a future PR) or intentionally deleted.

### Test Plan
- New test file(s) and what they cover
- Full suite results (file count / test count / failures)
- harness:check result

### Files Changed
A compact table:

| File | Δ |
|------|-----|
| `path/to/file.ts` | +N/-M |
