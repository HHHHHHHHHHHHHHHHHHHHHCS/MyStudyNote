---
name: git-commit-log-writer
description: Generate git commit messages and commit commands in the style of this repository. Use when preparing a commit, summarizing staged/unstaged changes, or asking for a ready-to-run commit title/body.
---

# Git Commit Log Skill

Follow this workflow to create commit messages aligned with this project.

## Style Baseline (from recent 30 commits)

- Start subject with an imperative verb: `Add`, `Refactor`, `Enhance`, `Implement`, `Update`, `Fix`, `Remove`.
- Use concise English, usually Title Case or sentence case with clear technical nouns.
- Mention concrete targets (for example: `shader`, `render pass`, `feature`, `system`, `assets`).
- Combine closely related work with `and`.
- Keep one-line subject focused on what changed, not why.

Preferred subject pattern:

`<Verb> <primary component/change> [and <secondary change>]`

Examples:

- `Add StrobePages render feature and assets`
- `Refactor and extend physically based sky rendering`
- `Add AtmosphericScattering render pass, remove define`
- `Enhance physically based sky rendering and LUT precomputation`

## Commit Message Generation Workflow

1. Inspect repo state.
2. Group changes into one coherent commit scope.
3. Pick one primary verb from the style baseline.
4. Generate subject line with concrete module names.
5. Optionally generate a short body when multiple files/systems changed.

## Commands to Collect Context

```powershell
git status --short
git diff --name-only
git diff --staged --name-only
git diff --staged
```

## Output Format

Return commit suggestion in this format:

```text
Subject: <one-line subject>

Body (optional):
- <change point 1>
- <change point 2>

Commands:
git add <files or -A>
git commit -m "<subject>"
```

If body is needed, use:

```powershell
git commit -m "<subject>" -m "<bullet 1>" -m "<bullet 2>"
```

## Quality Checks Before Commit

- Subject reflects actual changed files.
- Verb and wording match repository style.
- No unrelated files are mixed in the same commit.
- Subject is readable and specific (avoid vague words like `update stuff`).

## Fast Prompt Template

Use this prompt with the assistant:

```text
Read current git changes and generate one commit message in this repo's style.
Return:
1) Subject
2) Optional body bullets
3) Exact git add / git commit command
```

