# PAF Template Project

A starting point for building **multi-threaded Python applications** using the **Python Agent Framework (PAF)** — a lightweight, message-passing framework that lets independent modules communicate with each other through a unified protocol.

Project purpose and intent are documented in [PROJECT.md](PROJECT.md). In this template repository, it explains template-level intent; after forking, update it with project-specific intent.

---

## Overview

Modern applications often need to run multiple tasks concurrently — reading sensors, processing data, serving a UI, logging — without these concerns tangling together. PAF solves this by giving each concern its own **module**: a self-contained unit running in its own thread, communicating only through messages.

This template project provides:

- A pre-wired application entry point (`src/main.py`)
- The PAF communication library (`src/paf/communication/`)
- A working example module (`HelloWorld`)
- A module scaffold system powered by GitHub Copilot skills

---

## How It Works

### Modules

Each module is a class that extends `Module` and runs in its own thread. Modules do not call each other directly — they send messages.

```text
┌──────────┐        ┌──────────┐        ┌──────────┐
│  Main    │        │ Module A │        │ Module B │
│ (thread) │──────▶ │ (thread) │──────▶ │ (thread) │
└──────────┘  msg   └──────────┘  msg   └──────────┘
```

### Protocol

The `Protocol` is the message bus. Every module registers with it at startup and is assigned an address. Any part of the application can send a message to any module by address.

```python
protocol.send_action("sensor_reader", "read", {"channel": 1})
```

### Messages

A `Message` carries a destination address, a command string, and an optional data payload. Messages are delivered via a thread-safe priority queue — one per module address.

```python
Message(address="sensor_reader", command="read", data={"channel": 1})
```

### Module Types

| Type | Description |
| --- | --- |
| **Standard** | Extends `Module` directly. Simple, single-implementation modules. |
| **Factory** | Uses a factory pattern with a `Base<Name>` ABC and swappable implementations (e.g. `Simulated<Name>` for testing). |

---

## Project Structure

```text
src/
├── main.py                        # Application entry point
└── paf/
    ├── communication/             # PAF framework (git submodule)
    │   ├── message.py             # Message class
    │   ├── protocol.py            # Protocol (message bus)
    │   └── module.py              # Module base class
    └── modules/
        ├── __init__.py            # Public module exports
        └── hello_world/           # Example standard module
            ├── module.py
            ├── __init__.py
            ├── tests/
            └── scripts/
scripts/
    └── build-exe.bat              # PyInstaller build script
```

---

## Getting Started

Prefer guided setup in Copilot Chat? Use the `paf-init` skill at `.github/skills/paf-init/SKILL.md` to initialize submodules, `.venv`, and dependencies automatically.

### 1. Clone with submodules

```bash
git clone --recurse-submodules <repo-url>
```

Or if already cloned:

```bash
git submodule update --init --recursive
```

### 2. Create a virtual environment

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
python src/main.py
```

### 5. Run the tests

```bash
python -m unittest discover -s src -p "test_*.py"
```

You can also run tests directly from Copilot Chat using the `/paf-test` prompt, which discovers all module tests, runs them, and returns a formatted report with a summary table, per-module details, and failure output. Type `/paf-test` in the chat panel, or target a specific module:

```text
/paf-test hello_world
```

---

## Adding and Removing Modules

This project includes GitHub Copilot skills that automate module management. See the [Developer Guide](#developer-guide-using-paf-copilot-skills) below for full details.

**Quick reference:**

| Task | Skill |
| --- | --- |
| Initialize project environment | `paf-init` |
| Define project intent and module plan | `paf-init-project` |
| Create a new module | `paf-new-module` |
| Add implementation to a factory module | `paf-new-implementation` |
| Remove a module | `paf-remove-module` |
| Add a module from git | `paf-pull-module` |
| Initialize/convert module as submodule safely | `paf-init-module` |
| Code review (project or module) | `PAF Code Reviewer` agent |
| Run all tests | `test-runner` agent |
| Test report in chat | `/paf-test` prompt |

---

## Building an Executable

```bat
scripts\build-exe.bat
```

Produces a standalone `.exe` in `dist/` via PyInstaller.

> If your project includes factory modules, ensure each has a `--hidden-import paf.modules.<module_name>.simulated` line in the build script — PyInstaller cannot detect dynamic registrations automatically.

---

---

## Developer Guide: Using PAF Copilot Skills

This project includes a set of GitHub Copilot skills that automate common PAF module tasks directly from the chat panel. This guide explains what each skill does and how to invoke it.

---

## How to Invoke a Skill

Open the Copilot Chat panel in VS Code and attach the skill's prompt file using the `#` file reference, then describe your intent. The simplest form is:

