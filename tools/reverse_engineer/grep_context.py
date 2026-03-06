
import os
import sys
import argparse
import re
from typing import Literal

OffsetKind = Literal["py", "utf16", "byte", "all"]


def _read_text(filepath: str, encoding: str, errors: str) -> str:
    with open(filepath, "rb") as f:
        data = f.read()
    try:
        return data.decode(encoding, errors=errors)
    except UnicodeDecodeError as e:
        raise UnicodeDecodeError(
            e.encoding,
            e.object,
            e.start,
            e.end,
            f"{e.reason}. Try --errors replace if you must (offsets may drift).",
        )


def _py_to_utf16_index(content: str, py_index: int) -> int:
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
    if py_index <= 0:
        return 0
    if py_index >= len(content):
        py_index = len(content)
    total = 0
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


def _format_offset(kind: OffsetKind, content: str, idx_py: int) -> str:
    if kind == "py":
        return str(idx_py)
    if kind == "utf16":
        return str(_py_to_utf16_index(content, idx_py))
    if kind == "byte":
        return str(_py_to_byte_offset(content, idx_py))
    return f"py={idx_py} utf16={_py_to_utf16_index(content, idx_py)} byte={_py_to_byte_offset(content, idx_py)}"

def search_file(
    filepath,
    pattern,
    context_chars=100,
    ignore_case=False,
    encoding="utf-8",
    errors="strict",
    offset_kind: OffsetKind = "py",
    max_matches_per_file: int = 20,
    max_total_matches: int | None = None,
):
    """
    Search for a regex pattern in a file and print matches with character-based context.
    Suitable for minified files where line-based grep fails.
    """
    try:
        flags = re.IGNORECASE if ignore_case else 0
        regex = re.compile(pattern, flags)
        
        content = _read_text(filepath, encoding=encoding, errors=errors)
            
        matches = list(regex.finditer(content))
        
        if not matches:
            return 0, 0

        print(f"--- File: {filepath} ({len(matches)} matches) ---")
        
        to_print = matches[:max_matches_per_file]
        if max_total_matches is not None:
            to_print = to_print[: max(0, max_total_matches)]

        for i, match in enumerate(to_print):
            start_idx = match.start()
            end_idx = match.end()
            
            # Calculate context bounds
            ctx_start = max(0, start_idx - context_chars)
            ctx_end = min(len(content), end_idx + context_chars)
            
            # Extract text
            before = content[ctx_start:start_idx]
            matched_text = content[start_idx:end_idx]
            after = content[end_idx:ctx_end]
            
            # Replace newlines with visual indicators to keep output compact
            before = before.replace('\n', '\\n').replace('\r', '')
            matched_text = matched_text.replace('\n', '\\n').replace('\r', '')
            after = after.replace('\n', '\\n').replace('\r', '')
            
            print(f"Match #{i+1} @ Offset({offset_kind}) { _format_offset(offset_kind, content, start_idx) }:")
            print(f"...{before} >>>{matched_text}<<< {after}...")
            print("-" * 40)

        omitted = len(matches) - len(to_print)
        if omitted > 0:
            print(f"... and {omitted} more matches (omitted due to limits).")

        return len(matches), len(to_print)

    except Exception as e:
        print(f"Error reading {filepath}: {e}", file=sys.stderr)
        return 0, 0

def main():
    parser = argparse.ArgumentParser(description="Grep with Character Context (for minified files)")
    parser.add_argument("pattern", help="Regex pattern to search for")
    parser.add_argument("path", help="File or directory to search")
    parser.add_argument("-c", "--context", type=int, default=100, help="Number of characters of context (default: 100)")
    parser.add_argument("-i", "--ignore-case", action="store_true", help="Ignore case")
    parser.add_argument("-r", "--recursive", action="store_true", help="Recursive search")
    parser.add_argument("--max-files", type=int, default=25, help="Max files to scan when using -r (default: 25)")
    parser.add_argument("--max-total-matches", type=int, default=200, help="Max total matches to print across all files (default: 200)")
    parser.add_argument("--max-matches-per-file", type=int, default=20, help="Max matches to print per file (default: 20)")
    parser.add_argument(
        "--offset-kind",
        choices=["py", "utf16", "byte", "all"],
        default="py",
        help="Which offset kind to print. Default: py.",
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
    
    found_count = 0
    printed_total = 0
    remaining_total = max(0, int(args.max_total_matches)) if args.max_total_matches is not None else None
    
    if os.path.isfile(args.path):
        found, printed = search_file(
            args.path,
            args.pattern,
            args.context,
            args.ignore_case,
            encoding=args.encoding,
            errors=args.errors,
            offset_kind=args.offset_kind,
            max_matches_per_file=max(0, int(args.max_matches_per_file)),
            max_total_matches=remaining_total,
        )
        found_count += found
        printed_total += printed
    elif os.path.isdir(args.path):
        if not args.recursive:
            print("Path is a directory. Use -r for recursive search.")
            sys.exit(1)
            
        max_files = max(0, int(args.max_files))
        scanned = 0
        for root, _, files in os.walk(args.path):
            for file in files:
                if remaining_total is not None and remaining_total <= 0:
                    print("Reached --max-total-matches limit; stopping.")
                    break
                if max_files and scanned >= max_files:
                    print("Reached --max-files limit; stopping.")
                    break
                scanned += 1
                filepath = os.path.join(root, file)
                # Skip binary-looking extensions or huge assets if needed, but for now search all
                found, printed = search_file(
                    filepath,
                    args.pattern,
                    args.context,
                    args.ignore_case,
                    encoding=args.encoding,
                    errors=args.errors,
                    offset_kind=args.offset_kind,
                    max_matches_per_file=max(0, int(args.max_matches_per_file)),
                    max_total_matches=remaining_total,
                )
                found_count += found
                printed_total += printed
                if remaining_total is not None:
                    remaining_total -= printed
                    remaining_total = max(0, remaining_total)
            if (remaining_total is not None and remaining_total <= 0) or (max_files and scanned >= max_files):
                break
    else:
        print(f"Path not found: {args.path}")
        sys.exit(1)

    if found_count == 0:
        print("No matches found.")

if __name__ == "__main__":
    main()
