---
name: inheriting-sibling-working-tree
description: How to take over a working tree that was left dirty by a sibling session/subagent — assess state, identify your scope, fix common bug patterns, surgical commit. Triggered by `git status` showing `M` or `??` files that you didn't change.
---

# Inheriting a Sibling's Working Tree

## When to use

- `git status --short` shows `M` or `??` files that you didn't author this session
- A previous session crashed mid-work and left dirty state
- You are about to commit and discover sibling-modified files in the staging area
- Multi-session git arena: you didn't make the change, but you need to ship a release / fix / commit

**When NOT to use**: working tree is clean (no `M`/`??`), or every dirty file is yours.

## Steps

### 1. Don't panic, don't trust your memory of "what I changed"

The sibling may have made coherent progress, OR introduced bugs you can't see. **Don't**
write a clean commit assuming only your changes exist. **Don't** blindly `git add -A`
to "clean up" — that bundles sibling code into your commit.

**Self-check**: if you find yourself saying "I think I changed X", stop and look at the
actual diff. This is the **凭印象作答** failure mode — it bit the butler 3 times in
one session (M3 multimodal claim, SOUL.md content claim, "sibling is alive" claim).
Every one of those times, the real state was in the file system, not in memory.

### 2. Map the working tree

```bash
git status --short           # full dirty file list
git diff --stat               # per-file line change counts (working tree)
git ls-files --others --exclude-standard   # untracked only
```

Build a mental table: **file → modified/added → likely author → your decision**.

For each file, decide:
- **Mine** → keep, will commit
- **Sibling's, looks good** → keep, will commit in same/separate commit
- **Sibling's, has bugs** → fix first, then commit (only if user has signed off on the scope)
- **Sibling's, should be reverted** → `git restore <file>` and tell user

### 3. Diff-read each sibling file (don't skim)

Sibling code has a **higher bug rate** than your own. Why? The sibling may have:
- Patched a small region but accidentally consumed neighboring content (`patch` with
  insufficient `old_string` context)
- Reorganized structure but left orphan titles / duplicate blocks
- Optimistically "deleted" something that turned out to be referenced

**Concrete bug patterns observed in 2026-06-04 sibling SKILL.md edits** (from
`subagent-driven-development/SKILL.md`):

1. **Duplicate blocks** — Pitfall段写完后, sibling 复制粘贴了同一段到一个错误位置
   (e.g. `## Steps` 标题下). Check: `grep -c "<unique phrase from段>"` 数字应等于
   该段本应出现的次数. 1 段 = 1 次.
2. **误删的相邻段** — sibling 用新段替换旧段时, 把旧段**后面紧跟的段**也吞掉了.
   Check: `git show HEAD:<file> | grep -n "<原段唯一短语>"` 必须能找到, 否则
   该段被 sibling 误删了.
3. **复制粘贴的镜像段** — sibling 想"重新组织"内容, 复制原段到新位置, 但
   忘了删原段. 表现为"两段几乎一字不差". Check: 对比两段 `diff`.
4. **孤儿标题** — sibling 加了 `## New Section` 标题但下面没内容, 或者标题下
   内容是 `### ⚠️` 的子标题错位. Check: 全文 grep `^## ` 看每个标题下是否
   有合理内容承接.

### 4. Sanity checks before staging (3-step gate)

This is the **git-commit-staging-verification** 3-step pattern (see
`references/git-commit-staging-verification.md` for the full reference).

| Step | Command | Catches |
|---|---|---|
| 1 | `git status --short` | unexpected files in the tree |
| 2 | `git diff --cached --stat` | wrong files in staging area |
| 3 | `git diff --cached <file>` (per file) | content you didn't author |

Step 1 runs **before** `git add` (mapping the tree). Steps 2-3 run **after** `git add`,
**before** `git commit`. Run all three. Every time.

### 5. Fix bugs surgically (or don't)

If sibling's file has bugs:

- **Fix in place** if user has signed off on the scope. Use `patch` with sufficient
  context, not `write_file` (which clobbers the rest of the file).
- **Revert sibling's file** if the bugs are deep and you don't have time / scope
  to fix. `git restore <file>` and tell user the file was reverted.
- **Ask the user** if unsure. Default to asking, not assuming.

**Don't** silently rewrite the sibling's entire file. **Don't** "improve" sibling
code beyond what's needed to make it correct. Both behaviors are scope creep.

### 6. Stage with explicit paths

```bash
# ✅ Explicit paths — safe even if working tree has surprises
git add path/to/file1 path/to/file2

# ❌ Avoid unless working tree is verified clean
git add -A
git add .
```

