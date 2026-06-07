# Git Stash Pop Conflict: --ours vs --theirs Semantics

## The Pitfall

In `git stash pop` conflict resolution, `--ours` and `--theirs` have **opposite** meanings from rebase:

| Context | `--ours` | `--theirs` |
|---|---|---|
| **rebase** | current branch (being rebased) | upstream (branch being rebased onto) |
| **merge** | current branch (HEAD) | merged branch |
| **stash pop** | working tree BEFORE stash pop (HEAD/index) | **stash content** (the changes being popped) |

## Why This Bites

When resolving a stash pop conflict, the natural instinct is to think "I want the upstream/release version" and run `git checkout --theirs`. **This gives you the old stash content, not the current HEAD.**

```
stash pop conflict flow:

  Before pop:  HEAD = v2026.6.5 (20031-line run.py)
  Stash:       old base (18205-line run.py + owner's backoff hacks)
  
  Pop triggers conflict → both versions mixed in index.
  Stage 2 (ours)  = HEAD version (v2026.6.5)
  Stage 3 (theirs) = stash version (old base + hacks)
  
  WRONG: git checkout --theirs gateway/run.py   → gets OLD stash version
  CORRECT: git checkout --ours gateway/run.py   → keeps HEAD (current release)
```

## Correct Decision Tree

1. **Want to keep HEAD (discard stash changes for this file)?** → `git checkout --ours <file>`
2. **Want to apply stash changes (discard HEAD for this file)?** → `git checkout --theirs <file>`
3. **Want manual merge?** → Edit the conflict markers by hand, then `git add <file>`

## After Resolving

```bash
git add <file>           # mark resolved
git stash drop stash@{0} # clean up (stash kept on conflict for safety)
```

## When You're Unsure

Check what each side contains:
```bash
git show :2:<file> | head -20  # stage 2 = ours = HEAD
git show :3:<file> | head -20  # stage 3 = theirs = stash
```

## Real Cost

2026-06-07: This pitfall cost ~30 minutes and forced a full rebase redo. Agent selected `--theirs` twice thinking it meant "upstream/release version", but it actually selected the old stash content, silently discarding 1712 commits of v2026.6.5 release changes.
