---
name: paf-new-implementation
description: "Create a new implementation for an existing PAF factory module by deriving from its Base class and stubbing all required abstract methods. Use when: add factory implementation, new implementation type, extend factory module, create simulated or hardware implementation."
argument-hint: "<factory-module-name> <implementation-name>"
---

# New PAF Factory Implementation

Creates a new implementation file for an existing factory module under `src/paf/modules/<module_name>/`, inheriting from `Base<ClassName>` and implementing every required abstract method.

## When to Use
- "Add a hardware implementation for the MotorController factory"
- "Create a second implementation for sensor_reader"
- "Add a new implementation type to an existing factory module"

## Inputs

Collect from the user before proceeding (ask if not provided in the invocation):

1. **Factory module name** — snake_case folder name under `src/paf/modules/`.
   - If omitted, ask: "Which factory module should receive the new implementation?"
2. **Implementation name** — implementation key and file stem (for example: `hardware`, `mock`, `can_bus`).
  - This is required. If omitted, ask for it explicitly and do not continue until provided.
3. **Optional class suffix override** — if not provided, class name uses `PascalCase(implementation_name)` + `ClassName` (example: `HardwareMotorController`).
4. **Method body style** (optional) — `not-implemented` or `safe-stub`.
  - Default: `safe-stub`.

## Procedure

### Step 1 — Gather and normalize inputs

- Ensure module name is provided; ask if missing.
- Ensure implementation name is provided; ask if missing and stop until provided.
- Normalize values:
  - `module_name`: snake_case folder name
  - `implementation_key`: lowercase string used in factory registration
  - `implementation_file`: `<implementation_key>.py`

### Step 2 — Validate target is a factory module

Inspect:
- `src/paf/modules/<module_name>/module.py`
- `src/paf/modules/<module_name>/__init__.py`

Confirm all are true:
- Factory class exists (for example `MotorController`)
- Base class exists and follows `Base<ClassName>` pattern
- Base class inherits from `Module` and `ABC`
- Base class declares abstract methods with `@abstractmethod`

If it is not a factory module, stop and explain why.

### Step 3 — Extract required methods from the base class

From `Base<ClassName>` in `module.py`:
- Collect all `@abstractmethod` methods (name and signature)
- Preserve parameter names and defaults
- Include any required return annotations if present

These methods must be implemented in the new class body.

### Step 4 — Create the implementation file

Create:
- `src/paf/modules/<module_name>/<implementation_file>`

Write:
- Imports required by method signatures and type hints
- `from .module import <FactoryClass>, Base<ClassName>`
- Class definition:
  - `class <ImplementationClassName>(Base<ClassName>):`
- Concrete method stubs for every abstract method copied from the base class signatures
- Module-level registration line:
  - `<FactoryClass>.register("<implementation_key>", <ImplementationClassName>)`

Implementation stubs should be valid and explicit:
- If style is `not-implemented`, each generated method body should be:
  - `raise NotImplementedError("TODO: implement <method_name>")`
- If style is `safe-stub` (default), generate minimal return-safe stubs based on return annotation:
  - `-> bool`: `return False`
  - `-> None` or no annotation: `return None`
  - `-> Optional[...]`: `return None`
  - Any other annotation: use `raise NotImplementedError("TODO: implement <method_name>")`
- Avoid leaving methods missing, so class is instantiable

### Step 5 — Update module exports

Edit `src/paf/modules/<module_name>/__init__.py`:
- Import the new implementation class from the new file
- Add the class to `__all__`

Do not remove existing exports.

### Step 6 — Optional wiring in main

Do not auto-switch production usage unless user asked.
If requested, update `src/main.py` instantiation for that factory module to:
- `implementation_type="<implementation_key>"`

### Step 7 — Validation

Run module tests:
- `python -m unittest discover -s src/paf/modules/<module_name>/tests -t src -p "test_*.py" -v`

If tests fail due to new behavior gaps, report exact failing tests and leave scaffolding in place.

### Step 8 — Confirm deliverables

Report:
- New file created
- Existing files modified
- Abstract methods implemented
- Registration key added
- Test results

## Quality Checks

- New class inherits from `Base<ClassName>`
- Every abstract method from base class is implemented with matching signature
- Registration line exists at module level
- `__init__.py` exports include the new class
- No direct module-to-module calls introduced
- Existing module behavior unchanged unless explicitly requested

## Notes

- Keep `self.debug` assignment order unchanged in constructor chains handled by base classes.
- Factory registration must happen at import time.
- If method semantics are unknown, implement safe placeholders and flag TODOs clearly for domain logic.
