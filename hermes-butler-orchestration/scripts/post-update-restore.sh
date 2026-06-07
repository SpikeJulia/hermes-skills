#!/usr/bin/env bash
# Post-Hermes-Update Restore Script
# Run this after `hermes update` to restore all customizations.
#
# Usage: bash ~/.hermes/skills/software-development/subagent-driven-development/scripts/post-update-restore.sh

set -euo pipefail

HERMES_HOME="${HOME}/.hermes"
SKILL_DIR="${HERMES_HOME}/skills/software-development/subagent-driven-development"
GIT_DIR="${HERMES_HOME}/.git"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

check_git() {
    if [[ ! -d "$GIT_DIR" ]]; then
        log_error "No git repo found at ${HERMES_HOME}. Cannot restore."
        exit 1
    fi
}

# 1. Restore tracked files (skills + config) — ONLY our custom files, leave Hermes updates intact
restore_tracked() {
    log_info "Restoring custom tracked files (36 files)..."
    cd "$HERMES_HOME"
    
    # Stash any uncommitted changes first
    if ! git diff --quiet HEAD 2>/dev/null; then
        log_warn "Uncommitted changes detected. Stashing..."
        git stash push -m "pre-update-stash-$(date +%Y%m%d_%H%M%S)"
    fi
    
    # Restore ONLY our tracked files (not everything — preserve Hermes updates)
    git checkout HEAD -- $(git ls-files) 2>/dev/null || true
    
    log_info "Custom files restored. Hermes updates preserved."
}

# 2. Re-apply config patches that Hermes update might overwrite
reapply_config() {
    log_info "Re-applying config customizations..."
    
    CONFIG="${HERMES_HOME}/config.yaml"
    
    # Check if personality is set
    if ! grep -q "^  personality: butler-chan" "$CONFIG" 2>/dev/null; then
        log_warn "butler-chan personality missing. Re-applying..."
        # Use Python to safely modify YAML
        python3 -c "
import yaml, sys
with open('$CONFIG') as f:
    c = yaml.safe_load(f)
c['agent']['personality'] = 'butler-chan'
with open('$CONFIG', 'w') as f:
    yaml.dump(c, f, default_flow_style=False, allow_unicode=True)
print('Personality restored')
" 2>/dev/null || log_warn "Could not re-apply personality. Manual fix needed."
    fi
    
    # Check auto_load
    if ! python3 -c "import yaml; c=yaml.safe_load(open('$CONFIG')); print('subagent-driven-development' in c.get('skills',{}).get('auto_load',[]))" 2>/dev/null | grep -q "True"; then
        log_warn "auto_load missing. Re-applying..."
        python3 -c "
import yaml
with open('$CONFIG') as f:
    c = yaml.safe_load(f)
if 'skills' not in c: c['skills'] = {}
c['skills']['auto_load'] = ['subagent-driven-development']
with open('$CONFIG', 'w') as f:
    yaml.dump(c, f, default_flow_style=False, allow_unicode=True)
print('auto_load restored')
" 2>/dev/null || log_warn "Could not re-apply auto_load."
    fi
    
    # Check delegation limit
    if ! python3 -c "import yaml; c=yaml.safe_load(open('$CONFIG')); print(c.get('delegation',{}).get('max_concurrent_children'))" 2>/dev/null | grep -q "6"; then
        log_warn "max_concurrent_children not 6. Re-applying..."
        python3 -c "
import yaml
with open('$CONFIG') as f:
    c = yaml.safe_load(f)
if 'delegation' not in c: c['delegation'] = {}
c['delegation']['max_concurrent_children'] = 6
c['delegation']['max_spawn_depth'] = 1
with open('$CONFIG', 'w') as f:
    yaml.dump(c, f, default_flow_style=False, allow_unicode=True)
print('delegation restored')
" 2>/dev/null || log_warn "Could not re-apply delegation."
    fi
    
    log_info "Config re-applied."
}

# 3. Verify everything is in place
verify() {
    log_info "Verifying restoration..."
    
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
    
    if [[ $ERRORS -eq 0 ]]; then
        log_info "All verifications passed. Restoration complete!"
        echo ""
        echo "Next step: /reset to start a fresh session with butler-chan loaded."
    else
        log_error "${ERRORS} verification(s) failed. Check logs above."
        exit 1
    fi
}

# Main
main() {
    echo "=== Hermes Post-Update Restore ==="
    echo ""
    
    check_git
    restore_tracked
    reapply_config
    verify
}

main "$@"
