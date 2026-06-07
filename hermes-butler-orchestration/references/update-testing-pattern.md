# Update Testing — Dry-Run Pattern

## When to Use

Before running any destructive or complex script (especially `hermes-update.sh`), test with `--dry-run` first.

## Pattern

```bash
# 1. Preview mode — shows what WOULD happen without making changes
bash script.sh --dry-run

# 2. Review output for:
#    - Correct file list (only tracked files, not everything)
#    - Config values being applied
#    - No unexpected overwrites

# 3. If preview looks correct, run for real
bash script.sh
```

## What to Check in Dry-Run Output

| Check | Why |
|---|---|
| File list matches `git ls-files` | Ensures only custom files are restored, not Hermes updates |
| Config values are correct | personality, delegation, auto_load |
| No syntax errors in Python heredocs | `${HOME}` vs `os.path.expanduser()` |
| Verification steps are listed | Ensures the script actually checks results |

## Common Pitfall: Python heredoc variable expansion

**Wrong** (variable not expanded):
```bash
python3 << 'PYEOF'
config_path = "${HOME}/.hermes/config.yaml"  # Literal string, not expanded
PYEOF
```

**Correct**:
```bash
python3 << PYEOF
import os
config_path = os.path.expanduser("~/.hermes/config.yaml")
PYEOF
```

Or use env var passing:
```bash
HERMES_HOME="$HOME/.hermes" python3 << 'PYEOF'
import os
config_path = os.environ["HERMES_HOME"] + "/config.yaml"
PYEOF
```

## Config Format Migration

Hermes may auto-migrate config.yaml format between versions. Watch for:

| Old format | New format |
|---|---|
| `system_prompt` in agent block | `personalities` dictionary + `personality` key |
| No `_config_version` | `_config_version: 22` |
| `model` block at top level | `model` nested differently |

**Detection:**
```bash
python3 -c "import yaml; c=yaml.safe_load(open('config.yaml')); print('_config_version' in c)"
```

**Recovery:** The `hermes-update.sh` script handles this by using Python to safely modify YAML, preserving the new format while re-applying custom values.
