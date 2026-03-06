#!/usr/bin/env python3
"""
js_paths.py - Extract URL patterns from JavaScript files.

Usage:
    python js_paths.py <file_or_directory>

Examples:
    python js_paths.py bundle.js
    python js_paths.py ./site_media/bundles/

Output includes index_py offsets compatible with other tools:
    python js_paths.py bundle.js --json | jq '.[0].index_py'
    python goto_def.py bundle.js <index_py>
    python trace_chain.py bundle.js <variable> <index_py>
"""

import os
import re
import sys
import json
import argparse
from dataclasses import dataclass, field
from typing import Literal

OffsetKind = Literal["py", "utf16", "byte", "all"]


# =============================================================================
# Offset Conversion (matches other tools)
# =============================================================================

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


# =============================================================================
# URL Pattern Detection
# =============================================================================

@dataclass
class URLMatch:
    pattern: str
    file: str
    index_py: int
    end_index_py: int
    usage: str
    confidence: int
    variables: list[str] = field(default_factory=list)
    context: str = ""
    _content: str = field(default="", repr=False)

    @property
    def index_utf16(self) -> int:
        return _py_to_utf16_index(self._content, self.index_py)

    @property
    def end_index_utf16(self) -> int:
        return _py_to_utf16_index(self._content, self.end_index_py)

    @property
    def index_byte(self) -> int:
        return _py_to_byte_offset(self._content, self.index_py)

    @property
    def end_index_byte(self) -> int:
        return _py_to_byte_offset(self._content, self.end_index_py)

    @property
    def line(self) -> int:
        return self._content.count('\n', 0, self.index_py) + 1

    def to_dict(self) -> dict:
        return {
            "pattern": self.pattern,
            "file": self.file,
            "index_py": self.index_py,
            "end_index_py": self.end_index_py,
            "index_utf16": self.index_utf16,
            "end_index_utf16": self.end_index_utf16,
            "index_byte": self.index_byte,
            "end_index_byte": self.end_index_byte,
            "line": self.line,
            "usage": self.usage,
            "confidence": self.confidence,
            "variables": self.variables,
            "context": self.context,
        }


# Template variable: ${varName}
TEMPLATE_VAR_RE = re.compile(r'\$\{([^}]+)\}')

# Route params: :paramName
ROUTE_PARAM_RE = re.compile(r':([a-zA-Z_]\w*)')


def extract_variables(pattern: str) -> list[str]:
    """Extract variable names from a URL pattern."""
    variables = []

    for match in TEMPLATE_VAR_RE.finditer(pattern):
        var = match.group(1).strip()
        variables.append(var.split('.')[0].split('[')[0])

    for match in ROUTE_PARAM_RE.finditer(pattern):
        variables.append(match.group(1))

    return list(dict.fromkeys(variables))


def is_noise(s: str) -> bool:
    """Filter out obvious non-URL patterns."""
    if not s or len(s) < 2:
        return True

    # Very short single-char paths are noise
    if len(s) <= 2 and s in ('/', '//', '/.', '/..'):
        return True

    # CSS selectors (but allow paths that happen to start with class-like names)
    if s.startswith('.') and '/' not in s:
        return True
    if s.startswith('#') and '/' not in s:
        return True

    # Asset files
    asset_exts = ('.css', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.woff', '.woff2',
                  '.ttf', '.eot', '.ico', '.map', '.scss', '.less', '.sass',
                  '.mp3', '.mp4', '.webm', '.ogg', '.wav', '.pdf', '.zip', '.tar')
    if s.lower().endswith(asset_exts):
        return True

    # Node modules, webpack internals
    if 'node_modules' in s:
        return True
    if '__webpack' in s.lower():
        return True

    # Source maps
    if s.startswith('//# source') or s.startswith('//# sourceMappingURL'):
        return True

    # Data URIs
    if s.startswith('data:'):
        return True

    # Common JS patterns that aren't URLs
    if s in ('use strict', 'use asm'):
        return True

    # Pure numbers or weird patterns
    if re.match(r'^/\d+$', s):  # Just /123
        return True

    # Single slash or dots
    if s in ('/', '.', '..', './', '../'):
        return True

    return False


