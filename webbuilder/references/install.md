# Installation

WebBuilder is a portable Skill folder. Install the whole `webbuilder/` directory, not only `SKILL.md`.

## Codex

Personal install:

```text
~/.codex/skills/webbuilder/
```

## Claude Code

Personal install:

```text
~/.claude/skills/webbuilder/
```

Project install:

```text
.claude/skills/webbuilder/
```

## Hermes

Personal install:

```text
~/.hermes/skills/webbuilder/
```

## Recommended Entry

Use the dynamic slash command when available:

```text
/webbuilder 初始化当前项目
/webbuilder 启用工作流
/webbuilder 根据 requirements.md 开始开发
/webbuilder 继续当前任务
/webbuilder 查看状态
/webbuilder 生成交付报告
```

Equivalent natural-language requests are also valid:

```text
use WebBuilder for this project
start WebBuilder mode
enable WebBuilder workflow
resume WebBuilder
```

## Optional Project Hook

Add this to `CLAUDE.md` or `AGENTS.md` only when the project should keep using Spec2Web after initialization:

```text
Use the webbuilder Skill only when explicitly requested or when webbuilder/loop-state.md exists with status active. Do not let it override ordinary coding tasks when the workflow has not been initialized.
```
