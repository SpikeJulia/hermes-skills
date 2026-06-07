---
name: git-commit-staging-verification
description: 3-step verification gate before `git commit` in multi-session / multi-agent repos. Pinned rule from 2026-06-04 session.
---

# Git Commit Staging Verification

## When to use

**Always** before `git commit` when ANY of:
- Multiple sessions / subagents may be modifying the same repo
- Working tree already has `M` or `??` files (someone else is working)
- You just did `git add <files>` and got a success message
- The repo is `~/.hermes/` or any other shared config repo (CHANGELOG.md / SKILL.md shared)

## 3-step mandatory verification (in order)

### Step 1: `git status --short`

Look at the **full** list of changes — not just the files you think you changed.

```
M  .gitignore                      # your change
M  skills/.../SKILL.md             # SIBLING'S change — STOP if you didn't expect this
?? profiles/                       # untracked, may or may not be yours
```

**Red flag**: any file you don't recognize = someone else is in the tree. Either:
- Stop and ask user which to commit
- Stage only the files you actually modified (`git add <specific-path>` not `git add -A`)

### Step 2: `git diff --cached --stat`

After `git add`, confirm **exactly** which files are in the staging area:

```
.gitignore             | 10 ++++++++-
SOUL.md                | 59 ++++++++
profiles/coder/SOUL.md |  1 +
3 files changed, 69 insertions(+), 1 deletion(-)
```

**Red flag**: file count or names differ from what you intended. Run `git restore --staged <unwanted>` to back out, then re-stage carefully.

### Step 3: `git diff --cached <staged-file>`

For **each** staged file, read the diff. Catches:
- Content you didn't write
- Sibling's edits accidentally staged
- Debug print statements / scratch code
- Wrong branch's content (if you `git checkout`'d)

## Case study: 2026-06-04 SOUL.md 入仓

Setup: 主人 said "把 SOUL.md 全部入仓". I had:
- Modified `.gitignore` (add whitelist rules)
- Created `SOUL.md` to stage
- Created `profiles/coder/SOUL.md` to stage

Sibling subagent (parallel session) had:
- Modified `skills/.../SKILL.md` (new skill reference)
- Modified `skills/.../references/butler-agent.md` (also referenced new skill)
- Created `references/soul-md-editing-protocol.md`

**My commit sequence**:
1. `git status --short` → saw all 6 modified/new files (mine + sibling's)
2. **Identified sibling's files** by checking the M files' content (`git diff` on each)
3. `git add .gitignore SOUL.md profiles/coder/SOUL.md` — **specific paths, not `git add -A`**
4. `git diff --cached --stat` → confirmed exactly 3 files staged, all mine
5. `git diff --cached` on each file → confirmed content was 100% mine
6. `git commit -m "chore(config): track SOUL.md files (main + coder profile) via .gitignore whitelist"`
7. Post-commit: `git status --short` → only sibling's 3 files remained (untouched, not their problem)

**Result**: clean surgical commit (4 files changed: 3 mine + CHANGELOG.md), 0 sibling contamination.

## Anti-patterns (causes 13-file-bundled-commit syndrome)

- ❌ `git add -A` / `git add .` when working tree has other people's changes
- ❌ Trusting `git add <file>` success message without checking the full staging list
- ❌ Committing on a branch you didn't verify (`git status` shows branch at top)
- ❌ Skipping the per-file diff review "because it's just config" — config diffs are the easiest to mis-stage
- ❌ Using `git commit -am "msg"` (adds all tracked changes) — no way to know what got added

## Recovery (if you already committed wrong files)

```bash
# 1. Soft reset (keeps changes in working tree, undoes commit)
git reset --soft HEAD~1

# 2. Unstage the wrong files
git restore --staged <wrong-file-1> <wrong-file-2>

# 3. Re-stage only yours
git add <your-files>

# 4. Commit again
git commit -m "..."
```

If you **pushed** the bad commit, recovery is harder — needs `git revert` or force push (which affects the owner). **Prevention is cheaper.**

## Related rules

- Owner explicitly said: "反感'打包 working tree 全部 dirty 一起 commit'"
- CHANGELOG.md 已有 `bde931c` 案例: 13 files误打包
- Multi-session git arena dynamics: see `neat-freak/references/multi-session-git-arena.md`
