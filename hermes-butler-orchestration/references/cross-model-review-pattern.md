# Cross-Model Review Pattern

## When to Use

When one model (A) has performed analysis/diagnosis and you want a second
model (B) to independently audit that work before acting on it. Common
triggers:

- Model A produced a root-cause analysis and fix plan
- The fix touches a critical state machine or core logic
- The user explicitly requests a second opinion ("用 DS 审查一下 M3")
- The task has high blast radius (chat store, auth, data persistence)

## Pattern

### Step 1: Model B reads the same source material Model A used
Don't trust Model A's excerpts or paraphrases. Go back to the original
code/files and read them independently. This is the single most important
step — cross-model review without independent source verification is
just sequential hallucination.

### Step 2: Verify each link in the diagnostic chain
For each claim Model A made:
- [ ] Is the code location correct? (line numbers, file paths)
- [ ] Is the flow description complete? (all code paths, not just the one cited)
- [ ] Are there other code paths that produce the same symptom?
- [ ] Is the scope accurate? (e.g., "only happens at run boundary" vs "also happens within-run")

### Step 3: Identify what was missed
The most valuable output of a cross-model review is what Model A **didn't**
see:
- Other trigger points for the same bug
- Edge cases not covered by the proposed fix
- Second handlers/code paths that need the same fix
- Harness/CI constraints Model A didn't know about

### Step 4: Present findings as a structured diff against Model A's analysis
Format:
```
1. Model A 的结论 → 我的验证结果
2. 遗漏/错误 → 我的修正
3. 方案评估 → 我的建议
```

## Real Example: Reasoning Merge Bug (2026-06-04)

- **Model A (MiniMax-M3)** diagnosed: `run.completed` clears `activeAssistantMessageId`,
  causing reasoning.delta to create new messages at run boundaries. Proposed 方案 A.
- **Model B (DeepSeek)** independently read chat.ts (~2700 lines), found:
  1. M3's root cause was correct but **incomplete** — `tool.started` (line 1748)
     also clears the pointer, causing the bug WITHIN a single run, not just at boundaries
  2. M3's fix only addressed run boundaries, would still produce N bubbles per run
  3. Corrected fix: remove the clear from tool.started + relax isStreaming gate in reasoning.delta
  4. Identified the two-handler symmetry requirement (live + history replay)

## Pitfalls

- **Don't review from M3's excerpt**: always read the original source
- **Don't trust line numbers**: code shifts between reads, use `grep -n` to re-locate
- **Check both handlers**: chat.ts has two identical event trees — if one has the bug, both do
