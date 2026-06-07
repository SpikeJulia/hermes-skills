# Dispatch Checklist — Task Delegation Quality Gate

The butler runs this checklist before dispatching any task. Must pass all items before execution.

---

## Step -1: Sync or Async? — The Blocking Decision

**This is the FIRST decision. Get it wrong and the user is blocked — or agent collaboration breaks.**

### Decision Tree

```
Does the task involve MULTIPLE agents that need to communicate?
  │
  ├─ YES → SYNC (delegate_task)
  │   Reason: P2P inbox + discussions require persistent agent sessions.
  │   Cron jobs are one-shot — they can't poll inbox or participate in discussions.
  │
  └─ NO (single agent, independent work)
       │
       ├─ Task takes > 2 minutes? → ASYNC (cronjob)
       │   3+ subagent rounds, multi-file ops, data analysis, multi-source research
       │
       └─ Task takes ≤ 2 minutes? → SYNC (delegate_task)
           One-file edit, single search, format fix, simple query
```

### Core Criterion: P2P Communication Need

| Factor | SYNC (delegate_task) | ASYNC (cronjob) |
|---|---|---|
| **Agent-to-agent P2P** | ✅ inbox polling + discussions work | ❌ one-shot, can't maintain session |
| **team-workspace status.json** | ✅ updates after each task | ✅ updates once at completion |
| **Butler real-time monitoring** | ✅ can check progress mid-task | ❌ fire-and-forget until completion |
| **User interaction** | ❌ blocked during execution | ✅ user can continue chatting |
| **Context inheritance** | ✅ inherits butler message context | ❌ starts fresh, prompt must be self-contained |
| **Result delivery** | ✅ immediate to butler | ✅ auto-delivers to chat on completion |

### Detailed Decision Rules

**MUST use SYNC (delegate_task) when:**
1. **Multi-agent collaboration needed.** Two or more agents need to message each other via P2P inbox, participate in discussions, or negotiate shared contracts. Cron jobs can't poll inbox or join discussions — they run once and exit.
2. **User said "wait for it".** User explicitly expects the result immediately, and blocking is acceptable.
3. **Next butler action depends on result.** Butler needs to inspect the output, run verification, then decide the next step.
4. **Task is interactive.** Subagent needs to ask clarifying questions (though rare — most tasks should be self-contained enough).

**MUST use ASYNC (cronjob) when:**
1. **Single agent, independent work.** No other agent depends on live communication with this one.
2. **Task time > 2 minutes.** 3+ subagent rounds, multi-file generation, data analysis, multi-source research compilation.
3. **User should not wait.** The task is a "do this and get back to me" type, not a "need this to continue" type.

**Butler's call (tiebreaker):**
- When both would work, prefer ASYNC. A non-blocked user is always better than a fast result.

### Async Dispatch Recipe

```python
# 1. Create one-shot cron job
cronjob(
    action='create',
    name='task-<slug>',
    schedule='now',
    repeat=1,
    deliver='origin',         # auto-delivers result back to current chat
    prompt="""<SELF-CONTAINED PROMPT — see requirements below>""",
    skills=['subagent-driven-development'],
    enabled_toolsets=['terminal', 'file'],  # match the role
)

# 2. Fire immediately (use the job_id from create response)
cronjob(action='run', job_id='<returned-id>')
```

### Async Prompt Requirements

Cron jobs start fresh — no conversation context. The prompt MUST be self-contained:

```
TASK: <what to do, specific file paths>
ROLE: <implementer/reviewer/researcher/...>
RULES: <Steps and Never Do from role template — inject directly>
FILES: <absolute paths>
OUTPUT: <deliverable description — what the user should see>
EXIT: <verifiable criteria>
```

### Butler Response After Async Dispatch

One line only:
```
已派后台执行 — <task-name> 🎀 完成后自动回复你~
```

### Common Pitfalls

1. **Using async for multi-agent tasks.** If agent A needs to message agent B, both must be alive simultaneously — cron jobs can't do this. This is the #1 reason sync still exists.
2. **Vague async prompts.** "Research X and write a report" will produce garbage because the cron session has no context. Inject the full role template rules.
3. **Forgetting to inject role template.** A cron job subagent without Steps/Never Do is an unsupervised agent — unpredictable.
4. **Async task depends on another async task.** Two independent cron jobs can't coordinate. Use sync team-workspace for tasks with dependencies.

