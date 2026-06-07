# copilot-acp Provider Pitfall: Subagent Transport Hijack

## Symptom

Subagent fails on every API call with:

```
[subagent-N] ⚠️  API call failed (attempt 1/3): RuntimeError
[subagent-N]    🔌 Provider: copilot-acp  Model: <random-model>
[subagent-N]    🌐 Endpoint: https://<parent-provider-endpoint>
[subagent-N]    📝 Error: Copilot ACP process exited early: error: unknown option '--acp'
```

Then fallback kicks in (`deepseek-v4-flash via deepseek` etc.) and the task still
succeeds — but the retries waste ~15s per subagent.

## Root Cause

The `copilot-acp` model-provider plugin lives at
`plugins/model-providers/copilot-acp/` and is discovered at startup.  When a
child subagent is constructed in `_build_child_agent()`, the code at
`tools/delegate_tool.py` line 1037–1038 inherits the parent's `acp_command`:

```python
effective_acp_command = override_acp_command or getattr(
    parent_agent, "acp_command", None
)
```

If the parent session somehow carries `acp_command` set (even to an empty
string after environment probing), the child will receive a non-None
`effective_acp_command`.  The child agent is then initialized with
`acp_command=effective_acp_command` which causes `agent_init.py` line 225 to
store it:

```python
agent.acp_command = acp_command or command
```

Even though the child's provider is set correctly (e.g. `deepseek`), the
presence of `acp_command` triggers the `CopilotACPClient` code path in
`agent_init.py` lines 622–624:

```python
if agent.provider == "copilot-acp":
    client_kwargs["command"] = agent.acp_command
```

However, the actual routing to ACP transport happens upstream during
provider resolution — the display label `Provider: copilot-acp` indicates
that the provider itself was resolved to `copilot-acp`, NOT just the
command being present.  The exact trigger path depends on the Hermes version
and how `copilot-acp` plugin interacts with the runtime provider resolver
(`hermes_cli/runtime_provider.py`).

Note: A fix was landed at commit `6b6fc28e8` that clears `acp_command` when
`override_provider` is explicitly set (i.e., `delegation.provider` is
configured).  But when `delegation.provider` is empty (`''`), the fix does
NOT fire, and the parent's `acp_command` can still leak through.

## Debugging

```bash
# 1. Check env vars that the copilot-acp client reads
echo "HERMES_COPILOT_ACP_COMMAND=$HERMES_COPILOT_ACP_COMMAND"
echo "COPILOT_CLI_PATH=$COPILOT_CLI_PATH"

# 2. Check if copilot CLI exists
which copilot  # None → not installed, ACP will always fail

# 3. Check delegation config (ensure no duplicate blocks)
grep -n '^delegation:' ~/.hermes/config.yaml
# Should appear exactly ONCE

# 4. Check provider config
grep -A2 '^delegation:' ~/.hermes/config.yaml | head -10
# provider: ''  is correct for inheriting from parent
```

## Fix Options

### Option A: Remove the plugin (cleanest)
```bash
mv ~/.hermes/hermes-agent/plugins/model-providers/copilot-acp \
   ~/.hermes/hermes-agent/plugins/model-providers/copilot-acp.bak
# Restart Hermes completely (Ctrl+C → relaunch)
```

### Option B: Explicit delegation provider
In `~/.hermes/config.yaml`, set:
```yaml
delegation:
  provider: deepseek
```
This makes `override_provider` truthy, which triggers the `6b6fc28e8` fix to
clear `acp_command`.  The child will use the DeepSeek provider directly.

### Option C: Ignore (if fallback works)
The error is self-healing — the fallback chain (`deepseek-v4-flash via deepseek`)
recovers within 3 retries (~15s).  Only bother fixing if the wasted time and
noise bothers you.

## Verification

After fixing, dispatch a test subagent and check its provider line:
```
[subagent-0] 🔌 Provider: deepseek  Model: deepseek-v4-flash
```
No more `copilot-acp` in the output.
