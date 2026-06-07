# Role Template Creation Rules

When adding a new agent role to the template library, follow these rules. They were derived from a static review that caught 7 violations across 7 templates in a single pass.

## Structural Rules

| Rule | Requirement | Anti-Pattern |
|---|---|---|
| **Goal** | ONE sentence. Use em-dash or colon to join ideas. | "Do X. Also do Y." — split into two sentences. |
| **Steps** | 2-5 items, each starts with a verb. One action per step. | "Understand the problem and research" — two actions, split into two steps. |
| **Exit** | ≥3 verifiable criteria. Must be checkbox-able (falsifiable). | "Make it better" — impossible to verify. |
| **Never** | ≥3 specific red lines. Actionable prohibitions. | "Don't be bad at this" — too vague to enforce. |
| **Length** | ≤40 lines total. Sub-50 target for context efficiency. | 60+ lines of verbose explanation — subagents don't need a textbook. |

## Field Checklist

```
# <Name> Agent Template

## Role
<one word, lowercase>

## Goal
<ONE sentence — use — or : to connect ideas, not periods>

## When to Use
- <trigger 1>
- <trigger 2>
- <trigger 3>

## Steps
1. <verb-first action>
2. <verb-first action>
3. <verb-first action>

## Exit Criteria
- [ ] <verifiable criterion 1>
- [ ] <verifiable criterion 2>
- [ ] <verifiable criterion 3>

## Never Do
- <specific red line 1>
- <specific red line 2>
- <specific red line 3>
```

## Review Checklist

After writing a new template, verify:
- [ ] Goal is ONE sentence (no periods mid-goal)
- [ ] Steps are verb-first, one action each
- [ ] Exit criteria are falsifiable (can definitively say PASS/FAIL)
- [ ] Never Do items are specific enough to enforce
- [ ] Total file is ≤40 lines
- [ ] No contradictions with existing templates (e.g., implementer's Never says "don't test" while reviewer says "must have tests")
