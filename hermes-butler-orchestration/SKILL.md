---
name: hermes-butler-orchestration
description: "管家编排手册 — SOUL.md 治理架构的执行索引层，含角色模板、pitfall 库、dispatch 清单（原名 subagent-driven-development）"
---

# Hermes Butler Orchestration

> **前置依赖**: 本 skill 依赖 `~/.hermes/SOUL.md` 作为治理宪法。如果你还没有 SOUL.md，先看 → [references/bootstrap-soil-md.md](references/bootstrap-soil-md.md)

Operational playbook for `delegate_task` subagents. This skill is the **Index Layer** between SOUL.md (Governance) and individual references/templates/scripts (Execution).

## Prerequisites

1. `~/.hermes/SOUL.md` 存在且 version ≥ 1.1, < 2.0
2. 如果没有，按 [bootstrap-soil-md.md](references/bootstrap-soil-md.md) 从零搭建（3 分钟）

## When To Load

Load this skill whenever:
- Spawning subagents via `delegate_task`
- Reviewing subagent output against verification protocols
- Following multi-agent orchestration patterns
- Performing git operations that affect the working tree (rebase, stash, conflict resolution)

## Reference Index

- **bootstrap**: references/bootstrap-soil-md.md — 3 分钟从零搭建 SOUL.md
- governance: references/governance-model.md — SOUL.md compatibility & version tracking
- verification: references/verification-protocol.md — test isolation & dirty-tree traps
- git workflows: references/git-stash-pop-conflict-pitfall.md — --ours/--theirs semantics in stash pop
- butler agent: references/butler-agent.md — Agent role definition
- dispatch: references/dispatch-checklist.md — Pre-dispatch validation
- security reviewer: references/security-reviewer-agent.md

## Templates

- `templates/documenter.md` — Documentation subagent goal template
- `templates/reviewer.md` — Code review subagent goal template
- `templates/implementer.md` — Implementation subagent goal template

## Scripts

- `scripts/post-update-restore.sh` — Post-hermes-update state restoration
- `scripts/hermes-update.sh` — Safe hermes update with pre/post hooks

## Core Principles

1. **Subagents have NO memory** — pass ALL context explicitly
2. **Self-reports are untrusted** — verify external side-effects yourself
3. **Leaf subagents cannot** use clarify, memory, send_message, execute_code
4. **Orchestrator subagents** retain delegate_task but still cannot clarify
5. **Halt Before Commit** applies to main agent AND subagent outputs that modify repos
