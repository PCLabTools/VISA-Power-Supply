---
name: paf-test
description: "Run all PAF module unit tests and report results. Use when: run tests, test all modules, check test results, test report, unit tests, paf-test."
argument-hint: "Optional: specific module name to test, or leave blank for all"
agent: agent
---

Run all PAF module unit tests and produce a formatted report.

## Steps

1. Use `file_search` to find all `test_*.py` files matching the pattern:
   `src/paf/modules/**/tests/test_*.py`

   If an argument was provided (e.g. `hello_world`), limit discovery to that module only.

2. Derive the unique set of module test folders from the discovered files (e.g. `src/paf/modules/hello_world/tests`). For each module, run its tests directly using Python's unittest from the project root:
   ```
   python -m unittest discover -s src/paf/modules/<module_name>/tests -t src -p "test_*.py" -v 2>&1
   ```
   The `-t src` flag sets `src` as unittest's top-level import root so `from paf...` imports resolve consistently.
   The `-v` flag produces per-test output. `2>&1` captures stderr (where unittest writes) alongside stdout.

   Run all modules in a single terminal session, one after another.

3. Parse each output to extract:
   - Module name (from the folder path)
   - Total tests run
   - Passed count
   - Failed count
   - Error count
   - Time taken

## Output Format

Present the results in this exact structure:

---

## 🧪 PAF Test Report

### Summary

| Module | Tests | ✅ Passed | ❌ Failed | 💥 Errors | ⏱ Time |
|--------|-------|-----------|-----------|-----------|--------|
| `hello_world` | 6 | 6 | 0 | 0 | 0.01s |
| _(more rows...)_ | | | | | |
| **Total** | **N** | **N** | **N** | **N** | |

### Overall Result

- If all tests passed: `✅ All N tests passed across M modules.`
- If any failed or errored: `❌ N failure(s) / N error(s) detected. See details below.`

---

### 📋 Per-Module Details

For each module, show a collapsible-style block:

**`hello_world`** — ✅ 6/6 passed

```
test_background_task_running ... ok
test_handle_message_custom_action ... ok
test_handle_message_unknown ... ok
test_init ... ok
test_init_with_debug ... ok
test_message_custom_action ... ok
```

---

### ❌ Failures & Errors (if any)

For each failed or errored test, show:

**Module:** `sensor_reader`
**Test:** `test_handle_message_custom_action`
**Type:** FAIL

```
AssertionError: True is not false
  File "...", line 42
```

---

## Notes

- Use ✅ for fully passing modules, ❌ for any failures, ⚠️ for modules with errors
- If a module's test discovery fails (e.g. import error, missing `__init__.py`), report it as `⚠️ Discovery error` with the stderr output
- If no test files are found, report: `⚠️ No test files found under src/paf/modules/`