---

## Step -0.5: Serial or Parallel? — The Multi-Task Dispatch Decision

**This step determines how to dispatch when there are 2+ tasks to run.**

### Decision Tree

```
How many tasks?
  │
  ├─ 1 task → skip this step, go to Step 0
  │
  └─ 2+ tasks
       │
       ├─ Do any tasks DEPEND on output from another?
       │   │
       │   ├─ YES → Identify dependency chains
       │   │   ├─ Group independent tasks → PARALLEL batch 1
       │   │   ├─ Wait for upstream → then dispatch dependent tasks
       │   │   └─ Continue until all done
       │   │
       │   └─ NO → All independent
       │        │
       │        ├─ Do any tasks touch the SAME file?
       │        │   ├─ YES → SERIAL (avoid merge conflicts)
       │        │   └─ NO → PARALLEL — dispatch all in one batch
       │        │
       │        └─ Default: PARALLEL. Serial is the exception.
       │
       └─ Max 6 concurrent (delegation.max_concurrent_children)
```

### The Default: Parallel

**If tasks are independent and touch different files, dispatch them together.** There is no reason to wait.

```python
# ✅ Parallel — one call, all tasks run simultaneously
delegate_task(tasks=[
    {"goal": "Test ChromaDB plugin",  "context": "...", "toolsets": ["terminal","file"]},
    {"goal": "Build wiki index",       "context": "...", "toolsets": ["terminal","file"]},
    {"goal": "Research Kimi API docs", "context": "...", "toolsets": ["web"]},
])
```

### Serial-Only Cases

```python
# ❌ Must be serial — Task B needs Task A's output file
# Dispatch A first, wait for result, then dispatch B with A's output path

# ❌ Must be serial — both tasks edit the same file
# Dispatch one at a time to avoid merge conflicts
```

### Dependency Chain Pattern

```
Tasks: A (build DB schema), B (write API), C (write tests), D (research docs)

Dependencies: A → B → C (B needs schema, C needs API)
Independent: D

Dispatch:
  Batch 1: [A, D]          ← parallel (A+D don't touch same files)
  Wait for A
  Batch 2: [B]             ← depends on A's output
  Wait for B
  Batch 3: [C]             ← depends on B's output
```

### Common Pitfalls

1. **Serial-by-default.** "I'll just dispatch one at a time" — this wastes the user's time. Always ask: can these run together?

2. **False dependency.** "Task B mentions the same project as Task A" is NOT a dependency. Only actual data-flow dependencies (B reads A's output file, B needs A's generated API) count.

3. **Over-serialization.** "Let me verify A before starting B" — verification happens AFTER all dispatches return. Don't serialize for verification.

4. **Ignoring file conflicts.** Two tasks editing `config.yaml` simultaneously WILL conflict. Serialize these.

5. **Mixing sync + async in thinking.** All tasks in a `delegate_task(tasks=[...])` batch are synchronous. If some need async, split them out into separate cronjob calls.

---

### 0.1 Match Against Known Roles

| Task Type | Role | Template |
|---|---|---|
| Write code, fix bugs, refactor | implementer | `implementer-agent.md` |
| Review code, check spec compliance | reviewer | `reviewer-agent.md` |
| Find information, verify facts | researcher | `researcher-agent.md` |
| Diagnose bugs, find root cause | debugger | `debugger-agent.md` |
| Create plans, designs (no code) | planner | `planner-agent.md` |
| Write docs, README, API refs | documenter | `documenter-agent.md` |
| Analyze data, stats, viz | data-analyst | `data-analyst-agent.md` |
| Test strategy, cases, execution | tester | `tester-agent.md` |
| Security audit, injection, secrets | security-reviewer | `security-reviewer-agent.md` |

**Role selection test:** Would this role's "Never Do" rules be violated by the task? If yes, wrong role.

### 0.2 No Match → Create On-Demand Role

If no role matches, generate a temporary role using this framework BEFORE dispatching:

```
Role: <one-word name>
Goal: <one sentence — what this role believes>
Steps:
1. <concrete step 1>
2. <concrete step 2>
3. <concrete step 3>
Exit:
- [ ] <verifiable criterion 1>
- [ ] <verifiable criterion 2>
Never:
- <red line 1>
- <red line 2>
- <red line 3>
```

