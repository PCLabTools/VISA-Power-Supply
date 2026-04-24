---
name: paf-new-module
description: "Create a new PAF module from scratch. Use when: adding a module, creating a new module, new standard module, new factory module, new actor, scaffold module."
argument-hint: "<module-name> [standard|factory] [--review]"
---

# New PAF Module

Creates a fully wired PAF module — source files, `__init__.py` export, and `main.py` registration — from the project templates.

## When to Use
- "Create a new module called SensorReader"
- "Add a factory module named MotorController"
- "Scaffold a new standard PAF module"

## Inputs

Collect from the user before proceeding (ask if not provided in the invocation):

1. **Module name** — e.g. `SensorReader`. Used to derive:
   - `ClassName` = PascalCase of the name (e.g. `SensorReader`)
   - `module_name` = snake_case of the name (e.g. `sensor_reader`)
   - `module_address` = lowercase of the name (e.g. `sensor_reader`)
2. **Module type** — `standard` or `factory`
3. **Description** — one-line description for the module's docstring
4. **Author** — for the file header (default: `"Your Name (your.email@example.com)"`)
5. **`--review` flag** _(optional)_ — If provided, automatically invoke the PAF Code Reviewer agent after module creation to validate architecture compliance

## Procedure

### Step 1 — Gather inputs

If the user has not provided the module name, ask now. Infer type from context if possible; otherwise ask. Default type is `standard`.

### Step 2 — Create the module folder

Create `src/paf/modules/<module_name>/` with these files:

#### For `standard` type:

**`module.py`** — copy from [./assets/standard_module.py](./assets/standard_module.py), replacing:
- `{{ClassName}}` → PascalCase class name
- `{{MODULE_DESCRIPTION}}` → user's description
- `{{AUTHOR}}` → author string

**`__init__.py`** — copy from [./assets/standard_init.py](./assets/standard_init.py), replacing:
- `{{ClassName}}` → PascalCase class name
- `{{module_name}}` → snake_case module name
- `{{AUTHOR}}` → author string

**`tests/__init__.py`** — create as an empty file.

**`tests/test_module.py`** — copy from [./assets/standard_test_module.py](./assets/standard_test_module.py), replacing:
- `{{ClassName}}` → PascalCase class name
- `{{module_name}}` → snake_case module name

**`scripts/run-tests.bat`** — copy from [./assets/run-tests.bat](./assets/run-tests.bat), replacing:
- `{{module_name}}` → snake_case module name

**`.gitignore`** — copy from [./assets/.gitignore](./assets/.gitignore) verbatim.

#### For `factory` type:

**`module.py`** — copy from [./assets/factory_module.py](./assets/factory_module.py), replacing all `{{ClassName}}` and `Base{{ClassName}}` placeholders.

**`simulated.py`** — copy from [./assets/factory_simulated.py](./assets/factory_simulated.py), replacing all `{{ClassName}}` and `Simulated{{ClassName}}` placeholders.

**`__init__.py`** — copy from [./assets/factory_init.py](./assets/factory_init.py), replacing all class name placeholders.

**`tests/__init__.py`** — create as an empty file.

**`tests/test_module.py`** — copy from [./assets/factory_test_module.py](./assets/factory_test_module.py), replacing:
- `{{ClassName}}` → PascalCase class name
- `Base{{ClassName}}` → `Base` + PascalCase class name
- `Simulated{{ClassName}}` → `Simulated` + PascalCase class name
- `Dummy{{ClassName}}` → `Dummy` + PascalCase class name
- `{{module_name}}` → snake_case module name

**`scripts/run-tests.bat`** — copy from [./assets/run-tests.bat](./assets/run-tests.bat), replacing:
- `{{module_name}}` → snake_case module name

**`.gitignore`** — copy from [./assets/.gitignore](./assets/.gitignore) verbatim.

### Step 3 — Register in `src/paf/modules/__init__.py`

Add the import and export. Example for standard:
```python
from .<module_name> import <ClassName>
```
Add `<ClassName>` to `__all__`.

For factory, also add `Base<ClassName>` and `Simulated<ClassName>`.

### Step 4 — Instantiate in `src/main.py`

Add the import at the top:
```python
from paf.modules import <ClassName>
```

Add instantiation in `Main.__init__()`:
```python
# Standard:
<ClassName>("<module_address>", self.protocol, debug=self.debug)

# Factory (assign to self if HTTP server needs reference, otherwise inline):
<ClassName>("<module_address>", self.protocol, debug=self.debug, implementation_type="simulated")
```

For factory type, also add a `send_action` call in `Main.run()` following the existing pattern.

### Step 5 — Optional: Code review (if `--review` flag provided)

If the user provided the `--review` flag:

1. Invoke the **PAF Code Reviewer agent** with the newly created module path
2. Report review findings to the user:
   - **No issues:** Confirm module passes PAF compliance checks
   - **Issues found:** Display violations with severity (high/medium/low)
3. For **high-severity issues**, ask user permission before proceeding:
   - Auto-fix structural issues if possible (naming, imports, file organization)
   - Defer business logic issues to the user
4. Include review summary in the final confirmation

**Example workflow:**

```
✓ Created module SensorReader
✓ Registered in src/paf/modules/__init__.py
✓ Instantiated in src/main.py

[Invoking PAF Code Reviewer...]

Review Results for sensor_reader:
• No high-severity issues found
• 1 medium-priority: background_task uses blocking sleep without timeout guard
  → Recommendation: Add timeout-aware polling loop

✓ Module ready for development
```

### Step 6 — Factory-only: PyInstaller hidden import

For factory modules, remind the user to add to `scripts/build-exe.bat`:
```
--hidden-import paf.modules.<module_name>.simulated ^
```
(immediately after the existing `--hidden-import` lines)
## Examples

### Create a standard module with review
```
Create a new module called SensorReader standard --review
```

### Create a factory module
```
Create a factory module named MotorController
```

### Create and immediately review
```
Add a module named DataLogger standard with code review
```
### Step 7 — Confirm

List all files created/modified. Remind the user to:
- Fill in any `# TODO:` placeholders in the new module
- Run per-module tests: `src/paf/modules/<module_name>/scripts/run-tests.bat`
- Run all tests: `python -m unittest discover -s src -p "test_*.py"`
- Review code review findings (if `--review` was used) and address medium/low-priority recommendations

## Key Conventions (from codebase)

- `self.debug` **must** be set before `super().__init__()` — the base class accesses it during startup
- `handle_message` returns `True` to shutdown, `False` to keep running
- Unknown commands must call `super().handle_message(message)` (raises `NotImplementedError` for truly unknown commands)
- Module addresses are plain lowercase strings
- Factory implementations **must** call `<FactoryClass>.register("name", <ImplClass>)` at import time (bottom of `simulated.py`)