def calculate_confidence(pattern: str, usage: str) -> int:
    """Score confidence that this is a real API/page URL."""
    score = 50

    # Usage type scoring
    usage_scores = {
        'fetch': 40,
        '$http': 40,
        'axios': 40,
        'xhr': 35,
        'request': 35,
        'iframe.src': 35,
        'window.location': 30,
        'navigate': 30,
        'router.push': 30,
        'redirect': 30,
        'href': 25,
        'route': 30,
        'path-prop': 25,
        'src': 20,
        'action': 25,
        'URL()': 25,
        'template': 15,
        'concat': 15,
        'string-slash': 10,
        'string-path': 5,
    }
    score += usage_scores.get(usage, 0)

    # Path structure signals
    if pattern.startswith('/'):
        score += 10
    if pattern.startswith('http://') or pattern.startswith('https://'):
        score += 15
    if pattern.startswith('//'):  # Protocol-relative
        score += 10

    # API-like patterns
    if re.search(r'/api/', pattern, re.I):
        score += 15
    if re.search(r'/v\d+/', pattern):
        score += 10
    if re.search(r'/(graphql|rest|rpc)/', pattern, re.I):
        score += 15

    # Common path segments
    if re.search(r'/(auth|login|logout|register|signup|signin)/', pattern, re.I):
        score += 10
    if re.search(r'/(users?|patients?|admin|dashboard|settings|profile)/', pattern, re.I):
        score += 10
    if re.search(r'/(chart|erx|misc|inner|fhir)/', pattern, re.I):
        score += 10

    # Has parameters = likely dynamic endpoint
    if '${' in pattern:
        score += 15
    if re.search(r':[a-zA-Z_]', pattern):
        score += 15
    if '*' in pattern:  # Wildcard route
        score += 10

    # Multiple path segments = more likely real
    slash_count = pattern.count('/')
    if slash_count >= 3:
        score += 10
    elif slash_count >= 2:
        score += 5

    # Negative signals
    if len(pattern) < 3:
        score -= 20
    if re.search(r'\s', pattern):  # Whitespace
        score -= 30
    if pattern.count('$') > 3:  # Too many variables
        score -= 10

    # Very generic single segments
    if re.match(r'^/[a-z]+$', pattern) and len(pattern) < 8:
        score -= 10

    return max(0, min(100, score))


def get_context(content: str, start: int, end: int, chars: int = 50) -> str:
    """Get surrounding context for a match."""
    ctx_start = max(0, start - chars)
    ctx_end = min(len(content), end + chars)

    before = content[ctx_start:start].replace('\n', '\\n')
    matched = content[start:end]
    after = content[end:ctx_end].replace('\n', '\\n')

    if len(matched) > 80:
        matched = matched[:40] + "..." + matched[-37:]

    result = f"{before}>>>{matched}<<<{after}"
    if len(result) > 220:
        result = result[:220] + "..."

    return result


# =============================================================================
# Pattern Matchers - AGGRESSIVE
# =============================================================================

