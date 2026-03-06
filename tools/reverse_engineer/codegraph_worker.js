
const fs = require('fs');
const path = require('path');

// Try to load acorn from likely locations
let acorn, walk;
try {
    acorn = require('acorn');
    walk = require('acorn-walk');
} catch (e) {
    // Try local node_modules if running from root or sibling
    try {
        acorn = require('../ast-xray/node_modules/acorn');
        walk = require('../ast-xray/node_modules/acorn-walk');
        console.error("Loaded acorn from sibling directory");
    } catch (e2) {
        try {
            acorn = require('./ast-xray/node_modules/acorn');
            walk = require('./ast-xray/node_modules/acorn-walk');
        } catch (e3) {
            console.error("Could not find acorn/acorn-walk. Please install them.");
            process.exit(1);
        }
    }
}

// Many platforms ship extremely large bundles. Parsing huge files into an AST can be slow and
// memory-heavy, but refusing to operate at all makes the tool feel "broken".
//
// We keep a default limit to protect the common case, but allow overrides via env.
// Example:
//   CODEGRAPH_MAX_FILE_SIZE_MB=200 node codegraph_worker.js trace <file> <offset>
const MAX_FILE_SIZE = (parseInt(process.env.CODEGRAPH_MAX_FILE_SIZE_MB || '50', 10) || 50) * 1024 * 1024; // default 50MB

function parseFile(filePath) {
    if (!fs.existsSync(filePath)) return null;
    const content = fs.readFileSync(filePath, 'utf8');
    if (content.length > MAX_FILE_SIZE) return null;
    
    try {
        // Bundles can be classic scripts (Webpack IIFEs, legacy code) or ES modules (Vite/Rollup).
        // Parse as `script` first for maximum compatibility, then fall back to `module` to support
        // top-level `import` / `export` syntax.
        const parseOptsBase = {
            locations: true,
            ecmaVersion: 'latest',
            allowReturnOutsideFunction: true // Handle edge cases in bundled code
        };

        try {
            const ast = acorn.parse(content, { ...parseOptsBase, sourceType: 'script' });
            return { ast, content };
        } catch (eScript) {
            const ast = acorn.parse(content, { ...parseOptsBase, sourceType: 'module' });
            return { ast, content };
        }
    } catch (e) {
        console.error(`Parse Error in ${filePath}:`, e.message);
        return null;
    }
}

/**
 * Scans a file for Webpack module definitions.
 * Pattern: { 123: function(e,t,n) { ... }, 456: (e,t,n) => { ... } }
 */
/**
 * Fallback regex indexer for when AST fails
 */
