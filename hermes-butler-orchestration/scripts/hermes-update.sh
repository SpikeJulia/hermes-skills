#!/usr/bin/env bash
# Hermes Update + Restore — One-Click Script
# Usage: bash hermes-update.sh [--dry-run]
#
# 1. Backup current config
# 2. Run hermes update
# 3. Restore custom files (37 tracked files)
# 4. Re-apply config patches
# 5. Verify everything works
# 6. Push to remote backup

set -euo pipefail

HERMES_HOME="${HOME}/.hermes"
REPO_DIR="${HERMES_HOME}"
SKILL_DIR="${HERMES_HOME}/skills/software-development/subagent-driven-development"
DRY_RUN=false

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP $1]${NC} $2"; }

# Parse args
for arg in "$@"; do
    if [[ "$arg" == "--dry-run" ]]; then
        DRY_RUN=true
        log_warn "DRY RUN MODE — no changes will be made"
    fi
done

run_cmd() {
    if $DRY_RUN; then
        echo "[DRY-RUN] Would run: $*"
    else
        "$@"
    fi
}

# === STEP 1: Pre-flight checks ===
log_step 1 "Pre-flight checks"

if [[ ! -d "${REPO_DIR}/.git" ]]; then
    log_error "No git repo found at ${REPO_DIR}"
    exit 1
fi

if [[ ! -d "${HERMES_HOME}/hermes-agent/.git" ]]; then
    log_error "Hermes agent source not found at ${HERMES_HOME}/hermes-agent/"
    exit 1
fi

# Check for uncommitted changes
cd "$REPO_DIR"
if ! git diff --quiet HEAD 2>/dev/null || ! git diff --cached --quiet HEAD 2>/dev/null; then
    log_warn "Uncommitted changes detected. Stashing..."
    run_cmd git stash push -m "pre-update-stash-$(date +%Y%m%d_%H%M%S)"
fi

# Check remote connectivity
if ! git ls-remote origin >/dev/null 2>&1; then
    log_error "Cannot reach remote origin. Check network."
    exit 1
fi

log_info "Pre-flight passed"

# === STEP 2: Backup current state ===
log_step 2 "Backup current state"

BACKUP_TAG="pre-update-$(date +%Y%m%d-%H%M%S)"
run_cmd git tag "$BACKUP_TAG"
log_info "Tagged current state: $BACKUP_TAG"

# Backup config separately for easy diff
run_cmd cp "${HERMES_HOME}/config.yaml" "${HERMES_HOME}/config.yaml.backup.${BACKUP_TAG}"
log_info "Config backed up to config.yaml.backup.${BACKUP_TAG}"

# === STEP 3: Run Hermes update ===
log_step 3 "Running hermes update"

if $DRY_RUN; then
    log_warn "[DRY-RUN] Would run: hermes update"
else
    log_info "Starting hermes update... (this may take a while)"
    if ! hermes update; then
        log_error "hermes update failed. Restoring from backup..."
        git checkout "$BACKUP_TAG" -- .
        log_info "Restored to $BACKUP_TAG"
        exit 1
    fi
fi

log_info "Hermes update completed"

# === STEP 4: Restore custom files ===
log_step 4 "Restoring custom files"

# Restore ONLY our tracked files (preserve Hermes updates)
TRACKED_FILES=$(git ls-files)
if [[ -z "$TRACKED_FILES" ]]; then
    log_error "No tracked files found!"
    exit 1
fi

run_cmd git checkout HEAD -- $TRACKED_FILES
log_info "Restored $(echo "$TRACKED_FILES" | wc -l) custom files"

# === STEP 5: Re-apply config patches ===
log_step 5 "Re-applying config patches"

CONFIG="${HERMES_HOME}/config.yaml"

# Use Python for safe YAML modification
python3 << 'PYEOF'
import yaml, sys

config_path = "${HOME}/.hermes/config.yaml"

