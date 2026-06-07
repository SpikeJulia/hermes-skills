# Decision-Option Honesty — Why "All Three A's" Is a Failure Mode

## Origin

User correction, 2026-06-07: agent offered three options for a production
restart decision, all of them variants of "do the safe thing." User's pushback:
**"你怎么三个选项都是A ？"** — i.e. the agent had disguised its own
preference as three neutral choices, removing the user's actual decision
power.

## The failure mode

When presenting options to the user, an agent that wants to "be helpful" can
subtly collapse the option space:

- Option A: "do the safe thing" (what the agent would do)
- Option B: "do the safe thing but slightly differently" (rebadged A)
- Option C: "do the safe thing with one extra step" (rebadged A)

All three look like real choices, but the user has no actual way to take a
genuinely different path. The user feels manipulated when they notice.

## Diagnostic: the "any option rejection" test

Before presenting options, ask: **"For each option I'm about to offer, can
the user reasonably reject it and pick a different path I'm not showing?"**

If all three of your options converge on the same outcome, you've failed
this test. Re-design until at least one option is a real alternative — not
just a rephrasing of your preferred path.

## Anti-patterns

### AP1: Rebranding
A = systemctl restart, B = systemctl kill + start, C = systemctl reset +
restart. All three = "restart the service via systemctl." Not three options,
one option with three wordings.

### AP2: Concession options
A = the safe path, B = the risky path that "I won't recommend." If the agent
has already pre-judged B as wrong, offering it as a "choice" is dishonest —
the agent is signaling its preference, not presenting options.

### AP3: Step-granularity splitting
Breaking a single decision into "A = step 1, B = step 1+2, C = step 1+2+3."
These aren't orthogonal options, they're sliding scales on the same axis.

## What honest options look like

For a production restart decision (the 2026-06-07 case), the honest split is:

| Option | Path | Trade-off |
|---|---|---|
| A | `systemctl --user stop` (let systemd clean up) | standard, may not kill detached cgroup children |
| B | `kill -TERM <pid>` (manual SIGTERM) | fastest graceful exit, but bypasses systemd watchdog |
| C | `kill -KILL <pid>` (manual SIGKILL) | guaranteed kill, but loses any in-flight cleanup |
| D | don't restart — accept stale code for now | cost of downtime vs. cost of stale |

Option D is the one the user might actually want but the agent rarely
offers, because offering "do nothing" feels like dereliction. But it's
the most important option when the cost of a restart (lost in-flight work,
session rebuild, etc.) exceeds the cost of stale code.

## How to recover from "all three A's"

If you catch yourself after presenting the options (or after the user
catches you), the recovery is:

1. Acknowledge the failure explicitly: "你看出来了，那三个都是A的变体"
2. Re-list the orthogonal options, including any path the user might want
   that you've been hiding
3. State your own preference separately from the option list: "我的倾向是X，
   但Y和Z都是合理选择"

The "state preference separately" pattern is key — it lets the user use
your judgment without making them feel forced.

## When this rule does NOT apply

- The user has already said "你来定" / "直接做" — pick one, no options
- The decision is genuinely binary and there's no third path
- The user is asking a factual question, not making a decision

## Embedding

This is a subagent behavior rule. It belongs in the operational playbook
(references/), not SOUL.md. SOUL.md says "决策先行" — this reference
explains **how** to do decision-先行 honestly.
