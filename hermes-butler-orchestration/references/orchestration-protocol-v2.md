# 编排协议 v2.0 (Orchestration Protocol v2)

> 2026-06-05 — GPT-5.5 架构评审驱动升级。SOUL.md 同步生效。

## 流水线：7 步

```
Clarify（澄清）→ Plan（规划）→ Assign（派发）→ Execute（执行）→ Verify（审核）→ Review（审查）→ Present（呈现）
```

对比 v1: `Clarify → Select Role → Dispatch → Verify → Test → Review → Present`
- 新增 `Plan`：复杂任务先出 plan 到 `.hermes/plans/`，主人确认
- 合并 `Select Role + Dispatch` → `Assign`
- `Test` 并入 `Verify`（测试是验证的子集）
- `Execute` 显式化（v1 隐含在 Dispatch→Verify 之间）

## TaskSpec：替代 5-Context

v1 用【当前状态、最终目标、技术栈边界、核心依赖、交付标准】— 是 Context 不是 Contract。

v2 用 TaskSpec 六要素：

| 要素 | 含义 | 反例 |
|------|------|------|
| **Goal** | 一句话最终产出 | "改一下登录"（太模糊） |
| **Scope** | 涉及文件/模块（glob） | 没说边界导致改到 OAuth |
| **OutOfScope** | 禁区 | 没标禁区 → 改了 signup |
| **DoD** | 可验证验收条件 | "看起来对了" |
| **Evidence** | 要求返回的凭据 | 无凭据 → 自报通过 |
| **Risk** | 高危操作标注 | 删库操作没标风险 |

## 测试分层

v1: "禁止自测" → v2: **允许自测，禁止自验收**

| Level | 角色 | 规则 |
|-------|------|------|
| **L1 单元测试** | 实现 Agent 自己 | ✅ 允许 |
| **L2 集成/E2E** | QA Agent 交叉指派 | ❌ 实现 Agent 禁止 |
| **L3 最终验收** | 管家 (小糖) | ❌ 任何人禁止自报通过 |

## 熔断：Severity-weighted

| Severity | 示例 | 最大重试 |
|----------|------|----------|
| **S1 致命** | 删库、数据损坏、生产事故 | 1 次 → 立刻升级 |
| **S2 高** | 核心功能逻辑错误 | 2 次 |
| **S3 中** | 类型/接口不匹配 | 3 次 |
| **S4 低** | 样式/文案 | 5 次 |

## artifact_id 铁律

任何外部副作用操作（HTTP POST/PUT、远程写、共享路径建文件、发布）：
- 子 Agent **必须返回** artifact_id（URL / ID / 绝对路径 / HTTP 状态码）
- 管家 Verify 阶段 **必须亲自** fetch URL / stat 文件 / read back
- artifact_id 无效或缺失 → 任务视同失败，走熔断

## max_spawn_depth

config.yaml: `delegation.max_spawn_depth: 2`（允许一层嵌套）
- depth=1（旧）: Hermes → leaf only
- depth=2（新）: Hermes → orchestrator → leaf (e.g. Architect → Test Agent)
