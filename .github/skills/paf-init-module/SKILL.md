---
name: paf-init-module
description: "Initialize a PAF module as a git submodule with safe conflict handling. Use when: paf-init-module, init-module, convert module to submodule, add module from git, pull module repository, replace local module folder with submodule."
argument-hint: "[module_name]"
---

# Initialize Module as Submodule

Converts a module under `src/paf/modules/` into a git submodule safely, with user-controlled conflict decisions.

## When to Use
- "Run paf-init-module for hello_world"
- "Convert this module folder into a submodule"
- "Pull this module from git into src/paf/modules"

## Inputs

Collect these before making changes:

1. **Module name** (snake_case folder name under `src/paf/modules/`)
2. **Git repository URL** for that module (required if the module is not already a submodule)

If `module_name` is not provided in invocation arguments, ask for it first.

## Procedure

### Step 1 - Resolve module name

- If invocation includes a module name, use it.
- Otherwise, ask the user: "Which module should I initialize as a submodule?"

Set:
- `module_path = src/paf/modules/<module_name>`

### Step 2 - Check whether it is already a submodule

Run one or both checks:

1. `git submodule status -- src/paf/modules/<module_name>`
2. Inspect `.gitmodules` for a section with `path = src/paf/modules/<module_name>`

Decision:
- If already a submodule: **stop immediately** and report no action taken.
- If not a submodule: continue.

### Step 3 - Ask for repository URL

Ask for the git URL if it was not provided:
- Example: `https://github.com/org/paf-my-module`

Validate it is non-empty. If missing, stop and explain why no action was taken.

### Step 4 - Preflight safety checks

- Confirm the workspace is a git repository.
- Check whether `module_path` exists.

Branch:
- If `module_path` does not exist: go directly to Step 6 (`git submodule add`).
- If `module_path` exists: continue to Step 5 for safe conversion.

### Step 5 - Safe conversion when folder already exists

The folder must be empty for `git submodule add`. Do not delete files.

1. Create temporary backup directory inside the repository, for example:
   - `src/paf/modules/.tmp/<module_name>-pre-submodule-<timestamp>/`
2. Move all existing files from `module_path` into that temporary directory.
3. Verify `module_path` is now empty (or removed).

If move fails, stop and restore any partially moved files.

### Step 6 - Add the submodule

Run:

```bash
git submodule add <repo_url> src/paf/modules/<module_name>
```

If this fails, stop and surface the exact error.

If Step 5 created a backup, continue to Step 7.

### Step 7 - Restore previous files and surface conflicts

Reconcile backup content with the newly cloned submodule directory.

1. Compute relative-path overlaps between:
   - backup files
   - files currently in `module_path` (from cloned submodule)
2. Present overlaps to the user as potential conflicts.
3. Ask the user to choose a strategy before copying anything:
   - **Keep submodule files** (skip conflicting backup files)
   - **Keep previous local files** (overwrite conflicts with backup files)
   - **Manual per-file merge** (pause and let user decide file-by-file)
   - **Abort and restore original module folder**

Important:
- Do not choose conflict resolution automatically.
- Leave all conflict decisions to the user.
- If overlaps exist, require an explicit user choice before continuing.

After user choice:
- Apply the chosen strategy.
- Copy non-conflicting backup files into the submodule folder.
- If user chose abort, use a simple, context-appropriate restore approach and restore the original module folder from backup.

### Step 8 - Final verification and report

Report:
- Whether module is now a submodule
- Submodule path and URL
- Whether backup content was restored
- Any conflicts and which strategy was selected
- Any files requiring manual follow-up

## Quality Checks

Before declaring success, verify:

1. `git submodule status -- src/paf/modules/<module_name>` returns the module.
2. `.gitmodules` contains `src/paf/modules/<module_name>`.
3. If backup existed, confirm temporary directory is either:
   - removed after successful restore, or
   - kept intentionally with user acknowledgement.
4. User-confirmed conflict strategy was applied.

## Failure Handling

- If module already submodule -> stop with an informational message.
- If URL missing/invalid -> stop and ask for valid URL.
- If `git submodule add` fails -> show stderr and stop.
- If restore/conflict processing fails -> stop and preserve both backup and cloned submodule so the user can decide next action.

## Notes

- Never use `rm -rf` / force-delete as a default path in this workflow.
- Never hide merge conflicts; always show the conflict list to the user.
- Temporary backups must remain under `src/paf/modules/.tmp/` unless the user requests otherwise.
- Do not modify unrelated project files unless user explicitly asks for module wiring or registration changes.
