# Claude Code Delegation Pitfalls

Lessons from hermes-ui development session (2026-05-22).

## Pitfall 1: Redesigns Silently Drop Critical Functionality

When Claude Code rewrites a component for visual redesign, it can completely remove
business logic. In this session, ChatPanel.vue was redesigned for hermes-web-ui
visual style, and the entire Socket.IO chat pipeline was deleted:

```typescript
// BEFORE (working):
const socket = connectSocket()
socket.emit('chat:run', { sessionId, message, model })
socket.on('chat:token', (data) => { ... })
socket.on('chat:done', (data) => { ... })

// AFTER (broken — Claude Code redesign):
function handleSend(content: string) {
  chatStore.addMessage(...)  // local only, never hits backend!
}
```

**Prevention**: After ANY Claude Code component rewrite, the butler MUST diff-check:
1. All `socket.emit` / `socket.on` calls are preserved
2. All `import` statements for external modules (socket, stores, APIs)
3. All event handlers exist and connect to the backend
4. The `handleSend` or equivalent function actually communicates with the server

## Pitfall 2: UI Elements Go Missing During Redesign

Claude Code removed the Settings navigation icon from NavSidebar.vue during the
redesign. The Settings page existed but was unreachable without manually typing the URL.

**Prevention**: After redesign, verify EVERY navigation element from the plan:
- Router-links for all pages
- Action buttons (create, delete, save, send)
- Dropdowns and selectors
- Status indicators

## Pitfall 3: Store Synchronization Breaks

ModelSelector.vue updated `settingsStore.model` but NOT `chatStore.model`.
The session badge showed stale model labels because the two stores diverged.

```typescript
// BROKEN:
function selectModel(id: string) {
  settingsStore.setModel(id)  // only settings store
}

// FIXED:
function selectModel(id: string) {
  settingsStore.setModel(id)
  chatStore.model = id        // both stores
}
```

**Prevention**: For any component that modifies shared state, verify ALL stores
that depend on that value are updated. Check with: "what other components read
this value and would break if only one store is updated?"

## Pitfall 4: Component Recursion Kills Rendering

When AppLayout used `<router-view>` and ChatView/SettingsView wrapped themselves
in `<AppLayout>`, Vue hit infinite recursion and rendered `<!---->` (empty).

**Fix**: AppLayout should use `<slot />` when views wrap themselves in it.

**Prevention**: Check for recursive template patterns: if a view's template
contains the layout, the layout must NOT contain another `<router-view>`.

## Pitfall 5: Subagent Tests Are Shallow

Claude Code's built-in "verification" checks only:
- `vue-tsc --noEmit` (type check)
- `vite build` (build check)
- `curl` API endpoints

These do NOT catch: broken Socket.IO, missing UI elements, store sync bugs,
theme issues, or anything requiring actual browser interaction.

**The user's explicit requirement**: "所有按钮，所有功能，所有操作，都跑单元测试了吗"
(Every button, every function, every operation — did you run unit tests?)

**Required**: After subagent work, the butler MUST run browser-level E2E tests.
At minimum:
- Navigate to every page
- Click every button/icon
- Send a test message and verify streaming response
- Create/switch/delete sessions and verify reactivity
- Toggle settings and verify persistence
- Check browser console for JS errors