```text
Follow instructions in #prompt:SKILL.md with these arguments: <args>
```

Each skill also has a natural-language description that allows Copilot to invoke it automatically when you describe what you want — e.g. _"create a new module called SensorReader"_ will trigger `paf-new-module` without needing to attach the file manually.

---

## Available Skills

### 1. `paf-init` — Initialize the development environment

**File:** `.github/skills/paf-init/SKILL.md`

Bootstraps the project so `src/main.py` can run: initializes git submodules, creates or reuses `.venv`, installs dependencies from available manifests, validates imports, and performs an optional startup smoke check.

**Arguments:**

- `--recreate-venv` _(optional — force rebuild of `.venv`)_
- `--skip-main-check` _(optional — skip startup smoke check)_

**Examples:**

```text
Follow instructions in #prompt:SKILL.md with these arguments: paf-init
```

```text
Follow instructions in #prompt:SKILL.md with these arguments: paf-init --recreate-venv
```

---

### 2. `paf-init-project` — Define project intent and module plan

**File:** `.github/skills/paf-init-project/SKILL.md`

Runs a structured project-start discovery workflow that interviews the user, refines project intent, updates `PROJECT.md`, optionally records reusable constraints in `MEMORY.md`, and breaks high-level goals into candidate PAF modules.

**Arguments:**

- `--max-rounds <1-20>` _(optional — maximum number of interview rounds, default `20`)_
- `--skip-memory` _(optional — do not write reusable rules to `MEMORY.md`)_

**Examples:**

```text
Follow instructions in #prompt:SKILL.md with these arguments: paf-init-project
```

```text
Follow instructions in #prompt:SKILL.md with these arguments: paf-init-project --max-rounds 12
```

```text
Initialize this fork by interviewing me and mapping the goals into PAF modules
```

**What it does:**

1. Reads existing `PROJECT.md` and `MEMORY.md`
2. Runs an iterative interview with explicit continue/finish control after each question
3. Merges and preserves existing project intent by default, replacing older content only when explicitly requested or clearly superseded by newer user input
4. Produces a structured project definition in `PROJECT.md`
5. Identifies candidate PAF modules, responsibilities, and message boundaries
6. Stores only concise reusable rules in `MEMORY.md`

---

### 3. `paf-new-module` — Create a new module

**File:** `.github/skills/paf-new-module/SKILL.md`

Creates a fully wired PAF module from scratch: generates all source files, registers the export in `src/paf/modules/__init__.py`, and instantiates it in `src/main.py`. Optionally invokes automated code review to validate architecture compliance.

**Arguments:**

- Module name (PascalCase)
- Module type: `standard` or `factory`
- Description _(optional — will ask if omitted)_
- Author _(optional — defaults to placeholder)_
- `--review` _(optional — automatically review with PAF Code Reviewer agent after creation)_

**Examples:**

```text
Follow instructions in #prompt:SKILL.md with these arguments: SensorReader standard
```

```text
Follow instructions in #prompt:SKILL.md with these arguments: MotorController factory --review
```

```text
Create a new module called DataLogger standard with code review
```

**What gets created** (standard example for `SensorReader`):

