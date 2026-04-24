---
name: paf-init
description: "Set up this PAF project for development by initializing submodules, creating a virtual environment, installing dependencies, and validating the main entry point. Use when: first clone, fresh machine setup, environment reset, onboarding, cannot run src/main.py."
argument-hint: "[--recreate-venv] [--skip-main-check]"
---

# PAF Environment Initialization

Prepare this repository so a developer can run the application entry point at src/main.py.

## When to Use
- First-time repository setup
- New machine or CI bootstrap
- Broken or missing .venv
- Import errors when running src/main.py

## Inputs

Ask only if the user did not provide them:

1. Recreate virtual environment (`yes`/`no`, default: `no`)
2. Run main entry-point smoke check (`yes`/`no`, default: `yes`)

## Procedure

### Step 1 - Confirm repository root

1. Ensure commands run from the workspace root (folder containing src/ and scripts/).
2. Verify src/main.py exists.

### Step 2 - Initialize git submodules

1. Run: `git submodule update --init --recursive`
2. If this fails, stop and report the git error because src/paf/communication is required for imports.

### Step 3 - Ensure virtual environment exists

1. If `--recreate-venv` is set and `.venv` exists, remove and recreate it.
2. If `.venv` does not exist, create it:
   - `python -m venv .venv`
3. Determine the venv Python executable:
   - Windows: `.venv\Scripts\python.exe`
   - macOS/Linux: `.venv/bin/python`
4. Verify the executable exists before proceeding.

### Step 4 - Upgrade packaging tooling in venv

Run:
- `<venv-python> -m pip install --upgrade pip setuptools wheel`

If this fails, stop and return the full pip error.

### Step 5 - Install project dependencies

Use the first dependency manifest found in this order:

1. `requirements.txt`:
   - `<venv-python> -m pip install -r requirements.txt`
2. `pyproject.toml` (if present):
   - `<venv-python> -m pip install -e .`
3. `setup.py` (if present):
   - `<venv-python> -m pip install -e .`

If none of these files exist, report: "No dependency manifest found; continuing with base environment only."

### Step 6 - Validate runtime imports

1. Run a quick import check:
   - `<venv-python> -c "from paf.communication import Protocol; from paf.modules import HelloWorld; print('imports-ok')"`
2. If imports fail, stop and report missing package/module details.

### Step 7 - Optional main entry-point smoke check

If `--skip-main-check` is not set:

1. Start the app with timeout protection (because it enters a loop):
   - Windows PowerShell example:
     - `& <venv-python> src/main.py`
2. Confirm startup reaches a healthy state by checking output contains:
   - `Received greeting: Hello, World!`
3. Stop the process cleanly after startup verification.

## Completion Criteria

All must be true:
- Submodules initialized successfully
- .venv exists and is usable
- Dependency install step completed (or explicitly skipped due to no manifest)
- Import validation prints `imports-ok`
- If main check enabled, output includes `Received greeting: Hello, World!`

## Report Back

Provide:
1. Whether .venv was created or reused
2. Which dependency manifest was used
3. Whether import and main smoke checks passed
4. Exact next command for the developer to run

Example next command:
- `.venv\Scripts\python.exe src/main.py`

## Failure Handling

If any step fails:
1. Stop immediately
2. Report the failing command and key stderr lines
3. Suggest a focused retry command
