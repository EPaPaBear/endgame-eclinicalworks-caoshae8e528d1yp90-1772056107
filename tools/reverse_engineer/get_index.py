import sys
import re
import json
import argparse
from typing import Literal


IDENT_START_RE = re.compile(r"[A-Za-z_$]")
IDENT_RE = re.compile(r"[A-Za-z0-9_$]")

OffsetKind = Literal["py", "utf16", "byte", "all"]


def _read_text_and_bytes(file_path: str, encoding: str, errors: str) -> tuple[str, bytes]:
    """
    Read a file as bytes, decode to text with the requested encoding/error policy.

    IMPORTANT: Offsets depend on the decoded text. Using errors="ignore"/"replace"
    changes the decoded string length vs on-disk bytes, which makes offsets non-roundtrippable.
    For reliable offsets, prefer errors="strict".
    """
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


def _py_to_utf16_index(content: str, py_index: int) -> int:
    """
    Convert Python codepoint index -> JS UTF-16 code unit index.
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


def _py_to_byte_offset(content: str, py_index: int) -> int:
    """
    Convert Python codepoint index -> UTF-8 byte offset without allocating huge substrings.
    """
    if py_index <= 0:
        return 0
    if py_index >= len(content):
        py_index = len(content)
    total = 0
    # One-pass over the prefix; for typical bundles this is ASCII-fast.
    for ch in content[:py_index]:
        o = ord(ch)
        if o <= 0x7F:
            total += 1
        elif o <= 0x7FF:
            total += 2
        elif o <= 0xFFFF:
            total += 3
        else:
            total += 4
    return total


def _format_index_line(kind: OffsetKind, content: str, idx_py: int) -> str:
    if kind == "py":
        return f"{idx_py}"
    if kind == "utf16":
        return f"{_py_to_utf16_index(content, idx_py)}"
    if kind == "byte":
        return f"{_py_to_byte_offset(content, idx_py)}"
    # all
    return f"py={idx_py} utf16={_py_to_utf16_index(content, idx_py)} byte={_py_to_byte_offset(content, idx_py)}"


def _align_to_identifier_start(content: str, start_at: int) -> int | None:
    """Return index of first identifier-start char at/after start_at."""
    i = max(0, min(len(content), start_at))
    while i < len(content) and not IDENT_START_RE.match(content[i]):
        i += 1
    if i >= len(content):
        return None
    return i


def _read_identifier(content: str, start_at: int) -> tuple[str, int, int] | None:
    """Return (ident, start, end) if content[start_at] starts an identifier."""
    if start_at < 0 or start_at >= len(content):
        return None
    if not IDENT_START_RE.match(content[start_at]):
        return None
    j = start_at + 1
    while j < len(content) and IDENT_RE.match(content[j]):
        j += 1
    return content[start_at:j], start_at, j


def _find_identifier_near(
    content: str,
    ident: str,
    start_at: int,
    window: int,
) -> int | None:
    """
    Find exact identifier token `ident` in a window starting at start_at.
    Ensures word-boundary semantics for JS identifiers.
    """
    if not ident:
        return None
    lo = max(0, min(len(content), start_at))
    hi = min(len(content), lo + max(0, window))
    segment = content[lo:hi]
    # JS-ish identifier boundary: not preceded/followed by [A-Za-z0-9_$]
    pat = re.compile(rf"(?<![A-Za-z0-9_$]){re.escape(ident)}(?![A-Za-z0-9_$])")
    m = pat.search(segment)
    if not m:
        return None
    return lo + m.start()

def _find_definition_near(
    content: str,
    ident: str,
    near_at: int,
    window: int,
) -> int | None:
    """
    Best-effort: find a likely definition/assignment site for `ident` near `near_at`.

    This helps avoid landing in tiny lambdas like `()=>U("allergy")` when you really want
    the surrounding scope where `U = ...` is defined.

    Returns the start index of the identifier token at the definition site.
    """
    if not ident:
        return None

    lo = max(0, min(len(content), near_at) - max(0, window))
    hi = min(len(content), min(len(content), near_at) + max(0, window))
    seg = content[lo:hi]

    # Prefer explicit declarations first, then assignment.
    # Capture group 1 is the identifier occurrence we want to return.
    pats = [
        rf"(?<![A-Za-z0-9_$])(?:const|let|var)\s+({re.escape(ident)})(?![A-Za-z0-9_$])\s*=",
        rf"(?<![A-Za-z0-9_$])({re.escape(ident)})(?![A-Za-z0-9_$])\s*=",
        # Handle patterns like `ident=...=>` are covered by `=`, but keep a hint for arrow-ish defs.
        rf"(?<![A-Za-z0-9_$])({re.escape(ident)})(?![A-Za-z0-9_$])\s*=\s*(?:\([^)]*\)\s*=>|[A-Za-z0-9_$]+\s*=>|function\b)",
    ]

    best_abs: int | None = None
    best_dist: int | None = None

    for pat in pats:
        rx = re.compile(pat)
        for m in rx.finditer(seg):
            # Return the identifier group position, not the whole match.
            g1 = m.start(1)
            abs_idx = lo + g1
            dist = abs(abs_idx - near_at)
            if best_abs is None or dist < (best_dist or 0):
                best_abs = abs_idx
                best_dist = dist

    return best_abs


def find_indices(
    file_path,
    pattern,
    limit=20,
    align_identifier=None,
    align_window=400,
    literal=False,
    def_align=False,
    def_window=5000,
    json_out=False,
    encoding="utf-8",
    errors="strict",
    offset_kind: OffsetKind = "py",
):
    try:
        content, raw_bytes = _read_text_and_bytes(file_path, encoding=encoding, errors=errors)
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    if not json_out:
        print(f"Searching for '{pattern}' in {file_path}...\n")

    matches = []
    if literal:
        # Literal substring search (no regex escaping footguns).
        if pattern == "":
            if not json_out:
                print("Empty pattern.")
            return
        start = 0
        while True:
            idx = content.find(pattern, start)
            if idx == -1:
                break
            matches.append((idx, idx + len(pattern), pattern))
            start = idx + 1
    else:
        try:
            for m in re.finditer(pattern, content):
                matches.append((m.start(), m.end(), m.group(0)))
        except re.error as e:
            if json_out:
                print(
                    re.sub(
                        r"\s+",
                        " ",
                        f'{{"error":"Invalid regex pattern: {str(e).replace(chr(34), chr(39))}"}}',
                    )
                )
            else:
                print(f"Invalid regex pattern: {e}")
                print("Tip: If you're searching for a literal string, use --literal.")
            return
    
    if not matches:
        if json_out:
            print("[]")
        else:
            print("No matches found.")
        return

    total = len(matches)
    showing = min(total, limit)

    if json_out:
        out = []
    else:
        print(f"Found {total} matches (showing first {showing}):\n")
    
    for i, (start_index, end_index, matched_text_full) in enumerate(matches[:limit]):

        aligned_index = None
        aligned_ident = None
        if align_identifier is not None:
            aligned_index = _find_identifier_near(
                content, align_identifier, start_index, align_window
            )
            if aligned_index is None:
                aligned_index = _align_to_identifier_start(content, start_index)
            if aligned_index is not None:
                ident_info = _read_identifier(content, aligned_index)
                if ident_info is not None:
                    aligned_ident = ident_info[0]

        def_index = None
        if def_align and align_identifier is not None:
            def_index = _find_definition_near(
                content, align_identifier, start_index, def_window
            )
            
        # Get context (50 chars before and after)
        ctx_start = max(0, start_index - 50)
        ctx_end = min(len(content), end_index + 50)
        
        context = content[ctx_start:ctx_end]
        
        # Truncate matched text if too long
        matched_text = matched_text_full
        if len(matched_text) > 60:
            matched_text = matched_text[:30] + "..." + matched_text[-27:]
        
        # Highlight match in context (use truncated version for display)
        display_context = context[:start_index-ctx_start] + ">>>" + matched_text + "<<<" + context[end_index-ctx_start:]
        
        # Truncate entire context if still too long
        if len(display_context) > 200:
            display_context = display_context[:200] + "..."
        
        # Calculate line number
        line_num = content.count('\n', 0, start_index) + 1

        if json_out:
            out.append(
                {
                    "matchNumber": i + 1,
                    # Back-compat: keep `index`/`endIndex` as Python offsets.
                    "index": start_index,
                    "endIndex": end_index,
                    # New: always include all coordinate systems.
                    "index_py": start_index,
                    "endIndex_py": end_index,
                    "index_utf16": _py_to_utf16_index(content, start_index),
                    "endIndex_utf16": _py_to_utf16_index(content, end_index),
                    "index_byte": _py_to_byte_offset(content, start_index),
                    "endIndex_byte": _py_to_byte_offset(content, end_index),
                    "line": line_num,
                    "context": display_context.replace("\n", " "),
                    "alignedIdentifier": align_identifier,
                    "alignedIndex": aligned_index,
                    "alignedToken": aligned_ident,
                    "definitionIndex": def_index,
                    "encoding": encoding,
                    "errors": errors,
                }
            )
        else:
            print(f"Match #{i+1}")
            print(f"Index({offset_kind}): {_format_index_line(offset_kind, content, start_index)}")
            print(f"EndIndex({offset_kind}): {_format_index_line(offset_kind, content, end_index)}")
            if align_identifier is not None:
                if aligned_index is None:
                    print(f"AlignedIndex({align_identifier}): <not found>")
                else:
                    # Show what identifier we actually landed on (useful if fallback kicked in)
                    extra = f" ({aligned_ident})" if aligned_ident else ""
                    print(
                        f"AlignedIndex({align_identifier}, {offset_kind}): "
                        f"{_format_index_line(offset_kind, content, aligned_index)}{extra}"
                    )
                if def_align:
                    if def_index is None:
                        print(f"DefinitionIndex({align_identifier}): <not found>")
                    else:
                        print(
                            f"DefinitionIndex({align_identifier}, {offset_kind}): "
                            f"{_format_index_line(offset_kind, content, def_index)}"
                        )
            print(f"Line:  {line_num}")
            print(f"Context: {display_context.replace(chr(10), ' ')}") # Replace newlines for readable output
            print("-" * 50)

    if json_out:
        print(json.dumps(out, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Find 0-based character indices of a regex pattern in a file."
    )
    parser.add_argument("file_path")
    parser.add_argument("search_pattern", help="Regex pattern (re.finditer), unless --literal is used.")
    parser.add_argument("limit", nargs="?", type=int, default=20)
    parser.add_argument(
        "--limit",
        dest="limit_opt",
        type=int,
        default=None,
        help="Max matches to show (overrides positional limit).",
    )
    parser.add_argument(
        "--literal",
        action="store_true",
        help="Treat search_pattern as a literal substring (no regex).",
    )
    parser.add_argument(
        "--identifier",
        dest="align_identifier",
        default=None,
        help=(
            "If set, also compute an identifier-aligned index near each match "
            "(useful for feeding into codegraph trace/refs)."
        ),
    )
    parser.add_argument(
        "--window",
        dest="align_window",
        type=int,
        default=400,
        help="Search window (chars) after match for --identifier (default: 400).",
    )
    parser.add_argument(
        "--def",
        dest="def_align",
        action="store_true",
        help="Also try to find a likely definition/assignment site for --identifier near each match.",
    )
    parser.add_argument(
        "--def-window",
        dest="def_window",
        type=int,
        default=5000,
        help="Search window (chars) around match for --def (default: 5000).",
    )
    parser.add_argument(
        "--json",
        dest="json_out",
        action="store_true",
        help="Output JSON (array of matches) instead of human text.",
    )
    parser.add_argument(
        "--offset-kind",
        dest="offset_kind",
        choices=["py", "utf16", "byte", "all"],
        default="py",
        help="Which offset kind to print in human output. JSON always includes py/utf16/byte. Default: py.",
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
    args = parser.parse_args()

    find_indices(
        args.file_path,
        args.search_pattern,
        args.limit_opt if args.limit_opt is not None else args.limit,
        align_identifier=args.align_identifier,
        align_window=args.align_window,
        literal=args.literal,
        def_align=args.def_align,
        def_window=args.def_window,
        json_out=args.json_out,
        encoding=args.encoding,
        errors=args.errors,
        offset_kind=args.offset_kind,
    )
