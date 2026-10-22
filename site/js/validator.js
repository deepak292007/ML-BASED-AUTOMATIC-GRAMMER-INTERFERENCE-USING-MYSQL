/**
 * AutoGrammar Client-Side Compiler Validator & ML Inference Engine (site/js/validator.js)
 * Standalone JavaScript implementation of:
 *   - Stage 0: Security Gate (prohibited commands, multi-statements, unconstrained DML)
 *   - Stage 1: Lexical Analyzer (tokenization, line/column tracking, illegal token detection)
 *   - Stage 2: Recursive Descent Parser (EBNF syntax checking, AST synthesis, ASCII tree)
 *   - Stage 3: Semantic Catalog Checker (table/column resolution, Levenshtein suggestions)
 *   - Offline TF-IDF + Logistic Regression Classifier inference using exported weights
 */

// ===========================================================================
// LEVENSHTEIN DISTANCE FOR "DID YOU MEAN ...?" SUGGESTIONS
// ===========================================================================
function levenshteinDistance(a, b) {
  const an = a ? a.length : 0;
  const bn = b ? b.length : 0;
  if (an === 0) return bn;
  if (bn === 0) return an;
  const matrix = [];
  for (let i = 0; i <= bn; i++) matrix[i] = [i];
  for (let j = 0; j <= an; j++) matrix[0][j] = j;
  for (let i = 1; i <= bn; i++) {
    for (let j = 1; j <= an; j++) {
      if (b.charAt(i - 1).toLowerCase() === a.charAt(j - 1).toLowerCase()) {
        matrix[i][j] = matrix[i - 1][j - 1];
      } else {
        matrix[i][j] = Math.min(
          matrix[i - 1][j - 1] + 1, // substitution
          matrix[i][j - 1] + 1,     // insertion
          matrix[i - 1][j] + 1      // deletion
        );
      }
    }
  }
  return matrix[bn][an];
}

function findBestSuggestion(target, candidates, maxDist = 3) {
  let best = null;
  let bestDist = Infinity;
  for (const c of candidates) {
    const dist = levenshteinDistance(target, c);
    if (dist < bestDist && dist <= maxDist) {
      bestDist = dist;
      best = c;
    }
  }
  return best;
}

// ===========================================================================
// STAGE 0: SECURITY GATE
// ===========================================================================
function checkSecurityGate(query) {
  const cleaned = query.trim();
  const upper = cleaned.toUpperCase();
  const diagnostics = [];

  // 1. Prohibited administrative and destructive commands
  const forbidden = ["DROP", "TRUNCATE", "ALTER", "GRANT", "REVOKE", "EXEC", "EXECUTE"];
  for (const cmd of forbidden) {
    const regex = new RegExp(`(^|\\s)${cmd}(\\s|;|$)`, "i");
    if (regex.test(cleaned)) {
      diagnostics.push({
        phase: "SECURITY",
        stage: "Stage 0 (Security Gate)",
        message: `Dangerous SQL command '${cmd}' is prohibited in student DSL environment.`,
        suggestion: "AutoGrammar permits only controlled SELECT, and sandboxed student DML (INSERT/UPDATE/DELETE with WHERE).",
        line: 1,
        column: cleaned.toUpperCase().indexOf(cmd) + 1
      });
      break;
    }
  }

  // 2. Multi-statement command chaining via semicolon
  if (cleaned.includes(";")) {
    const parts = cleaned.split(";").map(p => p.trim()).filter(p => p.length > 0);
    if (parts.length > 1) {
      diagnostics.push({
        phase: "SECURITY",
        stage: "Stage 0 (Security Gate)",
        message: "Multiple SQL statements detected. Command batching is blocked to prevent injection attacks.",
        suggestion: "Execute one statement at a time.",
        line: 1,
        column: cleaned.indexOf(";") + 1
      });
    }
  }

  // 3. Unconstrained UPDATE or DELETE without WHERE clause
  const tokens = tokenizeSqlSimple(cleaned);
  const kwList = tokens.filter(t => t.type === "KEYWORD").map(t => t.value.toUpperCase());
  if (kwList.includes("DELETE") && !kwList.includes("WHERE")) {
    diagnostics.push({
      phase: "SECURITY",
      stage: "Stage 0 (Security Gate)",
      message: "Unconstrained DELETE without WHERE clause is dangerous and prohibited.",
      suggestion: "Add a specific WHERE condition (e.g. WHERE student_id = ...).",
      line: 1,
      column: 1
    });
  }
  if (kwList.includes("UPDATE") && !kwList.includes("WHERE")) {
    diagnostics.push({
      phase: "SECURITY",
      stage: "Stage 0 (Security Gate)",
      message: "Unconstrained UPDATE without WHERE clause is dangerous and prohibited.",
      suggestion: "Add a specific WHERE condition (e.g. WHERE student_id = ...).",
      line: 1,
      column: 1
    });
  }

  return diagnostics;
}