PATTERNS = [
    # =========================================================================
    # HIGH CONFIDENCE: Explicit API/fetch calls
    # =========================================================================

    # Fetch API
    (r'''fetch\s*\(\s*["'`]([^"'`]+)["'`]''', 'fetch'),
    (r'''fetch\s*\(\s*`([^`]+)`''', 'fetch'),

    # jQuery AJAX
    (r'''\$\.(?:get|post|ajax|getJSON)\s*\(\s*["'`]([^"'`]+)["'`]''', 'fetch'),

    # Angular $http
    (r'''\$http\.(?:get|post|put|delete|patch|head|options)\s*\(\s*["'`]([^"'`]+)["'`]''', '$http'),

    # Axios
    (r'''axios\.(?:get|post|put|delete|patch|head|options|request)\s*\(\s*["'`]([^"'`]+)["'`]''', 'axios'),
    (r'''axios\s*\(\s*\{[^}]*url\s*:\s*["'`]([^"'`]+)["'`]''', 'axios'),

    # XMLHttpRequest
    (r'''\.open\s*\(\s*["'][A-Z]+["']\s*,\s*["'`]([^"'`]+)["'`]''', 'xhr'),

    # Generic request functions
    (r'''(?:request|sendRequest|apiCall|httpRequest)\s*\(\s*["'`]([^"'`]+)["'`]''', 'request'),

    # =========================================================================
    # HIGH CONFIDENCE: Navigation
    # =========================================================================

    # window.location
    (r'''(?:window\.)?location(?:\.href)?\s*=\s*["'`]([^"'`]+)["'`]''', 'window.location'),
    (r'''location\.(?:assign|replace)\s*\(\s*["'`]([^"'`]+)["'`]''', 'window.location'),

    # React Router / Next.js / Vue Router navigation
    (r'''navigate\s*\(\s*["'`]([^"'`]+)["'`]''', 'navigate'),
    (r'''\.push\s*\(\s*["'`]([^"'`]+)["'`]''', 'router.push'),
    (r'''\.replace\s*\(\s*["'`]([^"'`]+)["'`]''', 'router.push'),
    (r'''redirect\s*\(\s*["'`]([^"'`]+)["'`]''', 'redirect'),
    (r'''Router\.push\s*\(\s*["'`]([^"'`]+)["'`]''', 'router.push'),
    (r'''router\.push\s*\(\s*["'`]([^"'`]+)["'`]''', 'router.push'),
    (r'''history\.push\s*\(\s*["'`]([^"'`]+)["'`]''', 'router.push'),
    (r'''history\.replace\s*\(\s*["'`]([^"'`]+)["'`]''', 'router.push'),

    # =========================================================================
    # HIGH CONFIDENCE: URL construction
    # =========================================================================

    (r'''new\s+URL\s*\(\s*["'`]([^"'`]+)["'`]''', 'URL()'),
    (r'''new\s+URL\s*\(\s*`([^`]+)`''', 'URL()'),
    (r'''URL\.resolve\s*\([^,]+,\s*["'`]([^"'`]+)["'`]''', 'URL()'),

    # =========================================================================
    # MEDIUM CONFIDENCE: Property assignments
    # =========================================================================

    # Route definitions (React Router, Vue, Angular, Express)
    (r'''path\s*:\s*["'`]([^"'`]+)["'`]''', 'route'),
    (r'''<Route[^>]*\s+path\s*=\s*["'`]([^"'`]+)["'`]''', 'route'),
    (r'''<Route[^>]*\s+path\s*=\s*\{?\s*["'`]([^"'`]+)["'`]''', 'route'),

    # Link/navigation components
    (r'''to\s*[=:]\s*["'`]([^"'`]+)["'`]''', 'route'),
    (r'''<Link[^>]*\s+to\s*=\s*["'`]([^"'`]+)["'`]''', 'route'),
    (r'''<NavLink[^>]*\s+to\s*=\s*["'`]([^"'`]+)["'`]''', 'route'),
    (r'''<a[^>]*\s+href\s*=\s*["'`]([^"'`]+)["'`]''', 'href'),

    # src/href assignments
    (r'''\.src\s*=\s*["'`]([^"'`]+)["'`]''', 'src'),
    (r'''\.href\s*=\s*["'`]([^"'`]+)["'`]''', 'href'),
    (r'''src\s*:\s*["'`]([^"'`]+)["'`]''', 'src'),
    (r'''href\s*:\s*["'`]([^"'`]+)["'`]''', 'href'),

    # Form action
    (r'''action\s*[=:]\s*["'`]([^"'`]+)["'`]''', 'action'),
    (r'''<form[^>]*\s+action\s*=\s*["'`]([^"'`]+)["'`]''', 'action'),

    # URL/endpoint properties
    (r'''(?:url|endpoint|apiUrl|baseUrl|basePath|apiPath|pathname)\s*:\s*["'`]([^"'`]+)["'`]''', 'path-prop'),
    (r'''(?:url|endpoint|apiUrl|baseUrl|basePath|apiPath|pathname)\s*=\s*["'`]([^"'`]+)["'`]''', 'path-prop'),

    # =========================================================================
    # MEDIUM CONFIDENCE: Template literals with paths
    # =========================================================================

    # Template literal with variables (most likely dynamic URLs)
    (r'`(/[^`]*\$\{[^`]*)`', 'template'),
    (r'`(https?://[^`]*\$\{[^`]*)`', 'template'),

    # Template literal without variables but path-like
    (r'`(/[a-zA-Z][^`]*)`', 'template'),

    # =========================================================================
    # LOWER CONFIDENCE: String concatenation (path chunks)
    # =========================================================================

    # String before + (path chunk)
    (r'''["'](/[^"']*?)["']\s*\+''', 'concat'),
    (r'''\+\s*["'](/[^"']*?)["']''', 'concat'),
    (r'''["']([^"']*/)["']\s*\+''', 'concat'),

    # =========================================================================
    # CATCH-ALL: Any string that looks like a path
    # =========================================================================

    # Any string starting with / (absolute path)
    (r'''["'](/[a-zA-Z0-9_$.{}\[\]:*?&=/@-]+)["']''', 'string-slash'),

    # Any string starting with ./ or ../ (relative path)
    (r'''["'](\.\.?/[a-zA-Z0-9_$.{}\[\]:*?&=/@-]+)["']''', 'string-slash'),

    # Protocol-relative URLs
    (r'''["'](//[a-zA-Z0-9_$.{}\[\]:*?&=/@.-]+)["']''', 'string-slash'),

    # Full URLs
    (r'''["'](https?://[^"']+)["']''', 'string-slash'),

    # Route params pattern (:id style) in any string
    (r'''["']([^"']*:[a-zA-Z_]\w*[^"']*)["']''', 'string-path'),

    # Wildcard routes
    (r'''["']([^"']*\*[^"']*)["']''', 'string-path'),

    # Any string with path-like structure (word/word)
    (r'''["']([a-zA-Z][\w-]*/[\w./${}:*?&=-]+)["']''', 'string-path'),
]


