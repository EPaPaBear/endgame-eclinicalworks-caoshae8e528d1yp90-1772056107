import argparse
import json
import os
import re
import subprocess
import sys
import codecs
from typing import Any, Dict, Optional, Tuple


WORKER_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "codegraph_worker.js")
DEFAULT_MODULE_MAP_FILE = "codegraph_map.json"


def run_worker(command: str, arg1: str, arg2: Optional[str] = None) -> Optional[Dict[str, Any]]:
    cmd = ["node", WORKER_SCRIPT, command, str(arg1)]
    if arg2 is not None:
        cmd.append(str(arg2))
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return None
        return json.loads(result.stdout)
    except Exception:
        return None


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
    # Each non-BMP codepoint becomes a surrogate pair (adds +1 code unit).
    for ch in content[:py_index]:
        if ord(ch) > 0xFFFF:
            extra += 1
    return py_index + extra


def _utf16_code_unit_index_to_py_index(content: str, utf16_index: int) -> int:
    """
    Convert JS UTF-16 code unit index -> Python codepoint index by scanning.
    (Needed when callers provide offsets from DevTools.)
    """
    if utf16_index <= 0:
        return 0
    if utf16_index >= len(content):
        # Fast path: mostly ASCII bundles
        # This is safe even if there are non-BMP chars; we clamp later.
        pass
    cu = 0
    py = 0
    for ch in content:
        cu += 2 if ord(ch) > 0xFFFF else 1
        if cu > utf16_index:
            return py
        py += 1
        if cu == utf16_index:
            return py
    return len(content)


def _byte_offset_to_py_index(file_bytes: bytes, byte_offset: int, encoding: str) -> int:
    """
    Convert UTF-8 byte offset -> Python codepoint index.
    Assumes byte_offset lands on a UTF-8 codepoint boundary; if not, we step back.
    """
    if byte_offset <= 0:
        return 0
    if byte_offset > len(file_bytes):
        byte_offset = len(file_bytes)
    # Step back up to 3 bytes to find a boundary if needed.
    for back in range(0, 4):
        cut = byte_offset - back
        try:
            return len(file_bytes[:cut].decode(encoding, errors="strict"))
        except UnicodeDecodeError:
            continue
    # If decoding still fails, fall back to replace (offsets may drift).
    return len(file_bytes[:byte_offset].decode(encoding, errors="replace"))


def _read_text_and_bytes(file_path: str, encoding: str, errors: str) -> tuple[str, bytes]:
    with open(file_path, "rb") as f:
        data = f.read()
    try:
        text = data.decode(encoding, errors=errors)
    except UnicodeDecodeError as e:
        raise UnicodeDecodeError(
            e.encoding,
            e.object,
            e.start,
            e.end,
            f"{e.reason}. Try --errors replace if you must (offsets may drift).",
        )
    return text, data


def _find_module_map(start_dir: str) -> Optional[str]:
    """
    Search upward for codegraph_map.json so the tool works regardless of CWD.
    """
    cur = os.path.abspath(start_dir)
    while True:
        candidate = os.path.join(cur, DEFAULT_MODULE_MAP_FILE)
        if os.path.exists(candidate):
            return candidate
        parent = os.path.dirname(cur)
        if parent == cur:
            return None
        cur = parent


