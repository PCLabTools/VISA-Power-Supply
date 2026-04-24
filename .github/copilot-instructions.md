# PAF Template Project — Agent Instructions

This is a **Python Actor Framework (PAF)** template project. Every feature is a `Module` subclass running in its own thread, communicating only through a shared `Protocol` message bus. Never have modules call each other directly.

---

## Project Purpose and Intent

Read [PROJECT.md](../PROJECT.md) at the start of work and use it as the primary source of project-level purpose and intent for contextual awareness.

This repository is a template, so `PROJECT.md` currently describes template-level intent. For forks, treat fork-specific updates in `PROJECT.md` as authoritative context for understanding prompts and queries.

---

## Rolling Agent Memory

In the project root, [MEMORY.md](../MEMORY.md) is the rolling memory file for agents working on this repository.

`MEMORY.md` starts empty when this template is first used.

When an agent completes a task that changes the project, and the user later indicates the implementation was wrong or needs adjustment, record a concise entry in `MEMORY.md` that can guide similar future actions.

Each memory entry should focus on reusable guidance (what was attempted, what was wrong, and what to do next time).

---

## Project Layout

```
src/
  main.py                          # Entry point — instantiates Protocol and all modules
  paf/
    communication/                 # Core framework (git submodule — do not edit)
      message.py                   # Message(address, command, payload, source)
      protocol.py                  # Protocol — thread-safe message bus
      module.py                    # Module base class
    modules/
      __init__.py                  # Re-exports every module class; update when adding/removing
      <module_name>/
        module.py                  # Module implementation
        __init__.py                # Exports ClassName (+ Base/Simulated for factory)
        tests/
          test_module.py           # unittest tests
        scripts/
          run-tests.bat            # Per-module test runner
        .gitignore                 # Contains __pycache__
scripts/
  build-exe.bat                    # PyInstaller build — update for factory hidden imports
.github/
  skills/
        paf-init/SKILL.md              # Initialize submodules, venv, and dependencies
    paf-new-module/SKILL.md        # Scaffold a new module
        paf-new-implementation/SKILL.md # Add a new implementation to a factory module
    paf-remove-module/SKILL.md     # Remove a module
    paf-pull-module/SKILL.md       # Add a module from git as submodule
        paf-init-module/SKILL.md       # Initialize or convert module folder into a git submodule with conflict handling
  prompts/
    paf-test.prompt.md             # /paf-test — run all unit tests and report results
```

---

## Build & Test Commands

```bash
# Run the application
python src/main.py

# Run all tests
python -m unittest discover -s src -p "test_*.py"

# Run tests for a single module
python -m unittest discover -s src/paf/modules/<module_name>/tests -p "test_*.py" -v

# Build standalone executable
scripts\build-exe.bat
```

Virtual environment: `.venv\Scripts\activate` (Windows)

---

## Core Framework

### Protocol (message bus)

```python
protocol = Protocol("main")                    # registers "main" address
protocol.register_module("addr")               # adds a PriorityQueue for that address
protocol.send_action("addr", "cmd", payload)   # fire-and-forget
protocol.send_request("addr", "cmd", timeout=5) # synchronous — blocks until response
protocol.send_response(source_message, data)   # reply to a send_request caller
protocol.broadcast_message("shutdown")         # sends to all registered modules
protocol.receive_message("addr", timeout=1)    # raises TimeoutError if empty
protocol.get_registered_modules()              # returns list of addresses
```

### Module base class

- Constructor signature: `__init__(self, address: str, protocol: Protocol)` — no `debug` parameter
- Registers itself with `protocol`, starts a `self.thread` running `run()`
- Built-in commands handled by base: `shutdown`, `start`, `stop`, `status`
- Unknown commands: `raise NotImplementedError(...)` — subclasses must handle or delegate to `super()`

### Message

```python
Message(address="target", command="cmd", payload={"key": "val"}, source=None)
```
`payload` is `dict[str, Any]`. `source` is a `PriorityQueue` set automatically by `send_request`.

---

## Module Conventions

### Standard module structure

```python
from typing import Optional
from paf.communication import Message, Protocol, Module

class MyModule(Module):
    def __init__(self, address: str, protocol: Protocol, debug: Optional[int] = 0):
        self.debug = debug          # MUST be set BEFORE super().__init__()
        super().__init__(address, protocol)

    def handle_message(self, message: Message) -> bool:
        if message.command == "my_cmd":
            return self.message_my_cmd(message)
        return super().handle_message(message)  # handles shutdown/start/stop/status

    def background_task(self):
        while self.background_task_running:
            # do work
            sleep(1)

    def message_my_cmd(self, message: Message) -> bool:
        # ... logic ...
        return False   # True = shutdown this module
```

