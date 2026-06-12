---
name: git-commit-log-writer
description: Fast, low-token commit message generation with optional direct git commit execution.
---

# Git Commit Log Skill

## Core Policy

- Default to `Generate mode`.
- Use `Execute mode` only for explicit commit-now intent (`commit this/now/just commit/go ahead and commit`, including equivalent Chinese intent).
- In `Execute mode`, rebase with upstream before commit when an upstream branch exists.
- Keep one commit scope coherent. Do not mix unrelated files.
- Prefer already staged files when staged scope matches intent.

## Context Collection Ladder (Cheapest First)

Run in this order and stop as soon as confident:

```powershell
git status --short
git diff --staged --name-status
git diff --name-status
```

If still unclear, inspect only target files:

```powershell
git diff --staged -- <file>
git diff -- <file>
```

Only when needed, use full patch views:

```powershell
git diff --staged
git diff
```

Optional style fallback:

```powershell
git log -30 --pretty=%s
```

## Message Rules

- Subject format: `<Verb> <primary component/change> [and <secondary change>]`
- Preferred verbs: `Add`, `Refactor`, `Enhance`, `Implement`, `Update`, `Fix`, `Remove`
- Subject must describe what changed (specific technical nouns), not vague intent.
- Add body only when useful (1-3 bullets, multi-module or non-obvious changes).

## Generate Mode Output

```text
Subject: <one-line subject>

Body (optional):
- <change point 1>
- <change point 2>

Commands:
git pull --rebase --autostash    # when upstream exists
git add <files or -A>
git commit -m "<subject>"
```

Body form when needed:

```powershell
git commit -m "<subject>" -m "<bullet 1>" -m "<bullet 2>"
```

## Execute Mode Steps

1. Collect context using the ladder above.
2. Rebase first when possible:
- Check upstream branch with PowerShell-safe quoting:
  `git rev-parse --abbrev-ref --symbolic-full-name '@{u}'`
- Never pass bare `@{u}` in PowerShell; it is parsed as a hash literal before Git receives it.
- If upstream exists, run `git pull --rebase --autostash`.
- If rebase fails/conflicts, stop and report; do not continue to commit.
3. Stage files:
- Reuse staged files when scope is correct.
- If nothing staged, run `git add <scoped files>`.
- Use `git add -A` only when user intent is clearly commit-all.
4. Commit with generated subject/body.
5. Return:

```text
Committed: <subject>
Commit: <short-hash>
Files: <count or list>
```

Use `git log -1 --oneline` for the hash. If nothing is commit-ready, state it clearly.

## Guardrails

- Subject must match actual diffs (not filenames only).
- Avoid vague text like `update stuff`.
- Never continue commit after a failed or unresolved rebase.
- Use non-interactive git flows.
- Do not use `--amend` unless explicitly requested.
