# Vue 3 + Pinia Reactivity Pitfalls (in delegated frontend work)

These emerge when subagents build Vue frontends and the butler reviews. Caught during hermes-ui development.

## Critical: Pinia store mutations must trigger reactivity

In Socket.IO event callbacks (or any code outside Vue's component tree), direct property mutation on nested ref objects does NOT trigger Vue's reactivity system.

### ❌ WRONG — no re-render
```typescript
// In chat:token handler (Socket.IO callback)
const msgs = chatStore.messages[sessionId]
const last = msgs[msgs.length - 1]
last.content += data.text  // BUG: no reactivity trigger
```

### ✅ RIGHT — object spread creates new reference
```typescript
// In store action:
msgs[idx] = { ...last, content: last.content + text }
```

### ❌ WRONG — array push on nested ref
```typescript
messages.value[sessionId].push(message)
```

### ✅ RIGHT — array spread
```typescript
messages.value[sessionId] = [...messages.value[sessionId], message]
```

**Rule: every mutation in a Pinia store action must create a new reference.** Use `{ ...obj, key: newVal }` for objects, `[...arr, item]` for arrays.

## Naive UI `useMessage()` requires provider

If any component uses `useMessage()` from naive-ui, the root App.vue MUST wrap `<router-view>` with `<n-message-provider>`. Otherwise the component silently fails to render.

## AppLayout with router-view causes infinite recursion

If your views wrap themselves in a shared `<AppLayout>` component, and AppLayout itself contains `<router-view>`, Vue enters infinite recursion → renders `<!---->` (empty). Fix: AppLayout must use `<slot/>` instead of `<router-view/>`.

## Field name mismatch between frontend and backend

Always verify Socket.IO event payloads: backend emits `{ text: token }` but frontend listens for `{ token: data.token }` → silently drops all messages. Grep both sides for event payload shapes.

## Default models from config, not hardcoded

Never hardcode model names like `'gpt-4'`. Read real names from:
- Backend: parse `config.yaml` for provider→model mappings across ALL top-level keys
- Frontend: fetch from `GET /api/models` on mount, use first model as default

## Verification: browser, not just compile

After delegated fixes, verify in the browser with actual interactions (type message, press Enter, check DOM). TypeScript compilation and build alone do NOT catch reactivity bugs.
