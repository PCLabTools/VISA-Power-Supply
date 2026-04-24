---
name: paf-remove-module
description: "Remove a PAF module from the project. Use when: deleting a module, removing a module, unregister module, clean up module, delete actor."
argument-hint: "<module-name>"
---

# Remove PAF Module

Safely removes a PAF module — deletes its folder and strips all references from `src/paf/modules/__init__.py` and `src/main.py`.

## When to Use
- "Remove the Tester module"
- "Delete the SensorReader module"
- "Clean up the MotorController module"

## Inputs

Collect from the user before proceeding (ask if not provided in the invocation):

1. **Module name** — the name of the module to remove. Used to derive:
   - `ClassName` = PascalCase (e.g. `Tester`)
   - `module_name` = snake_case folder name (e.g. `tester`)
   - `module_address` = the address string used in `main.py` (usually same as `module_name`)

## Procedure

### Step 1 — Gather inputs

If module name is not provided, ask now. Confirm with the user before proceeding — deletion cannot be undone.

### Step 2 — Verify the module exists

Check that `src/paf/modules/<module_name>/` exists. If not, tell the user and stop.

Also check `src/paf/modules/__init__.py` to confirm the import is present, and inspect `src/main.py` to identify:
- The import line referencing `<ClassName>`
- The instantiation line(s) in `Main.__init__()`
- Any `send_action` calls using the module's address in `Main.run()`

For factory modules, also check `scripts/build-exe.bat` for a `--hidden-import` line referencing the module.

### Step 3 — Check for git submodule and remove the folder

First, check whether the module folder is a git submodule by running:
```
git submodule status src/paf/modules/<module_name>
```

**If it is a git submodule**, remove it properly using:
```
git submodule deinit -f src/paf/modules/<module_name>
git rm -f src/paf/modules/<module_name>
```
This updates `.gitmodules`, removes the submodule entry from `.git/config`, and deletes the working tree — without corrupting the parent repository. Do **not** use `rm -rf` or `Remove-Item` for submodule folders.

**If it is not a git submodule**, delete the folder directly:
```
# PowerShell:
Remove-Item -Recurse -Force src/paf/modules/<module_name>
```

### Step 4 — Update `src/paf/modules/__init__.py`

Remove:
- The `from .<module_name> import <ClassName>` line (and `Base<ClassName>`, `Simulated<ClassName>` for factory)
- `<ClassName>` (and related names) from the `__all__` list

### Step 5 — Update `src/main.py`

Remove all of the following that are present:
- The import of `<ClassName>` from the `from paf.modules import …` line (or the whole line if it's the only import)
- The instantiation line `<ClassName>("…", self.protocol, …)` in `Main.__init__()`
- Any `self.protocol.send_action("<module_address>", …)` calls in `Main.run()` that target this module

### Step 6 — Factory-only: build script cleanup

If the module was a factory type, remind the user to remove the corresponding `--hidden-import paf.modules.<module_name>.simulated ^` line from `scripts/build-exe.bat`.

### Step 7 — Confirm

List all files deleted/deregistered and all lines removed from modified files. If a submodule was removed, note that `.gitmodules` and `.git/config` were updated automatically. Suggest running:
```
python -m unittest discover -s src -p "test_*.py"
```
to verify nothing else was broken.

## Key Conventions

- Only remove what directly references this module — do not touch unrelated imports or logic
- If `<ClassName>` is the only import on its `from paf.modules import …` line in `main.py`, remove the entire line; otherwise only remove the name from the list
- `standard_template`, `factory_template`, and `webserver` are built-in framework modules — warn the user and ask for explicit confirmation before removing any of these
