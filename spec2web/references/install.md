# Installation

Spec2Web V1.1 is a portable Skill folder. Install the whole `spec2web/` directory, not only `SKILL.md`.

## Codex

Personal install:

```text
~/.codex/skills/spec2web/
```

## Claude Code

Personal install:

```text
~/.claude/skills/spec2web/
```

Project install:

```text
.claude/skills/spec2web/
```

## Hermes

Personal install:

```text
~/.hermes/skills/spec2web/
```

## Recommended Entry

Use the dynamic slash command when available:

```text
/spec2web 初始化当前项目
/spec2web 启用工作流
/spec2web 根据 requirements.md 开始开发
/spec2web 继续当前任务
/spec2web 查看状态
/spec2web 生成交付报告
```

Equivalent natural-language requests are also valid:

```text
use Spec2Web for this project
start Spec2Web mode
enable Spec2Web workflow
resume Spec2Web
```

## Optional Project Hook

Add this to `CLAUDE.md` or `AGENTS.md` only when the project should keep using Spec2Web after initialization:

```text
Use the spec2web Skill only when explicitly requested or when spec2web/loop-state.md exists with status active. Do not let it override ordinary coding tasks when the workflow has not been initialized.
```
