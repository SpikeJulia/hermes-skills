# Check Official Docs Before Declaring "This Is a Bug"

> **Captured:** 2026-06-04 from the SOUL.md misjudgment (user: "这特么还改啥啊，应该改的是你吧... 既然 soul 优先级高，那肯定要把人格相关设置放到 soul.md 里面去吧")
> **Trigger:** any time the agent is about to tell the user "X is broken / unused / a bug" based on code-reading alone — especially for mature, opinionated open-source projects (Hermes, Django, Rails, Kubernetes, etc.)
> **Companion to:** `parent-spot-check-recipe.md` (broader pattern of verifying subagent claims before acting)

## TL;DR

Before declaring something a bug, **read the project's official user-facing documentation first**. Code tells you HOW; docs tell you WHY. The user's intuition that "this shouldn't be a bug in a mature project" is usually right — and the official docs almost always explain the mechanism the agent missed.

## The pattern that bit us (2026-06-04)

A `researcher` subagent reported "SOUL.md is a write-only decorative surface, not consumed by the agent" based on reading `cli.py:7360-7442` (the `/personality` command source — which is *one of several* persona-loading paths). The parent agent adopted the conclusion and proposed "let's patch web-ui to wire SOUL.md into the prompt". The user pushed back: "这特么还改啥啊，应该改的是你吧".

On re-investigation, the official `~/.hermes/hermes-agent/website/docs/user-guide/profiles.md` and `profile-commands.md` documented the mechanism that the subagent never read:
- `HERMES_HOME` is set by `_apply_profile_override()` in the entry point **before any module is imported**
- `load_soul_md()` reads `get_hermes_home() / "SOUL.md"` — which is profile-aware via the env var
- SOUL.md is in fact the **official** persona file (slot #1 identity, the highest priority in the stable tier)
- The correct fix was a **data migration** (write persona to SOUL.md, clear `config.yaml:agent.system_prompt`), NOT a code change

**There was no bug.** The subagent's "I grepped the wrong surface" was a research-method error, not a finding.

## Why docs-first catches what code-only misses

| What code tells you | What docs tell you |
|---|---|
| "load_soul_md reads get_hermes_home() / 'SOUL.md'" | "SOUL.md is the official persona file" |
| "HERMES_HOME is an env var" | "HERMES_HOME is set by `_apply_profile_override` before import" |
| "config.yaml:agent.system_prompt exists" | "agent.system_prompt is the ephemeral tier, not the primary persona" |
| "personalities.<name> is a dict in config" | "personalities is a `/personality` preset list, default empty" |

The code gives you **one piece at a time**. The docs give you the **whole picture**, including the design intent. For a mature project, the design intent is what determines whether "X looks weird" is a bug or a feature.

## When to apply this (decision tree)

Before declaring "X is a bug / unused / broken", ask:

1. **Is the project mature and opinionated?** (Hermes, Django, Rails, Kubernetes, Rust core libraries)
   - YES → **stop, read docs first** before telling the user
   - NO (fresh hobby project, small library, internal tool) → code-only is usually fine

2. **Did I only look at one code surface?** (e.g. only `cli.py`, only the controller, only the public API)
   - YES → **stop, look at the broader architecture** (entry point, env var setup, config loading, plugin system)
   - NO (I've traced through the full call chain including entry points) → proceed with caution

3. **Does the user's intuition contradict my finding?**
   - YES → **stop, verify the user's intuition first** before defending my position (see `parent-spot-check-recipe.md` for the broader pattern)
   - NO → proceed

4. **Is the issue a regression from a previous version?**
   - YES → check release notes / changelog for that version (often explains intentional changes)
   - NO → proceed

If any answer is "YES I should stop", the next action is **read the docs**, not defend the finding.

## How to read the docs efficiently

For Hermes specifically (most relevant to this skill):
```bash
# Main user guides
ls ~/.hermes/hermes-agent/website/docs/user-guide/
# → features/, profiles.md, cli-usage.md, etc.

# Command references
ls ~/.hermes/hermes-agent/website/docs/reference/
# → cli-commands.md, profile-commands.md, environment-variables.md, etc.

# Search for your topic
grep -r "SOUL.md" ~/.hermes/hermes-agent/website/docs/ 2>/dev/null
```

For other projects: prefer **the official docs site** over README. README gives the elevator pitch; docs give the architecture.

## What "is a bug" looks like vs what "is intentional" looks like

**Looks like a bug but is intentional** (Hermes examples):
- `load_soul_md()` always reads `get_hermes_home() / "SOUL.md"` — looks hard-coded, but HERMES_HOME is pre-parsed in entry point
- `personalities.<name>` exists but defaults to `{}` — looks like a feature gap, but it's an opt-in preset system
- `config.yaml:agent.system_prompt` exists alongside SOUL.md — looks redundant, but it's a different injection tier (ephemeral vs identity)
- `MEMORY.md` and `USER.md` are in `~/.hermes/memories/` but `SOUL.md` is in `~/.hermes/` root — looks asymmetric, but reflects "SOUL.md is identity, not memory"

**Actually a bug** (signals):
- Behavior contradicts the docs
- Multiple community reports of the same issue
- A clear regression from a previous version's behavior
- Untested edge case (empty input, unicode, large input, etc.) that the tests don't cover
- Configuration option that doesn't work as documented

## Defense for the next session

When tempted to say "X is a bug", replace with one of:

- "Based on reading the code in [file:section], this LOOKS like [X], but I haven't checked [docs/entrypoint/test] yet. Want me to verify?"
- "The subagent found [X]. Before we act, let me read [official docs] to confirm — I don't want to propose a patch for what's actually intentional design."
- "User said this shouldn't be a bug in a mature project. They might be right. Let me check the docs before defending my position."

These phrasings cost 30 seconds and prevent hours of rollback + lost user trust.

## Related

- `parent-spot-check-recipe.md` — broader pattern of verifying subagent claims
- `subagent-verification-pitfalls.md` — verifying subagent test reports (different domain)
- `~/.hermes/hermes-agent/website/docs/user-guide/profiles.md` — example of "docs that explain why code looks weird"