Then dispatch with the generated role injected into context. After the task completes, if the role proved useful and reusable, save it as a permanent template.

---

## Step 1: Dispatch Assembly — Required Elements

Every dispatched context MUST contain these 5 sections:

### 1.1 Specific Task Description
```
TASK: <one-line summary>
WHAT: <specific what to do, file paths, constraints>
WHY: <why this matters, what depends on it>
```

### 1.2 Role Rules
Copy the Steps and Never Do from the selected role template. Do NOT make the subagent load the file — inject directly.

```
IMPLEMENTER RULES:
1. Write failing test first → verify fail
2. Write minimal code → verify pass
3. Full test suite → no regressions
4. Commit

## ⛔ Halt-Before-Commit Gate

**Any git commit/push/PR must be preceded by a halt.** Present the diff summary
(files changed, lines +/-) and wait for explicit user approval. Never commit
first and report after. Never `git push` without showing what will be pushed.
Even trivial-looking fixes must pass this gate.

This rule was reinforced 2026-06-06 when the user halted a commit mid-flow:
"为什么不经过我运行就commit." It overrides any default efficiency-first
behavior.

NEVER: skip failing test, add unspec'd features,
       leave debug prints, proceed with failing tests
```

### 1.3 Environment
```
PROJECT: <path or repo name>
RELEVANT FILES: <file paths the subagent needs to know>
EXISTING PATTERNS: <conventions or patterns to follow>
```

### 1.4 Toolsets
Match to task type. Default: `['terminal', 'file']`.

| Role | Default Toolsets | When to add |
|---|---|---|
| implementer | terminal, file | Add `web` if needs API docs |
| reviewer | file | Add `terminal` if needs to run tests |
| researcher | web, file | Add `terminal` if needs codebase search |
| debugger | terminal, file | Add `web` if needs external bug reports |
| planner | file | Add `web` if needs research for design |
| documenter | file | Add `terminal` if needs to verify code references |
| data-analyst | terminal, file | Add `web` if needs external datasets |
| tester | terminal, file | Add `web` if needs external test data |
| security-reviewer | file, search | Add `terminal` if needs to run security scans |

**Rule:** Never give more toolsets than needed. Every unnecessary tool is a distraction.

### 1.5 Exit Criteria
Exactly 3-4 checkable items the subagent must complete.

```
EXIT CRITERIA:
- [ ] Item 1 (specific and verifiable)
- [ ] Item 2
- [ ] Item 3
```

---

## Step 2: Pre-Flight Quality Checks

Before hitting dispatch, verify:

- [ ] **Goal is self-contained.** A subagent reading only the `goal` field understands what to do
- [ ] **Context has all 5 sections.** Don't skip any
- [ ] **File paths are absolute or clearly relative** to the working directory
- [ ] **No contradictory instructions.** "Be thorough" + "Be quick" in same context = confused subagent
- [ ] **Toolsets match.** terminal+file for code, web for research, etc.
- [ ] **Exit criteria are falsifiable.** "Make it better" is not a criterion. "All tests pass" is.

---

## Step 3: Quality Anti-Patterns

| Anti-Pattern | Example | Fix |
||---|---|---|
| Cross-agent field drift | Backend emits `{ text }`, frontend destructures `data.token` | Grep both sides; align field names exactly |
| Fake model names | UI shows provider key "Deepseek" instead of "deepseek-v4-flash" | Read config.yaml NOT just auth.json |
| ACP on unsupported version | `delegate_task(acp_command='claude')` with Claude Code v2.1.x | Omit acp_command; use built-in transport ||---|---|---|
| Vague task | "Fix the login bug" | "Login returns 500 when email field is empty. Fix in src/auth/login.py:42 to return 400 with validation message." |
| Missing context | No file paths given | Always include at least one relevant file path |
| Conflicting toolsets | researcher gets `terminal` but no `web` | Researcher MUST have `web` |
| Over-engineered goal | 200-word goal that tells the subagent HOW to think | Goal = what, not how. Rules = how. |
| No exit criteria | Subagent decides when it's "done enough" | Always define concrete exit criteria |
| Irrelevant rules | Reviewer gets TDD rules | Only inject rules relevant to the role |