def extract_from_content(content: str, filepath: str) -> list[URLMatch]:
    """Extract all URL patterns from file content."""
    matches = []
    seen = set()

    for pattern_re, usage in PATTERNS:
        try:
            for m in re.finditer(pattern_re, content, re.IGNORECASE):
                url = m.group(1)

                if is_noise(url):
                    continue

                # Dedupe by (pattern, file)
                key = (url, filepath)
                if key in seen:
                    continue
                seen.add(key)

                start_idx = m.start(1)
                end_idx = m.end(1)

                match = URLMatch(
                    pattern=url,
                    file=filepath,
                    index_py=start_idx,
                    end_index_py=end_idx,
                    usage=usage,
                    confidence=calculate_confidence(url, usage),
                    variables=extract_variables(url),
                    context=get_context(content, m.start(), m.end()),
                    _content=content,
                )
                matches.append(match)
        except re.error:
            continue

    return matches


# =============================================================================
# File Processing
# =============================================================================

def read_file(filepath: str, encoding: str = "utf-8", errors: str = "replace") -> str | None:
    """Read file content, handling encoding errors gracefully."""
    try:
        with open(filepath, 'rb') as f:
            data = f.read()
        return data.decode(encoding, errors=errors)
    except Exception as e:
        print(f"Error reading {filepath}: {e}", file=sys.stderr)
        return None


def process_file(filepath: str) -> list[URLMatch]:
    """Process a single file."""
    content = read_file(filepath)
    if content is None:
        return []
    return extract_from_content(content, filepath)