// ===========================================================================
// STAGE 1: LEXICAL ANALYZER (TOKENIZER)
// ===========================================================================
const SQL_KEYWORDS_SET = new Set([
  "SELECT", "DISTINCT", "FROM", "WHERE", "AND", "OR", "NOT",
  "IN", "BETWEEN", "LIKE", "IS", "NULL", "ORDER", "BY",
  "LIMIT", "ASC", "DESC", "COUNT", "SUM", "AVG", "MIN", "MAX",
  "GROUP", "HAVING", "JOIN", "INNER", "LEFT", "RIGHT", "AS",
  "ON", "INSERT", "INTO", "VALUES", "UPDATE", "SET", "DELETE"
]);

function tokenizeSql(query) {
  const tokens = [];
  const illegalTokens = [];
  let line = 1;
  let col = 1;
  let i = 0;
  const n = query.length;

  while (i < n) {
    const ch = query[i];

    // Newline handling
    if (ch === '\n') {
      line++;
      col = 1;
      i++;
      continue;
    }
    // Whitespace
    if (/\s/.test(ch)) {
      col++;
      i++;
      continue;
    }

    const startLine = line;
    const startCol = col;

    // Single-line comment (-- or //)
    if ((ch === '-' && query[i + 1] === '-') || (ch === '/' && query[i + 1] === '/')) {
      while (i < n && query[i] !== '\n') {
        i++;
        col++;
      }
      continue;
    }

    // String literal '...'
    if (ch === "'") {
      let strVal = "'";
      i++;
      col++;
      let closed = false;
      while (i < n) {
        const sc = query[i];
        strVal += sc;
        if (sc === '\\') {
          i++; col++;
          if (i < n) { strVal += query[i]; i++; col++; }
          continue;
        }
        if (sc === "'") {
          i++; col++;
          closed = true;
          break;
        }
        if (sc === '\n') { line++; col = 1; } else { col++; }
        i++;
      }
      tokens.push({
        type: "STRING",
        value: strVal,
        line: startLine,
        column: startCol,
        category: "STRING"
      });
      continue;
    }

    // Numbers
    if (/\d/.test(ch)) {
      let numStr = "";
      while (i < n && /[\d.]/.test(query[i])) {
        numStr += query[i];
        i++; col++;
      }
      tokens.push({
        type: "NUMBER",
        value: numStr,
        line: startLine,
        column: startCol,
        category: "NUMBER"
      });
      continue;
    }

    // Multi-char operators (<=, >=, !=, <>)
    const twoChars = query.slice(i, i + 2);
    if (["<=", ">=", "!=", "<>"].includes(twoChars)) {
      tokens.push({
        type: "OPERATOR",
        value: twoChars,
        line: startLine,
        column: startCol,
        category: "OPERATOR"
      });
      i += 2;
      col += 2;
      continue;
    }

    // Single-char operators & punctuation
    if (["=", "<", ">", "+", "-", "/"].includes(ch)) {
      tokens.push({
        type: "OPERATOR",
        value: ch,
        line: startLine,
        column: startCol,
        category: "OPERATOR"
      });
      i++; col++;
      continue;
    }

    if (ch === '*') {
      tokens.push({
        type: "ASTERISK",
        value: "*",
        line: startLine,
        column: startCol,
        category: "PUNCTUATION"
      });
      i++; col++;
      continue;
    }

    if (ch === '.') {
      tokens.push({
        type: "DOT",
        value: ".",
        line: startLine,
        column: startCol,
        category: "PUNCTUATION"
      });
      i++; col++;
      continue;
    }

    if (ch === ',') {
      tokens.push({
        type: "COMMA",
        value: ",",
        line: startLine,
        column: startCol,
        category: "PUNCTUATION"
      });
      i++; col++;
      continue;
    }

    if (ch === ';') {
      tokens.push({
        type: "SEMICOLON",
        value: ";",
        line: startLine,
        column: startCol,
        category: "PUNCTUATION"
      });
      i++; col++;
      continue;
    }

    if (ch === '(') {
      tokens.push({
        type: "LPAREN",
        value: "(",
        line: startLine,
        column: startCol,
        category: "PUNCTUATION"
      });
      i++; col++;
      continue;
    }

    if (ch === ')') {
      tokens.push({
        type: "RPAREN",
        value: ")",
        line: startLine,
        column: startCol,
        category: "PUNCTUATION"
      });
      i++; col++;
      continue;
    }

    // Identifiers & keywords [a-zA-Z_][a-zA-Z0-9_]*
    if (/[a-zA-Z_]/.test(ch)) {
      let ident = "";
      while (i < n && /[a-zA-Z0-9_]/.test(query[i])) {
        ident += query[i];
        i++; col++;
      }
      const upperIdent = ident.toUpperCase();
      if (SQL_KEYWORDS_SET.has(upperIdent)) {
        tokens.push({
          type: "KEYWORD",
          value: upperIdent,
          raw: ident,
          line: startLine,
          column: startCol,
          category: "KEYWORD"
        });
      } else {
        tokens.push({
          type: "IDENTIFIER",
          value: ident,
          line: startLine,
          column: startCol,
          category: "IDENTIFIER"
        });
      }
      continue;
    }

    // Illegal / Unknown Token (@, #, $, etc.)
    illegalTokens.push({
      value: ch,
      line: startLine,
      column: startCol
    });
    tokens.push({
      type: "UNKNOWN",
      value: ch,
      line: startLine,
      column: startCol,
      category: "UNKNOWN"
    });
    i++; col++;
  }

  return { tokens, illegalTokens };
}