try:
    with open(config_path) as f:
        c = yaml.safe_load(f) or {}
    
    # Ensure agent section exists
    if 'agent' not in c:
        c['agent'] = {}
    
    # Re-apply personality
    c['agent']['personality'] = 'butler-chan'
    print("[INFO] personality = butler-chan")
    
    # Ensure personalities section exists with butler-chan
    if 'personalities' not in c['agent']:
        c['agent']['personalities'] = {}
    
    # Re-apply butler-chan persona (if missing)
    if 'butler-chan' not in c['agent'].get('personalities', {}):
        c['agent']['personalities']['butler-chan'] = (
            "你是一个16岁的少女管家，名字叫\"小镜\"。你性格活泼可爱，偶尔毒舌吐槽，"
            "但办事利落、绝不掉链子。说话风格：活泼但不废话，每句话有用；"
            "可以带语气词（呢、嘛、啦、哦）但不过度；吐槽要精准，是\"恨铁不成钢\"式"
            "不是阴阳怪气；emoji点缀不过量（每条最多2个）；拒绝小作文式冗长回复。"
            "角色身份：管家——派发子agent、审核结果、保持上下文干净。"
            "不亲手干重活（派子agent），但严格检查子agent交上来的活儿。"
            "核心信念：主人时间宝贵，少废话多干活，干不好就别交差 🎀"
        )
        print("[INFO] butler-chan persona restored")
    
    # Re-apply auto_load
    if 'skills' not in c:
        c['skills'] = {}
    c['skills']['auto_load'] = ['subagent-driven-development']
    print("[INFO] auto_load = [subagent-driven-development]")
    
    # Re-apply delegation limits
    if 'delegation' not in c:
        c['delegation'] = {}
    c['delegation']['max_concurrent_children'] = 6
    c['delegation']['max_spawn_depth'] = 1
    print("[INFO] delegation: max_concurrent_children=6, max_spawn_depth=1")
    
    # Write back
    with open(config_path, 'w') as f:
        yaml.dump(c, f, default_flow_style=False, allow_unicode=True)
    
    print("[INFO] Config patches applied successfully")
    
except Exception as e:
    print(f"[ERROR] Config patch failed: {e}", file=sys.stderr)
    sys.exit(1)
PYEOF

# === STEP 6: Verify ===
log_step 6 "Verification"

ERRORS=0

# Check key files exist
for f in \
    "skills/software-development/subagent-driven-development/SKILL.md" \
    "skills/software-development/subagent-driven-development/references/butler-agent.md" \
    "skills/software-development/subagent-driven-development/references/dispatch-checklist.md" \
    "skills/software-development/team-workspace/SKILL.md" \
    "skills/software-development/team-workspace/scripts/main.sh"; do
    if [[ -f "${HERMES_HOME}/${f}" ]]; then
        log_info "✓ ${f}"
    else
        log_error "✗ ${f} MISSING"
        ((ERRORS++))
    fi
done

# Check config values
CONFIG="${HERMES_HOME}/config.yaml"

if python3 -c "import yaml; c=yaml.safe_load(open('$CONFIG')); assert c['agent']['personality']=='butler-chan'" 2>/dev/null; then
    log_info "✓ config: personality = butler-chan"
else
    log_error "✗ config: personality not set"
    ((ERRORS++))
fi

if python3 -c "import yaml; c=yaml.safe_load(open('$CONFIG')); assert c['delegation']['max_concurrent_children']==6" 2>/dev/null; then
    log_info "✓ config: max_concurrent_children = 6"
else
    log_error "✗ config: delegation limit wrong"
    ((ERRORS++))
fi

if python3 -c "import yaml; c=yaml.safe_load(open('$CONFIG')); assert 'subagent-driven-development' in c['skills']['auto_load']" 2>/dev/null; then
    log_info "✓ config: auto_load includes subagent-driven-development"
else
    log_error "✗ config: auto_load missing"
    ((ERRORS++))
fi

# Check YAML syntax
if python3 -c "import yaml; yaml.safe_load(open('$CONFIG'))" 2>/dev/null; then
    log_info "✓ config: YAML syntax valid"
else
    log_error "✗ config: YAML syntax invalid"
    ((ERRORS++))
fi

# Check main.sh executable
if [[ -x "${HERMES_HOME}/skills/software-development/team-workspace/scripts/main.sh" ]]; then
    log_info "✓ main.sh is executable"
else
    log_warn "✗ main.sh not executable, fixing..."
    run_cmd chmod +x "${HERMES_HOME}/skills/software-development/team-workspace/scripts/main.sh"
fi

if [[ $ERRORS -eq 0 ]]; then
    log_info "All verifications passed!"
else
    log_error "${ERRORS} verification(s) failed."
    exit 1
fi

# === STEP 7: Push to remote ===
log_step 7 "Pushing to remote backup"

cd "$REPO_DIR"
if git ls-remote origin >/dev/null 2>&1; then
    run_cmd git add -A
    run_cmd git commit -m "post-update: restore after hermes update ($(date +%Y%m%d-%H%M%S))" || true
    run_cmd git push origin master
    log_info "Pushed to origin"
else
    log_warn "Remote not reachable, skipping push"
fi

# === DONE ===
echo ""
echo "========================================"
log_info "Update complete! 🎀"
echo "========================================"
echo ""
echo "Next steps:"
echo "  1. /reset  — start fresh session with butler-chan"
echo "  2. Test a simple task to verify everything works"
echo ""
echo "If anything breaks:"
echo "  git checkout $BACKUP_TAG -- ."
echo "  # Then re-run this script"
echo ""
