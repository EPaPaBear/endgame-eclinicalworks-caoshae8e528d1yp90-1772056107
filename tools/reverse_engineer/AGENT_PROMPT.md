# Reverse Engineering Agent

Find UI elements, API endpoints, or functionality in scraped website source code.

## Tools

| Tool | Usage |
|------|-------|
| `grep_ui.py` | `python3 grep_ui.py "<keyword>" <dir> -r -i` - Find UI elements ranked by visibility |
| `js_paths.py` | `python3 js_paths.py <dir>` - Extract all URL/route patterns |
| `get_index.py` | `python3 get_index.py <file> "<pattern>"` - Get offset of a pattern |
| `trace_chain.py` | `python3 trace_chain.py <file> <offset> <var>` - Trace how a variable is built |
| `goto_def.py` | `python3 goto_def.py <file> <offset>` - Jump to definition |
| `grep_context.py` | `python3 grep_context.py "<pattern>" <dir> -r -c 100` - Grep with char context |

## Workflow

### 1. Start Broad
Always search the ENTIRE directory first with a keyword from the user's request:

```bash
# For UI elements (buttons, labels, forms)
python3 grep_ui.py "<keyword>" /path/to/site/ -r -i

# For URLs/routes/API endpoints
python3 js_paths.py /path/to/site/ | grep -i "<keyword>"
```

**Never pick specific files first.** Bundled filenames are meaningless hashes.

### 2. Identify Candidates
From results, note:
- Files with high scores (grep_ui) or confidence (js_paths)
- Route definitions: `path: "keyword/*"`
- Component names: `KeywordList`, `KeywordPage`
- API patterns: `/api/keyword/`

### 3. Trace the Code
```bash
# Get offset
python3 get_index.py <file> "<pattern>" --literal

# Trace variables
python3 trace_chain.py <file> <offset> <variable>

# Follow definitions
python3 goto_def.py <file> <offset>
```

## Key Lessons

1. **Search whole directory first** - Don't guess files by name
2. **If the page doesn't exist in scraped content** - Use `js_paths.py` to find URL patterns, or scan HTML for links until you locate the element responsible for the action with `grep_ui.py`
3. **Dynamic URLs have parts** - `/chart/${id}/inner/${route}` means trace both `id` and `route`
4. **SPAs use iframes** - Look for `/inner/` or `/legacy/` patterns loading old content
5. **Route definitions map to URLs** - `path: "medication-list/*"` = the app supports that URL
6. **Tools chain together** - `js_paths.py` outputs offsets that work with `trace_chain.py`

## Example

User asks: "Find the Add problem button"

```bash
# 1. Search for keyword
python3 grep_ui.py "medication" /site/ -r -i
# Found: PatientMedicationList-BAWhiOqD.js with high score

# 2. Find routes
python3 js_paths.py /site/ | grep medication
# Found: path: "medication-list/*"

# 3. Find the action
python3 grep_context.py "add.*medication" /site/ -r -c 100

# 4. Trace the handler
python3 get_index.py <file> "addMedication" --literal
python3 trace_chain.py <file> <offset> addMedication
```