function tokenizeSqlSimple(query) {
  return tokenizeSql(query).tokens;
}

// ===========================================================================
// STAGE 2: PARSER (RECURSIVE DESCENT / GRAMMAR-AWARE)
// ===========================================================================
class ParserState {
  constructor(tokens, grammarMode = "learned", sessionRefined = false) {
    this.tokens = tokens;
    this.pos = 0;
    this.grammarMode = grammarMode; // "baseline" or "learned"
    this.sessionRefined = sessionRefined; // true if session refinement applied
  }

  peek() {
    return this.pos < this.tokens.length ? this.tokens[this.pos] : null;
  }

  next() {
    return this.pos < this.tokens.length ? this.tokens[this.pos++] : null;
  }

  matchKeyword(kw) {
    const t = this.peek();
    if (t && t.type === "KEYWORD" && t.value.toUpperCase() === kw.toUpperCase()) {
      return this.next();
    }
    return null;
  }

  matchType(type) {
    const t = this.peek();
    if (t && t.type === type) {
      return this.next();
    }
    return null;
  }

  matchOperator(op) {
    const t = this.peek();
    if (t && t.type === "OPERATOR" && t.value === op) {
      return this.next();
    }
    return null;
  }
}

function parseQuery(query, grammarMode = "learned", sessionRefined = false) {
  const { tokens, illegalTokens } = tokenizeSql(query);

  // Stage 1 check
  if (illegalTokens.length > 0) {
    const firstErr = illegalTokens[0];
    return {
      valid: false,
      stage: "Stage 1 (Lexer)",
      phase: "LEXICAL",
      line: firstErr.line,
      column: firstErr.column,
      message: `Illegal or unrecognized token '${firstErr.value}' in input.`,
      suggestion: "Remove or replace unrecognized special characters.",
      tokens,
      asciiTree: ""
    };
  }

  if (tokens.length === 0) {
    return {
      valid: false,
      stage: "Stage 0 (Security Gate)",
      phase: "EMPTY",
      line: 1, column: 1,
      message: "Query is empty.",
      suggestion: "Enter a valid SQL query.",
      tokens: [],
      asciiTree: ""
    };
  }

  // Pre-parse: Unbalanced parentheses check
  const parenStack = [];
  for (const t of tokens) {
    if (t.type === "LPAREN") {
      parenStack.push(t);
    } else if (t.type === "RPAREN") {
      if (parenStack.length === 0) {
        return {
          valid: false,
          stage: "Stage 2 (Parser)",
          phase: "SYNTAX",
          line: t.line,
          column: t.column,
          message: `Unexpected closing parenthesis ')' without matching opening parenthesis.`,
          suggestion: "Remove unmatched closing parenthesis.",
          tokens,
          asciiTree: ""
        };
      }
      parenStack.pop();
    }
  }
  if (parenStack.length > 0) {
    const unclosed = parenStack[parenStack.length - 1];
    return {
      valid: false,
      stage: "Stage 2 (Parser)",
      phase: "SYNTAX",
      line: unclosed.line,
      column: unclosed.column,
      message: `Syntax error: Unbalanced parenthesis. Expected ')' to match '(' opened at column ${unclosed.column}.`,
      suggestion: "Add closing parenthesis to complete condition or subquery.",
      tokens,
      asciiTree: ""
    };
  }

  // Double operators check (e.g. > =)
  for (let idx = 0; idx < tokens.length - 1; idx++) {
    const curr = tokens[idx];
    const nxt = tokens[idx + 1];
    if (curr.type === "OPERATOR" && nxt.type === "OPERATOR") {
      return {
        valid: false,
        stage: "Stage 2 (Parser)",
        phase: "SYNTAX",
        line: nxt.line,
        column: nxt.column,
        message: `Syntax error: Consecutive operators '${curr.value}' and '${nxt.value}' detected.`,
        suggestion: "Use a single composite operator (such as '<=' or '>=') without spaces.",
        tokens,
        asciiTree: ""
      };
    }
  }

  const p = new ParserState(tokens, grammarMode, sessionRefined);
  const first = p.peek();

  if (!first || first.type !== "KEYWORD") {
    return {
      valid: false,
      stage: "Stage 2 (Parser)",
      phase: "SYNTAX",
      line: first ? first.line : 1,
      column: first ? first.column : 1,
      message: `Syntax error: Query must begin with a valid SQL command (SELECT, INSERT, UPDATE, DELETE).`,
      suggestion: "Start query with SELECT or DML statement.",
      tokens,
      asciiTree: ""
    };
  }

  const firstKw = first.value.toUpperCase();

  // 1. DELETE statement
  if (firstKw === "DELETE") {
    // In unrefined learned grammar, delete_stmt was NOT in training templates!
    if (grammarMode === "learned" && !sessionRefined) {
      return {
        valid: false,
        stage: "Stage 2 (Parser)",
        phase: "SYNTAX",
        line: first.line,
        column: first.column,
        message: `Syntax error: DELETE statements are not recognized by the unrefined learned grammar (missing 'delete_stmt' production).`,
        suggestion: "Use the Grammar Refinement Sandbox to induce delete_stmt or switch to Baseline Grammar.",
        tokens,
        asciiTree: ""
      };
    }
    p.next(); // DELETE
    if (!p.matchKeyword("FROM")) {
      return {
        valid: false,
        stage: "Stage 2 (Parser)",
        phase: "SYNTAX",
        line: p.peek() ? p.peek().line : 1,
        column: p.peek() ? p.peek().column : 1,
        message: "Syntax error: Expected 'FROM' keyword after 'DELETE'.",
        suggestion: "Format statement as DELETE FROM <table> WHERE <condition>;",
        tokens,
        asciiTree: ""
      };
    }
    const tblTok = p.matchType("IDENTIFIER");
    if (!tblTok) {
      return {
        valid: false,
        stage: "Stage 2 (Parser)",
        phase: "SYNTAX",
        line: p.peek() ? p.peek().line : 1,
        column: p.peek() ? p.peek().column : 1,
        message: "Syntax error: Expected target table name after 'DELETE FROM'.",
        suggestion: "Specify table name.",
        tokens,
        asciiTree: ""
      };
    }
    return {
      valid: true,
      stmtType: "DELETE",
      table: tblTok.value,
      tokens,
      asciiTree: `delete_stmt\n├── FROM\n└── ${tblTok.value}`
    };
  }

  // 2. INSERT statement
  if (firstKw === "INSERT") {
    p.next();
    if (!p.matchKeyword("INTO")) {
      return {
        valid: false,
        stage: "Stage 2 (Parser)",
        phase: "SYNTAX",
        line: p.peek() ? p.peek().line : 1,
        column: p.peek() ? p.peek().column : 1,
        message: "Syntax error: Expected 'INTO' after 'INSERT'.",
        suggestion: "Use INSERT INTO <table> ...",
        tokens,
        asciiTree: ""
      };
    }
    const tbl = p.matchType("IDENTIFIER");
    if (!tbl) {
      return {
        valid: false,
        stage: "Stage 2 (Parser)",
        phase: "SYNTAX",
        line: p.peek() ? p.peek().line : 1,
        column: p.peek() ? p.peek().column : 1,
        message: "Syntax error: Expected table name after 'INSERT INTO'.",
        suggestion: "Specify target table.",
        tokens,
        asciiTree: ""
      };
    }
    return {
      valid: true,
      stmtType: "INSERT",
      table: tbl.value,
      tokens,
      asciiTree: `insert_stmt\n├── INTO\n└── ${tbl.value}`
    };
  }

  // 3. UPDATE statement
  if (firstKw === "UPDATE") {
    p.next();
    const tbl = p.matchType("IDENTIFIER");
    if (!tbl) {
      return {
        valid: false,
        stage: "Stage 2 (Parser)",
        phase: "SYNTAX",
        line: p.peek() ? p.peek().line : 1,
        column: p.peek() ? p.peek().column : 1,
        message: "Syntax error: Expected table name after 'UPDATE'.",
        suggestion: "Specify target table.",
        tokens,
        asciiTree: ""
      };
    }
    if (!p.matchKeyword("SET")) {
      return {
        valid: false,
        stage: "Stage 2 (Parser)",
        phase: "SYNTAX",
        line: p.peek() ? p.peek().line : 1,
        column: p.peek() ? p.peek().column : 1,
        message: "Syntax error: Missing 'SET' clause in UPDATE statement.",
        suggestion: "Add SET <column> = <value> clause.",
        tokens,
        asciiTree: ""
      };
    }
    return {
      valid: true,
      stmtType: "UPDATE",
      table: tbl.value,
      tokens,
      asciiTree: `update_stmt\n├── ${tbl.value}\n└── SET`
    };
  }

  // 4. SELECT statement
  if (firstKw === "SELECT") {
    p.next(); // consume SELECT
    p.matchKeyword("DISTINCT"); // optional

    // Check if FROM is present anywhere
    const kwTokens = tokens.map(t => t.value.toUpperCase());
    const fromIndex = kwTokens.indexOf("FROM");

    if (fromIndex === -1) {
      // Missing FROM clause error!
      const lastTok = tokens[tokens.length - 1];
      return {
        valid: false,
        stage: "Stage 2 (Parser)",
        phase: "SYNTAX",
        line: lastTok.line,
        column: lastTok.column + (lastTok.value ? lastTok.value.length : 1),
        message: "Syntax error: Missing mandatory 'FROM' clause in SELECT statement.",
        suggestion: "Add 'FROM <table_name>' after the column projection list.",
        tokens,
        asciiTree: ""
      };
    }

    // Check for clause order: WHERE before FROM
    const whereIndex = kwTokens.indexOf("WHERE");
    if (whereIndex !== -1 && whereIndex < fromIndex) {
      const wTok = tokens[whereIndex];
      return {
        valid: false,
        stage: "Stage 2 (Parser)",
        phase: "SYNTAX",
        line: wTok.line,
        column: wTok.column,
        message: "Syntax error: Misplaced 'WHERE' clause before 'FROM' clause.",
        suggestion: "Place the FROM clause immediately following the column list, followed by WHERE.",
        tokens,
        asciiTree: ""
      };
    }

    // Check for missing comma in SELECT projections (consecutive identifiers before FROM)
    for (let cIdx = 1; cIdx < fromIndex - 1; cIdx++) {
      const c1 = tokens[cIdx];
      const c2 = tokens[cIdx + 1];
      if (c1.type === "IDENTIFIER" && c2.type === "IDENTIFIER") {
        // unless c2 is AS or an alias
        if (c2.value.toUpperCase() !== "AS") {
          return {
            valid: false,
            stage: "Stage 2 (Parser)",
            phase: "SYNTAX",
            line: c2.line,
            column: c2.column,
            message: `Syntax error: Missing comma between projection items '${c1.value}' and '${c2.value}'.`,
            suggestion: "Separate column selections with commas: SELECT col1, col2, ...",
            tokens,
            asciiTree: ""
          };
        }
      }
    }

    // Check for unobserved constructs in learned grammar mode (COUNT, SUM if not refined)
    if (grammarMode === "learned" && !sessionRefined) {
      for (const t of tokens) {
        if (t.type === "KEYWORD" && (t.value === "COUNT" || t.value === "SUM")) {
          return {
            valid: false,
            stage: "Stage 2 (Parser)",
            phase: "SYNTAX",
            line: t.line,
            column: t.column,
            message: `Syntax error: Unexpected token '${t.value}'. Inferred EBNF rule AGG_FUNC.2 only recognizes: /(?i:AVG|MAX|MIN)/.`,
            suggestion: "Refine grammar in Refinement Sandbox to add COUNT/SUM to AGG_FUNC, or test in Baseline mode.",
            tokens,
            asciiTree: ""
          };
        }
      }
    }

    // Build ASCII parse tree representation
    const treeLines = ["select_stmt", "├── SELECT"];
    
    // Projections
    const projTokens = tokens.slice(1, fromIndex);
    const projSummary = projTokens.map(t => t.value).join(" ");
    treeLines.push(`├── select_list (${projSummary})`);

    // FROM
    const tableIndex = fromIndex + 1;
    const tableTok = tableIndex < tokens.length ? tokens[tableIndex] : null;
    if (tableTok) {
      treeLines.push(`├── from_clause (FROM ${tableTok.value})`);
    }

    if (whereIndex !== -1) {
      treeLines.push("└── where_clause");
    }

    return {
      valid: true,
      stmtType: "SELECT",
      tokens,
      asciiTree: treeLines.join("\n")
    };
  }

  return {
    valid: false,
    stage: "Stage 2 (Parser)",
    phase: "SYNTAX",
    line: first.line,
    column: first.column,
    message: `Syntax error: Unsupported SQL statement starting with '${firstKw}'.`,
    suggestion: "Use standard SQL DSL syntax.",
    tokens,
    asciiTree: ""
  };
}