| File | Description |
| --- | --- |
| `src/paf/modules/sensor_reader/module.py` | Module class with `handle_message` and `background_task` |
| `src/paf/modules/sensor_reader/__init__.py` | Public export |
| `src/paf/modules/sensor_reader/tests/test_module.py` | Unit tests (includes start/stop/status and cycle tests) |
| `src/paf/modules/sensor_reader/tests/__init__.py` | Test package marker |
| `src/paf/modules/sensor_reader/scripts/run-tests.bat` | Per-module test runner |
| `src/paf/modules/sensor_reader/.gitignore` | Ignores `__pycache__` |

**What gets modified:**

- `src/paf/modules/__init__.py` — adds `from .sensor_reader import SensorReader` and updates `__all__`
- `src/main.py` — adds import, instantiation in `__init__`, and `send_action` call in `run()`

**Code Review (with `--review` flag):**

When `--review` is provided, the skill automatically invokes the PAF Code Reviewer agent to validate the new module against PAF conventions:

- **High-severity issues:** Reported and may be auto-fixed (naming, structure) with user confirmation
- **Medium/Low-priority:** Displayed as recommendations for manual review
- **Report:** Included in final confirmation before completion

> **Factory modules** additionally generate `simulated.py` and `Base`/`Simulated` class variants, and prompt you to add a `--hidden-import` line to `scripts/build-exe.bat`. Review is especially useful for factory modules to validate implementation patterns.

---

### 4. `paf-remove-module` — Remove a module

**File:** `.github/skills/paf-remove-module/SKILL.md`

Safely removes a PAF module — deletes its folder and strips all references from `__init__.py` and `main.py`. Handles both regular folders and git submodules correctly.

**Arguments:**

- Module name

> ⚠️ Built-in modules (`standard_template`, `factory_template`, `webserver`) trigger an explicit confirmation prompt before proceeding.

**Examples:**

```text
Follow instructions in #prompt:SKILL.md with these arguments: SensorReader
```

```text
Follow instructions in #prompt:SKILL.md with these arguments: webserver
```

**What happens:**

1. Confirms the module exists
2. Detects whether it is a git submodule (`git submodule status`)
   - **Submodule:** runs `git submodule deinit -f` + `git rm -f` (updates `.gitmodules` and `.git/config`)
   - **Regular folder:** runs `Remove-Item -Recurse -Force`
3. Removes the import from `src/paf/modules/__init__.py`
4. Removes the import, instantiation, and any `send_action` calls from `src/main.py`
5. For factory modules: reminds you to remove the `--hidden-import` line from `scripts/build-exe.bat`

---

### 5. `paf-pull-module` — Add a module from a git repository

**File:** `.github/skills/paf-pull-module/SKILL.md`

Pulls a remote PAF module as a git submodule, then registers and instantiates it — the reverse of `paf-remove-module`.

**Arguments:**

- Git repository URL
- Folder name _(optional — inferred from the repo name by default)_

**Examples:**

```text
Follow instructions in #prompt:SKILL.md with these arguments: https://github.com/PCLabTools/PAF-Module-Simple-Web-Server.git
```

```text
Follow instructions in #prompt:SKILL.md with these arguments: https://github.com/PCLabTools/PAF-Module-Standard-Template.git standard_template
```

**What happens:**

1. Runs `git submodule add <url> src/paf/modules/<module_name>`
2. Reads the module's `__init__.py` to discover exported class names
3. Registers in `src/paf/modules/__init__.py`
4. Adds import and instantiation to `src/main.py`
5. For factory modules: reminds you to add `--hidden-import` to `scripts/build-exe.bat`

---

### 6. `paf-new-implementation` — Add an implementation to a factory module

**File:** `.github/skills/paf-new-implementation/SKILL.md`

Creates a new implementation file for an existing factory module by inheriting from its `Base<ClassName>`, generating all required abstract method overrides, registering the implementation key, and updating module exports.

**Arguments:**

- Factory module name _(required)_
- Implementation name _(required)_

If arguments are omitted, the skill asks for them and does not continue until both are provided.

**Examples:**

```text
Follow instructions in #prompt:SKILL.md with these arguments: paf-new-implementation motor_controller hardware
```

