# Parent Spot-Check Recipe — Verifying Subagent Research Before Adopting

> **Captured:** 2026-06-04 from a real failure mode: a `researcher` subagent reported "SOUL.md is a write-only decorative surface, not consumed by the agent", the parent adopted it, the user corrected it ("应该改的是你吧，既然 soul 优先级高，那肯定要把人格相关设置放到 soul.md 里面去吧"), and re-investigation found `agent.prompt_builder.load_soul_md()` + the slot #1 identity assembly path that the subagent never grepped. The parent's failure was accepting the report without independent spot-check.
>
> **Trigger:** when the parent agent is about to adopt a subagent's research conclusion as a basis for action. Especially when the conclusion will lead to a code change, config change, or user-facing claim.

## TL;DR

A subagent's "I researched X and found Y" is a **claim**, not a fact. Before you (the parent) act on it — re-run at least one of the subagent's key greps/commands yourself, and ideally one more from a different angle. Five minutes of spot-check prevents hours of rollback + lost trust.

**Rule of thumb**: if the subagent's conclusion will lead to a destructive action (file edit, config change, dependency update, user-facing claim of the form "X doesn't work"), you **must** spot-check. If it's just background reading for your next response, accepting without spot-check is fine.

---

## Failure #2 (same day, afternoon): the "this is a bug" trap

Subagent AND parent both declared "load_soul_md() is not profile-aware, this is a bug" after only reading `agent/prompt_builder.py:load_soul_md()`. The user pushed back: "Hermes 官方不应该踩吧，这个是个大bug，我建议你再看看官方文档". Re-reading of `website/docs/user-guide/profiles.md` and `hermes_cli/main.py:_apply_profile_override` revealed the bridge lives in the CLI entry point — it pre-parses `-p` / `--profile` and sets `HERMES_HOME` BEFORE any module is imported, which makes `get_hermes_home()` return the profile-specific path and makes `load_soul_md()` work correctly without any profile-aware code in the function itself.

**Lesson (carried over from Failure #1)**: for "is this code path wired up?" questions, grep BOTH the entry-point/initialization layer AND the runtime layer. Either alone is incomplete.

**Even stronger lesson (new)**: mature projects document their mechanisms. Before declaring "this is a bug", read the official docs. The docs often explain the WHY that the code alone doesn't reveal. If you can't articulate the design rationale from the docs, you don't yet understand the system well enough to call its behavior a bug.

**Live test as final defense**: if a claim involves env vars, config files, or CLI flags, simulate it before reporting to the user. A 5-second test (`HERMES_HOME=... python3 -c "..."`) often resolves a 30-minute "is this a bug" debate.

---

## 1. When to spot-check (the trigger conditions)

**Mandatory spot-check** before adopting a subagent's conclusion when ANY of these apply:

- The conclusion contradicts something the user has said or implied
- The conclusion leads to a code/config change (not just information)
- The conclusion is a negative claim ("X doesn't work", "X is unused", "X is a write-only surface")
- The subagent's "Exit Criteria" weren't all checked (they often run out of iterations)
- The subagent reported an API/tool/feature as missing or non-functional
- The conclusion affects the user's primary agent setup (persona, model config, memory)
- The conclusion will be quoted in user-facing output (a doc, a commit message, a skill update)

**Skip spot-check** when:
- The subagent's conclusion is just background context for your next response
- The subagent reported an obvious, easily-verifiable factual thing (e.g. "the file is 100 lines")
- The subagent's task is the kind where their self-report is the deliverable (e.g. "write a doc with section X" — read the doc, that's the verification)

## 2. The 5-minute spot-check recipe

Pick the **single most load-bearing claim** in the subagent's report — usually the one whose falsity would invalidate the whole conclusion. Re-verify it yourself with one of these patterns:

### Pattern A: Re-run the subagent's key grep/command

```bash
# The subagent said "grep for load_soul_md in cli.py shows 0 hits → SOUL.md unused"
# You re-run a BROADER grep, in a different location:
grep -rn "load_soul_md\|SOUL\.md" ~/.hermes/hermes-agent/agent/ 2>/dev/null | head -20
# → finds agent/prompt_builder.py:1313 + agent/system_prompt.py:91
# → conclusion was wrong, the subagent looked in the wrong directory
```

**Why this works**: the subagent's grep usually has a too-narrow scope (one file, one dir, one keyword). Re-running with a broader scope in 30 seconds catches it.

### Pattern B: Trace one specific code path end-to-end

```bash
# The subagent said "the controller doesn't import any persona-loading code → no bridge"
# You trace the actual path: what calls the controller? Where is the persona used?
grep -rn "personality\|persona\|system_prompt" packages/server/src/ | head -20
# Look for: who calls this server? Does the server feed SOUL.md to the LLM? Or does
# a separate Python agent process that the server talks to do that?
```

**Why this works**: code-archaeology questions are about *integration*, not *file contents*. The subagent reads individual files; you trace the wires between them.

### Pattern C: Cross-validate via a second independent source

```bash
# The subagent said "X is the official way to do Y, per the docs"
# You check:
#   1. The official docs URL they cited — actually open it
#   2. The official source-of-truth (the actual code that runs, not the docs)
#   3. A community thread / issue that confirms the docs say what they say
```