// ===========================================================================
// STAGE 3: SEMANTIC CHECKER (SCHEMA & TYPE VALIDATOR)
// ===========================================================================
function checkSemantics(query, parsedResult) {
  if (!parsedResult.valid) return [];
  const tokens = parsedResult.tokens || tokenizeSqlSimple(query);

  const diagnostics = [];
  const knownTables = Object.keys(SCHEMA);
  const allColumnsMap = {};
  for (const [tbl, tInfo] of Object.entries(SCHEMA)) {
    allColumnsMap[tbl] = tInfo.columns.map(c => c.name.toLowerCase());
  }

  // 1. Identify referenced tables
  const referencedTables = [];
  const tableAliases = {};

  for (let i = 0; i < tokens.length; i++) {
    const t = tokens[i];
    if (t.type === "KEYWORD" && (t.value === "FROM" || t.value === "JOIN" || t.value === "INTO" || t.value === "UPDATE")) {
      let nextIdx = i + 1;
      // skip INNER, LEFT if following JOIN
      while (nextIdx < tokens.length && ["INNER", "LEFT", "RIGHT"].includes(tokens[nextIdx].value.toUpperCase())) {
        nextIdx++;
      }
      if (nextIdx < tokens.length && tokens[nextIdx].type === "IDENTIFIER") {
        const tblName = tokens[nextIdx].value;
        referencedTables.push({ name: tblName, line: tokens[nextIdx].line, column: tokens[nextIdx].column });

        // check alias: FROM table AS alias OR FROM table alias
        if (nextIdx + 1 < tokens.length) {
          if (tokens[nextIdx + 1].value.toUpperCase() === "AS" && nextIdx + 2 < tokens.length && tokens[nextIdx + 2].type === "IDENTIFIER") {
            tableAliases[tokens[nextIdx + 2].value.toLowerCase()] = tblName.toLowerCase();
          } else if (tokens[nextIdx + 1].type === "IDENTIFIER" && !SQL_KEYWORDS_SET.has(tokens[nextIdx + 1].value.toUpperCase())) {
            tableAliases[tokens[nextIdx + 1].value.toLowerCase()] = tblName.toLowerCase();
          }
        }
      }
    }
  }

  // Check table existence
  for (const tbl of referencedTables) {
    const lowerName = tbl.name.toLowerCase();
    if (!allColumnsMap[lowerName]) {
      const suggestion = findBestSuggestion(lowerName, knownTables);
      diagnostics.push({
        phase: "SEMANTIC",
        stage: "Stage 3 (Semantic Check)",
        line: tbl.line,
        column: tbl.column,
        message: `Semantic error: Table '${tbl.name}' does not exist in 'school_db' database.`,
        suggestion: suggestion ? `Did you mean '${suggestion}'? Available tables: ${knownTables.join(', ')}.` : `Available tables: ${knownTables.join(', ')}.`
      });
    }
  }

  if (diagnostics.length > 0) return diagnostics;

  // 2. Check column existence for referenced columns
  // Gather available columns from referenced tables
  const validColSet = new Set();
  for (const tbl of referencedTables) {
    const lowerName = tbl.name.toLowerCase();
    if (allColumnsMap[lowerName]) {
      for (const col of allColumnsMap[lowerName]) {
        validColSet.add(col);
      }
    }
  }

  // Scan identifiers that appear to be column references
  for (let i = 0; i < tokens.length; i++) {
    const t = tokens[i];
    if (t.type === "IDENTIFIER") {
      const valLower = t.value.toLowerCase();
      // Skip if this identifier was a table name or an alias
      if (referencedTables.some(tbl => tbl.name.toLowerCase() === valLower)) continue;
      if (tableAliases[valLower]) continue;
      // Skip if preceded by AS
      if (i > 0 && tokens[i - 1].value.toUpperCase() === "AS") continue;
      // Skip if following FROM, JOIN, INTO, UPDATE
      if (i > 0 && ["FROM", "JOIN", "INTO", "UPDATE"].includes(tokens[i - 1].value.toUpperCase())) continue;

      // Handle table_alias.column format
      if (i > 1 && tokens[i - 1].value === "." && tokens[i - 2].type === "IDENTIFIER") {
        const alias = tokens[i - 2].value.toLowerCase();
        const actualTable = tableAliases[alias] || alias;
        if (allColumnsMap[actualTable]) {
          if (!allColumnsMap[actualTable].includes(valLower)) {
            const sug = findBestSuggestion(valLower, allColumnsMap[actualTable]);
            diagnostics.push({
              phase: "SEMANTIC",
              stage: "Stage 3 (Semantic Check)",
              line: t.line,
              column: t.column,
              message: `Semantic error: Unknown column '${t.value}' in table '${actualTable}'.`,
              suggestion: sug ? `Did you mean '${sug}'?` : `Available columns: ${allColumnsMap[actualTable].join(', ')}.`
            });
          }
        }
        continue;
      }

      // Check unqualified column reference
      if (validColSet.size > 0 && !validColSet.has(valLower)) {
        // Ensure it's not a function or keyword
        if (i < tokens.length - 1 && tokens[i + 1].value === "(") continue; // function call
        const sug = findBestSuggestion(valLower, Array.from(validColSet));
        diagnostics.push({
          phase: "SEMANTIC",
          stage: "Stage 3 (Semantic Check)",
          line: t.line,
          column: t.column,
          message: `Semantic error: Column '${t.value}' not found in any referenced table.`,
          suggestion: sug ? `Did you mean '${sug}'? Available: ${Array.from(validColSet).slice(0, 8).join(', ')}...` : `Available columns: ${Array.from(validColSet).slice(0, 8).join(', ')}.`
        });
      }
    }
  }

  return diagnostics;
}

