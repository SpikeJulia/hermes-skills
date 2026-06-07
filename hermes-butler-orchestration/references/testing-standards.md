# Testing Standards — Mandatory Post-Task Testing

> Referenced by: `butler-agent.md` Step 5-6, `tester-agent.md`

## The Rule

**After ALL dispatched subagents complete, the butler MUST dispatch a dedicated tester subagent for full-coverage testing.** Never skip. Never let the implementer test their own work.

## Full-Coverage Definition

| Category | What to Test | Minimum |
|----------|-------------|---------|
| **Functional** | Every modified command/function/endpoint | Run all with expected inputs |
| **Edge Cases** | Empty input, null, boundary values, unicode | At least 3 edge cases per modified file |
| **Integration** | Cross-file/module interaction, P2P messaging | Test every new interface |
| **Regression** | Existing behavior unchanged | Run existing test suite; spot-check 3 unchanged features |
| **Config/Syntax** | YAML/JSON validity, bash -n, python -c compile | Every modified config/script file |

## Tester Subagent Dispatch

### Context to Provide
```
- ALL modified file paths (from git diff --name-only)
- Original task specs/goals from the dispatch
- Expected behavior for each change
- Any known pitfalls or edge cases mentioned during development
- toolsets: ["terminal", "file"]
```

### Tester Output Format
```
## Test Report

| # | File | Test | Expected | Actual | Status |
|---|------|------|----------|--------|--------|
| 1 | main.sh | health cmd syntax | exit 0 | exit 0 | PASS |
| 2 | main.sh | health output format | "Result: X PASS" | "Result: 6 PASS" | PASS |
...

Result: X PASS, Y FAIL, Z WARN
```

## Butler's Review Checklist

After receiving the tester's report, the butler MUST:

- [ ] Read EVERY line of the test report (not just the pass/fail count)
- [ ] For each FAIL: assess severity (critical/important/minor)
- [ ] If any critical FAIL → fix immediately, then re-dispatch tester
- [ ] If coverage gaps found → re-dispatch tester with specific gap instructions
- [ ] If all critical/important pass → proceed to Present
- [ ] Include test report alongside modification report in final output

## Common Pitfalls

| Pitfall | Consequence | Prevention |
|---------|-------------|------------|
| "Changes are small, skip testing" | Undetected regression | ALWAYS test, regardless of size |
| "Subagent said it passed" | Implementer overconfidence | Independent tester, never same agent |
| "No time, user is waiting" | Wasted time on rework | Testing catches problems early |
| "I spot-checked 2 things" | Missed edge cases | Full coverage, not sampling |
| Presenting before test report arrives | User finds bugs later | Never present without test report |

## Real Session Lessons

**2026-05-20 P2/P3 session:** Butler presented P2 and P3 results twice without dispatching tester subagent. User had to ask "P1修复的都验证测试过了吗" and "P3测试了吗" — each time requiring a corrective tester dispatch. Root cause: no mandatory testing step in the butler cycle. Fixed by adding Steps 5-6 to butler-agent.md.
