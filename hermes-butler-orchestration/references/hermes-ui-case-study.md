# Hermes UI Case Study — Full-Stack Web Chat UI via Subagent-Driven Development

Date: 2026-05-22
Subagents: Claude Code (kimi-k2.6 via Kimi Coding API)

## Architecture

```
Browser (Vue 3 + Naive UI) → HTTP/WS → Koa 2 (8649) → hermes CLI
```

### Tech Stack
- **Frontend**: Vue 3 + TypeScript + Vite + Naive UI + Pinia + Vue Router + Socket.IO client + markdown-it + highlight.js
- **Backend**: Koa 2 + Socket.IO + child_process.spawn
- **Storage**: JSON files (~/.hermes-ui/data/)
- **Chat Bridge**: `hermes chat -q "message" -m model -Q`

### Project Structure
```
hermes-ui/
├── package.json          # npm workspaces: ["client", "server"]
├── client/               # Vue 3 SPA
│   ├── src/
│   │   ├── views/        # ChatView.vue, SettingsView.vue
│   │   ├── components/   # layout/, chat/, settings/
│   │   ├── stores/       # chat.ts, settings.ts (Pinia)
│   │   ├── api/          # http.ts, socket.ts
│   │   └── types/
│   └── dist/             # Vite build output
└── server/
    └── src/
        ├── index.ts      # Koa + Socket.IO + SPA fallback
        ├── routes/       # sessions, models, settings
        ├── bridge/       # chat.ts (hermes CLI spawn)
        └── storage/      # JSON file-based session store
```

## Dispatch Pattern

### Task 1: Project Skeleton (serial, 1 subagent)
```
delegate_task(acp_command='claude', goal="Create project skeleton...")
```
- Outcome: All config files, type stubs, npm install. vue-tsc + tsc both passed.
- Duration: ~3.5 min, 19 API calls

### Task 2: Backend Implementation (serial, 1 subagent)
```
delegate_task(acp_command='claude', goal="Implement FULL backend...")
```
- Outcome: Session CRUD, model discovery (auth.json), settings, Socket.IO chat with hermes CLI bridge.
- Duration: ~2 min, 29 API calls
- Key detail: `hermes chat` uses `-q` not `--prompt`, `-Q` for quiet mode.

### Task 3: Full Frontend (serial, 1 subagent)
```
delegate_task(acp_command='claude', goal="IMPLEMENT THE ENTIRE FRONTEND...")
```
- Outcome: 10 components + 2 views + 2 stores. All working with streaming, themes, Markdown.
- Duration: ~4 min, 50 API calls (hit max_iterations but completed)

### Butler Review & Fixes

Three bugs found during butler review:

1. **Infinite recursion**: AppLayout used `<router-view />` → ChatView/SettingsView wrapped AppLayout → infinite recursion → Vue renders `<!---->`.
   - Fix: Change `<router-view />` to `<slot />` in AppLayout.

2. **Blank settings page**: SettingsForm used `useMessage()` without `<n-message-provider>` → component crash → blank page.
   - Fix: Wrap `<router-view>` with `<n-message-provider>` in App.vue.

3. **SPA routing 404**: Backend returned 404 for /settings (client-side route).
   - Fix: Add catch-all middleware that serves index.html for non-API routes.

## Verification Checklist

After each subagent task, the butler should verify:
- [ ] TypeScript: `npx vue-tsc --noEmit` and `npx tsc --noEmit` pass
- [ ] Build: `npx vite build` or equivalent succeeds
- [ ] Server starts without crash
- [ ] REST API endpoints return expected data
- [ ] Browser renders the UI correctly
- [ ] Core user flow works (in this case: send message → streaming response)

## Naive UI Pitfalls

- `useMessage()`, `useDialog()`, `useNotification()` all require `<n-message-provider>` / `<n-dialog-provider>` / `<n-notification-provider>` in the component tree. Missing provider = silent crash.
- `useMessage()` must be called inside `setup()`, not in event handlers.
- Naive UI components can be used via global `app.use(naive)` OR per-component imports. Mixing both is fine but imports must be from 'naive-ui'.

## Vue Router Pitfalls

- `createWebHistory()` needs server-side SPA fallback (catch-all → index.html).
- When a layout component wraps page components, use `<slot>` not `<router-view>` — otherwise infinite recursion.
- `<router-link>` works for client-side nav; `<a href>` causes full reload.