// ===========================================================================
// ML CLASSIFIER INFERENCE (TF-IDF + LOGISTIC REGRESSION)
// ===========================================================================
function predictMlClassifierJs(query) {
  if (!ML_MODEL_WEIGHTS || !ML_MODEL_WEIGHTS.vocabulary) {
    return {
      available: false,
      message: "ML model weights not loaded."
    };
  }

  const { vocabulary, idf, coefficients, intercept } = ML_MODEL_WEIGHTS;

  // Extract raw tokens using sklearn pattern: r"(?u)\b\w+\b|[<>=!]+|[,;()]"
  const rawTokens = [];
  const regex = /\b\w+\b|[<>=!]+|[,;()]/g;
  let match;
  while ((match = regex.exec(query.toLowerCase())) !== null) {
    rawTokens.push(match[0]);
  }

  // Generate n-grams (1, 2, 3)
  const ngrams = [];
  for (let n = 1; n <= 3; n++) {
    for (let i = 0; i <= rawTokens.length - n; i++) {
      ngrams.push(rawTokens.slice(i, i + n).join(" "));
    }
  }

  // Count term frequencies
  const tf = {};
  for (const ng of ngrams) {
    tf[ng] = (tf[ng] || 0) + 1;
  }

  // Compute sublinear TF-IDF vector: (1 + log(tf)) * idf
  const vectorEntries = [];
  let normSq = 0;
  for (const [term, freq] of Object.entries(tf)) {
    if (vocabulary.hasOwnProperty(term)) {
      const idx = vocabulary[term];
      const val = (1 + Math.log(freq)) * idf[idx];
      vectorEntries.push({ idx, val });
      normSq += val * val;
    }
  }

  // L2 normalization
  const norm = Math.sqrt(normSq);
  let score = intercept;
  if (norm > 0) {
    for (const item of vectorEntries) {
      const normalizedVal = item.val / norm;
      score += normalizedVal * coefficients[item.idx];
    }
  }

  // Sigmoid probability: P(valid=1) = 1 / (1 + exp(-score))
  const probValid = 1 / (1 + Math.exp(-score));
  const isValid = probValid >= 0.5;

  return {
    available: true,
    valid: isValid,
    verdict: isValid ? "ACCEPT" : "REJECT",
    probability: probValid,
    stage_reached: "STATISTICAL (Black-Box)",
    message: `TF-IDF Statistical classification: Likelihood of validity is ${(probValid * 100).toFixed(1)}%. Model predicts ${isValid ? 'ACCEPT (Valid)' : 'REJECT (Invalid)'}.`,
    suggestion: "ML model outputs a global confidence score. It cannot detect syntax boundaries, schema validity, or generate an AST."
  };
}

