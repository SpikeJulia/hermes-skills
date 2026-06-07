# Update Survival Guide — Surviving `hermes update`

## The Problem

`hermes update` pulls the latest source from the Hermes Agent repo, overwriting **everything** in `~/.hermes/` including:

- `config.yaml` — your personality, delegation limits, auto_load aliases
- `skills/` — all custom skills (butler-agent, team-workspace, role templates)
- `workspaces/` — active team collaboration workspaces
- Any source patches (gateway/run.py, weixin.py, etc.)

## The Solution: Git + Restore Script

### Layer 1: Git Tracking

Keep a git repo in `~/.hermes/` with a whitelist `.gitignore`:

```gitignore
# Exclude everything by default
/*

# Whitelist: only skills we created/modified
!/skills/
/skills/*
!/skills/software-development/
/skills/software-development/*
!/skills/software-development/subagent-driven-development/
!/skills/software-development/team-workspace/

# Whitelist: config
!/config.yaml

# Whitelist: workspaces
!/workspaces/
/workspaces/.archive/

# Secrets and sensitive
.env
auth.json
auth.lock
*.bak.*

# Runtime data
.hermes_history
channel_directory.json
state.db*
.update_check
cache/
audio_cache/
checkpoints/
sessions/
cron/
cron.db
logs/

# Upstream repo (already tracked separately)
hermes-agent/

# Misc
SOUL.md
bin/
```

### Layer 2: Remote Backup

Push to GitHub for off-site backup:

```bash
cd ~/.hermes
git remote add origin https://github.com/YOURNAME/hermes-config.git
git push -u origin master
```

### Layer 3: Automated Restore Script

`scripts/post-update-restore.sh` — run once after `hermes update`:

```bash
bash ~/.hermes/skills/software-development/subagent-driven-development/scripts/post-update-restore.sh
```

What it does:
1. `git checkout HEAD -- .` — restore all tracked files
2. Re-apply config.yaml values that update overwrote:
   - `agent.personality` → butler-chan
   - `skills.auto_load` → subagent-driven-development (via alias)
   - `delegation.max_concurrent_children` → 6
3. Verify everything is in place

## Manual Recovery (if .git was also deleted)

```bash
# Clone from remote
cd ~
git clone https://github.com/YOURNAME/hermes-config.git hermes-backup

# Copy customizations back
cp -r hermes-backup/skills ~/.hermes/
cp hermes-backup/config.yaml ~/.hermes/

# Re-apply config values
hermes config set agent.personality butler-chan
hermes config set delegation.max_concurrent_children 6
# ... etc
```

## Pre-Update Checklist

Before running `hermes update`:

- [ ] `cd ~/.hermes && git status` — no uncommitted changes (or stash them)
- [ ] `git push` — remote is up to date
- [ ] Note any source patches (gateway/run.py, weixin.py) — these need manual re-application
- [ ] Export cron jobs if needed: `hermes cron list > ~/cron-backup.txt`

## Post-Update Checklist

After `hermes update`:

- [ ] Run `post-update-restore.sh`
- [ ] `hermes config check` — verify config is valid
- [ ] `/reset` — start fresh session with butler-chan
- [ ] Re-apply any source patches (WeChat typing indicator, rate limit backoff, etc.)
- [ ] `hermes gateway restart` — if gateway config changed

## What Gets Lost Even With Git

| Item | Survives update? | Recovery |
|---|---|---|
| Custom skills | ✅ Yes (git tracked) | `git checkout` |
| config.yaml values | ✅ Yes (git tracked) | `git checkout` + restore script |
| Workspaces | ✅ Yes (git tracked) | `git checkout` |
| Source patches (gateway/run.py) | ❌ No (in hermes-agent/ which is excluded) | Manual re-patch from memory/skill docs |
| Session history | ❌ No (in sessions/, excluded) | Gone — export before update if needed |
| Cron jobs | ⚠️ Maybe (stored in cron.db, not tracked) | Export before update |
| Auth tokens | ⚠️ Maybe (in auth.json, excluded) | Re-authenticate if lost |

## Key Lesson

**Git tracks your customizations. Hermes update overwrites everything. The two are in constant tension.**

Always push before updating. Always run the restore script after updating. Never update blindly.
