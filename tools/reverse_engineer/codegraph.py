
import os
import sys
import json
import subprocess
import glob
import time
import re
from typing import Optional, Tuple

WORKER_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'codegraph_worker.js')
MODULE_MAP_FILE = 'codegraph_map.json'

def _py_index_to_utf16_code_unit_index(content: str, py_index: int) -> int:
    """
    Convert a Python string index (Unicode code points) to a JS string index
    (UTF-16 code units), which is what acorn uses for node.start/node.end.

    Most bundles are ASCII-only, so this is usually a no-op. But if the file
    contains astral-plane characters earlier (emoji, some symbols in strings),
    JS indices will be larger than Python indices.
    """
    if py_index <= 0:
        return 0
    if py_index >= len(content):
        py_index = len(content)
    extra = 0
    for ch in content[:py_index]:
        if ord(ch) > 0xFFFF:
            extra += 1
    return py_index + extra

def _convert_offset_for_worker(file_path: str, offset: int) -> int:
    """
    Convert user-provided offsets (typically from Python tooling like grep_ui/get_index)
    to the UTF-16 offsets expected by the JS worker.
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        return _py_index_to_utf16_code_unit_index(content, int(offset))
    except Exception:
        return int(offset)

def run_worker(command, arg1, arg2=None):
    cmd = ['node', WORKER_SCRIPT, command, str(arg1)]
    if arg2:
        cmd.append(str(arg2))
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return None
        return json.loads(result.stdout)
    except Exception as e:
        return None

def build_index(directory):
    print(f"Building Module Index for {directory}...")
    module_map = {}
    
    # Find all JS files
    # Handle both single files and directories
    files = []
    if os.path.isfile(directory):
        # Single file passed - index it directly
        files.append(directory)
    else:
        # Directory passed - use glob to find all js/bundle files recursively
        files.extend(glob.glob(os.path.join(directory, "**", "*.js"), recursive=True))
        files.extend(glob.glob(os.path.join(directory, "**", "*.bundle"), recursive=True))
    
    count = 0
    for f in files:
        if "node_modules" in f: continue
        
        # Run worker to get modules in this file
        modules = run_worker('index', f)
        if modules:
            for mod_id, info in modules.items():
                # We need to save the ABSOLUTE path because relative path logic is fragile
                # when moving CWD.
                #
                # NOTE: Some workspaces index multiple unrelated sites in one directory.
                # Module IDs can collide across builds. Historically we overwrote entries.
                # To preserve backwards compatibility while improving usefulness, we keep
                # the first entry as the primary target and store additional candidates
                # in a `candidates` array.
                key = str(mod_id)
                entry = {
                    "file": os.path.abspath(f),
                    "info": info
                }
                if key not in module_map:
                    module_map[key] = entry
                else:
                    existing = module_map[key]
                    # Normalize existing candidates list.
                    if "candidates" not in existing:
                        existing["candidates"] = [{
                            "file": existing.get("file"),
                            "info": existing.get("info")
                        }]
                    existing["candidates"].append(entry)
                count += 1
        
        if count % 100 == 0 and count > 0:
            print(f"Indexed {count} modules...")

    with open(MODULE_MAP_FILE, 'w') as f:
        json.dump(module_map, f, indent=2)
    
    print(f"Index complete. Found {len(module_map)} modules. Saved to {MODULE_MAP_FILE}.")

def trace_symbol(file_path, index):
    raw_index = int(index)
    index = _convert_offset_for_worker(file_path, raw_index)
    # 1. Run trace locally
    result = run_worker('trace', file_path, index)
    if not result:
        print("Error: Could not trace symbol (worker failed).")
        return
    # If conversion was unnecessary or wrong for this file, try original index.
    if result.get('error') and raw_index != index:
        alt = run_worker('trace', file_path, raw_index)
        if alt and not alt.get('error'):
            result = alt
    # If we still couldn't trace, try best_index candidates (common when cursor is in strings/punctuation).
    if result.get('error'):
        bi = run_worker('best_index', file_path, index)
        if bi and not bi.get('error'):
            tried = set()
            candidates = []
            best = bi.get('best') or {}
            candidates.append(best)
            candidates.extend(bi.get('alternates') or [])
            for c in candidates:
                role = (c.get('role') or "")
                ci = c.get('index')
                if not isinstance(ci, int):
                    continue
                if ci in tried:
                    continue
                if "in_string" in role:
                    continue
                tried.add(ci)
                alt2 = run_worker('trace', file_path, ci)
                if alt2 and not alt2.get('error'):
                    result = alt2
                    break

    # Check for errors
    if result.get('error'):
        print(f"\nError: {result.get('error')}")
        return

    print("\n--- Trace Result ---")
    print(f"Symbol: {result.get('name')}")
    print(f"Type: {result.get('type')}")
    print(f"Defined at Line: {result.get('line')}")
    
    # Handle different result types
    if result.get('type') == 'PropertyKey':
        print(f"Value Type: {result.get('valueType')}")
        if result.get('valuePreview'):
            print(f"Value: {result.get('valuePreview')}")
    elif result.get('initCode'):
        print(f"Code: {result.get('initCode')}")

    # 2. Check for Webpack Import
    import_id = result.get('importId')
    if import_id:
        print(f"\n[!] Detected Webpack Import of Module {import_id}")
        
        # Load map
        if os.path.exists(MODULE_MAP_FILE):
            with open(MODULE_MAP_FILE, 'r') as f:
                module_map = json.load(f)
            
            target = module_map.get(str(import_id))
            if target:
                print(f"--> JUMP TO: {target['file']}")
                print(f"    Line: {target['info']['line']}")
                if target.get("candidates"):
                    print(f"    (Multiple candidates exist for this module id; index stored {len(target['candidates'])} candidates.)")
            else:
                print(f"--> Module {import_id} not found in index. (Try rebuilding index)")
        else:
            print("--> No module index found. Run 'python codegraph.py index <dir>' first.")

def inspect_module(module_id):
    def _extract_module_by_brace_matching(content: str, header_idx: int) -> Tuple[int, int]:
        """
        Given an index pointing at the module body's opening '{', return (start,end) span.

        Handles strings and comments; supports template literals well enough for bundle code.
        """
        def _looks_like_regex_start(s: str, slash_i: int) -> bool:
            """
            Heuristic: decide whether `s[slash_i] == '/'` begins a regex literal.

            We must handle cases like `return/^\\/\\//.test(x)` (no whitespace), where
            previous non-ws char is an identifier character, but the token is the keyword `return`.
            """
            j = slash_i - 1
            while j >= 0 and s[j].isspace():
                j -= 1
            if j < 0:
                return True

            prev = s[j]
            if prev in "([{:;,=!?&|+-*%^~<>":
                return True

            # Check for `=>/regex/`
            if prev == '>' and j - 1 >= 0 and s[j - 1] == '=':
                return True

            # Check for preceding keyword like `return` / `throw` / `case`
            k = j
            while k >= 0 and (s[k].isalnum() or s[k] in "_$"):
                k -= 1
            word = s[k + 1:j + 1]
            if word in {"return", "throw", "case", "else", "do", "in", "of"}:
                return True

            return False

        def _skip_regex_literal(s: str, slash_i: int) -> int:
            """
            Skip over a JS regex literal starting at `slash_i` (which must be '/').
            Returns index just after the regex literal (including trailing flags).

            Important: regex bodies can contain `//` and `/* */` sequences that must NOT
            be treated as comments.
            """
            i2 = slash_i + 1
            escaped = False
            in_class = False
            while i2 < len(s):
                ch2 = s[i2]
                if escaped:
                    escaped = False
                    i2 += 1
                    continue
                if ch2 == '\\':
                    escaped = True
                    i2 += 1
                    continue
                if in_class:
                    if ch2 == ']':
                        in_class = False
                    i2 += 1
                    continue
                if ch2 == '[':
                    in_class = True
                    i2 += 1
                    continue
                if ch2 == '/':
                    i2 += 1
                    # flags
                    while i2 < len(s) and s[i2].isalpha():
                        i2 += 1
                    return i2
                i2 += 1
            # Unterminated regex: fall back to end of file.
            return len(s)

        i = header_idx
        depth = 0
        in_str = None  # ', ", `
        esc = False
        in_line_comment = False
        in_block_comment = False
        in_template_expr = 0  # when inside `${ ... }` of a template literal
        # Regex literal mode. (We only need this to avoid mis-parsing `//` inside /.../.)
        in_regex = False

        while i < len(content):
            ch = content[i]
            nxt = content[i + 1] if i + 1 < len(content) else ''

            if in_regex:
                # We should never reach here because we skip regex literals in one go,
                # but keep for safety.
                i += 1
                continue

            if in_line_comment:
                if ch == '\n':
                    in_line_comment = False
                i += 1
                continue
            if in_block_comment:
                if ch == '*' and nxt == '/':
                    in_block_comment = False
                    i += 2
                    continue
                i += 1
                continue

            if in_str is not None:
                if in_str == '`' and in_template_expr == 0 and ch == '$' and nxt == '{':
                    # Enter template expression; braces in expression should count.
                    in_template_expr = 1
                    i += 2
                    continue

                if in_str == '`' and in_template_expr > 0:
                    # Inside template expression: treat like code until we close the matching '}'.
                    if ch == '{':
                        in_template_expr += 1
                    elif ch == '}':
                        in_template_expr -= 1
                    i += 1
                    continue

                # Regular string scanning
                if esc:
                    esc = False
                elif ch == '\\':
                    esc = True
                elif ch == in_str:
                    in_str = None
                i += 1
                continue

            # not in string/comment
            if ch == '/' and nxt == '/':
                in_line_comment = True
                i += 2
                continue
            if ch == '/' and nxt == '*':
                in_block_comment = True
                i += 2
                continue

            # Regex literal (must come AFTER comment checks, BEFORE brace counting).
            if ch == '/' and nxt not in ('/', '*') and _looks_like_regex_start(content, i):
                i = _skip_regex_literal(content, i)
                continue

            if ch in ("'", '"', '`'):
                in_str = ch
                i += 1
                continue

            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return header_idx, i + 1
            i += 1

        raise ValueError("Unterminated module body")

    def _extract_module_from_file(file_path: str, module_id: str, start_hint: Optional[int] = None) -> Optional[str]:
        """
        Robust extractor that finds `<id>:(...)=>{ ... }` in the raw bundle and brace-matches the body.

        We prefer this over using worker-provided `start/end` because those offsets
        point to the function node, not the module wrapper, and can be misleading for
        minified one-line bundles.
        """
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Match module header. Require a preceding delimiter so we don't match IDs in strings.
        header_re = re.compile(
            rf"(?P<prefix>[,{{\n]){re.escape(str(module_id))}:\s*(?:function\b|\([^)]*\)\s*=>|[A-Za-z0-9_$]+\s*=>)\s*\{{"
        )
        matches = list(header_re.finditer(content))
        if not matches:
            return None

        # Choose the closest match to the hint (if we have one), else the first.
        if start_hint is not None:
            chosen = min(matches, key=lambda m: abs(m.start() - start_hint))
        else:
            chosen = matches[0]

        header_start = chosen.start() + 1  # skip delimiter
        body_start = chosen.end() - 1      # points at '{'
        _, body_end = _extract_module_by_brace_matching(content, body_start)
        return content[header_start:body_end]

    # 1. Load map
    if not os.path.exists(MODULE_MAP_FILE):
        print("Error: No module index found.")
        return

    with open(MODULE_MAP_FILE, 'r') as f:
        module_map = json.load(f)
    
    target = module_map.get(str(module_id))
    if not target:
        print(f"Error: Module {module_id} not found.")
        return

    file_path = target['file']
    info = target['info']
    candidates = target.get("candidates") or []
    
    print(f"--- Module {module_id} ---")
    print(f"File: {file_path}")
    print(f"Line: {info.get('line')}")
    if candidates:
        print(f"Note: {len(candidates)} candidates found for this module id; showing the first match.")
    print("-------------------------")
    
    try:
        # Prefer robust extraction from raw file.
        extracted = _extract_module_from_file(file_path, str(module_id), info.get('start'))
        if extracted is not None:
            print(extracted)
            return

        # Fallback: if extraction fails, use the worker offsets (best-effort).
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        start = info['start']
        end = info['end']
        print(content[start:end])
    except Exception as e:
        print(f"Error reading file: {e}")

def fingerprint_symbol(file_path, index):
    raw_index = int(index)
    index = _convert_offset_for_worker(file_path, raw_index)
    result = run_worker('fingerprint', file_path, index)
    if not result:
        print("Error: Worker failed.")
        return
    if result.get('error') and raw_index != index:
        alt = run_worker('fingerprint', file_path, raw_index)
        if alt and not alt.get('error'):
            result = alt
    if result.get('error'):
        print(f"Error: {result.get('error')}")
        return

    print(f"\n--- Fingerprint: {result.get('variable')} ---")
    
    props = result.get('properties', [])
    calls = result.get('calls', [])
    assigns = result.get('assignments', [])

    if not props and not calls and not assigns:
        print("No property accesses found in scope.")
        return

    print("Properties Accessed:")
    for p in props:
        suffix = ""
        if p in calls: suffix += " (Called)"
        if p in assigns: suffix += " (Assigned)"
        print(f"  - .{p}{suffix}")

def find_refs(file_path, index):
    raw_index = int(index)
    index = _convert_offset_for_worker(file_path, raw_index)
    result = run_worker('refs', file_path, index)
    if not result:
        print("Error: Worker failed.")
        return
    if result.get('error') and raw_index != index:
        alt = run_worker('refs', file_path, raw_index)
        if alt and not alt.get('error'):
            result = alt
    # If refs can't find an identifier at the exact cursor, try best_index candidates.
    if result.get('error'):
        bi = run_worker('best_index', file_path, index)
        if bi and not bi.get('error'):
            tried = set()
            candidates = []
            best = bi.get('best') or {}
            candidates.append(best)
            candidates.extend(bi.get('alternates') or [])
            for c in candidates:
                role = (c.get('role') or "")
                ci = c.get('index')
                if not isinstance(ci, int):
                    continue
                if ci in tried:
                    continue
                if "in_string" in role:
                    continue
                tried.add(ci)
                alt2 = run_worker('refs', file_path, ci)
                if alt2 and not alt2.get('error'):
                    result = alt2
                    break
    if result.get('error'):
        print(f"Error: {result.get('error')}")
        return

    refs = result.get('references', [])
    print(f"\n--- References: {result.get('variable')} ---")
    print(f"Found {len(refs)} references in scope.\n")

    for r in refs:
        print(f"Line {r['line']}: {r['preview'].strip()}")

def extract_strings(file_path, min_len):
    result = run_worker('literals', file_path, min_len)
    if not result:
        print("Error: Worker failed.")
        return
    if result.get('error'):
        print(f"Error: {result.get('error')}")
        return
    
    # result is { ScopeName: [strings...] }
    print(f"\n--- String Literals (Min Len: {min_len}) ---\n")
    
    for scope, strings in result.items():
        print(f"[{scope}]")
        for s in strings:
            print(f"  - \"{s}\"")
        print("")

def best_index(file_path, index):
    raw_index = int(index)
    index = _convert_offset_for_worker(file_path, raw_index)
    result = run_worker('best_index', file_path, index)
    if not result:
        print("Error: Worker failed.")
        return
    if result.get('error') and raw_index != index:
        alt = run_worker('best_index', file_path, raw_index)
        if alt and not alt.get('error'):
            result = alt
    if result.get('error'):
        print(f"Error: {result.get('error')}")
        return
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python codegraph.py index <directory>")
        print("  python codegraph.py trace <file> <index>")
        print("  python codegraph.py best_index <file> <offset>")
        print("  python codegraph.py inspect <moduleId>")
        print("  python codegraph.py fingerprint <file> <index>")
        print("  python codegraph.py refs <file> <index>")
        print("  python codegraph.py literals <file> [min_length]")
        sys.exit(1)
        
    cmd = sys.argv[1]
    if cmd == 'index':
        build_index(sys.argv[2])
    elif cmd == 'trace':
        trace_symbol(sys.argv[2], sys.argv[3])
    elif cmd == 'inspect':
        inspect_module(sys.argv[2])
    elif cmd == 'fingerprint':
        fingerprint_symbol(sys.argv[2], sys.argv[3])
    elif cmd == 'refs':
        find_refs(sys.argv[2], sys.argv[3])
    elif cmd == 'literals':
        min_len = 5
        if len(sys.argv) > 3: min_len = sys.argv[3]
        extract_strings(sys.argv[2], min_len)
    elif cmd == 'best_index':
        best_index(sys.argv[2], sys.argv[3])
