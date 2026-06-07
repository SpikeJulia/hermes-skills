# Frontend Debugging Pitfalls (Vue 3 + Pinia + Socket.IO)

Lessons from hermes-ui development where chat messages didn't render despite data flowing correctly.

## Ladder of Reactivity Failures

When UI doesn't update but data appears correct, check in this order:

### 1. Socket.IO Event Field Name Mismatch
Backend emits `socket.emit('chat:token', { text: chunk })` but frontend listens for `(data) => data.token`.
→ Silent failure: handler runs but `data.token` is `undefined`. Always verify field names match across the wire.

### 2. Pinia Store Direct Property Mutations
```js
// BROKEN — Vue doesn't track nested property changes in Socket.IO callbacks
const last = msgs[msgs.length - 1]
last.content += data.text

// FIXED — Create new object reference to trigger reactivity
msgs[idx] = { ...last, content: last.content + data.text }
```
Same for arrays: use `[...arr, item]` instead of `arr.push(item)`.

### 3. Component Computed Values Not Recomputing
```js
// BROKEN — parseContent() runs once at setup, result destructured as plain vars
const { thinking, mainContent } = parseContent(props.message.content)
const mainContentHtml = computed(() => renderMarkdown(mainContent))

// FIXED — Wrap parsing in computed() so it re-runs on prop change
const parsed = computed(() => parseContent(props.message.content))
const mainContentHtml = computed(() => renderMarkdown(parsed.value.mainContent))
```

### 4. Backend Default Values Propagating Stale Labels
Frontend store has `model = ref('gpt-4')`, backend storage has `model: data.model || 'gpt-4'`.
New sessions always labeled 'gpt-4' regardless of actual model.
→ Fix: frontend loads real model from `/api/models`, backend reads from settings.json.

## Debugging Methodology

### Browser Console Injection
Add temporary `console.log` to Socket.IO handlers:
```js
socket.on('chat:token', (data) => {
  console.log('[DEBUG] chat:token', { len: data.text?.length, preview: data.text?.substring(0, 30) })
  // ... existing handler
})
```
Then check `browser_console` after sending a message to confirm which events fire.

### Screenshot Before/After Comparison
The most reliable verification method:
1. `browser_vision` → "BEFORE" screenshot
2. Perform action (send message, delete session)
3. `browser_vision` → "AFTER" screenshot  
4. Compare: did the expected change occur?

### Fake Data Detection
When UI shows numbers/data, verify against the real source:
- Token counter "1K / 200.0k" → Does Hermes have a token counting API? No → remove it.
- Model name "gpt-4" → Is gpt-4 in auth.json? No → read from config.yaml.
- Attachment icon → Is file upload implemented? No → remove it.

## Model Name Resolution
Hermes config.yaml stores models as:
```yaml
model:
  provider: minimax-cn
  default: MiniMax-M2.7
vision:
  provider: kimi-coding
  model: kimi-for-coding
compression:
  provider: deepseek
  model: deepseek-v4-flash
```
Scan ALL top-level keys for `{provider, model/default}` pairs.
Do NOT use `config.providers.<key>.model` (it's empty).
Filter out providers with empty credentials in auth.json.