**Critical rule:** `self.debug` must be assigned before `super().__init__()`. The base class accesses `self.debug` during startup.

**`handle_message` return values:**
- `True` → module shuts down
- `False` → module keeps running
- Always delegate unknown commands: `return super().handle_message(message)` (raises `NotImplementedError` for truly unrecognised commands)

### Factory module structure

Three files:

**`module.py`** — factory class + abstract base:
```python
class MyFactory:
    _implementations: dict[str, type["BaseMyFactory"]] = {}

    @classmethod
    def register(cls, name, cls_impl): ...

    def __new__(cls, address, protocol, debug=0, implementation_type="simulated"):
        return cls.create(address, protocol, debug, implementation_type)

class BaseMyFactory(Module, ABC):
    def __init__(self, address, protocol, debug=0):
        self.debug = debug
        super().__init__(address, protocol)
    @abstractmethod
    def message_custom_action(self, message): ...
    @abstractmethod
    def background_task(self): ...
```

**`simulated.py`** — default implementation:
```python
class SimulatedMyFactory(BaseMyFactory):
    def background_task(self): ...
    def message_custom_action(self, message): ...

MyFactory.register("simulated", SimulatedMyFactory)   # must be at module level
```

**`__init__.py`** exports: `MyFactory`, `BaseMyFactory`, `SimulatedMyFactory`

---

## Registering Modules

### `src/paf/modules/__init__.py`

Every module must be imported and listed in `__all__`:

```python
from .hello_world import HelloWorld
from .my_module import MyModule

__all__ = ["HelloWorld", "MyModule"]
```

For factory: also export `BaseMyModule`, `SimulatedMyModule`.

### `src/main.py`

```python
from paf.modules import HelloWorld, MyModule

class Main:
    def __init__(self):
        self.debug = 1
        self.address = "main"
        self.protocol = Protocol(self.address)
        HelloWorld("hello_world", self.protocol, debug=self.debug)
        MyModule("my_module", self.protocol, debug=self.debug)

    def run(self):
        self.protocol.send_action("my_module", "custom_action", {"data": "Hello!"})
        while True:
            try:
                message = self.protocol.receive_message(self.address, timeout=1)
                if self.handle_message(message):
                    break
            except TimeoutError:
                continue
            except KeyboardInterrupt:
                self.protocol.broadcast_message("shutdown")
                break
```

---

## Factory Modules and PyInstaller

Factory modules use dynamic class registration (`register()` at import time). PyInstaller cannot detect this automatically. For each factory module, add to `scripts/build-exe.bat`:

```bat
--hidden-import paf.modules.<module_name>.simulated ^
```

---

## Git Submodules

`src/paf/communication/` and any pulled modules are git submodules. To remove a submodule:

```bash
git submodule deinit -f src/paf/modules/<name>
git rm -f src/paf/modules/<name>
```

Never use `Remove-Item` or `rm -rf` on a submodule folder.

To add a module from a remote repo:

```bash
git submodule add <url> src/paf/modules/<name>
```

---

## Copilot Skills

Load the relevant skill before working on these tasks:

| Task | Skill file |
|---|---|
| Initialize project environment | `.github/skills/paf-init/SKILL.md` |
| Define project intent, scope, and candidate PAF modules at project start | `.github/skills/paf-init-project/SKILL.md` |
| Create a new module | `.github/skills/paf-new-module/SKILL.md` |
| Add implementation to a factory module | `.github/skills/paf-new-implementation/SKILL.md` |
| Remove a module | `.github/skills/paf-remove-module/SKILL.md` |
| Add a module from git | `.github/skills/paf-pull-module/SKILL.md` |
| Initialize/convert module as submodule safely | `.github/skills/paf-init-module/SKILL.md` |

Use `paf-init-project` at project kickoff or soon after forking when the project intent needs to be clarified and broken down into candidate PAF modules.

Run `/paf-test` in chat to execute all unit tests and produce a formatted report.

---

## Test Patterns

All module tests follow this structure:

```python
class TestMyModule(unittest.TestCase):
    def setUp(self):
        self.protocol = Protocol()   # no address — test protocol

    def tearDown(self):
        for name in self.protocol.get_registered_modules():
            try: self.protocol.send_action(name, "shutdown")
            except: pass
        time.sleep(0.1)
        for name in self.protocol.get_registered_modules():
            try: self.protocol.unregister_module(name)
            except: pass
        del self.protocol
```

Tests instantiate modules directly and call `handle_message()` synchronously to verify behaviour without relying on threads.