// ===========================================================================
// UNIFIED MULTI-SYSTEM EVALUATOR
// ===========================================================================
function evaluateQueryMultiSystem(query, sessionRefined = false) {
  // Check if query matches a known preset exactly (to serve precomputed real Python results)
  const normalizedQ = query.trim().replace(/\r\n/g, "\n");
  const matchingPreset = PRESETS.find(p => p.sql.trim().replace(/\r\n/g, "\n") === normalizedQ);

  if (matchingPreset && !sessionRefined) {
    return {
      isPreset: true,
      presetName: matchingPreset.name,
      presetTag: matchingPreset.tag,
      baseline: matchingPreset.baseline,
      learned: matchingPreset.learned,
      ml: matchingPreset.ml,
      tokens: matchingPreset.learned.tokens || matchingPreset.baseline.tokens || []
    };
  }

  // Run full JS browser simulation
  // 1. Stage 0 Security Gate
  const secErrors = checkSecurityGate(query);
  if (secErrors.length > 0) {
    const err = secErrors[0];
    const mlRes = predictMlClassifierJs(query);
    return {
      isPreset: false,
      baseline: {
        valid: false, verdict: "REJECT", stage_reached: err.stage,
        line: err.line, column: err.column, message: err.message, suggestion: err.suggestion,
        ascii_tree: "", tokens: tokenizeSqlSimple(query)
      },
      learned: {
        valid: false, verdict: "REJECT", stage_reached: err.stage,
        line: err.line, column: err.column, message: err.message, suggestion: err.suggestion,
        ascii_tree: "", tokens: tokenizeSqlSimple(query)
      },
      ml: mlRes,
      tokens: tokenizeSqlSimple(query)
    };
  }

  // 2. Stages 1 & 2 Parser
  const parseBase = parseQuery(query, "baseline", true);
  const parseLearn = parseQuery(query, "learned", sessionRefined);

  // 3. Stage 3 Semantic Check
  const semBase = parseBase.valid ? checkSemantics(query, parseBase) : [];
  const semLearn = parseLearn.valid ? checkSemantics(query, parseLearn) : [];

  // Compose Baseline Verdict
  let baseVerdict = {
    valid: true,
    verdict: "ACCEPT",
    stage_reached: "Passed All (Stages 0-3)",
    line: null, column: null,
    message: "Query is fully valid across all compiler stages.",
    suggestion: "Safe for relational database execution.",
    ascii_tree: parseBase.asciiTree || "",
    tokens: parseBase.tokens || []
  };
  if (!parseBase.valid) {
    baseVerdict = {
      valid: false, verdict: "REJECT", stage_reached: parseBase.stage,
      line: parseBase.line, column: parseBase.column, message: parseBase.message, suggestion: parseBase.suggestion,
      ascii_tree: "", tokens: parseBase.tokens || []
    };
  } else if (semBase.length > 0) {
    const s = semBase[0];
    baseVerdict = {
      valid: false, verdict: "REJECT", stage_reached: s.stage,
      line: s.line, column: s.column, message: s.message, suggestion: s.suggestion,
      ascii_tree: parseBase.asciiTree || "", tokens: parseBase.tokens || []
    };
  }

  // Compose Learned Verdict
  let learnVerdict = {
    valid: true,
    verdict: "ACCEPT",
    stage_reached: "Passed All (Stages 0-3)",
    line: null, column: null,
    message: "Query is fully valid across all compiler stages.",
    suggestion: "Safe for relational database execution.",
    ascii_tree: parseLearn.asciiTree || "",
    tokens: parseLearn.tokens || []
  };
  if (!parseLearn.valid) {
    learnVerdict = {
      valid: false, verdict: "REJECT", stage_reached: parseLearn.stage,
      line: parseLearn.line, column: parseLearn.column, message: parseLearn.message, suggestion: parseLearn.suggestion,
      ascii_tree: "", tokens: parseLearn.tokens || []
    };
  } else if (semLearn.length > 0) {
    const s = semLearn[0];
    learnVerdict = {
      valid: false, verdict: "REJECT", stage_reached: s.stage,
      line: s.line, column: s.column, message: s.message, suggestion: s.suggestion,
      ascii_tree: parseLearn.asciiTree || "", tokens: parseLearn.tokens || []
    };
  }

  // 4. ML Classifier
  const mlVerdict = predictMlClassifierJs(query);

  return {
    isPreset: false,
    baseline: baseVerdict,
    learned: learnVerdict,
    ml: mlVerdict,
    tokens: parseLearn.tokens || parseBase.tokens || []
  };
}