function indexModulesRegex(content) {
    const modules = {};
    // Regex to match Webpack-like module table entries:
    // - "123: function" or "abcd: (e,t,n) =>" or "'O8uH':function"
    // We are conservative to avoid false positives in strings
    const regex = /["']?([A-Za-z0-9_$]+)["']?:\s*(?:function\b|\([^)]*\)\s*=>|[A-Za-z0-9_$]+\s*=>)/g;
    
    let match;
    while ((match = regex.exec(content)) !== null) {
        const id = match[1];
        // Accept alphanumeric module IDs (modern webpack often uses hashed IDs like "O8uH")
        modules[id] = {
            start: match.index,
            line: 1 // Regex doesn't track lines well, assuming minified
        };
    }
    return modules;
}

function indexModules(filePath) {
    const result = parseFile(filePath);
    if (!result) {
        // Try regex fallback
        try {
            const content = fs.readFileSync(filePath, 'utf8');
            return indexModulesRegex(content);
        } catch(e) {
            return {};
        }
    }

    const { ast } = result;
    const modules = {};

    /**
     * Webpack JSONP chunks sometimes encode the module table as an ArrayExpression:
     *   (self["webpackJsonpNAME"]=self["webpackJsonpNAME"]||[]).push([[chunkId],[function(...) {...}, ...], ...])
     *
     * In this format, module IDs are the array indices (0..N-1).
     *
     * Our original indexer only handled the ObjectExpression form:
     *   { 123: function(...) {...}, ... }
     *
     * We support both, conservatively, by recognizing the `push([[chunkIds], <modules>, ...])` shape.
     */
    function indexWebpackJsonpArrayModules(callNode) {
        if (!callNode || callNode.type !== 'CallExpression') return;
        const callee = callNode.callee;
        if (!callee || callee.type !== 'MemberExpression') return;

        // Must be a `.push(...)` call
        let propName = null;
        if (callee.property) {
            if (!callee.computed && callee.property.type === 'Identifier') propName = callee.property.name;
            else if (callee.computed && callee.property.type === 'Literal') propName = String(callee.property.value);
        }
        if (propName !== 'push') return;

        // Webpack JSONP push usually passes a single ArrayExpression argument.
        if (!callNode.arguments || callNode.arguments.length !== 1) return;
        const arg0 = callNode.arguments[0];
        if (!arg0 || arg0.type !== 'ArrayExpression') return;
        if (!arg0.elements || arg0.elements.length < 2) return;

        const chunkIds = arg0.elements[0];
        const modTable = arg0.elements[1];

        // Shape guard: first element should be an array of numeric chunk ids (or null placeholders)
        if (!chunkIds || chunkIds.type !== 'ArrayExpression') return;
        const chunkIdEls = chunkIds.elements || [];
        const chunkIdLooksValid = chunkIdEls.some(el => el && el.type === 'Literal' && typeof el.value === 'number');
        if (!chunkIdLooksValid) return;

        // Second element: array module table
        if (!modTable || modTable.type !== 'ArrayExpression') return;

        const els = modTable.elements || [];
        for (let i = 0; i < els.length; i++) {
            const el = els[i];
            if (!el) continue;
            if (el.type === 'FunctionExpression' || el.type === 'ArrowFunctionExpression') {
                // Heuristic: Webpack module factories usually have 2 or 3 params (module, exports, require).
                if (el.params && el.params.length >= 2) {
                    const moduleId = String(i);
                    // Don't overwrite an existing entry for the same ID from ObjectExpression indexing.
                    if (!modules[moduleId]) {
                        modules[moduleId] = {
                            start: el.start,
                            end: el.end,
                            line: el.loc ? el.loc.start.line : 1
                        };
                    }
                }
            }
        }
    }

    // Pass 1: Index Webpack JSONP array-module chunks (if present).
    walk.simple(ast, {
        CallExpression(node) {
            indexWebpackJsonpArrayModules(node);
        }
    });

    walk.simple(ast, {
        Property(node) {
            // Look for keys that are Numbers or String-Numbers
            let moduleId = null;
            if (node.key.type === 'Literal') moduleId = node.key.value;
            else if (node.key.type === 'Identifier') moduleId = node.key.name; // Less common for IDs but possible
            
            // Force string conversion for consistency
            if (moduleId !== null) moduleId = String(moduleId);

            // Accept alphanumeric module IDs (webpack can emit hashed IDs like "O8uH")
            if (moduleId === null) return;
            if (typeof moduleId !== 'string' || moduleId.length === 0) return;
            // Avoid obviously non-module keys
            if (!/^[A-Za-z0-9_$]+$/.test(moduleId)) return;


            // Value must be a function
            const val = node.value;
            if (val.type === 'FunctionExpression' || val.type === 'ArrowFunctionExpression') {
                // Heuristic: Webpack modules usually have 2 or 3 params (module, exports, require)
                if (val.params.length >= 2) {
                    modules[moduleId] = {
                        start: val.start,
                        end: val.end,
                        line: node.loc.start.line
                    };
                }
            }
        }
    });

    return modules;
}

function lineAtIndex(content, idx) {
    // Efficient-ish line counter for large content.
    // (We keep it simple; most minified bundles are line 1 anyway.)
    if (idx <= 0) return 1;
    let line = 1;
    // Count newlines in chunks to avoid huge temporary strings.
    const step = 1024 * 64;
    const end = Math.min(idx, content.length);
    for (let i = 0; i < end; i += step) {
        const chunk = content.slice(i, Math.min(end, i + step));
        for (let j = 0; j < chunk.length; j++) {
            if (chunk.charCodeAt(j) === 10) line++; // '\n'
        }
    }
    return line;
}

function identifierAtOffsetRegex(content, targetIndex) {
    // Extract a JS identifier at/near the cursor using purely textual rules.
    // This is used when AST parsing fails (file too large / syntax edge cases).
    if (typeof targetIndex !== 'number' || targetIndex < 0 || targetIndex > content.length) return null;
    const isIdentChar = (ch) => /[A-Za-z0-9_$]/.test(ch);

    let i = targetIndex;
    // If cursor is on non-ident char, nudge left then right a bit.
    if (i >= content.length) i = content.length - 1;

    // Search a small radius for an identifier character.
    const radius = 80;
    let found = -1;
    for (let d = 0; d <= radius; d++) {
        const left = i - d;
        const right = i + d;
        if (left >= 0 && isIdentChar(content[left])) { found = left; break; }
        if (right < content.length && isIdentChar(content[right])) { found = right; break; }
    }
    if (found === -1) return null;

    let start = found;
    let end = found + 1;
    while (start > 0 && isIdentChar(content[start - 1])) start--;
    while (end < content.length && isIdentChar(content[end])) end++;

    const name = content.slice(start, end);
    if (!name || !/^[A-Za-z_$]/.test(name)) return null;
    return { name, start, end };
}

function findDefinitionRegex(content, name, beforeIndex) {
    // Try to locate a likely definition *before* beforeIndex.
    // We search backwards in expanding windows to avoid scanning the entire file repeatedly.
    const patterns = [
        // function foo(...)
        { type: 'Function', re: new RegExp(`\\bfunction\\s+${name}\\b`) },
        // class Foo ...
        { type: 'Class', re: new RegExp(`\\bclass\\s+${name}\\b`) },
        // var/let/const foo =
        { type: 'Variable', re: new RegExp(`\\b(?:var|let|const)\\s+${name}\\b`) },
        // foo = function(...) / foo = (...) => ...
        { type: 'Variable', re: new RegExp(`\\b${name}\\s*=\\s*(?:function\\b|\\([^)]*\\)\\s*=>|[A-Za-z0-9_$]+\\s*=>)`) },
    ];

    let windowSize = 1024 * 1024 * 2; // 2MB
    let start = Math.max(0, beforeIndex - windowSize);
    let lastFound = null;

    while (true) {
        const slice = content.slice(start, beforeIndex);
        for (const p of patterns) {
            p.re.lastIndex = 0;
            let m;
            while ((m = p.re.exec(slice)) !== null) {
                const absIndex = start + m.index;
                if (!lastFound || absIndex > lastFound.defStart) {
                    lastFound = { type: p.type, defStart: absIndex };
                }
            }
        }
        if (start === 0) break;
        if (lastFound) break; // Prefer nearest definition (good enough) without scanning whole file.
        windowSize *= 2;
        start = Math.max(0, beforeIndex - windowSize);
    }

    if (!lastFound) return null;

    // Produce a small preview range.
    const previewEnd = Math.min(content.length, lastFound.defStart + 250);
    const preview = content.slice(lastFound.defStart, previewEnd);

    return {
        type: lastFound.type,
        defStart: lastFound.defStart,
        defEnd: previewEnd,
        line: lineAtIndex(content, lastFound.defStart),
        initCode: preview
    };
}

function detectImportIdFromInitRegex(content, name, defStart, defEnd) {
    // Best-effort: detect patterns like `var x=n(123)` or `const x=__webpack_require__(456)`
    // near the definition preview.
    const slice = content.slice(defStart, defEnd);
    const re = new RegExp(`\\b${name}\\b\\s*=\\s*(?:__webpack_require__|[A-Za-z_$][A-Za-z0-9_$]{0,2})\\s*\\(\\s*(\\d+)\\s*\\)`);
    const m = re.exec(slice);
    if (!m) return null;
    return parseInt(m[1], 10);
}

/**
 * Helper: Find the Identifier node at a given character offset.
 * We prefer walk.full over walk.simple because minified/bundled AST shapes
 * can cause acorn-walk's simple walker to skip some binding identifiers.
 */
function findIdentifierAtOffset(ast, targetIndex) {
    let targetNode = null;
    walk.full(ast, (node) => {
        if (!node || typeof node !== 'object') return;
        if (node.type === 'Identifier') {
            // acorn node.end is exclusive
            if (targetIndex >= node.start && targetIndex < node.end) {
                targetNode = node;
            }
        }
    });
    return targetNode;
}

function detectImportIdFromCallExpression(callExpr) {
    // Detect Webpack-like require forms:
    // - n(123) in minified bundles
    // - __webpack_require__(123) in modern webpack/Next.js bundles
    if (!callExpr || callExpr.type !== 'CallExpression') return null;
    if (!callExpr.arguments || callExpr.arguments.length !== 1) return null;
    const arg0 = callExpr.arguments[0];
    if (!arg0 || arg0.type !== 'Literal') return null;
    const callee = callExpr.callee;
    if (!callee) return null;
    if (callee.type === 'Identifier') {
        const name = callee.name || '';
        if (name.length <= 2 || name === '__webpack_require__') {
            return arg0.value;
        }
    }
    return null;
}

/**
 * Traces a variable from a specific usage point to its definition.
 */
function traceDefinition(filePath, targetIndex, symbolHint) {
    const result = parseFile(filePath);
    if (!result) {
        // Regex fallback mode: works for very large bundles / parse edge cases,
        // but is necessarily less accurate than AST scope tracing.
        try {
            const content = fs.readFileSync(filePath, 'utf8');
            
            // Fix drift using symbolHint
            if (symbolHint) {
                const range = 50000; // ample range for minified drift
                const start = Math.max(0, targetIndex - range);
                const end = Math.min(content.length, targetIndex + range);
                const slice = content.slice(start, end);
                
                // Find nearest occurrence
                let bestIdx = -1;
                let minDist = Infinity;
                let pos = 0;
                while (true) {
                    const idx = slice.indexOf(symbolHint, pos);
                    if (idx === -1) break;
                    
                    // Verify it's a whole word match?
                    // For minified code, maybe not safe to assume word boundaries.
                    // But for `saveAppointment`, it is safe.
                    const absIdx = start + idx;
                    const dist = Math.abs(absIdx - targetIndex);
                    if (dist < minDist) {
                        minDist = dist;
                        bestIdx = absIdx;
                    }
                    pos = idx + 1;
                }
                
                if (bestIdx !== -1) {
                    targetIndex = bestIdx;
                }
            }

            const ident = identifierAtOffsetRegex(content, targetIndex);
            if (!ident) return { error: `No identifier found at index ${targetIndex}` };

            const def = findDefinitionRegex(content, ident.name, ident.start);
            if (!def) return { type: "Global/Implicit", name: ident.name };

            const importId = detectImportIdFromInitRegex(content, ident.name, def.defStart, def.defEnd);
            return {
                type: def.type,
                name: ident.name,
                line: def.line,
                defStart: def.defStart,
                defEnd: def.defEnd,
                importId,
                initCode: def.initCode
            };
        } catch (e) {
            return { error: "Parse failed" };
        }
    }
    const { ast, content } = result;

    // Fix drift using symbolHint (AST mode)
    if (symbolHint) {
        const range = 50000;
        const start = Math.max(0, targetIndex - range);
        const end = Math.min(content.length, targetIndex + range);
        const slice = content.slice(start, end);
        
        let bestIdx = -1;
        let minDist = Infinity;
        let pos = 0;
        while (true) {
            const idx = slice.indexOf(symbolHint, pos);
            if (idx === -1) break;
            const absIdx = start + idx;
            const dist = Math.abs(absIdx - targetIndex);
            if (dist < minDist) {
                minDist = dist;
                bestIdx = absIdx;
            }
            pos = idx + 1;
        }
        
        if (bestIdx !== -1) {
            targetIndex = bestIdx;
        }
    }

    // Align targetIndex to an identifier start when possible.
    // This helps when the cursor is at token boundaries in minified code.
    // Avoid aligning into string-literal contents (e.g. `"createClientFlyout"`).
    let rid = identifierAtOffsetRegex(content, targetIndex);
    
    // Fix: If we landed on a declaration keyword (async, function, etc.), jump to the next identifier.
    // This fixes issues where the offset points to "async saveAppointment" instead of "saveAppointment".
    const defKeywords = new Set(['async', 'function', 'class', 'const', 'let', 'var', 'static', 'get', 'set']);
    if (rid && defKeywords.has(rid.name)) {
        let nextIdx = rid.end;
        // Skip whitespace
        while (nextIdx < content.length && /\s/.test(content[nextIdx])) nextIdx++;
        const nextRid = identifierAtOffsetRegex(content, nextIdx);
        if (nextRid) {
            rid = nextRid;
            targetIndex = nextRid.start;
        }
    }

    if (rid && typeof rid.start === 'number') {
        const prev = rid.start > 0 ? content[rid.start - 1] : '';
        if (prev !== '"' && prev !== "'") {
            targetIndex = rid.start;
        }
    }

    // Helper: Add parent pointers
    walk.full(ast, (node, state, type) => {
        for (const key in node) {
            const val = node[key];
            if (val && typeof val === 'object') {
                if (Array.isArray(val)) {
                    val.forEach(child => { if (child && typeof child === 'object') child._parent = node; });
                } else if (val.type) {
                    val._parent = node;
                }
            }
        }
    });

    // 1. Find the node at targetIndex
    // NOTE: acorn-walk's base walker can miss some Identifier positions in bundled/minified code
    // (notably binding identifiers like `const qb=...` / `var Gp=...`), depending on node types present.
    // We use walk.full to ensure we see *all* nodes.
    let targetNode = null;
    let propertyKeyNode = null;  // Track if we hit a property key
    walk.full(ast, (node) => {
        if (!node || typeof node !== 'object') return;

        if (node.type === 'Identifier') {
            if (targetIndex >= node.start && targetIndex < node.end) {
                targetNode = node;
            }
        } else if (node.type === 'Property') {
            // Check if targetIndex is within the property KEY (not value)
            if (node.key) {
                if (targetIndex >= node.key.start && targetIndex < node.key.end) {
                    propertyKeyNode = node;
                }
            }
        } else if (node.type === 'MethodDefinition') {
            // Class/object method definition key
            if (node.key && node.key.type === 'Identifier') {
                if (targetIndex >= node.key.start && targetIndex < node.key.end) {
                    // Treat like a definition site
                    targetNode = node.key;
                }
            }
        } else if (node.type === 'PropertyDefinition') {
            // Class field definition key
            if (node.key && node.key.type === 'Identifier') {
                if (targetIndex >= node.key.start && targetIndex < node.key.end) {
                    targetNode = node.key;
                }
            }
        } else if (node.type === 'MemberExpression') {
            if (targetIndex >= node.start && targetIndex < node.end) {
                // If we hit a MemberExpression (like LP.LoanContext), we prefer the specific PROPERTY or OBJECT identifier if possible
                // But if we missed the identifier, taking the whole expression is a decent fallback
                if (!targetNode) targetNode = node;
            }
        }
    });

    // If we found a property key, return info about it
    if (propertyKeyNode && !targetNode) {
        const keyName = propertyKeyNode.key.name || (propertyKeyNode.key.type === 'Literal' ? propertyKeyNode.key.value : null);
        if (keyName) {
            const valueType = propertyKeyNode.value.type;
            let valuePreview = '';
            
            if (valueType === 'FunctionExpression' || valueType === 'ArrowFunctionExpression') {
                valuePreview = 'function';
            } else {
                valuePreview = content.substring(propertyKeyNode.value.start, Math.min(propertyKeyNode.value.end, propertyKeyNode.value.start + 50));
            }
            
            return {
                type: "PropertyKey",
                name: keyName,
                line: propertyKeyNode.loc ? propertyKeyNode.loc.start.line : null,
                defStart: propertyKeyNode.start,
                defEnd: propertyKeyNode.end,
                valueType: valueType,
                valuePreview: valuePreview
            };
        }
    }

    if (!targetNode) {
        // Fallback: if we found a property key but failed to match an identifier, assume it's a literal key
        if (propertyKeyNode) {
             const keyName = propertyKeyNode.key.name || (propertyKeyNode.key.type === 'Literal' ? propertyKeyNode.key.value : null);
             if (keyName) {
                return {
                    type: "PropertyKey",
                    name: keyName,
                    line: propertyKeyNode.loc ? propertyKeyNode.loc.start.line : null,
                    defStart: propertyKeyNode.start,
                    defEnd: propertyKeyNode.end,
                    valueType: propertyKeyNode.value.type,
                    valuePreview: content.substring(propertyKeyNode.value.start, Math.min(propertyKeyNode.value.end, propertyKeyNode.value.start + 50))
                };
             }
        }
        
        // Final fallback: try to extract a string literal if the cursor is on one
        if (targetIndex >= 0 && targetIndex < content.length) {
             const ident = identifierAtOffsetRegex(content, targetIndex);
             // If we're inside a string literal, we might be looking at a key like "value":"AddUserDashboard"
             // Acorn walk might not visit the *value* node if we aren't careful, or we just missed it.
             // But if we found an "ident" via regex that matches the text, we can return a dummy node.
             if (ident) {
                 return {
                     type: "LiteralIdentifier", 
                     name: ident.name,
                     line: lineAtIndex(content, ident.start),
                     defStart: ident.start,
                     defEnd: ident.end
                 };
             }
        }

        return { error: `No identifier found at index ${targetIndex}` };
    }

    // If the cursor is on the *definition* identifier, return it directly.
    // This is common when jumping from search results to `var x=...` / `const x=...`.
    if (targetNode.type === 'Identifier' && targetNode._parent) {
        const p = targetNode._parent;
        // class Foo { bar() {} }  -> MethodDefinition key
        if (p.type === 'MethodDefinition' && p.key === targetNode) {
            return {
                type: "MethodDefinition",
                name: targetNode.name,
                line: p.loc ? p.loc.start.line : null,
                defStart: p.start,
                defEnd: p.end,
                initCode: content.substring(p.start, p.end)
            };
        }
        // class Foo { bar = () => {} } -> PropertyDefinition key
        if (p.type === 'PropertyDefinition' && p.key === targetNode) {
            const importId = detectImportIdFromCallExpression(p.value);
            return {
                type: "PropertyDefinition",
                name: targetNode.name,
                line: p.loc ? p.loc.start.line : null,
                defStart: p.start,
                defEnd: p.end,
                importId,
                initCode: content.substring(p.start, p.end)
            };
        }
        // `var x = <init>`
        if (p.type === 'VariableDeclarator' && p.id === targetNode) {
            const importId = detectImportIdFromCallExpression(p.init);
            return {
                type: "Variable",
                name: targetNode.name,
                line: p.loc ? p.loc.start.line : null,
                defStart: p.start,
                defEnd: p.end,
                importId,
                initCode: content.substring(p.start, p.end)
            };
        }
        // `function foo(){}` / `const foo = function foo(){}` / named function expressions
        if ((p.type === 'FunctionDeclaration' || p.type === 'FunctionExpression') && p.id === targetNode) {
            return {
                type: "Function",
                name: targetNode.name,
                line: p.loc ? p.loc.start.line : null,
                defStart: p.start,
                defEnd: p.end
            };
        }
    }

    // 2. Walk up scopes to find definition
    let currentNode = targetNode;
    // Handle MemberExpressions (LP.LoanContext) by taking the object (LP).
    // If the MemberExpression object is not an Identifier (e.g. `Object.keys(x).every(...)`),
    // there isn't a useful local definition to jump to (an editor would usually jump to lib typings).
    // In that case, return a stable non-error payload.
    let variableName = null;
    if (targetNode.type === 'MemberExpression') {
        if (targetNode.object && targetNode.object.type === 'Identifier') {
            variableName = targetNode.object.name;
        } else if (targetNode.property && targetNode.property.type === 'Identifier' && !targetNode.computed) {
            return {
                type: "MemberProperty",
                name: targetNode.property.name,
                line: targetNode.loc ? targetNode.loc.start.line : null,
                defStart: targetNode.start,
                defEnd: targetNode.end
            };
        } else {
            return { type: "Global/Implicit", name: null };
        }
    } else {
        variableName = targetNode.name;
    }

    if (!variableName) return { type: "Global/Implicit", name: null };
    
    while (currentNode) {
        const parent = currentNode._parent;
        if (!parent) break;

        // Check Params
        if (['FunctionDeclaration', 'FunctionExpression', 'ArrowFunctionExpression'].includes(parent.type)) {
            const param = parent.params.find(p => p.name === variableName);
            if (param) {
                return {
                    type: "Parameter",
                    name: variableName,
                    line: param.loc.start.line,
                    defStart: param.start,
                    defEnd: param.end
                };
            }
        }

        // Check Variable Declarations in Blocks
        if (parent.body && Array.isArray(parent.body)) {
            for (const stmt of parent.body) {
                if (stmt.type === 'VariableDeclaration') {
                    for (const decl of stmt.declarations) {
                        if (decl.id.type === 'Identifier' && decl.id.name === variableName && decl.start < targetNode.start) {
                            // Check for Webpack Import: z = n(123)
                            const importId = detectImportIdFromCallExpression(decl.init);

                            return {
                                type: "Variable",
                                name: variableName,
                                line: decl.loc.start.line,
                                defStart: decl.start,
                                defEnd: decl.end,
                                importId: importId, // Special field for Webpack
                                initCode: content.substring(decl.start, decl.end)
                            };
                        }
                    }
                } else if (stmt.type === 'ImportDeclaration') {
                    // Check ES6 Imports
                    if (stmt.specifiers) {
                        for (const spec of stmt.specifiers) {
                            if (spec.local.name === variableName) {
                                return {
                                    type: "Import",
                                    name: variableName,
                                    line: spec.loc.start.line,
                                    defStart: spec.start,
                                    defEnd: spec.end,
                                    source: stmt.source.value,
                                    importedName: spec.type === 'ImportDefaultSpecifier' ? 'default' : (spec.imported ? spec.imported.name : 'namespace'),
                                    initCode: content.substring(stmt.start, stmt.end)
                                };
                            }
                        }
                    }
                }
            }
        }
        currentNode = parent;
    }

    return { type: "Global/Implicit", name: variableName };
}

/**
 * Fingerprint Variable: Scans for all property accesses on a given variable name.
 */
function fingerprintVariable(filePath, targetIndex) {
    const result = parseFile(filePath);
    if (!result) return { error: "Parse failed" };
    const { ast } = result;

    walk.full(ast, (node) => {
        for (const key in node) {
            const val = node[key];
            if (val && typeof val === 'object') {
                if (Array.isArray(val)) {
                    val.forEach(child => { if (child && typeof child === 'object') child._parent = node; });
                } else if (val.type) {
                    val._parent = node;
                }
            }
        }
    });

    const targetNode = findIdentifierAtOffset(ast, targetIndex);

    if (!targetNode) return { error: `No identifier found at index ${targetIndex}` };
    const variableName = targetNode.name;

    // Find scope
    let scopeNode = null;
    let curr = targetNode;
    while (curr) {
        if (['FunctionDeclaration', 'FunctionExpression', 'ArrowFunctionExpression', 'Program'].includes(curr.type)) {
            scopeNode = curr;
            break;
        }
        curr = curr._parent;
    }
    if (!scopeNode) scopeNode = ast;

    const props = new Set();
    const calls = new Set();
    const assignments = new Set();

    walk.simple(scopeNode, {
        MemberExpression(node) {
            if (node.object.type === 'Identifier' && node.object.name === variableName) {
                if (node.property.type === 'Identifier' && !node.computed) {
                    props.add(node.property.name);
                    if (node._parent && node._parent.type === 'CallExpression' && node._parent.callee === node) {
                        calls.add(node.property.name);
                    }
                    if (node._parent && node._parent.type === 'AssignmentExpression' && node._parent.left === node) {
                        assignments.add(node.property.name);
                    }
                }
            }
        }
    });

    return {
        variable: variableName,
        properties: Array.from(props),
        calls: Array.from(calls),
        assignments: Array.from(assignments)
    };
}

/**
 * Find References: Finds all usages of a variable in its scope.
 */
function findReferences(filePath, targetIndex) {
    const result = parseFile(filePath);
    if (!result) return { error: "Parse failed" };
    const { ast, content } = result;

    walk.full(ast, (node) => {
        for (const key in node) {
            const val = node[key];
            if (val && typeof val === 'object') {
                if (Array.isArray(val)) {
                    val.forEach(child => { if (child && typeof child === 'object') child._parent = node; });
                } else if (val.type) {
                    val._parent = node;
                }
            }
        }
    });

    const targetNode = findIdentifierAtOffset(ast, targetIndex);

    if (!targetNode) return { error: `No identifier found at index ${targetIndex}` };
    const variableName = targetNode.name;

    let scopeNode = null;
    let curr = targetNode;
    while (curr) {
        if (['FunctionDeclaration', 'FunctionExpression', 'ArrowFunctionExpression', 'Program'].includes(curr.type)) {
            scopeNode = curr;
            break;
        }
        curr = curr._parent;
    }
    if (!scopeNode) scopeNode = ast;

    const refs = [];
    walk.simple(scopeNode, {
        Identifier(node) {
            if (node.name === variableName) {
                if (node._parent.type === 'Property' && node._parent.key === node && !node._parent.computed) return;
                if (node._parent.type === 'MemberExpression' && node._parent.property === node && !node._parent.computed) return;
                
                refs.push({
                    start: node.start,
                    end: node.end,
                    line: node.loc.start.line,
                    preview: content.substring(Math.max(0, node.start - 30), Math.min(content.length, node.end + 30)).replace(/\n/g, ' ')
                });
            }
        }
    });

    return { variable: variableName, references: refs };
}

/**
 * Extract Strings: Extracts string literals grouped by scope.
 */
function extractStrings(filePath, minLength = 5) {
    const result = parseFile(filePath);
    if (!result) return { error: "Parse failed" };
    const { ast } = result;

    const stringsByScope = {}; 

    function visit(node, scopeName) {
        if (!node) return;
        
        let nextScope = scopeName;
        if (['FunctionDeclaration', 'FunctionExpression', 'ArrowFunctionExpression'].includes(node.type)) {
            const name = node.id ? node.id.name : 'anonymous';
            const line = node.loc ? node.loc.start.line : '?';
            nextScope = `Function '${name}' (Line ${line})`;
        }

        if (node.type === 'Literal' && typeof node.value === 'string') {
            if (node.value.length >= minLength) {
                if (!stringsByScope[nextScope]) stringsByScope[nextScope] = [];
                stringsByScope[nextScope].push(node.value);
            }
        }

        for (const key in node) {
            const val = node[key];
            if (key === 'loc' || key === 'start' || key === 'end' || key === '_parent') continue;
            if (val && typeof val === 'object') {
                if (Array.isArray(val)) {
                    val.forEach(child => visit(child, nextScope));
                } else if (val.type) {
                    visit(val, nextScope);
                }
            }
        }
    }

    visit(ast, "Global");
    return stringsByScope;
}

/**
 * Best Traceable Index:
 * Given an arbitrary byte offset, return a "best" Identifier start index suitable for `trace`,
 * plus alternate Identifier indices nearby (e.g. MemberExpression object vs property).
 */
function bestTraceableIndex(filePath, targetIndex) {
    const result = parseFile(filePath);
    if (!result) {
        // Regex fallback for huge bundles: pick an identifier near the cursor.
        try {
            const content = fs.readFileSync(filePath, 'utf8');
            const ident = identifierAtOffsetRegex(content, targetIndex);
            if (!ident) return { error: `No identifier found at index ${targetIndex}` };
            const ctxStart = Math.max(0, targetIndex - 80);
            const ctxEnd = Math.min(content.length, targetIndex + 120);
            return {
                file: filePath,
                offset: targetIndex,
                anchorType: "RegexFallback",
                best: {
                    index: ident.start,
                    name: ident.name,
                    nodeType: "Identifier",
                    role: "cursor.identifier",
                    range: [ident.start, ident.end],
                    line: lineAtIndex(content, ident.start)
                },
                alternates: [],
                context: content.substring(ctxStart, ctxEnd).replace(/\n/g, ' ')
            };
        } catch (e) {
            return { error: "Parse failed" };
        }
    }
    const { ast, content } = result;

    // Attach parent pointers.
    walk.full(ast, (node) => {
        for (const key in node) {
            const val = node[key];
            if (val && typeof val === 'object') {
                if (Array.isArray(val)) {
                    val.forEach(child => { if (child && typeof child === 'object') child._parent = node; });
                } else if (val.type) {
                    val._parent = node;
                }
            }
        }
    });

    // Gather all nodes containing the offset; pick the innermost by smallest span.
    const containing = [];
    walk.full(ast, (node) => {
        if (!node || typeof node !== 'object') return;
        if (typeof node.start !== 'number' || typeof node.end !== 'number') return;
        // acorn node.end is exclusive
        if (targetIndex >= node.start && targetIndex < node.end) {
            containing.push(node);
        }
    });

    if (containing.length === 0) {
        return { error: `No AST node found at index ${targetIndex}` };
    }

    containing.sort((a, b) => (a.end - a.start) - (b.end - b.start));
    const innermost = containing[0];

    // Pick an "anchor" node: prefer MemberExpression/CallExpression/VariableDeclarator/AssignmentExpression
    // when the cursor is inside those constructs.
    let anchor = innermost;
    let curr = innermost;
    while (curr) {
        if (['MemberExpression', 'CallExpression', 'VariableDeclarator', 'AssignmentExpression', 'Property', 'MethodDefinition', 'PropertyDefinition'].includes(curr.type)) {
            anchor = curr;
            break;
        }
        curr = curr._parent;
    }

    // Helper to build candidate objects.
    function candFromIdent(node, role) {
        return {
            index: node.start,
            name: node.name,
            nodeType: node.type,
            role,
            range: [node.start, node.end],
            line: node.loc ? node.loc.start.line : null
        };
    }

    // Collect candidates, with light structure-aware roles.
    const candidates = [];

    // Always include a regex-derived identifier near the cursor.
    // This is robust in minified code where AST ranges can be surprising.
    //
    // If the identifier is inside a string literal (e.g. `"createClientFlyout"`),
    // de-prioritize it: it's not a real symbol we can trace.
    const rid = identifierAtOffsetRegex(content, targetIndex);
    if (rid) {
        const prev = rid.start > 0 ? content[rid.start - 1] : '';
        const role = (prev === '"' || prev === "'")
            ? "cursor.regex_identifier_in_string"
            : "cursor.regex_identifier";
        candidates.push({
            index: rid.start,
            name: rid.name,
            nodeType: "Identifier",
            role,
            range: [rid.start, rid.end],
            line: lineAtIndex(content, rid.start)
        });
    }

    function leftmostIdentifierInMemberExpr(mem) {
        // Walk down `obj.prop.prop2` to find the leftmost Identifier (`obj`), if any.
        let cur = mem;
        while (cur && cur.type === 'MemberExpression') {
            if (cur.object && cur.object.type === 'Identifier') return cur.object;
            cur = cur.object;
        }
        return null;
    }

    // 1) If there's an Identifier directly under the cursor, that's a top candidate.
    walk.full(anchor, (node) => {
        if (node && node.type === 'Identifier' && targetIndex >= node.start && targetIndex < node.end) {
            candidates.push(candFromIdent(node, 'cursor.identifier'));
        }
    });

    // 2) Special-case anchor types.
    if (anchor.type === 'MemberExpression') {
        if (anchor.object && anchor.object.type === 'Identifier') {
            candidates.push(candFromIdent(anchor.object, 'memberexpr.object'));
        } else if (anchor.object && anchor.object.type === 'MemberExpression') {
            const lm = leftmostIdentifierInMemberExpr(anchor.object);
            if (lm) candidates.push(candFromIdent(lm, 'memberexpr.object_chain'));
        }
        if (anchor.property && anchor.property.type === 'Identifier' && !anchor.computed) {
            candidates.push(candFromIdent(anchor.property, 'memberexpr.property'));
        }
    } else if (anchor.type === 'CallExpression') {
        const callee = anchor.callee;
        if (callee) {
            if (callee.type === 'Identifier') {
                candidates.push(candFromIdent(callee, 'call.callee'));
            } else if (callee.type === 'MemberExpression') {
                if (callee.object && callee.object.type === 'Identifier') {
                    candidates.push(candFromIdent(callee.object, 'call.callee.memberexpr.object'));
                }
                if (callee.property && callee.property.type === 'Identifier' && !callee.computed) {
                    candidates.push(candFromIdent(callee.property, 'call.callee.memberexpr.property'));
                }
            }
        }
    } else if (anchor.type === 'VariableDeclarator') {
        if (anchor.id && anchor.id.type === 'Identifier') {
            candidates.push(candFromIdent(anchor.id, 'vardecl.lhs'));
        }
        if (anchor.init) {
            walk.full(anchor.init, (node) => {
                if (node && node.type === 'Identifier') {
                    candidates.push(candFromIdent(node, 'vardecl.rhs.identifier'));
                }
            });
        }
    } else if (anchor.type === 'AssignmentExpression') {
        if (anchor.left && anchor.left.type === 'Identifier') {
            candidates.push(candFromIdent(anchor.left, 'assign.lhs'));
        } else if (anchor.left && anchor.left.type === 'MemberExpression') {
            if (anchor.left.object && anchor.left.object.type === 'Identifier') {
                candidates.push(candFromIdent(anchor.left.object, 'assign.lhs.memberexpr.object'));
            }
            if (anchor.left.property && anchor.left.property.type === 'Identifier' && !anchor.left.computed) {
                candidates.push(candFromIdent(anchor.left.property, 'assign.lhs.memberexpr.property'));
            }
        }
        if (anchor.right) {
            walk.full(anchor.right, (node) => {
                if (node && node.type === 'Identifier') {
                    candidates.push(candFromIdent(node, 'assign.rhs.identifier'));
                }
            });
        }
    } else if (anchor.type === 'Property') {
        if (anchor.key && anchor.key.type === 'Identifier' && !anchor.computed) {
            // This corresponds to traceDefinition's PropertyKey support.
            candidates.push({
                index: anchor.key.start,
                name: anchor.key.name,
                nodeType: anchor.key.type,
                role: 'property.key',
                range: [anchor.key.start, anchor.key.end],
                line: anchor.loc ? anchor.loc.start.line : null
            });
        }
        if (anchor.value) {
            walk.full(anchor.value, (node) => {
                if (node && node.type === 'Identifier') {
                    candidates.push(candFromIdent(node, 'property.value.identifier'));
                }
            });
        }
    } else if (anchor.type === 'MethodDefinition') {
        if (anchor.key && anchor.key.type === 'Identifier' && !anchor.computed) {
            candidates.push({
                index: anchor.key.start,
                name: anchor.key.name,
                nodeType: anchor.key.type,
                role: 'method.key',
                range: [anchor.key.start, anchor.key.end],
                line: anchor.loc ? anchor.loc.start.line : null
            });
        }
    } else if (anchor.type === 'PropertyDefinition') {
        if (anchor.key && anchor.key.type === 'Identifier' && !anchor.computed) {
            candidates.push({
                index: anchor.key.start,
                name: anchor.key.name,
                nodeType: anchor.key.type,
                role: 'classfield.key',
                range: [anchor.key.start, anchor.key.end],
                line: anchor.loc ? anchor.loc.start.line : null
            });
        }
    }

    // 2b) Add nearby identifiers in a small radius. This helps when the cursor is
    // near a boundary and the innermost AST node is not the intended target.
    const nearbyRadius = 80;
    walk.full(ast, (node) => {
        if (!node || node.type !== 'Identifier') return;
        const dist = Math.abs(node.start - targetIndex);
        if (dist <= nearbyRadius) {
            candidates.push({
                index: node.start,
                name: node.name,
                nodeType: node.type,
                role: 'nearby.identifier',
                range: [node.start, node.end],
                line: node.loc ? node.loc.start.line : null
            });
        }
    });

    // 3) Fallback: if still empty, climb parents and collect first few identifiers.
    if (candidates.length === 0) {
        let p = anchor._parent;
        while (p && candidates.length === 0) {
            walk.full(p, (node) => {
                if (node && node.type === 'Identifier') {
                    candidates.push(candFromIdent(node, 'parent.identifier'));
                }
            });
            p = p._parent;
        }
    }

    // Deduplicate by start index + name.
    const seen = new Set();
    const uniq = [];
    for (const c of candidates) {
        const k = `${c.index}:${c.name}:${c.role}`;
        if (seen.has(k)) continue;
        seen.add(k);
        uniq.push(c);
    }

    // Ranking: prefer identifier directly under cursor, then memberexpr object, then call callee, then vardecl lhs, then assign lhs.
    const roleRank = {
        'cursor.regex_identifier': 0,
        'cursor.regex_identifier_in_string': 50,
        'cursor.identifier': 1,
        'method.key': 2,
        'classfield.key': 3,
        'memberexpr.object': 3,
        'memberexpr.object_chain': 3,
        'call.callee': 4,
        'vardecl.lhs': 5,
        'assign.lhs': 6,
        'property.key': 7,
        'nearby.identifier': 8,
        'memberexpr.property': 9,
        'call.callee.memberexpr.object': 10,
        'call.callee.memberexpr.property': 11,
        'assign.lhs.memberexpr.object': 12,
        'assign.lhs.memberexpr.property': 13
    };

    uniq.sort((a, b) => {
        const ra = roleRank[a.role] ?? 100;
        const rb = roleRank[b.role] ?? 100;
        if (ra !== rb) return ra - rb;
        const da = Math.abs(a.index - targetIndex);
        const db = Math.abs(b.index - targetIndex);
        if (da !== db) return da - db;
        return a.index - b.index;
    });

    const best = uniq[0] || null;
    const alternates = uniq.slice(1);

    const ctxStart = Math.max(0, targetIndex - 80);
    const ctxEnd = Math.min(content.length, targetIndex + 120);
    const context = content.substring(ctxStart, ctxEnd).replace(/\n/g, ' ');

    return {
        file: filePath,
        offset: targetIndex,
        anchorType: anchor.type,
        best,
        alternates,
        context
    };
}

/**
 * Trace Variable Chain: Scope-limited AST-based analysis of a variable
 * Returns: definition and all writes (assignments) within the containing function scope
 * Optimized for reverse engineering - focuses on what matters: how is the value built?
 */
function traceVariableChain(filePath, targetIndex, symbolHint) {
    const result = parseFile(filePath);
    if (!result) {
        return { error: "Parse failed - file too large or syntax error" };
    }
    const { ast, content } = result;

    // Fix drift using symbolHint
    if (symbolHint) {
        const range = 50000;
        const start = Math.max(0, targetIndex - range);
        const end = Math.min(content.length, targetIndex + range);
        const slice = content.slice(start, end);
        
        let bestIdx = -1;
        let minDist = Infinity;
        let pos = 0;
        while (true) {
            const idx = slice.indexOf(symbolHint, pos);
            if (idx === -1) break;
            const absIdx = start + idx;
            const dist = Math.abs(absIdx - targetIndex);
            if (dist < minDist) {
                minDist = dist;
                bestIdx = absIdx;
            }
            pos = idx + 1;
        }
        if (bestIdx !== -1) {
            targetIndex = bestIdx;
        }
    }

    // Add parent pointers to all nodes
    walk.full(ast, (node) => {
        for (const key in node) {
            const val = node[key];
            if (val && typeof val === 'object') {
                if (Array.isArray(val)) {
                    val.forEach(child => { if (child && typeof child === 'object') child._parent = node; });
                } else if (val.type) {
                    val._parent = node;
                }
            }
        }
    });

    // Find the identifier at the target index
    let targetNode = null;
    walk.full(ast, (node) => {
        if (node && node.type === 'Identifier') {
            if (targetIndex >= node.start && targetIndex < node.end) {
                targetNode = node;
            }
        }
    });

    // Get variable name - either from AST node or from symbolHint
    let variableName = null;
    
    if (targetNode) {
        variableName = targetNode.name;
    } else if (symbolHint) {
        // Use the symbol hint directly
        variableName = symbolHint;
    } else {
        // Try regex fallback
        const ident = identifierAtOffsetRegex(content, targetIndex);
        if (!ident) return { error: `No identifier found at index ${targetIndex}` };
        variableName = ident.name;
    }
    
    // Find the containing function scope (not global!)
    // Two approaches: walk parent chain from targetNode, OR find smallest function containing the offset
    let scopeNode = ast;
    
    // Approach 1: Walk parent chain if we have a targetNode
    if (targetNode) {
        let curr = targetNode;
        while (curr) {
            if (['FunctionDeclaration', 'FunctionExpression', 'ArrowFunctionExpression'].includes(curr.type)) {
                scopeNode = curr;
                break;
            }
            curr = curr._parent;
        }
    }
    
    // Approach 2: If still global, find the smallest function that contains targetIndex
    if (scopeNode === ast) {
        let smallestFunction = null;
        let smallestSize = Infinity;
        
        walk.full(ast, (node) => {
            if (!node) return;
            if (['FunctionDeclaration', 'FunctionExpression', 'ArrowFunctionExpression'].includes(node.type)) {
                if (targetIndex >= node.start && targetIndex < node.end) {
                    const size = node.end - node.start;
                    if (size < smallestSize) {
                        smallestSize = size;
                        smallestFunction = node;
                    }
                }
            }
        });
        
        if (smallestFunction) {
            scopeNode = smallestFunction;
        }
    }

    // Result structure - focused on writes only
    const traceResult = {
        variable: variableName,
        scope: scopeNode === ast ? 'global' : {
            type: scopeNode.type,
            start: scopeNode.start,
            end: scopeNode.end,
            line: scopeNode.loc ? scopeNode.loc.start.line : null
        },
        definition: null,
        writes: [],
        passed_to: []  // Where this variable is passed as an argument (the "exit point")
    };

    // Helper to create location info
    function locInfo(node, type, extra = {}) {
        const codeStart = node.start;
        const codeEnd = Math.min(node.end, node.start + 150);
        return {
            type,
            offset: node.start,
            line: node.loc ? node.loc.start.line : lineAtIndex(content, node.start),
            code: content.substring(codeStart, codeEnd).replace(/\n/g, ' '),
            ...extra
        };
    }

    // Walk the entire scope to find all references
    walk.full(scopeNode, (node) => {
        if (!node || node.type !== 'Identifier' || node.name !== variableName) return;

        const parent = node._parent;
        if (!parent) return;

        // Skip property keys (obj.prop where prop is not our variable reference)
        if (parent.type === 'MemberExpression' && parent.property === node && !parent.computed) {
            return;
        }
        // Skip object property keys
        if (parent.type === 'Property' && parent.key === node && !parent.computed) {
            // But if it's shorthand { variableName }, it IS a reference
            if (!parent.shorthand) return;
        }

        // Determine the role of this identifier
        
        // 1. Definition sites
        if (parent.type === 'VariableDeclarator' && parent.id === node) {
            const declNode = parent._parent; // VariableDeclaration
            const kind = declNode && declNode.kind ? declNode.kind : 'var';
            
            // Check if it's an import-like pattern: const x = require(...) or const x = n(123)
            let importInfo = null;
            if (parent.init) {
                const importId = detectImportIdFromCallExpression(parent.init);
                if (importId !== null) {
                    importInfo = { moduleId: importId };
                }
            }
            
            const info = locInfo(parent, 'definition', { 
                kind,
                hasInit: !!parent.init,
                importInfo
            });
            
            // Get the full initializer code if it exists
            if (parent.init) {
                info.initCode = content.substring(parent.init.start, parent.init.end);
                if (info.initCode.length > 2000) {
                    info.initCode = info.initCode.substring(0, 2000) + '...';
                }
            }
            
            traceResult.definition = info;
            return;
        }

        // Function declaration: function variableName() {}
        if (parent.type === 'FunctionDeclaration' && parent.id === node) {
            const info = locInfo(parent, 'function_definition', {
                params: parent.params.map(p => p.name || '?').join(', ')
            });
            info.fullCode = content.substring(parent.start, parent.end);
            if (info.fullCode.length > 5000) {
                info.fullCode = info.fullCode.substring(0, 5000) + '...';
            }
            traceResult.definition = info;
            traceResult.full_code = info.fullCode;
            return;
        }

        // Function parameter
        if (['FunctionDeclaration', 'FunctionExpression', 'ArrowFunctionExpression'].includes(parent.type)) {
            if (parent.params && parent.params.includes(node)) {
                traceResult.definition = locInfo(node, 'parameter', {
                    functionStart: parent.start
                });
                return;
            }
        }

        // Import specifier
        if (parent.type === 'ImportSpecifier' || parent.type === 'ImportDefaultSpecifier' || parent.type === 'ImportNamespaceSpecifier') {
            const importDecl = parent._parent;
            traceResult.definition = locInfo(parent, 'import', {
                source: importDecl && importDecl.source ? importDecl.source.value : '?',
                importedName: parent.imported ? parent.imported.name : 'default'
            });
            return;
        }

        // 2. Write sites (assignments)
        if (parent.type === 'AssignmentExpression' && parent.left === node) {
            const info = locInfo(parent, 'assignment', {
                operator: parent.operator
            });
            info.rightCode = content.substring(parent.right.start, Math.min(parent.right.end, parent.right.start + 200));
            traceResult.writes.push(info);
            return;
        }

        // Assignment to property: variableName.prop = value
        if (parent.type === 'MemberExpression' && parent.object === node) {
            const grandParent = parent._parent;
            if (grandParent && grandParent.type === 'AssignmentExpression' && grandParent.left === parent) {
                const propName = parent.property.name || parent.property.value || '?';
                const info = locInfo(grandParent, 'property_assignment', {
                    property: propName,
                    operator: grandParent.operator
                });
                info.rightCode = content.substring(grandParent.right.start, Math.min(grandParent.right.end, grandParent.right.start + 200));
                traceResult.writes.push(info);
                return;
            }
        }

        // Update expression: variableName++ or ++variableName
        if (parent.type === 'UpdateExpression' && parent.argument === node) {
            traceResult.writes.push(locInfo(parent, 'update', {
                operator: parent.operator,
                prefix: parent.prefix
            }));
            return;
        }

        // 3. Passed as argument to a function call (exit point)
        if (parent.type === 'CallExpression' && parent.arguments && parent.arguments.includes(node)) {
            // Find which argument position
            const argIndex = parent.arguments.indexOf(node);
            let calleeName = '?';
            if (parent.callee.type === 'Identifier') {
                calleeName = parent.callee.name;
            } else if (parent.callee.type === 'MemberExpression' && parent.callee.property) {
                calleeName = parent.callee.property.name || '?';
            }
            traceResult.passed_to.push(locInfo(parent, 'argument', {
                callee: calleeName,
                argIndex
            }));
            return;
        }

        // Skip reads - we only care about writes for reverse engineering
    });

    // Sort by offset (source order)
    const sortByOffset = (a, b) => a.offset - b.offset;
    traceResult.writes.sort(sortByOffset);
    traceResult.passed_to.sort(sortByOffset);

    // Add scope code preview
    if (scopeNode !== ast) {
        const scopeCode = content.substring(scopeNode.start, scopeNode.end);
        traceResult.scope_code = scopeCode.length > 3000 
            ? scopeCode.substring(0, 3000) + '...' 
            : scopeCode;
    }

    return traceResult;
}

// CLI
const [,, command, arg1, arg2, arg3] = process.argv;

if (command === 'index') {
    console.log(JSON.stringify(indexModules(arg1)));
} else if (command === 'trace') {
    console.log(JSON.stringify(traceDefinition(arg1, parseInt(arg2), arg3)));
} else if (command === 'trace_var') {
    console.log(JSON.stringify(traceVariableChain(arg1, parseInt(arg2), arg3)));
} else if (command === 'fingerprint') {
    console.log(JSON.stringify(fingerprintVariable(arg1, parseInt(arg2))));
} else if (command === 'refs') {
    console.log(JSON.stringify(findReferences(arg1, parseInt(arg2))));
} else if (command === 'literals') {
    console.log(JSON.stringify(extractStrings(arg1, parseInt(arg2) || 5)));
} else if (command === 'best_index') {
    console.log(JSON.stringify(bestTraceableIndex(arg1, parseInt(arg2))));
}
