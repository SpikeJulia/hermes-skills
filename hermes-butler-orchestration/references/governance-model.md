# SOUL.md × Skill 治理模型 (Governance Model)

> 来源：GPT-5.5 架构评审，2026-06-05
> 背景：SOUL.md v1.1 升级后发现 subagent-driven-development (611行 auto_load) 与 SOUL.md 存在多维度治理权冲突

## 核心诊断

问题不是"谁更先进"，而是**两个文件都在试图成为最高行为准则**。

| 源头 | 定位 | 问题 |
|------|------|------|
| SOUL.md (54行) | Persona 人格载体 | 定义了工作流、熔断、测试策略 |
| subagent-driven-development (611行 auto_load) | 子 Agent 派发手册 | 也定义了工作流、熔断、测试策略 — 且与 SOUL.md 矛盾 |

## 冲突后果（比想象严重）

模型不是规则引擎，是概率推断器。矛盾指令同时注入不会"仲裁"，而是：
- Session A: 走 SOUL.md 规则
- Session B: 走 skill 规则
- Session C: 混合执行

**尤其危险的信号**：大文档天然获得更多注意力权重。611 行 vs 54 行 → skill 会吞噬 SOUL.md。

## 解决方案：B+ 模型

```
SOUL.md ──────── 唯一宪法 (Governance Layer)
    │             回答：为什么做 / 怎么决策 / 什么是成功
    │             ⚖️ 任何 skill 冲突 → SOUL.md wins
    │
skill SKILL.md ─ 执行手册索引入口 (Execution Layer)
    │             回答：具体怎么干
    │             40-70 行摘要，只做索引
    │
    ├─ references/ ─ 按需查阅的料库
    ├─ templates/  ─ 派单时 copy-paste
    └─ scripts/    ─ 运维脚本
```

## 边界判断标准

| 删除 SOUL.md | 删除 skill |
|-------------|-----------|
| Hermes 失去人格和治理规则 | Hermes 仍能工作 |
| 不可接受 | 效率下降、经验减少、模板没了 |

→ SOUL = Constitution（宪法），Skill = Playbook（作战手册）

## 实施要点

1. skill 中删除所有与 SOUL.md 重复的治理规则
2. skill 开头声明 `inherits SOUL.md v1.1`
3. SOUL.md 加入 `任何 skill 冲突 → 以此为准`
4. auto_load 保留但只灌 40-70 行摘要
5. references/templates/scripts 全部保留，按需加载

## 反面教材

旧 subagent-driven-development (v1.2.0, 611行) 的三种失败模式：
- 重复定义工作流（有自己的 "butler cycle"）
- 定义过时规则（3-fix limit vs 现在 S1-S4 severity）
- 大文档吞噬小文档（611行 vs 54行 → skill 获得更多注意力权重）
