# Destructive-Command Safety Patterns (captured 2026-06-05)

Three concrete patterns from session work. Each is a near-miss or actual-miss that the agent would re-encounter without a written rule.

## Pattern 1: `rmdir` for "probably-empty" directory cleanup

**Scenario**: A previous step created a backup directory via `mkdir -p /path/to/backup && cp -a src/. backup/`. The `cp` failed because the source didn't exist yet, but `mkdir` had already created an empty backup directory. Now you need to clean it up.

**Wrong reflex**: `rm -rf /path/to/backup` — fast, recursive, dangerous if you typed the wrong path.

**Right reflex**:
1. `ls -la /path/to/backup` to confirm it's the target (not a typo for a real skill).
2. `find /path/to/backup -mindepth 1` to confirm it's empty.
3. `readlink /path/to/backup` to confirm it's not a symlink.
4. **Then** `rmdir /path/to/backup` (NOT `rm -rf`). `rmdir` will fail on non-empty, so the worst case is a no-op.

**Why**: `rmdir` is idempotent and refusal-based. `rm -rf` is silent and total. The cost of "rmdir failed because I targeted the wrong path" is one line of error output. The cost of "rm -rf wiped a real skill directory because I had a typo" is unrecoverable.

## Pattern 2: Verify skill is actually recognized, not just file-written

**Scenario**: You wrote `~/.hermes/skills/<category>/<name>/SKILL.md` and frontmatter looks correct. Time to declare done.

**Wrong reflex**: Trust the file exists and frontmatter parses.

**Right reflex** (3 layers):
1. `python3 -c "import yaml; yaml.safe_load(open('<path>').read().split('---',2)[1])"` — YAML parses.
2. `skill_view(name='<category>/<name>')` — Hermes internal index recognizes it (`success: true`, `readiness_status: available`).
3. `skills_list(category='<category>')` — Listed in the index by category.

**Compile-time ≠ Runtime.** A skill that's written but not indexed is silently dead.

## Pattern 3: Trigger-word self-test before declaring a new skill complete

**Scenario**: You wrote a skill with trigger words in `description:`. Will it actually auto-load when the operator says one of them?

**What you CAN verify**: char count (`awk '/^description:/{print length($0); exit}' <path>`), all listed words present (`grep -c`), language distribution.

**What you CAN'T verify without a fresh session**: Whether the trigger words actually match in Hermes's index. The matching algorithm isn't public.

**Right reflex**: After installing a new skill, in the same session, deliberately test the description against the awk char count + grep for each trigger word. If any trigger is missing or over the budget, fix before closing. Document the remaining uncertainty: "trigger matching algorithm is undocumented; verify in next fresh session".

## Anti-Pattern: Trusting the user's claim that a file "isn't there"

If the user says "I wrote X but it's not there" or "I changed Y, see for yourself":

1. **First** `ls -la <claimed path>` — confirm the path is what the user thinks it is.
2. **Then** read the actual content.
3. **Then** diff against the user's claim.

Do NOT scan the whole filesystem looking for the file. Do NOT trust the user that the file is missing. Do NOT trust the file matches the user's description. **Verify all three.**

(Memory 2026-06-05 captured this exact anti-pattern in the butler's working notes.)