def process_path(path: str, max_files: int = 100) -> list[URLMatch]:
    """Process a file or directory."""
    path = os.path.abspath(path)
    all_matches = []

    if os.path.isfile(path):
        return process_file(path)

    if os.path.isdir(path):
        extensions = ('.js', '.jsx', '.ts', '.tsx', '.html', '.htm', '.vue', '.svelte', '.mjs', '.cjs')
        files_processed = 0

        for root, _, files in os.walk(path):
            for fname in files:
                if files_processed >= max_files:
                    break
                if fname.endswith(extensions) and not fname.endswith('.map'):
                    fpath = os.path.join(root, fname)
                    matches = process_file(fpath)
                    all_matches.extend(matches)
                    files_processed += 1
            if files_processed >= max_files:
                break
    else:
        print(f"Path not found: {path}", file=sys.stderr)
        sys.exit(1)

    return all_matches


def dedupe_patterns(matches: list[URLMatch]) -> list[URLMatch]:
    """Deduplicate patterns, keeping highest confidence version."""
    by_pattern = {}
    for m in matches:
        key = m.pattern
        if key not in by_pattern or m.confidence > by_pattern[key].confidence:
            by_pattern[key] = m
    return list(by_pattern.values())


# =============================================================================
# Output Formatting
# =============================================================================

def format_human(matches: list[URLMatch], offset_kind: OffsetKind) -> str:
    """Format matches for human-readable output."""
    if not matches:
        return "No URL patterns found."

    matches = sorted(matches, key=lambda m: -m.confidence)

    lines = [f"Found {len(matches)} URL patterns (sorted by confidence):", ""]

    for i, m in enumerate(matches, 1):
        conf = "HIGH" if m.confidence >= 70 else "MED" if m.confidence >= 40 else "LOW"

        lines.append(f"[{i}] [{conf}] {m.pattern}")
        lines.append(f"    File: {os.path.basename(m.file)}")
        lines.append(f"    Usage: {m.usage}")
        lines.append(f"    Index({offset_kind}): {_format_offset(offset_kind, m._content, m.index_py)}")
        if m.variables:
            lines.append(f"    Variables: {', '.join(m.variables)}")
        lines.append(f"    Context: ...{m.context}...")
        lines.append("")

    lines.append("=" * 60)
    lines.append("To trace a URL pattern's construction:")
    lines.append("  python goto_def.py <file> <index_py>")
    lines.append("  python trace_chain.py <file> <variable> <index_py>")
    lines.append("")

    return "\n".join(lines)


def format_json(matches: list[URLMatch]) -> str:
    """Format matches as JSON for programmatic use."""
    matches = sorted(matches, key=lambda m: -m.confidence)
    return json.dumps([m.to_dict() for m in matches], indent=2)


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Extract URL patterns from JavaScript files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python js_paths.py bundle.js
    python js_paths.py ./site_media/bundles/
    python js_paths.py bundle.js --json

Chaining with other tools:
    python js_paths.py bundle.js --json | jq '.[0]'
    python goto_def.py bundle.js <index_py>
    python trace_chain.py bundle.js <variable> <index_py>
"""
    )
    parser.add_argument("path", help="File or directory to scan")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of human-readable text")
    parser.add_argument("--limit", type=int, default=50, help="Max patterns to output (default: 50)")
    parser.add_argument("--max-files", type=int, default=100, help="Max files to scan in directory (default: 100)")
    parser.add_argument(
        "--offset-kind",
        choices=["py", "utf16", "byte", "all"],
        default="py",
        help="Offset format for human output (default: py). JSON always includes all."
    )
    parser.add_argument(
        "--min-confidence",
        type=int,
        default=0,
        help="Only show patterns with confidence >= this value (0-100)"
    )

    args = parser.parse_args()

    matches = process_path(args.path, max_files=args.max_files)
    matches = dedupe_patterns(matches)

    # Filter by confidence
    if args.min_confidence > 0:
        matches = [m for m in matches if m.confidence >= args.min_confidence]

    # Limit output
    matches = sorted(matches, key=lambda m: -m.confidence)[:args.limit]

    if args.json:
        print(format_json(matches))
    else:
        print(format_human(matches, args.offset_kind))


if __name__ == "__main__":
    main()