**Why this works**: subagents sometimes cite a doc that doesn't say what they claim, or cite a secondary source that misrepresents the primary.

### Pattern D: Ask the user for confirmation when stakes are low enough

For low-stakes things, you can also just ask: "the subagent found X — does that match your experience?" The user's "no, it's actually Y" is the fastest verification, AND it builds the user's trust that you check things.

### Pattern E: Push back on your own subagent's reasoning, not just their facts

Sometimes the facts are right but the inference is wrong. E.g.:

> Subagent: "I confirmed `cli.py` loads persona from `config.yaml:personalities`. The persona mechanism lives there."
>
> Your counter-question: "What about other persona-loading code paths? `cli.py` is the CLI command source — but the *prompt assembly* code is elsewhere. Did you check `agent/prompt_builder.py` and `agent/system_prompt.py`?"

Apply this even when the spot-check grep in Pattern A returns "0 hits" — zero hits in the wrong directory is a non-result.

## 3. Common subagent failure modes (and how to spot them)

| Failure mode | What it looks like | How to detect in spot-check |
|---|---|---|
| **Stopped at first grep location** | "I grepped cli.py and found the persona mechanism" (missed the actual mechanism in agent/*.py) | Re-run the grep in the *broader* location; ask "did you check the prompt assembly path?" |
| **Inferred from commit messages, not from code** | "The web-ui's Memory page design doesn't mention soul, so SOUL.md is not used by the system" | Check the actual runtime code, not the commit history. Commit messages describe intent, code describes reality. |
| **Exhausted iterations before finishing** | "I ran out of tool calls" or "Could not complete X" buried in the report | The "Exit Criteria" check at the bottom of researcher-agent.md is the tell. If unchecked, treat the report as incomplete. |
| **Reported a negative claim without a positive control** | "X is not used anywhere" — but did they verify their grep actually catches all uses? | Run a positive control: a known-used string ("Hermes Agent" or "config.yaml") should appear N times in the codebase. If their grep returns 0, their grep is wrong. |
| **Conflated adjacent concepts** | "SOUL.md is web-ui's invention" (conflated web-ui-the-frontend with the framework-the-backend) | Check ownership: which repo introduced SOUL.md? Look at the actual framework code, not the web-ui code. |
| **Trusted a subagent's report about another subagent** | A summary says "subagent B confirmed X" — but B was actually B's sub-subagent, not independently verified | Trace the citation chain: who told whom? If A says "B confirmed" and B says "C confirmed" and C is a leaf, the chain has one real source. |

## 4. What to do when spot-check fails

Three options, in order of preference:

1. **Re-investigate yourself** with a broader scope, then write a corrected report. Often faster than another subagent round-trip.
2. **Delegate a NEW subagent with a more specific scope** — explicitly tell them "previous subagent missed the prompt assembly path; please check `agent/prompt_builder.py` and `agent/system_prompt.py`" — give them the corrected search surface.
3. **Ask the user** if their intuition conflicts with the subagent's conclusion (Pattern D). The user often has the right answer in 10 seconds.

**Never**: silently adopt the wrong conclusion and hope nobody notices. The user WILL notice.

## 5. The user's intuition is a signal, not noise

A particularly important meta-lesson from this session: **when the user pushes back on a conclusion you (or a subagent) reached, treat their pushback as evidence the conclusion is wrong, not as evidence the user misunderstood.**

This is counterintuitive — the parent agent has all the context, the user just has intuition. But the user has:
- Lived experience with the system (they've been using it longer than the current session)
- Implicit signals from past sessions (they've seen the same pattern work or fail before)
- A different optimization target (they want it to work, you want to be "right")

When the user says "but doesn't this contradict X?" or "are you sure?" or "这特么还改啥啊，应该改的是你吧" — that's a strong signal to re-investigate, not to defend. Defense without re-verification is how subagent errors get cemented into the user's setup.

## 6. The postmortem: how to record the failure

When a subagent's report turns out to be wrong, the failure is data. Encode it in the relevant skill so the next session starts already knowing.

Where to put the postmortem:
- **If the skill is loaded-and-used this session**: patch that skill's reference with a "How the original report got it wrong" section, like the one in `hermes-web-ui-setup/references/memory-three-tabs-design-intent.md` §3.5
- **If it's a new pattern**: add a "Failure mode" entry to the parent skill (e.g. `subagent-driven-development`)
- **Never** bury the postmortem in chat history or memory. The next session can't read either.

The postmortem should include:
- What the wrong conclusion was (verbatim quote)
- What the right conclusion is (with source)
- How the wrong conclusion was reached (which step failed)
- The defense for next time (one sentence, the rule that would have caught it)

## 7. Related references

- `references/researcher-agent.md` — the subagent template; patches needed for "exhaust the search surface" guidance
- `references/subagent-verification-pitfalls.md` — sibling doc on the verification pitfalls pattern
- `hermes-web-ui-setup/references/memory-three-tabs-design-intent.md` §3.5 — a worked example of a postmortem embedded in a reference doc