def load_module_map(module_map_path: str) -> Optional[Dict[str, Any]]:
    if not os.path.exists(module_map_path):
        return None
    try:
        with open(module_map_path, "r") as f:
            return json.load(f)
    except Exception:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="goto_def.py",
        description="Shift-click style: jump from cursor offset to definition (bundle-aware).",
    )
    parser.add_argument("file", help="Path to the JS file to analyze")
    parser.add_argument("offset", type=int, help="0-based character offset in the file")
    parser.add_argument(
        "--offset-kind",
        choices=["py", "utf16", "byte"],
        default="py",
        help="Interpret offset as Python codepoint index (py), JS UTF-16 code units (utf16), or UTF-8 byte offset (byte). Default: py.",
    )
    parser.add_argument(
        "--encoding",
        default="utf-8",
        help="File encoding for decoding bytes into text (default: utf-8).",
    )
    parser.add_argument(
        "--errors",
        default="strict",
        choices=["strict", "replace", "ignore"],
        help="Decode error handling. Use strict for stable offsets. Default: strict.",
    )
    parser.add_argument(
        "--module-map",
        default=None,
        help="Path to codegraph_map.json (defaults to searching upward from the target file directory).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output machine-readable JSON instead of human text",
    )
    args = parser.parse_args()

    # Load decoded text + raw bytes once.
    try:
        content, file_bytes = _read_text_and_bytes(args.file, encoding=args.encoding, errors=args.errors)
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        return 2

    # Normalize input offset into Python codepoint index for string slicing.
    if args.offset_kind == "py":
        cursor_offset_py = args.offset
    elif args.offset_kind == "utf16":
        cursor_offset_py = _utf16_code_unit_index_to_py_index(content, args.offset)
    else:  # byte
        cursor_offset_py = _byte_offset_to_py_index(file_bytes, args.offset, args.encoding)

    # 0) Improve cursor targeting in minified bundles:
    # prefer a "meaningful" identifier token near the cursor over 1-2 character minified names.
    # This prevents cases where the AST walker picks a nearby `P`/`a` instead of `showAddClientFlyout`.
    adjusted_offset_py = cursor_offset_py
    try:
        win = 250
        lo = max(0, cursor_offset_py - win)
        hi = min(len(content), cursor_offset_py + win)
        segment = content[lo:hi]
        ident_re = re.compile(r"[A-Za-z_$][A-Za-z0-9_$]*")

        tokens = []  # [(abs_start, abs_end, tok)]
        for m in ident_re.finditer(segment):
            tok = m.group(0)
            abs_start = lo + m.start()
            abs_end = lo + m.end()
            tokens.append((abs_start, abs_end, tok))

        # Prefer the *next* meaningful identifier after the cursor. This is useful when the cursor
        # lands at the tail of a previous identifier (common when using string match offsets in
        # minified bundles).
        forward = [
            (s, t) for (s, _e, t) in tokens
            if s >= cursor_offset_py and s <= cursor_offset_py + 200 and len(t) > 2
        ]
        if forward:
            forward.sort(key=lambda x: x[0])
            adjusted_offset_py = int(forward[0][0])
        else:
            # Otherwise, prefer the "best" token by a heuristic score.
            best_tok = None  # (score, abs_start, tok)
            for (abs_start, abs_end, tok) in tokens:
                if abs_start <= cursor_offset_py <= abs_end:
                    dist = 0
                else:
                    dist = min(abs(cursor_offset_py - abs_start), abs(cursor_offset_py - abs_end))

                score = 0.0
                if dist == 0:
                    score += 10_000.0
                score -= float(dist)
                score += float(len(tok)) * 2.0
                if len(tok) <= 2:
                    score -= 5_000.0

                if best_tok is None or score > best_tok[0]:
                    best_tok = (score, abs_start, tok)

            if best_tok is not None:
                adjusted_offset_py = int(best_tok[1])
    except Exception:
        adjusted_offset_py = cursor_offset_py

    # Convert offsets to UTF-16 code unit offsets for the node worker (acorn indices).
    cursor_offset_utf16 = (
        args.offset if args.offset_kind == "utf16" else _py_index_to_utf16_code_unit_index(content, cursor_offset_py)
    )
    adjusted_offset_utf16 = _py_index_to_utf16_code_unit_index(content, adjusted_offset_py)

    # 1) Find the best identifier to trace at/near the cursor.
    best = run_worker("best_index", args.file, str(adjusted_offset_utf16))
    if not best or best.get("error") or not best.get("best") or best["best"].get("index") is None:
        # Fallback: try tracing directly at the provided offset.
        trace = run_worker("trace", args.file, str(adjusted_offset_utf16))
        if args.json:
            print(
                json.dumps(
                    {
                        "cursor_offset": args.offset,
                        "cursor_offset_kind": args.offset_kind,
                        "cursor_offset_py": cursor_offset_py,
                        "adjusted_offset_py": adjusted_offset_py,
                        "cursor_offset_utf16": cursor_offset_utf16,
                        "adjusted_offset_utf16": adjusted_offset_utf16,
                        "best_index": best,
                        "trace": trace,
                    },
                    indent=2,
                )
            )
        else:
            if best and best.get("error"):
                print(f"best_index error: {best.get('error')}")
            print("Could not find a reliable identifier at that offset.")
            if trace and trace.get("error"):
                print(f"trace error: {trace.get('error')}")
        return 2

    trace_offset = int(best["best"]["index"])
    trace = run_worker("trace", args.file, str(trace_offset))
    if not trace:
        if args.json:
            print(json.dumps({"best_index": best, "trace": None}, indent=2))
        else:
            print("Error: worker trace failed.")
        return 2

    # If the "best" pick leads to an unhelpful result, try alternates.
    # This matters for minified bundles where the cursor can be near token boundaries.
    if trace.get("type") in ("Global/Implicit",) and best.get("alternates"):
        for alt in best["alternates"]:
            alt_index = alt.get("index")
            if alt_index is None:
                continue
            alt_trace = run_worker("trace", args.file, str(int(alt_index)))
            if not alt_trace or alt_trace.get("error"):
                continue
            if alt_trace.get("type") not in ("Global/Implicit",):
                trace_offset = int(alt_index)
                trace = alt_trace
                break

    # 2) If the traced definition is a Webpack import, resolve the module using codegraph_map.json.
    module_resolution = None
    import_id = trace.get("importId")
    module_map_path = args.module_map
    if module_map_path is None:
        module_map_path = _find_module_map(os.path.dirname(os.path.abspath(args.file))) or _find_module_map(os.getcwd())

    if import_id is not None:
        module_map = load_module_map(module_map_path) if module_map_path else None
        if module_map is not None:
            module_resolution = module_map.get(str(import_id))

    out = {
        "file": args.file,
        "cursor_offset": args.offset,
        "cursor_offset_kind": args.offset_kind,
        "cursor_offset_py": cursor_offset_py,
        "adjusted_offset_py": adjusted_offset_py,
        "cursor_offset_utf16": cursor_offset_utf16,
        "adjusted_offset_utf16": adjusted_offset_utf16,
        "trace_offset": trace_offset,
        "best_index": best,
        "trace": trace,
        "module_resolution": module_resolution,
        "module_map_path": module_map_path,
        "encoding": args.encoding,
        "errors": args.errors,
    }

    if args.json:
        print(json.dumps(out, indent=2))
        return 0

    # Human-readable output (VS Code-like).
    sym = trace.get("name")
    typ = trace.get("type")
    line = trace.get("line")
    print("--- Go To Definition ---")
    print(f"Symbol: {sym}")
    print(f"Type: {typ}")
    if line is not None:
        print(f"Defined at Line: {line}")

    if typ == "Global/Implicit":
        print("Note: no local definition found in this file/scope (likely a global or external import).")

    if trace.get("type") == "PropertyKey":
        print(f"Value Type: {trace.get('valueType')}")
        if trace.get("valuePreview"):
            print(f"Value: {trace.get('valuePreview')}")
    elif trace.get("initCode"):
        print(f"Code: {trace.get('initCode')}")

    if import_id is not None:
        print("")
        print(f"[!] Detected Webpack Import of Module {import_id}")
        if not module_map_path or not os.path.exists(module_map_path):
            print(f"--> No module index found ({DEFAULT_MODULE_MAP_FILE}). Run: python3 universal_reverse_engineer/codegraph.py index <dir>")
        elif module_resolution:
            print(f"--> JUMP TO: {module_resolution.get('file')}")
            info = module_resolution.get("info") or {}
            if info.get("line") is not None:
                print(f"    Line: {info.get('line')}")
            if module_resolution.get("candidates"):
                print(f"    (Multiple candidates exist for this module id; index stored {len(module_resolution['candidates'])} candidates.)")
        else:
            print("--> Module not found in index. (Try rebuilding index)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())







