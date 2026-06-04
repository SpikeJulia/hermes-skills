---
name: official-source-research
description: "When asked to research a technology/tool/project, go to the official website, GitHub official repository, or official documentation FIRST before using third-party summaries. 当要求调研某项技术/产品/项目时，优先去官网/GitHub 官方仓库查看一手资料，再以第三方资料作为补充验证。"
version: 1.0.0
metadata:
  hermes:
    tags: [research, verification, official-source, anti-hallucination, workflow]
    related_skills: [repo-design-research, spike, web-search-infra]
---

# Official Source Research (定向调研流)

Load this skill when the user asks to "看看" / "去看看" / "调研" / "研究一下" / "了解下" / "查一下" / "explore" / "look into" / "research" / "check out" a specific technology, tool, project, library, framework, or product — especially when a named project or technology is specified (e.g. "去看看 Supabase", "调研一下 Windsurf", "查一下 Hermes Agent 最新版本").

Do NOT load for:
- Code-level debugging → `systematic-debugging`
- Git archaeology on an existing repo → `repo-design-research`
- Throwaway prototypes → `spike`
- General news/buzz → `aihot` / `news-monitoring`

## Core Principle: One-Hop to Source

**Never start with blog posts, CSDN articles, or medium posts.** The research funnel is always:

```
🥇 Official Website (homepage, blog, docs)
🥇 Official GitHub Repository (README, Releases, Issues, Discussions)
🥈 Official Documentation Site (docs.xxx.com, api.xxx.com)
🥉 Community summaries, blog posts, third-party reviews — ONLY for cross-validation
```

If the user says a name that could refer to multiple things (e.g. "看看 Memory"), clarify which one before proceeding.

## Workflow (4 stages)

### Stage 1: Identify the Official Source

Determine the canonical source by:
1. **If well-known project**: navigate directly (`browser_navigate("https://github.com/org/repo")` or `"https://project.dev"`)
2. **If unknown**: use `web_search` with minimal context (e.g. `"ProjectName official website"` or `"ProjectName GitHub"`) to find the official URL — then open it. Do NOT rely on the search snippet alone.
3. **Verify authenticity**: Check that the GitHub org/repo name matches the official project identity (avoid lookalikes, forks mistaken for upstream, deprecated alternatives)

### Stage 2: Read Official Sources (depth-first)

Open the official homepage / GitHub README. Extract:

- **What is this?** — one-sentence positioning
- **Key features / value prop** — what makes it different
- **Version / release status** — latest stable, beta, alpha, archived?
- **Tech stack / prerequisites** — language, runtime, dependencies
- **License** — OSS license, pricing tier, self-hostable?
- **Quickstart / Installation** — how to get started in under 5 commands

For GitHub repos, prioritize in this order:

```bash
# 1. README.md - covers everything
# 2. Releases page - latest versions, changelogs
# 3. docs/ directory or wiki
# 4. Issues with "question" or "documentation" labels
# 5. Discussions
```

### Stage 3: Deep Dive (based on user's likely interest)

After the overview, look into areas relevant to the user's context:
- If the user is a **developer**: API, SDK, CLI usage, integration patterns
- If the user wants to **compare**: read official comparisons, benchmarks
- If the user is evaluating for **adoption**: pricing, self-hosting, migration guides
- If the user is **troubleshooting**: open issues, known limitations, workarounds

Use `browser_scroll` / `browser_click` / `browser_vision` to read in-page content. Use `browser_snapshot(full=true)` for text-dense pages.

### Stage 4: Synthesize & Cross-Validate

When reporting back:
1. **Lead with official source findings** — link to what you read directly
2. **Flag any discrepancies** — if the official docs say X but common wisdom says Y, note it explicitly
3. **Only then add third-party context** — "For additional context, community discussions suggest..."

## Output Format

Structure your findings as:

```markdown
## [Project Name] — 调研结果

### 官方信息
- **官网**: [URL](link)
- **GitHub**: [URL](link)
- **最新版本**: vX.Y.Z (YYYY-MM-DD)
- **定位**: 一句话总结
- **技术栈**: XXX
- **许可证 / 定价**: XXX

### 核心功能
- 功能 A
- 功能 B
- ...

### 关键发现 / 与我们相关的点
- ...

### 补充参考（第三方）
> 以下信息来自社区/第三方，建议自行验证：
- ...
```

## Pitfalls

- **Single-page apps with JS rendering**: `browser_navigate` + `browser_vision` for sites that rely heavily on JavaScript (typical for landing pages)
- **Docs sites with `/latest/` redirects**: always check the specific version, not just "latest"
- **GitHub default branch ≠ latest release**: check the Releases page, not just the main branch HEAD
- **README lies**: well-known. Cross-reference with actual code/docs when possible
- **Fork confusion**: verify the official org/repo name, don't trust the first search result
- **LLM cutoff confusion**: the user may be asking about a tool released after the model's training cutoff — this is when `browser_navigate` to official sources is most critical

## Verification Checklist

Before presenting results, verify:
- [ ] Did I start with the official website/GitHub repo?
- [ ] Did I read the actual README/docs, not just search snippets?
- [ ] Did I check release dates / version numbers directly?
- [ ] Did I flag any claims that came from third-party sources?
- [ ] Did I attempt to verify key claims across multiple official pages?