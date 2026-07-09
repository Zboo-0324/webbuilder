# Spec2Web

<div align="center">

**面向 AI 编程智能体的全栈 Web 交付 Workflow Skill**

需求基线 · 技术栈推荐 · 界面设计基线 · 任务拆解 · Loop Engineering · PR/Worktree 交接 · 验证交付

![skill](https://img.shields.io/badge/skill-spec2web-blue)
![install](https://img.shields.io/badge/install-Codex%20%7C%20Claude%20Code%20%7C%20Hermes-black)
![language](https://img.shields.io/badge/language-%E4%B8%AD%E6%96%87%20%7C%20English-blue)

中文 | [English](./README_EN.md)

</div>

Spec2Web 是一个轻量级 Skill，用来指导 AI 编程智能体完成全栈 Web 项目的交付流程。

它不是运行时、代码生成器、MCP Server、后台调度器或项目模板。Spec2Web 的重点是给智能体一套可恢复、可审查、可验证的工作流，让它从需求出发，逐步完成设计、拆解、开发、验证、修复和交付，同时保持方向、边界和项目记忆。

## 它能做什么

Spec2Web 会帮助智能体：

- 在实现前读取项目规则
- 建立需求基线
- 推荐并记录技术栈策略
- 在前端开发前定义界面设计基线
- 产出系统设计
- 将工作拆解成有边界的小任务
- 通过 PR/worktree 交接推进任务：Orchestrator 派发，子代理开发提交，Orchestrator 审查、测试、验收、集成
- 在 Git 项目中默认使用 task branch 和 worktree 隔离开发任务
- 在任务完成后继续推进下一个 ready task，直到阻塞或交付
- 记录验证证据和交付说明

## 它不做什么

Spec2Web V1 不会：

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
spec2web/
  SKILL.md
  agents/
    openai.yaml
  references/
    delivery-checklist.md
    install.md
    interface-design.md
    loop-engineering.md
    role-protocol.md
    state-files.md
    task-breakdown.md
    technology-strategy.md
    worktree-mode.md
  scripts/
    init-state.py
    check-state.py
```

## 安装

请安装整个 `spec2web/` 文件夹，而不是只复制 `SKILL.md`。

### Codex

```powershell
git clone https://github.com/Zboo-0324/spec2web.git
Set-Location spec2web

$src = (Resolve-Path ".\spec2web").Path
$dst = "$env:USERPROFILE\.codex\skills\spec2web"

New-Item -ItemType Directory -Force -Path (Split-Path $dst) | Out-Null
robocopy $src $dst /MIR
```

安装后重启 Codex。

### Claude Code

```powershell
git clone https://github.com/Zboo-0324/spec2web.git
Set-Location spec2web

$src = (Resolve-Path ".\spec2web").Path
$dst = "$env:USERPROFILE\.claude\skills\spec2web"

New-Item -ItemType Directory -Force -Path (Split-Path $dst) | Out-Null
robocopy $src $dst /MIR
```

安装后重启 Claude Code。

### Hermes

```powershell
git clone https://github.com/Zboo-0324/spec2web.git
Set-Location spec2web

$src = (Resolve-Path ".\spec2web").Path
$dst = "$env:USERPROFILE\.hermes\skills\spec2web"

New-Item -ItemType Directory -Force -Path (Split-Path $dst) | Out-Null
robocopy $src $dst /MIR
```

安装后重启 Hermes。

## 使用方式

当你希望启用 Spec2Web 工作流时，显式调用它：

```text
/spec2web initialize this project
/spec2web enable workflow
/spec2web start from requirements.md
/spec2web continue current task
/spec2web show status
/spec2web generate delivery report
```

也可以用自然语言：

```text
use Spec2Web for this project
start Spec2Web mode
resume Spec2Web
```

Spec2Web 不应该自动接管普通编码任务。只有当用户显式要求，或项目中存在 active 的 `spec2web/loop-state.md` 时，它才持续约束后续全栈开发工作。

## 项目状态文件

在项目中初始化后，Spec2Web 会创建：

```text
spec2web/
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
python spec2web/scripts/init-state.py --target .
```

检查状态文件：

```powershell
python spec2web/scripts/check-state.py --target .
```

检查脚本会验证必要状态文件和关键标记，包括：

- workflow 状态
- task-plan 字段
- 技术栈策略
- 界面设计基线
- 连续执行约束

## 工作流

顶层工作流：

```text
Project Rules
-> Requirement Baseline
-> Technology Strategy
-> Interface Design Baseline
-> System Design
-> Task Breakdown
-> Task Execution Loop
-> Integration Validation
-> Delivery
```

单个任务循环：

```text
Read State
-> Select Next Task or Parallel Batch
-> Create Task Branch and Worktree when Git is available
-> Delegate Worker with Task Contract
-> Worker Commits to Task Branch
-> PR Handoff Submission
-> Test and Review
-> Orchestrator Acceptance
-> Formal Integration Point or Repair or Record
-> Update State
```

一个任务完成后，只要 `loop-state.md` 仍为 active，且下一个任务依赖满足、验证方法明确、没有停止条件，Orchestrator 就继续推进下一个任务。

## PR/Worktree 模式

Spec2Web 在 Git 项目中默认使用 PR/worktree 交接：

- 默认一次执行一个任务
- 受控多 worker 模式只允许无冲突任务批次
- Orchestrator 创建 task branch 和 worktree
- 子代理 worker 只在自己的 worktree 中开发并提交到 task branch
- worker 提交本地 PR 包或远程 PR 后停止
- Orchestrator 通过 `merge`、`squash_merge`、`cherry_pick` 或 `integration_commit` 串行集成
- 每次集成后都需要在主工作区重新验证

V1 不提供自动 worker 池，也不提供无人值守的批量集成调度器。

## 验证

运行状态脚本 smoke check：

```powershell
$tmp = Join-Path $env:TEMP "spec2web-smoke"
Remove-Item -Recurse -Force -LiteralPath $tmp -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $tmp | Out-Null
python spec2web/scripts/init-state.py --target $tmp
python spec2web/scripts/check-state.py --target $tmp
```

校验 Skill 包：

```powershell
python "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py" spec2web
```

## 设计原则

- V1 保持轻量。
- 用显式状态文件作为项目记忆。
- 将大任务拆成有边界的小任务。
- 声称完成前必须验证。
- 分离 Maker 和 Checker 角色。
- 优先沿用现有项目约定。
- 改变已确认需求、增加高风险依赖、使用凭证或消耗付费资源前，必须询问用户。

## 路线图

V2 可以考虑：

- 更完整的 Codex、Claude Code、Hermes 分发打包
- 可选全局 CLI
- 更强的状态验证器
- 自动 worktree 池和冲突分析
- 示例项目
- marketplace 或 hub 分发元数据