If you must use `-A` / `.`, **always** run step 2-3 of the verification gate.

### 7. Commit message: name the sibling's contribution

If the commit contains both your work and the sibling's, the commit message should
say so. Example:

```
docs(skill): add SOUL.md editing protocol + 3 pinned rules

Captured from 2026-06-04 learnings (凭印象作答 failure mode,
SOUL.md ≠ skill boundary). Sibling subagent left 4 files in working
tree (3 of which had复制粘贴 bugs — fixed in this commit):

- references/butler-agent.md: 3 pinned rules (sibling's)
- references/soul-md-editing-protocol.md: new reference (sibling's)
- SKILL.md: 2 new pitfalls + bug fixes for sibling's 3复制粘贴 issues
- references/git-commit-staging-verification.md: new reference (mine)
```

**Don't** silently take credit for sibling work. **Don't** lump the credit into
a generic "added documentation" — name the contribution.

### 8. Post-commit: confirm clean state

```bash
git status              # should show clean working tree
git log --oneline -1    # the commit you just made
git log --stat -1       # confirm files are exactly what you intended
```

## Pitfalls

### ❌ "Sibling is still running, I can message it"

False. Sibling sessions either:
- Exited (most common) — `ps aux | grep hermes` shows no other process
- Are in a different workdir that doesn't share your `git status` — sending
  a message does nothing

**Test**: `ps aux | grep -E "hermes" | grep -v grep` — count processes. If only
yours, sibling is gone. Don't promise the user "I'll tell sibling to fix it".

### ❌ "Working tree is dirty, let me `git stash` and start over"

`git stash` saves dirty state but **doesn't** clean the sibling's bugs. You'll
re-encounter them when you `git stash pop`. Better: scope the bugs and fix
them surgically (step 5).

### ❌ "I'll just `git add -A` — it's all going to the same commit anyway"

If sibling's files are in the working tree, `git add -A` will add them. If
you didn't review them (step 3), you commit bugs. **Always** review before
adding. **Always** use explicit paths when possible.

### ❌ "Sibling was working on a similar topic, the changes are probably fine"

Probability of "sibling was right" is **not** 100%. The 2026-06-04 sibling had
3 of 4 files with复制粘贴 bugs. Even when the topic is right, the execution
often needs review.

### ❌ "I'll mention the sibling in the CHANGELOG after committing"

CHANGELOG should be staged **with** the commit, not as a follow-up edit. The
pattern of "commit code, then write what I did" loses information — you forget
the context. Stage CHANGELOG.md in the same `git add` as the other files.

## Case study: 2026-06-04 SOUL.md 入仓 + 体系建立

**Setup**: butler was told to put SOUL.md (main + coder profile) into git.
First commit `6c77561` did exactly that, in 4 files (surgical). After
that commit, working tree still showed:

```
M  skills/.../SKILL.md                  (sibling's)
M  skills/.../references/butler-agent.md (sibling's)
?? skills/.../references/soul-md-editing-protocol.md  (sibling's)
?? skills/.../references/git-commit-staging-verification.md  (butler's, NEW discovery)
```

**Process followed**:
1. `git status --short` → saw 4 dirty files, identified 3 as sibling's by reading
   each diff (step 2 of this skill).
2. Discovered sibling's SKILL.md had **3复制粘贴 bugs** (重复块, 误删段, 镜像段).
3. Asked user: "fix or revert?" → user chose fix.
4. Patched each bug surgically (precise `patch` calls with enough context).
5. Discovered the 4th file (`git-commit-staging-verification.md`) **after**
   staging 3 files — bumped commit from 3 files to 4 files (user approved).
6. Verified 4 files staged with `git diff --cached --stat` (213 insertions, 0 leftover).
7. Committed with explicit credit to sibling's 3 files + butler's bug fixes +
   new 4th reference.
8. Post-commit `git status` clean.

**Result**: 2 commits in the session, both single-topic, both surgical, no
sibling code clobbered, sibling's bugs fixed before commit landed.

## Related

- `references/git-commit-staging-verification.md` — the 3-step verification gate
  (status → diff-cached → per-file diff) that this skill depends on
- `references/butler-agent.md` — the persona / rules reference; has the
  "凭印象作答" and "SOUL.md ≠ skill" pitfalls that govern this work
- `references/soul-md-editing-protocol.md` — when the inherited file is SOUL.md
  itself, this is the editing protocol to follow
- `references/parent-spot-check-recipe.md` — Stage 0 spot-check pattern applies
  equally to sibling subagent output
