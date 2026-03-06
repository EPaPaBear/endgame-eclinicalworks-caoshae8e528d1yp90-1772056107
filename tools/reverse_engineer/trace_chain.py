#!/usr/bin/env python3
"""
Trace all writes to a variable within its scope (AST-based).
"""

import argparse
import json
import os
import subprocess
import sys
from typing import Any, Dict, Optional

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKER_SCRIPT = os.path.join(SCRIPT_DIR, "codegraph_worker.js")

def _py_index_to_utf16_code_unit_index(content: str, py_index: int) -> int:
    """
    Convert a Python string index (Unicode code points) to a JS string index
    (UTF-16 code units), which is what the node worker uses (acorn indices).

    Most bundles are ASCII-only, so this is usually a no-op. But if the file
    contains astral-plane characters earlier (emoji, some symbols), JS indices
    will be larger than Python indices.
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


def _byte_offset_to_py_index(file_bytes: bytes, byte_offset: int, encoding: str) -> int:
    """
    Convert UTF-8 byte offset -> Python codepoint index.
    If byte_offset lands mid-codepoint, step back a few bytes.
    """
    if byte_offset <= 0:
        return 0
    if byte_offset > len(file_bytes):
        byte_offset = len(file_bytes)
    for back in range(0, 4):
        cut = byte_offset - back
        try:
            return len(file_bytes[:cut].decode(encoding, errors="strict"))
        except UnicodeDecodeError:
            continue
    return len(file_bytes[:byte_offset].decode(encoding, errors="replace"))


def run_worker(command: str, file_path: str, arg: str, arg2: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Run the codegraph worker with a command."""
    cmd = ["node", WORKER_SCRIPT, command, file_path, str(arg)]
    if arg2:
        cmd.append(str(arg2))
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            if result.stderr:
                return {'error': f'Worker error: {result.stderr[:200]}'}
            return None
        return json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        return {'error': 'Worker timed out (120s)'}
    except json.JSONDecodeError as e:
        return {'error': f'Invalid JSON from worker: {str(e)[:100]}'}
    except Exception as e:
        return {'error': f'Worker failed: {str(e)[:100]}'}


def format_trace(trace: Dict[str, Any]) -> str:
    """Format the trace result for human-readable output."""
    lines = []
    
    if trace.get('error'):
        return f"❌ Error: {trace['error']}"
    
    var_name = trace.get('variable', '?')
    lines.append(f"🔍 Variable: {var_name}")
    lines.append("=" * 60)
    
    # Scope info
    scope = trace.get('scope')
    if scope and scope != 'global':
        lines.append(f"📍 Scope: {scope.get('type', '?')} (line {scope.get('line', '?')})")
    else:
        lines.append("📍 Scope: global")
    
    # Definition
    defn = trace.get('definition')
    if defn:
        lines.append("")
        lines.append("📌 DEFINITION")
        dtype = defn.get('type', '?')
        line = defn.get('line', '?')
        offset = defn.get('offset', '?')
        lines.append(f"   [{line}] @{offset} ({dtype})")
        
        if defn.get('kind'):
            lines.append(f"   Kind: {defn.get('kind')}")
        if defn.get('source'):
            lines.append(f"   Import: {defn.get('source')}")
        if defn.get('params'):
            lines.append(f"   Params: ({defn.get('params')})")
        
        if defn.get('initCode'):
            init = defn['initCode']
            # Show first few lines nicely
            init_lines = init.split('\n')[:10]
            lines.append("   Init:")
            for il in init_lines:
                lines.append(f"      {il[:100]}")
            if len(init) > 500:
                lines.append(f"      ... ({len(init) - 500} more chars)")
    else:
        lines.append("")
        lines.append("📌 DEFINITION: Not found in scope")
    
    # Writes (the main content!)
    writes = trace.get('writes', [])
    if writes:
        lines.append("")
        lines.append(f"✏️  WRITES ({len(writes)})")
        for w in writes:
            wtype = w.get('type', '?')
            line = w.get('line', '?')
            offset = w.get('offset', '?')
            code = w.get('code', '')[:100]
            
            # Property assignment gets special formatting
            if wtype == 'property_assignment':
                prop = w.get('property', '?')
                right = w.get('rightCode', '')[:60]
                lines.append(f"   [{line}] {var_name}.{prop} = {right}")
            elif wtype == 'assignment':
                right = w.get('rightCode', '')[:80]
                lines.append(f"   [{line}] {var_name} = {right}")
            else:
                lines.append(f"   [{line}] {code}")
    else:
        lines.append("")
        lines.append("✏️  WRITES: None found")
    
    # Passed to (exit points)
    passed_to = trace.get('passed_to', [])
    if passed_to:
        lines.append("")
        lines.append(f"➡️  PASSED TO ({len(passed_to)})")
        for p in passed_to:
            line = p.get('line', '?')
            callee = p.get('callee', '?')
            arg_idx = p.get('argIndex', 0)
            code = p.get('code', '')[:80]
            lines.append(f"   [{line}] {callee}(...{var_name}...) as arg{arg_idx}")
    
    # Scope code preview (optional, for context)
    scope_code = trace.get('scope_code')
    if scope_code:
        lines.append("")
        lines.append("📄 SCOPE CODE (first 1500 chars)")
        lines.append("-" * 40)
        preview = scope_code[:1500]
        lines.append(f"   {preview}")
        if len(scope_code) > 1500:
            lines.append(f"   ... ({len(scope_code) - 1500} more chars)")
    
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Trace all writes to a variable within its scope (AST-based)."
    )
    parser.add_argument("file", help="Path to the JS file")
    parser.add_argument("symbol", help="Variable/symbol name to trace")
    parser.add_argument("offset", type=int, help="Character offset in the file (use get_index.py to find)")
    parser.add_argument(
        "--offset-kind",
        choices=["py", "utf16", "byte"],
        default="py",
        help="Interpret offset as Python codepoint index (py), JS UTF-16 code unit index (utf16), or UTF-8 byte offset (byte). Default: py.",
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
        help="Decode error handling for reading files. Use strict for stable offsets. Default: strict.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )
    args = parser.parse_args()
    
    if not os.path.exists(args.file):
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        return 1

    # Convert to the node worker's coordinate system (UTF-16 code units).
    worker_offset = args.offset
    try:
        with open(args.file, "rb") as f:
            raw = f.read()
        content = raw.decode(args.encoding, errors=args.errors)
    except Exception:
        # Fall back to previous best-effort behavior.
        with open(args.file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        raw = content.encode("utf-8", errors="ignore")

    if args.offset_kind == "py":
        worker_offset = _py_index_to_utf16_code_unit_index(content, args.offset)
    elif args.offset_kind == "byte":
        py_off = _byte_offset_to_py_index(raw, args.offset, args.encoding)
        worker_offset = _py_index_to_utf16_code_unit_index(content, py_off)
    else:
        worker_offset = args.offset

    # Call the worker with both symbol and offset (worker expects UTF-16 indices).
    trace = run_worker("trace_var", args.file, str(worker_offset), args.symbol)
    
    if not trace:
        print("Error: Worker returned no result", file=sys.stderr)
        return 1
    
    if args.json:
        print(json.dumps(trace, indent=2))
    else:
        print(format_trace(trace))
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
