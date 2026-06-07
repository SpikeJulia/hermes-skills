# Subagent Template Design: Patterns from the Field

Synthesized from GitHub research (2026-05-19). Sources: VoltAgent/awesome-claude-code-subagents (131+ templates, 20.1k stars), BMad Method, sing1ee/claude-code-agent-template.

## Three Schools of Thought

### 1. VoltAgent — Task-Oriented Checklist

**Structure:**
```
Frontmatter: name, description, tools, model
Persona: "You are a senior X with expertise in Y"
When Invoked: 4-step numbered process
Checklist: 5-8 measurable quality criteria
Workflow: 3 phases (Analysis → Implementation → Excellence)
Communication Protocol: JSON inter-agent messages
Integration: explicit cross-agent handoff points
```

**Strengths:** Complete, measurable, inter-agent aware
**Weakness:** 200-300 lines per template — context-expensive for subagents

### 2. BMad Method — Agile Role Commands

**Structure:**
```
YAML dependencies → declares templates/tasks/data needed
Agent = Role (PM/Architect/Dev/QA/SM/PO)
Command-driven: /pm create-doc prd, /dev implement story 1.2
Template-driven: templates embed LLM processing instructions
```

**Strengths:** Role = command, self-contained templates, lean context loading
**Weakness:** Full agile team granularity, not task-level

### 3. sing1ee — Persona-First Minimalism

**Structure:**
```
COACH_CONFIG.md → identity + style + language examples (core)
ME.md → user profile
Persona.md → psychological profile (evolves over time)
methodologies/ → pluggable frameworks
```

**Strengths:** Single-sentence core belief, "forbidden expressions" constraints, extremely compact
**Weakness:** Coach-specific, not general-purpose

## What to Adopt for Hermes

| Source | Adopt | Skip |
|--------|-------|------|
| VoltAgent | Persona→Trigger→Standards→Exit flow | 200+ line verbosity, JSON protocol |
| VoltAgent | Checklist as exit criteria | 20-item checklists |
| BMad | Agent = single command | Agile-specific terminology |
| sing1ee | One-sentence core belief | Coach-specific Persona system |
| sing1ee | "Never do" negative constraints | — |
| All three | Clear role boundaries | — |

## Hermes Subagent Template Format

Derived from above analysis — optimized for delegate_task context budgets:

```
Fields (7 total):
  role          — single word: implementer | reviewer | researcher
  goal          — one-sentence core belief (sing1ee style)
  when_to_use   — 2-3 trigger conditions, not a catalog
  steps         — max 5, one sentence each, imperative mood
  exit_criteria — explicit PASS/FAIL conditions
  never_do      — forbidden behaviors (sing1ee negative constraints)
  tools         — toolsets needed: terminal, file, web, etc.

Principles:
  - Total ≤ 40 lines
  - Every line is an operational directive, zero fluff
  - No "Communication Protocol" (Hermes handles this)
  - No "Integration with other agents" (butler coordinates)
  - No JSON examples (wastes context, model already knows JSON)
```

## Key Insight

The VoltAgent templates are excellent reference material but too heavy for subagent context windows. The art is extracting the *structure* (persona → trigger → workflow → exit) while radically compressing the *content*. A good subagent prompt is like a good commit message: says what and why, not how and everything.
