# Governance Architecture — SOUL.md vs Skill 分层

> 2026-06-05，SOUL.md v1.1 + subagent-driven-development v2.0 重构完成。此文记录架构决策与教训。

## 问题：双脑治理 (Split-Brain Governance)

重构前，SOUL.md 和 subagent-driven-development skill **同时声称自己是管家行为准则**：

```
SOUL.md  ─┐
           ├─ workflow 定义
SKILL.md ─┘

SOUL.md  ─┐
           ├─ 熔断规则
SKILL.md ─┘

SOUL.md  ─┐
           ├─ 测试策略
SKILL.md ─┘
```

后果：
- 同一概念被定义两次，版本不同步
- 模型收到的两条矛盾指令，每次仲裁结果不稳定
- 长 skill (611行) 天然获得更多注意力权重，侵蚀短 SOUL (57行)

## 方案：五层单向继承

```
Layer 1  SOUL.md (~56行)        Governance — 唯一宪法
           ⚖️ 任何 skill 冲突时 SOUL.md 最高优先
           仅容 Persona / Governance / Decision Rules
           膨胀即信号 → 迁移至 skill references

Layer 2  SKILL.md (~75行)       Index — 执行手册入口
           governance_version: "1.1"
           compatible_with: "SOUL.md >=1.1,<2.0"

Layer 3  references/ (39)       Knowledge — 按需查阅

Layer 4  templates/  (9)        Execution — 派单模板

Layer 5  scripts/    (2)        Operations — 运维脚本
```

## 关键规则

1. **SOUL.md wins**: 编排纪律 §开头声明"任何 skill 冲突时以此为准"
2. **Version binding**: SKILL.md 含 `governance_version` + `compatible_with`，SOUL 升级时防静默漂移
3. **SOUL.md 维护边界**: 仅容 Persona / Governance / Decision Rules。案例库、pitfall、技术细节 → 迁移至 skill references
4. **auto_load 体量控制**: 611→75 行，保留索引入口，不灌知识库

## 判断标准

- 删除 SOUL → Hermes 失去人格和治理规则
- 删除 Skill → Hermes 仍能工作，只是效率下降、模板缺失
- 这证明：SOUL = Constitution, Skill = Playbook

## 相关文件

- `~/.hermes/SOUL.md` — 宪法层
- `~/.hermes/skills/software-development/subagent-driven-development/SKILL.md` — 索引层
- GPT-5.5 三次评审记录（本 session 对话历史）
