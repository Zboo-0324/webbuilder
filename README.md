# WebBuilder

<div align="center">

**面向全栈 Web 交付的自适应多智能体 Workflow Skill**

需求基线 · 技术栈推荐 · 界面设计基线 · 任务拆解 · Loop Engineering · PR/Worktree 交接 · 验证交付

![skill](https://img.shields.io/badge/skill-webbuilder-blue)
![install](https://img.shields.io/badge/install-Codex%20%7C%20Claude%20Code%20%7C%20Hermes-black)
![language](https://img.shields.io/badge/language-%E4%B8%AD%E6%96%87%20%7C%20English-blue)

中文 | [English](./README_EN.md)

</div>

WebBuilder 是一个轻量级 Skill，用来指导 AI 编程智能体完成全栈 Web 项目的交付流程。

它不是运行时、代码生成器、MCP Server、后台调度器或项目模板。Spec2Web 的重点是给智能体一套可恢复、可审查、可验证的工作流，让它从需求出发，逐步完成设计、拆解、开发、验证、修复和交付，同时保持方向、边界和项目记忆。

## 它能做什么

Spec2Web 会帮助智能体：

- 在实现前读取项目规则
- 建立需求基线
- 用第一性原理记录核心目标、硬约束、假设证据和阻塞问题
- 推荐并记录技术栈策略
- 在前端开发前定义界面设计基线
- 产出系统设计
- 将工作拆解成有边界的小任务
- 根据宿主容量和任务风险选择单会话、单任务委派或并行批次
- 通过 PR/worktree 交接推进任务：Orchestrator 派发，子代理开发提交，Orchestrator 审查、测试、验收、集成
- 按任务风险升级审查：高风险任务必须进行对抗性审查，并由独立 Tester 和 Reviewer 交叉审核
- 在 Git 项目中默认使用 task branch 和 worktree 隔离开发任务
- 在任务完成后继续推进下一个 ready task，直到阻塞或交付
- 记录验证证据和交付说明

## 它不做什么

Spec2Web 不会：

- 根据一句提示生成完整应用
- 提供全栈代码模板
- 作为后台服务运行
- 自动调度 worker 池
- 调用 Claude 或外部 AI 服务充当 worker
- 提供 MCP Server 或全局 CLI
- 自动部署应用
- 替代用户对高影响决策的确认

## 仓库结构

```text
webbuilder/
  SKILL.md
  agents/
    openai.yaml
  references/
    delivery-checklist.md
    install.md
    interface-design.md
    loop-engineering.md
    multi-agent-orchestration.md
    reasoning-and-review.md
    role-protocol.md
    state-files.md
    task-breakdown.md
    technology-strategy.md
    worktree-mode.md
  scripts/
    init-state.py
    check-state.py
    migrate-state.py
```

## 安装

请安装整个 `webbuilder/` 文件夹，而不是只复制 `SKILL.md`。

### Codex

```powershell
git clone https://github.com/Zboo-0324/spec2web.git
Set-Location spec2web

$src = (Resolve-Path ".\webbuilder").Path
$dst = "$env:USERPROFILE\.codex\skills\webbuilder"

New-Item -ItemType Directory -Force -Path (Split-Path $dst) | Out-Null
robocopy $src $dst /MIR
```

安装后重启 Codex。

### Claude Code

```powershell
git clone https://github.com/Zboo-0324/spec2web.git
Set-Location spec2web

$src = (Resolve-Path ".\webbuilder").Path
$dst = "$env:USERPROFILE\.claude\skills\webbuilder"

New-Item -ItemType Directory -Force -Path (Split-Path $dst) | Out-Null
robocopy $src $dst /MIR
```

安装后重启 Claude Code。

### Hermes

```powershell
git clone https://github.com/Zboo-0324/spec2web.git
Set-Location spec2web

$src = (Resolve-Path ".\webbuilder").Path
$dst = "$env:USERPROFILE\.hermes\skills\webbuilder"

New-Item -ItemType Directory -Force -Path (Split-Path $dst) | Out-Null
robocopy $src $dst /MIR
```

安装后重启 Hermes。

## 使用方式

当你希望启用 Spec2Web 工作流时，显式调用它：

```text
/webbuilder initialize this project
/webbuilder enable workflow
/webbuilder start from requirements.md
/webbuilder continue current task
/webbuilder show status
/webbuilder generate delivery report
```

也可以用自然语言：

```text
use Spec2Web for this project
start Spec2Web mode
resume Spec2Web
```

WebBuilder 不应该自动接管普通编码任务。只有当用户显式要求，或项目中存在 active 的 `webbuilder/loop-state.md` 时，它才持续约束后续全栈开发工作。

## 项目状态文件

在项目中初始化后，WebBuilder 会创建：

```text
webbuilder/
  project-rules.md
  requirements-baseline.md
  system-design.md
  task-plan.md
  loop-state.md
  validation-log.md
  delivery-report.md
```

这些文件是项目记忆的事实来源。对话上下文不能替代它们。

## 状态脚本

初始化状态文件：

```powershell
python webbuilder/scripts/init-state.py --target .
```

迁移已有状态：

```powershell
python webbuilder/scripts/migrate-state.py --target . --dry-run
python webbuilder/scripts/migrate-state.py --target .
```

迁移会先在项目的 `webbuilder/` 状态目录中创建时间戳备份；验证通过后请删除或保持本地，不要提交备份目录。

检查状态结构：

```powershell
python webbuilder/scripts/check-state.py --target . --phase structure
```

开始应用代码任务前，运行执行门禁：

```powershell
python webbuilder/scripts/check-state.py --target . --phase execution
```

最终交付前，运行交付门禁：

```powershell
python webbuilder/scripts/check-state.py --target . --phase delivery
```

检查脚本提供七个阶段：

- `structure`：schema、必要文件、智能体编排元数据、设计章节、任务契约和状态取值
- `execution`：已确认需求、已就绪的规则/设计/任务基线、无占位内容和 active 工作流
- `task`：选定任务、依赖、任务级审核策略、执行模式、交接方式、工作区和当前任务状态
- `parallel`：宿主容量、批次大小、独立 worktree、路径与声明式语义冲突、每任务审核策略
- `acceptance`：逐任务提交包、身份独立性、对抗性案例、分歧和 critical 控制证据
- `integration`：已验收任务、集成策略与提交、主工作区复验证据
- `delivery`：全部任务的验收和集成证据闭环、交付报告完成和终态工作流

旧版本状态文件不会被初始化脚本覆盖。将 V1、V1.0、V1.1 或 V1.2 状态迁移到 schema 1.3 后，缺少风险依据的任务会被标记为 `unclassified`，必须由 Planner 显式补充分类后才能执行。

## 工作流

顶层工作流：

```text
Project Rules
-> User Discovery Gate
-> First-Principles Analysis
-> Requirement Baseline
-> Technology Strategy
-> Interface Design Baseline
-> System Design
-> Task Breakdown
-> Task Execution Loop
-> Integration Validation
-> Delivery
```

WebBuilder 会先读取用户的一句话需求或已有需求文档，由 AI 形成产品需求假设，再一次只询问一个真正影响方向的问题。问题优先提供 2-3 个具体选项和推荐，不要求用户自行撰写核心需求或回答专业问卷；最终由用户确认 AI 汇总的需求与设计。`discovery_status` 在用户确认前保持 `pending`。

单个任务循环：

```text
Read State
-> Select Next Task or Parallel Batch
-> Select single, delegated, or parallel Execution Mode
-> Create Task Branch and Worktree when Git is available
-> Delegate Worker with Task Contract
-> Worker Commits to Task Branch
-> PR Handoff Submission
-> Test and Review
-> Acceptance Gate
-> Formal Integration Point
-> Integration Gate and Main-Workspace Verification
-> Repair or Record
-> Update State
```

一个任务完成后，只要 `loop-state.md` 仍为 active，且下一个任务依赖满足、验证方法明确、没有停止条件，Orchestrator 就继续推进下一个任务。

只有当 `project-rules.md`、`system-design.md`、`task-plan.md` 为 `ready`，`requirements-baseline.md` 为 `confirmed`，且执行门禁通过后，才开始编写应用代码。最终交付还要求所有任务为 `complete`、`delivery-report.md` 为 `complete`、`loop-state.md` 为 `current_phase: delivery` 和 `status: delivered`，并通过交付门禁。

## PR/Worktree 模式

Spec2Web 对 Git 项目中的委派或并行任务使用 PR/worktree 交接：

- 默认一次执行一个任务
- 受控多 worker 模式只允许无冲突任务批次
- worker 数量不得超过 ready task 数量和宿主报告的空闲子智能体槽位
- Orchestrator 创建 task branch 和 worktree
- 子代理 worker 只在自己的 worktree 中开发并提交到 task branch
- worker 提交本地 PR 包或远程 PR 后停止
- Orchestrator 通过 `merge`、`squash_merge`、`cherry_pick` 或 `integration_commit` 串行集成
- 每次集成后都需要在主工作区重新验证

Spec2Web 不提供自动 worker 池，也不提供无人值守的批量集成调度器。

Spec2Web 允许使用当前 Codex 宿主提供的本地或 Codex 云端智能体；未经用户明确授权，不调用第三方 AI 服务或外部智能体产品。

对于非 Git 项目或明确采用单会话回退的任务，使用 `handoff_mode: single_session` 和 `integration_strategy: direct_apply`；它表示改动已在主工作区中，由 Orchestrator 验收并完成主工作区验证，不虚构 merge 或 commit。

## 验证

运行状态脚本 smoke check：

```powershell
$tmp = Join-Path $env:TEMP "spec2web-smoke"
Remove-Item -Recurse -Force -LiteralPath $tmp -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $tmp | Out-Null
python webbuilder/scripts/init-state.py --target $tmp
python webbuilder/scripts/check-state.py --target $tmp --phase structure
```

校验 Skill 包：

```powershell
python -X utf8 "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py" webbuilder
```

## 设计原则

- 保持轻量。
- 用显式状态文件作为项目记忆。
- 将大任务拆成有边界的小任务。
- 声称完成前必须验证。
- 分离 Maker 和 Checker 角色。
- 用角色责任与评价标准驱动审查，而非只要求智能体模仿角色语气。
- 仅对高风险或关键任务强制对抗性审查和 Tester/Reviewer 分离。
- 优先沿用现有项目约定。
- 改变已确认需求、增加高风险依赖、使用凭证或消耗付费资源前，必须询问用户。
