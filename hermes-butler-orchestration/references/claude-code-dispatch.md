# Claude Code Dispatch via delegate_task

## Pre-flight: Verify Claude Code Availability

Before dispatching, check:
```bash
which claude && claude --version
# → /home/tangxuan/.nvm/versions/node/v24.13.1/bin/claude
# → 2.1.146 (Claude Code)

cat ~/.claude/settings.json
# Verify: ANTHROPIC_BASE_URL, ANTHROPIC_AUTH_TOKEN, ANTHROPIC_DEFAULT_MODEL
```

Quick smoke test:
```bash
claude --print "say hello, nothing else"
```

## Model Switching

Claude Code model is set via `ANTHROPIC_DEFAULT_MODEL` in `~/.claude/settings.json`:
```json
"env": {
  "ANTHROPIC_BASE_URL": "https://api.kimi.com/coding/",
  "ANTHROPIC_DEFAULT_MODEL": "kimi-k2.6"
}
```
User's current model: kimi-k2.6 (Kimi Coding API).

## Dispatch Pattern

```python
delegate_task(
    goal="...clear, specific, outcome-oriented...",
    toolsets=["terminal", "file"],
    acp_command="claude"
)
```

- `acp_command='claude'` spawns Claude Code as the subagent transport
- Toolsets: minimum needed — `terminal` for npm/tsc/vite, `file` for writing code
- Goal must reference PLAN.md path for full context
- Subagent has NO memory of your conversation — pass all constraints in goal/context

## Review Checklist After Claude Code Returns

Claude Code reports "completed" — but DO NOT TRUST this blindly:

1. **Type check**: `npx vue-tsc --noEmit` (frontend) / `npx tsc --noEmit` (backend)
2. **Build**: `npx vite build` (frontend)
3. **Startup**: start the server, verify it listens
4. **API smoke test**: curl key endpoints
5. **Browser verification**: open in browser, check DOM renders
6. **Route verification**: test ALL routes (not just /)
7. **Check for common Vue pitfalls**: see below

## Common Vue 3 + Naive UI Gotchas

### Infinite Recursion via router-view
**Symptom**: Page renders empty, DOM shows `<!---->` in route content area.
**Cause**: A route component wraps `<AppLayout>` which contains `<router-view>`. When the route component renders, the inner router-view tries to render the same route component → infinite loop → Vue bails out.
**Fix**: Use `<slot />` in AppLayout instead of `<router-view />`. Each view provides its content as slot children.

Pattern before (BROKEN):
```html
<!-- AppLayout.vue -->
<main><router-view /></main>

<!-- ChatView.vue -->
<AppLayout><ChatPanel /></AppLayout>  <!-- AppLayout's router-view tries to render ChatView again! -->
```

Pattern after (FIXED):
```html
<!-- AppLayout.vue -->
<main><slot /></main>

<!-- ChatView.vue -->
<AppLayout><ChatPanel /></AppLayout>  <!-- ChatPanel goes into slot ✅ -->
```

### useMessage() Requires Provider
**Symptom**: Page goes completely white/blank on specific routes.
**Cause**: `useMessage()` from Naive UI requires `<n-message-provider>` as an ancestor.
**Fix**: Wrap `<router-view>` or app root with `<n-message-provider>` in App.vue:
```html
<template>
  <n-message-provider>
    <router-view />
  </n-message-provider>
</template>
```

### SPA Fallback for Koa
**Symptom**: Direct navigation to /settings returns 404 or empty page.
**Cause**: SPA uses client-side routing — server must return index.html for all non-API routes.
**Fix**: After `koa-static`, add catch-all middleware:
```ts
const indexPath = path.join(clientDistPath, 'index.html')
app.use(async (ctx, next) => {
  await next()
  if (ctx.status === 404 && !ctx.path.startsWith('/api')) {
    ctx.type = 'html'
    ctx.body = fs.createReadStream(indexPath)
    ctx.status = 200
  }
})
```
