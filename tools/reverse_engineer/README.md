# Universal Reverse Engineer Tools

Tools for reverse engineering minified JavaScript bundles.

## Tools

| Tool | Description |
|------|-------------|
| `get_index.py` | Find 0-based offsets of a pattern in a file (regex by default; supports `--literal`, `--identifier`, `--def`, `--json`) |
| `grep_context.py` | Grep with character context (for minified single-line files) |
| `goto_def.py` | Jump from cursor offset to definition (bundle-aware) |
| `codegraph.py` | Index webpack modules, trace symbols, find refs |
| `trace_chain.py` | Trace all writes to a variable within its scope (AST-based; supports `--offset-kind`) |

## Agent-Only Tools (MCP)

These tools are available as MCP tools in the E2B agent sandbox:

| Tool | Description |
|------|-------------|
| `get_fresh_headers` | Request fresh auth headers when 401/403 detected. Calls backend to re-run login script. |

## Quick Reference

```bash
# Find offset of a pattern (regex)
python3 get_index.py <file> "<regex>"

# Find offset of a pattern (literal substring; no regex escaping)
python3 get_index.py <file> "<literal>" --literal

# Print offsets in multiple coordinate systems (useful when mixing tools)
python3 get_index.py <file> "<literal>" --literal --offset-kind all

# When the match is inside a tiny lambda, also compute the *definition* site of a symbol near the match
# (e.g. find `U=W=>...` near `onClick:()=>U("allergy")`)
python3 get_index.py <file> "<literal>" --literal --identifier U --def --def-window 12000

# Search with character context
python3 grep_context.py <pattern> <path> -c 100

# Jump to definition
python3 goto_def.py <file> <offset>

# If your offset comes from DevTools (UTF-16) or bytes, specify it:
python3 goto_def.py <file> <offset> --offset-kind utf16
python3 goto_def.py <file> <offset> --offset-kind byte

# Index webpack modules
python3 codegraph.py index <directory>

# Trace a symbol definition
python3 codegraph.py trace <file> <offset>

# Find all references
python3 codegraph.py refs <file> <offset>

# Trace all writes to a variable (scope-limited)
python3 trace_chain.py <file> <symbol> <offset>

# If your offset comes from JS/DevTools (UTF-16) or bytes:
python3 trace_chain.py <file> <symbol> <offset> --offset-kind utf16
python3 trace_chain.py <file> <symbol> <offset> --offset-kind byte
```

## Offsets (read this once — this avoids 90% of confusion)

### What “offset” means in this toolset

There are three common “offset” coordinate systems:

1) **Python offset (default in this repo)**  
   - A **0-based index into the decoded file text** (Python `str`)  
   - Counts **Unicode code points**  
   - This is what `get_index.py` stores as `index_py` / `endIndex_py`

2) **JS/DevTools offset (UTF-16)**  
   - A **0-based index into a JS string**  
   - Counts **UTF‑16 code units** (what many JS parsers / browser tooling use)

3) **Byte offset (UTF-8)**  
   - A **0-based byte offset** into the file on disk  
   - This is what some lower-level tooling reports when searching raw bytes

These offsets are usually identical for ASCII-only bundles, but can differ if the file contains non‑ASCII (especially non‑BMP emoji/symbols) *before* your target location.

### The rule of thumb (what to do)

- If you got your offset from **`get_index.py`**, you can use the printed `Index(py)` directly with other tools (default `--offset-kind py`):

```bash
python3 trace_chain.py <file> <symbol> <offset>
python3 goto_def.py <file> <offset>
```

- If you got your offset from **browser/JS tooling** (UTF‑16), pass `--offset-kind utf16`:

```bash
python3 trace_chain.py <file> <symbol> <offset> --offset-kind utf16
python3 goto_def.py <file> <offset> --offset-kind utf16
```

- If you got your offset from **byte-based tooling**, pass `--offset-kind byte`:

```bash
python3 trace_chain.py <file> <symbol> <offset> --offset-kind byte
python3 goto_def.py <file> <offset> --offset-kind byte
```

### Decode errors and why `--errors strict` matters

These tools decode files as UTF‑8 to build a text string that the JS parser/AST tools operate on.

- For **stable, round-trippable offsets**, prefer `--errors strict` (now the default in `get_index.py`/`grep_context.py`/`goto_def.py`/`trace_chain.py`).
- Using `--errors replace` or `--errors ignore` can change the decoded string length and make offsets drift from the original byte positions.

### Why `trace_chain.py` sometimes “can’t find the definition”

Even with a correct offset, you can land inside a **tiny callback scope** (e.g. `()=>U("allergy")`) where the definition is outside that micro-function.

Fix: compute a better offset near the *definition site* and trace from there:

```bash
python3 get_index.py <file> 'onClick:()=>U("allergy")' --literal --identifier U --def --def-window 12000
# then feed DefinitionIndex(U) into trace_chain.py
```

## trace_chain.py

Traces a variable within its containing function scope to see how a payload is constructed.

**Why AST-based?** Regex can't distinguish `T = x` (write) from `f(T)` (read) in minified code. AST parsing identifies node types (`AssignmentExpression`, `VariableDeclarator`, etc.) to correctly classify operations.

**Scope limiting:** Short variable names like `a`, `T` appear thousands of times globally. The tool finds the smallest function containing the target offset and limits analysis to that scope only.

**Writes-only:** For reverse engineering API payloads, you care about how a variable is *constructed*, not where it's read. The tool returns:
- Definition (where the variable is created)
- Writes (assignments to the variable or its properties)
- Passed-to (where it's sent as an argument)

### Usage

```bash
python3 trace_chain.py <file> <symbol> <offset> [--json] [--offset-kind py|utf16|byte]
```

### Example

```bash
# Find the submit handler
python3 get_index.py ./app.js "createAppointment" --literal
# Index: 2555240

# Trace the payload variable T at that location
python3 trace_chain.py ./app.js T 2556280
```

Output:
```
🔍 Variable: T
============================================================
📍 Scope: ArrowFunctionExpression (line 4502)

📌 DEFINITION
   [4502] @2556291 (definition)
   Kind: const
   Init: {...$,timezone:$?.timezone?.value}

✏️  WRITES (2)
   [4502] T.user_id = $.user.value
   [4502] T.external_videochat_url = null

➡️  PASSED TO (1)
   [4502] a(...T...) as arg0
```

### Tested On

- React/Webpack bundles
- Elm-compiled JS
- ExtJS/legacy bundles