```text
Follow instructions in #prompt:SKILL.md with these arguments: paf-new-implementation sensor_reader mock
```

**What happens:**

1. Validates the target module is factory-style
2. Extracts abstract methods from `Base<ClassName>`
3. Creates `src/paf/modules/<module_name>/<implementation_name>.py`
4. Registers with `<FactoryClass>.register("<implementation_name>", <ImplementationClass>)`
5. Updates `src/paf/modules/<module_name>/__init__.py` exports
6. Runs module tests with unittest top-level set to `src`

**Method body generation modes:**

### `safe-stub` (default)

- `-> bool` returns `False`
- `-> None` or `Optional[...]` returns `None`
- Other annotated returns use `NotImplementedError` placeholders

### `not-implemented`

- Every generated method uses `raise NotImplementedError("TODO: implement <method_name>")`

---

### 7. `paf-init-module` — Initialize or convert a module into a git submodule

**File:** `.github/skills/paf-init-module/SKILL.md`

Safely initializes a module path under `src/paf/modules/` as a git submodule, including conflict-aware conversion when a local folder already exists.

**Arguments:**

- Module name _(optional — if omitted, the skill asks before proceeding)_

If the target module is already a git submodule, the skill stops immediately with no changes.

**Examples:**

```text
Follow instructions in #prompt:SKILL.md with these arguments: paf-init-module hello_world
```

```text
Follow instructions in #prompt:SKILL.md with these arguments: paf-init-module
```

**What happens:**

1. Resolves module name (asks if missing)
2. Checks whether `src/paf/modules/<module_name>` is already a submodule
3. If not a submodule, asks for repository URL
4. If a folder already exists, moves current files to `src/paf/modules/.tmp/...`
5. Runs `git submodule add <url> src/paf/modules/<module_name>`
6. Detects path overlaps between moved files and cloned submodule content
7. Forces explicit user conflict choice before restore/merge
8. Reports final state and any follow-up items

---

### 8. `PAF Code Reviewer` — Automated code review agent

**Invocation:** Request code review in Copilot Chat using the `PAF Code Reviewer` agent

Provides automated architecture review and best-practice analysis for the entire project or specific modules. Validates module implementations against PAF conventions, identifies potential issues, and suggests improvements.

**When to use:**

- Reviewing a new module before merging
- Validating architecture changes
- Checking for compliance with PAF patterns
- Bug-risk assessment or regression review
- Scoping review to a specific module

**Examples:**

```text
Review the entire project for PAF compliance
```

```text
@PAF Code Reviewer review hello_world module for architecture issues
```

```text
@PAF Code Reviewer perform regression review on sensor_reader
```

**What it checks:**

- Module initialization patterns (`self.debug` assignment before `super().__init__()`)
- `handle_message` implementation and delegation to base class
- Message handler return values (True for shutdown, False for continue)
- Background task setup and lifecycle management
- Factory module registration and implementation pattern
- Thread safety and protocol usage
- Compliance with naming conventions
- Test coverage and test pattern adherence

---

## Naming Conventions

| Input | Convention | Example |
| --- | --- | --- |
| Module name argument | PascalCase | `SensorReader` |
| Folder name | snake_case | `sensor_reader` |
| Module address (in `main.py`) | snake_case | `"sensor_reader"` |
| Class name (in Python files) | PascalCase | `SensorReader` |

---

## Key Rules (from the codebase)

- `self.debug` **must** be assigned before `super().__init__()` in any module — the base class accesses it during startup.
- `handle_message` returns `True` to shut down the module, `False` to keep running.
- Unknown commands must be forwarded: `return super().handle_message(message)` (raises `NotImplementedError` for truly unknown commands).
- Factory implementations must self-register at import time: `FactoryClass.register("simulated", SimulatedClass)` at the bottom of `simulated.py`.
- After adding a factory module, add `--hidden-import paf.modules.<module_name>.simulated ^` to `scripts/build-exe.bat` — PyInstaller cannot detect dynamic registrations automatically.
