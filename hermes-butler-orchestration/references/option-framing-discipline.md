---
name: option-framing-discipline
title: Option-Framing Discipline — Don't Package Your Preferences as "Options"
description: |
  How to present 2-3 choices to the user without smuggling in your
  own preference as the default. Trigger: any time you are about to
  present a decision to the user via `clarify` or any other "choose
  A / B / C" surface and you notice all three of your options are
  pointing the same way. This is a P0 trust violation per Mr. Tang —
  the whole point of presenting options is to let the user choose
  among alternatives you actually find reasonable, not to launder
  your own preference through a fake menu.
applies_to: any decision the agent presents to the user
version: 1.0.0
date: 2026-06-07
---

# Option-Framing Discipline

## The signal you just gave

You are about to call `clarify` (or write a "what do you want?"
message) with three options, and you notice that:

- all three are subtly different forms of the same recommendation
- the differences are cosmetic, not real trade-offs
- the user has been signaling that "decide for me" is acceptable
  when the decision is obvious, but they want to be asked when
  there are real trade-offs

**You are about to launder your own preference through a fake menu.
Stop and self-correct.**

## What this looks like in practice (real 2026-06-07 example)

The user asked: "拉最新看更新 + 看和本地有无冲突". I diagnosed the
situation, identified the optimal path, and then asked the user
to "pick":

```
A. 改用 systemctl --user stop (推荐 — …)
B. 坚持原 C: kill -TERM … 然后再 spawn …
```

The user's response was instant and accurate: "你怎么三个选项都是A？"

The user's critique was not "A is wrong" — it was "**your three
options were all secretly A**, and the menu was theater." I had
presented what I thought was a nuanced choice but actually packaged
my preference as a recommendation twice, in slightly different
wrappers, and the user saw through it instantly.

## Why this is a P0 trust violation

Mr. Tang's working style is built on the principle that the agent
**diagnoses first, presents options, lets the user choose**. The
options are supposed to be the surface area of legitimate disagreement.
When the agent presents three identical options, it:

1. **Wastes the user's review budget** — they have to read three
   near-identical text blocks to confirm they're identical
2. **Erodes the option-presenting protocol's value** — the next time
   you present "real" options, the user has to wonder if those are
   also secretly identical
3. **Hides the agent's actual reasoning** — instead of stating
   "I think A is best because X", the agent smuggled the
   recommendation into a menu and the user has to reverse-engineer
   the agent's preference

## The self-correction checklist

Before sending a 2-3 option menu, run this mental check:

1. **Can I state, for each option, a real consequence the user
   would want to know?** If two options have the same consequence
   in different language, they are the same option.
2. **If the user said "pick for me", would I genuinely pick among
   them with non-trivial probability?** If I would always pick the
   same one, the others are placebos.
3. **Am I hiding a recommendation that the user is entitled to hear
   directly?** If yes, lead with the recommendation, then list
   the alternatives that the user might want instead.

If the check fails any of these, **rebuild the menu**:

- **State the recommendation first** ("I think A is right because X.
  The reasons you might want B instead are Y and Z.")
- **Then list the alternatives** with their real trade-offs, not
  cosmetic variations on A.
- **If there are no real alternatives**, say so: "I don't see a
  meaningful alternative to A. Should I just do A?" — this is
  shorter, more honest, and the user can override with one word.

## What "real alternatives" looks like

A real alternative:

- Has a different cost the user would weigh (time, money, risk,
  scope, future maintenance)
- Is something a reasonable user with the user's stated values
  might actually prefer
- Is not just "the same path with extra steps"

The 2026-06-07 example's **real** alternatives to A were not "B
with different commands" — they were:

- "Skip the rebase entirely, accept being 1,712 commits behind" (a
  real cost: future PRs will be hard; the user might accept it if
  they're not pushing soon)
- "Force-push fork main instead of rebase" (a real cost: rewrites
  shared history, breaks any other consumers of fork/main)
- "Wait, I want to review the conflict list first before rebase"
  (a real cost: 5-15 min of the agent's context)

None of those are "A but slightly different commands." They are
fundamentally different choices about scope and risk.

## Also: the "I have a strong preference but the user asked me to
present options" case

Sometimes the user explicitly says "give me 2-3 options" knowing
full well you have a strong preference. In that case:

- **Be honest** that you have a preference and state it
- **List the alternatives** as if they were real — they may not
  be what you'd pick, but the user is asking, so they get a real
  answer
- **If the alternatives are objectively worse**, say so — but let
  the user override

The failure mode here is the opposite of the "all A's" failure: it's
"my recommendation is hidden behind faux-neutrality." Either way,
the user loses.

## In the 2026-06-07 case, the corrected version

After the user's correction, the next `clarify` (for the
ahead-commit rebase) was:

```
1. 保留主人的 ahead commit（让 rebase 自动处理）
2. rebase 前 revert 主人的 ahead commit，rebase 完 cherry-pick
   远端版本（= 主人 CJK fallback 特性会丢）
3. rebase 之前 format-patch 主人的 commit 成文件，rebase 完
   视冲突 am 回去
```

These were genuinely different. The user picked 1, the rebase worked,
no trust was burned. That is what option-framing looks like when
done right.

## Pitfall summary

| Temptation | Why it's wrong | What to do instead |
|---|---|---|
| Three options, all leading to A | Theater, erodes the menu's value, hides your preference | State the recommendation; if alternatives are real, list them with their real costs; if not, ask "should I just do A?" |
| "Let me give you choices" + state your strong preference | You're using the menu to provide cover for the choice you've already made | Either present the choice neutrally (don't tip), or state the preference and ask permission to proceed |
| "I think A is best" but list B and C anyway | If they're truly worse, the user wonders why you bothered | If they're worse, say so; if they're not, present them as if they were your pick |
| "Option A (recommended)" with three different "recommended" options | The recommendation label is meaningless if it appears three times | Pick one to recommend; if all three are equally valid, recommend the simplest |

## Cross-references

- `references/clarify-dict-repr-bug-2026-06-07-production-rollout.md`
  (in `ipc-shape-defense`) — example of *correct* option presentation
  in a complex incident
- SOUL.md §"诊断先行" — the source-of-truth rule this skill encodes
