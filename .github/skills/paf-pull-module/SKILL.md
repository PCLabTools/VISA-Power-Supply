---
name: paf-pull-module
description: "Pull a PAF module from a git repository and wire it into the project. Use when: adding a module from git, cloning a module, git submodule, import module from repo, install module from URL."
argument-hint: "<git-repo-url>"
---

# Pull PAF Module from Git

Adds a remote PAF module as a git submodule under `src/paf/modules/`, then registers and instantiates it in the project.

## When to Use
- "Pull the SensorReader module from https://github.com/…"
- "Add this git repo as a PAF module: <url>"
- "Install a module from a git repository"

## Inputs

Collect from the user before proceeding (ask if not provided in the invocation):

1. **Git repository URL** — the URL to `git submodule add` (e.g. `https://github.com/org/paf-sensor-reader`)
2. **Module folder name** — snake_case name for the subfolder under `src/paf/modules/` (default: infer from the repo name by lowercasing and replacing hyphens with underscores, stripping any `paf-` prefix)

## Procedure

### Step 1 — Gather inputs

If the repo URL is not provided, ask now. Derive a suggested `module_name` from the URL's repo name and confirm with the user before proceeding.

### Step 2 — Add as a git submodule

Run:
```
git submodule add <repo-url> src/paf/modules/<module_name>
```

If `src/paf/modules/<module_name>/` already exists, stop and tell the user.

If `git submodule add` fails (e.g. not a git repo, network error), report the error and stop.

### Step 3 — Inspect the pulled module

Read `src/paf/modules/<module_name>/__init__.py` to discover what the module exports. Look for:
- The primary class name(s) in `__all__` or top-level `from … import …` statements
- Whether it is a **standard** or **factory** module (factory modules export a `Base<Name>` and `Simulated<Name>` alongside the factory class)

If no `__init__.py` exists or exports are unclear, warn the user that manual wiring may be needed and show what was found.

### Step 4 — Register in `src/paf/modules/__init__.py`

Add the import line after the existing imports:
```python
from .<module_name> import <ClassName>
```
Add `<ClassName>` to `__all__`.

For factory modules, also import `Base<ClassName>` and `Simulated<ClassName>` if exported.

### Step 5 — Instantiate in `src/main.py`

Add the import to the `from paf.modules import …` line.

Add instantiation in `Main.__init__()` following the existing pattern:
```python
# Standard:
<ClassName>("<module_name>", self.protocol, debug=self.debug)

# Factory:
<ClassName>("<module_name>", self.protocol, debug=self.debug, implementation_type="simulated")
```

For standard modules, also add a `send_action` call in `Main.run()` following the existing pattern:
```python
self.protocol.send_action("<module_name>", "custom_action", {"data": "Hello from main!"})
```

### Step 6 — Factory-only: PyInstaller hidden import

If the module is a factory type, remind the user to add to `scripts/build-exe.bat`:
```
--hidden-import paf.modules.<module_name>.simulated ^
```
(immediately after the existing `--hidden-import` lines)

### Step 7 — Confirm

List:
- The submodule path added
- Files modified (`src/paf/modules/__init__.py`, `src/main.py`)
- The class(es) now available

Remind the user to:
- Run `git submodule update --init --recursive` after cloning on other machines
- Run tests: `python -m unittest discover -s src -p "test_*.py"`

## Key Conventions

- The submodule folder name must match what is used in `from .<module_name> import …`
- If the pulled module does not follow PAF conventions (no `Module` subclass, no `__init__.py` exports), warn the user and skip Steps 4–5 rather than writing broken imports
- Do not modify `.gitmodules` manually — `git submodule add` handles it
