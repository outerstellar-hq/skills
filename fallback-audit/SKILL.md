---
name: fallback-audit
description: Audit codebases for useless fallback patterns that silently hide errors, mask null states, and introduce technical debt. Use when asked to review error handling, audit defensive programming, find over-engineered catch blocks, clean up null-default patterns, scan for catch-all exception handling, or improve code reliability.
---

# Fallback Audit

Scans codebases for fallback patterns that do more harm than good — catch-all blocks, silent null defaults, fallback chains, and defensive programming that conceals real errors. ~95% of fallbacks are unnecessary; the scanner finds candidates, you decide.

## Quick start

```bash
# Scan current directory (auto-detects languages)
python scripts/scan-fallbacks.py --dir .

# Scan a specific language
python scripts/scan-fallbacks.py --dir src/ --lang python

# Output JSON report (findings + per-file summary)
python scripts/scan-fallbacks.py --dir . --json fallbacks.json

# Verbose — see every match with context
python scripts/scan-fallbacks.py --dir . --verbose

# Verify scanner against test fixtures
pwsh scripts/verify-scan.ps1
```

## The rule of thumb

Before writing or keeping a fallback, ask: **"If this fallback didn't exist, would the resulting crash be easier to debug than the silent wrong behavior?"**

If yes → remove the fallback. The error should propagate.

If no → the fallback is papering over a design problem. Fix the design.

## Pattern catalog

| Code | Pattern | Danger |
|------|---------|--------|
| F001 | Bare catch-all (`catch(Exception)` returning default) | Loses every error. Turns failures into silent wrong data. |
| F002 | Silent catch (empty catch body) | The error happened. Nobody knows. Debugging from scratch. |
| F003 | Null masking (`a ?: default` where null is meaningful) | Null was a signal. Now it's a default. Cannot distinguish "not found" from "found with value 0/empty". |
| F004 | Fallback chain (`a ?? b ?? c ?? d` / `a or b or c`) | Every link can silently fail. Final default may be totally unrelated to reality. |
| F005 | Empty collection fallback (return `[]` / `nil, nil` on error) | Caller iterates nothing, assumes "no results". Reality: query failed. |
| F006 | Default parameter masking (`function f(x = true, y = 5)`) | Callers never think about the parameter. Wrong defaults go unnoticed. |
| F007 | Catch-log-continue (log warning, keep looping) | Partial failure invisible. Accumulated errors unnoticed. |
| F008 | `Optional.orElse(constant)` in Java | Default is evaluated on every call, even when value is present. |
| F009 | Result type fallback (`unwrap_or(default)`) | Failure == silent fallback. No one checks if the default is wrong. |
| F010 | `except: pass` in Python | Suppresses every error including `KeyboardInterrupt`, `SystemExit`. |
| F011 | `Task.FromResult` / `Task.CompletedTask` fallback in async methods | Hides async failures. Caller gets a completed task with wrong data. |
| F012 | Try-multiple-fallbacks / `recover()` / `runCatching.getOrDefault()` | Multi-layer fallbacks mean none is reliable. Original error is lost. |

## Supported languages

| Language | Patterns | Extensions |
|----------|----------|------------|
| Go | F002, F005, F012 | `.go` |
| Java | F001, F002, F003, F005, F008 | `.java` |
| Kotlin | F001, F002, F003, F012 | `.kt`, `.kts` |
| C# | F001, F002, F004, F005 | `.cs` |
| TypeScript | F001, F002, F003, F004 | `.ts`, `.tsx`, `.mts`, `.cts` |
| Python | F001, F002, F003, F004, F005, F007, F010 | `.py` |
| Rust | F003, F009, F012 | `.rs` |

## Workflow

1. **Scan** — run the scanner to get a hit list
2. **Filter** — remove false positives (legitimate retry loops, documented config defaults)
3. **Classify** — `high` (data loss/corruption), `medium` (masked errors), `low` (noisy but harmless)
4. **Fix** — remove fallback, let error propagate, or add proper typed error handling
5. **Verify** — run tests after each fix to confirm behavior changed as expected

### When fallbacks ARE justified

- Network call with retry (must log each failure)
- Documented configuration defaults with explicit key
- UI rendering guard with error boundary or fallback UI
- Migration/backward-compatibility shim with expiration TODO
- `default` in pattern-match when all variants are known (Rust, Kotlin `when`, C# switch) — but prefer exhaustiveness checks

## Test fixture verification

```bash
pwsh scripts\verify-scan.ps1
```

This runs the scanner against the included test fixtures and confirms every expected pattern is caught. Add test fixtures when you discover a new pattern.
