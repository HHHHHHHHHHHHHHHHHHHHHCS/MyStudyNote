---
name: git-commit-log-writer
description: Generate repository-style git commit messages and either provide ready-to-run commands or execute git commit directly. Use when preparing a commit, summarizing staged/unstaged changes, asking for a commit title/body, or explicitly asking to commit changes now.
---

# Git Commit Log Skill

Follow this workflow to create commit messages aligned with this project and execute commits when requested.

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

## Execution Modes

- `Generate mode`: Return subject/body and exact commands, but do not run `git commit`.
- `Execute mode`: When the user explicitly asks to commit now, run `git add` and `git commit` directly.

Use `Execute mode` for requests such as `commit this`, `直接提交`, `帮我提交`, `提交这些改动`.

## Commands to Collect Context

```powershell
git status --short
git diff --name-only
git diff --staged --name-only
git diff --staged
git diff
```

## Output Format

For `Generate mode`, return:

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

For `Execute mode`, perform these steps:

1. Inspect current changes.
2. Stage files:
   - Prefer already staged files if they match the intended scope.
   - If nothing is staged, run `git add <files>` for scoped files, or `git add -A` only when the request implies committing all current changes.
3. Run `git commit` with generated subject/body.
4. Return:

```text
Committed: <subject>
Commit: <short-hash>
Files: <count or list>
```

Use `git log -1 --oneline` to report the resulting commit hash.
If there is nothing to commit, state that clearly and do not fabricate a commit.

## Quality Checks Before Commit

- Subject reflects actual changed files.
- Verb and wording match repository style.
- No unrelated files are mixed in the same commit.
- Subject is readable and specific (avoid vague words like `update stuff`).
- Do not use interactive commit flows.
- Do not use `--amend` unless the user explicitly requests amend.

## Fast Prompt Template

Use this prompt with the assistant:

```text
Read current git changes and produce one commit in this repo's style.
If I explicitly ask to commit, execute git add + git commit.
Return:
1) Subject
2) Optional body bullets
3) Exact git add / git commit command or executed commit hash
```
