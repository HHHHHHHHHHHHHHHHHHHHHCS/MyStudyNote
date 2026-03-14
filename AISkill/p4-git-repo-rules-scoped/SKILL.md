
# Skill: P4 / Git Repository Rules (Scoped)

## Purpose
Ensure version control actions use the correct VCS based on directory path.

## Scope Limitation
This rule set applies **only to the following directories and their subdirectories**:

- F:\MyProjects
- F:\MyProjects\TestProject
- E:\MyUnrealEngine

Any other directory on the system **must follow the default behavior** of the agent and should not be constrained by this skill.

## Repository Mapping

### Perforce (P4) Repositories
The following directories are **Perforce workspaces**:

- F:\MyProjects
- F:\MyProjects\TestProject

For these directories and all subdirectories:

Use **Perforce (P4)** for all version control operations.

Typical operations include:

- submit
- checkout / edit
- revert
- diff
- status
- add / delete
- resolve
- sync
- changelist management

Recommended commands:

- p4 edit
- p4 opened
- p4 diff
- p4 revert
- p4 submit
- p4 sync

Do **not** use Git commands for these directories.

Forbidden examples:

- git status
- git add
- git commit
- git checkout
- git restore

### Git Repository

The following directory is a **Git repository**:

- E:\MyUnrealEngine

For this directory and all subdirectories:

Use **Git** for version control operations.

Typical commands:

- git status
- git add
- git commit
- git diff
- git checkout
- git pull

## Decision Logic

1. Determine which repository the target path belongs to.

2. If the path is inside:

   F:\MyProjects  
   or  
   F:\MyProjects\TestProject

   → Treat it as a **Perforce workspace** and use **P4 commands only**.

3. If the path is inside:

   E:\MyUnrealEngine

   → Treat it as a **Git repository** and use **Git commands**.

4. If a task involves both repositories:

   - Separate the operations by path.
   - Use **P4 for ProjectFY_hcs / FYGame**
   - Use **Git for FYEngine**
   - Never mix commands for the same directory.

## Behavior Requirements

When generating:

- commands
- scripts
- automation workflows
- troubleshooting steps

Always respect the repository boundaries defined above.

Before suggesting version control commands, identify whether the path belongs to **P4 or Git**.

## Default Behavior for Other Directories

If the directory is **not one of the three listed paths**, the agent should:

- Use its normal repository detection logic.
- Automatically detect Git / P4 / other systems if applicable.
- Not enforce the rules defined in this skill.

This skill **is not a global rule**, it is only a **targeted constraint for the three directories above**.