---

## Step 4: Post-Dispatch Verification (Butler Spot-Check)

After subagent returns, the butler performs a spot-check. This is separate from the mandatory tester subagent dispatch (see butler-agent.md Steps 5–6).

**Web UI projects — NON-NEGOTIABLE rules:**
- MUST test with browser_navigate + browser_click + browser_type + browser_vision
- MUST interactively click every button, type input, verify navigation, check data display
- MUST NOT rely solely on API curl — curl validates the backend, not the UX
- If the user says "测仔细一点" or "截图来验证", you failed to test properly the first time

**Data integrity — NON-NEGOTIABLE rules:**
- Compare displayed data against the ACTUAL source of truth (config files, databases, live APIs)
- NEVER accept hardcoded/fake data in the UI when real config exists
- If model names, labels, or identifiers are shown, verify they match actual configuration
- Example pitfall: displaying provider key names ("Deepseek") instead of real model names ("deepseek-v4-flash") from config.yaml

- [ ] Check exit criteria were actually met (don't trust self-report)
- [ ] For code: run tests yourself to verify
- [ ] For research: spot-check one source
- [ ] For reviews: confirm every issue has file:line

**After spot-check, the tester dispatch is AUTOMATIC.** Do not ask the user whether to test — the tester subagent is dispatched immediately after all tasks complete. Testing is a mandatory step in the pipeline, not a user decision.

---

## Step 5: The 3-Fix Limit (Hard Stop Rule)

Every task has a maximum of 3 fix attempts. This applies to:
- Subagent task failures (dispatch → fail → re-dispatch → fail → re-dispatch → fail → STOP)
- Reviewer feedback loops (implement → review → fix → re-review → fix → re-review → STOP)
- Any retry cycle where a subagent is dispatched to fix a prior failure

### Definition

**3-fix limit**: Maximum 3 fix attempts. After the 3rd failure, escalate to the user. Never attempt a 4th time.

| Attempt | Outcome | Action |
|---|---|---|
| 1st | Failure | Re-dispatch with specific fix instructions |
| 2nd | Failure | Re-dispatch with more specific instructions, or switch approach |
| 3rd | Failure | **STOP — escalate to user** with: what was tried, what failed, and what you need from them |

### Why This Exists

- Prevents infinite retry loops that waste tokens and time
- Forces escalation before the butler's context is polluted by repeated failures
- Respects the user's time — if 3 attempts didn't work, the 4th probably won't either without human input

### Escalation Format

When escalating after the 3-fix limit:

```
Task: [what was being attempted]
Attempts: 3
Failures:
  1. [what happened on 1st attempt]
  2. [what happened on 2nd attempt]
  3. [what happened on 3rd attempt]
What I need from you: [specific decision or information]
```

### Anti-Patterns

| Anti-Pattern | Why It's Wrong |
|---|---|
| "Let me try one more time" on the 4th attempt | Violates the limit; if 3 didn't work, you need human input |
| Re-dispatching with the same instructions | Each retry must have materially different context or approach |
| Hiding failures in summary | Report all 3 attempts clearly when escalating |
| Counting review rounds separately from fix attempts | Every dispatch to fix a problem counts as one fix attempt |

---

## Quick Reference Card

```
DISPATCH = {
    goal:       "One-sentence task summary",
    context:    "TASK + WHY + RULES + ENV + TOOLS + EXIT",
    toolsets:   [minimal set matching role],
}

// Multi-task: use tasks array for parallel dispatch
DISPATCH_BATCH = {
    tasks: [
        {goal: "...", context: "...", toolsets: [...]},
        {goal: "...", context: "...", toolsets: [...]},
    ]
}
// Only serialize when: tasks have data dependencies OR touch same files.
```

**Minimum viable context:**
``` 
TASK: [what]
ROLE: implementer
STEPS: 1. test → fail, 2. code → pass, 3. suite → pass, 4. commit
NEVER: skip test, add scope, leave debug
FILES: [path(s)]
EXIT: - [ ] all tests pass, - [ ] no regressions, - [ ] committed
```
*Note: ROLE+STEPS+NEVER together form the Rules section (§2.2). For tasks beyond a single-file edit, use the full 5-section format.*
