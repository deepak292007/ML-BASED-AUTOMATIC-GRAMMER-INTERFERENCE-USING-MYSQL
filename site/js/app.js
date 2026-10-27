/**
 * AutoGrammar Showcase Website Interactive Controller (site/js/app.js)
 * Standalone vanilla JavaScript application handling:
 *   - Dark/Light Theme Switching with safe localStorage
 *   - Presentation Mode (slide navigation via Left/Right Arrow keys)
 *   - Keyboard Shortcuts Modal ('?', '1'-'8', '/')
 *   - Scroll-Spy Navigation
 *   - Animated Count-Up Numbers
 *   - Interactive Stepper & 4-Stage Pipeline Inspector
 *   - Query Playground Controller with Presets, History, Schema insertion, and Tabs
 *   - Grammar Refinement Sandbox & Client-Side Blob Downloads
 *   - False-Rejection Explorer with search and template grouping
 *   - Viva Q&A Accordion
 */

// Global Application State
const STATE = {
  activePresetId: "p1_join",
  queryHistory: [],
  sessionGrammarRefined: false,
  presentationMode: false,
  currentSectionIndex: 0
};

// Section IDs for Presentation Mode and Scroll-Spy
const SECTIONS = [
  "sec-hero",
  "sec-approach",
  "sec-pipeline",
  "sec-demo",
  "sec-grammar",
  "sec-results",
  "sec-data",
  "sec-traceability",
  "sec-viva",
  "sec-reproduce"
];

// ===========================================================================
// 1. THEME SWITCHER (DARK / LIGHT WITH SAFE LOCALSTORAGE)
// ===========================================================================
function initTheme() {
  const toggleBtn = document.getElementById("btn-theme-toggle");
  let savedTheme = "dark";
  try {
    savedTheme = localStorage.getItem("autogrm_theme") || "dark";
  } catch (e) {
    savedTheme = "dark";
  }

  document.documentElement.setAttribute("data-theme", savedTheme);
  updateThemeButton(savedTheme);

  if (toggleBtn) {
    toggleBtn.addEventListener("click", () => {
      const current = document.documentElement.getAttribute("data-theme") || "dark";
      const next = current === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", next);
      try {
        localStorage.setItem("autogrm_theme", next);
      } catch (e) {}
      updateThemeButton(next);
    });
  }
}

function updateThemeButton(theme) {
  const btn = document.getElementById("btn-theme-toggle");
  if (btn) {
    btn.innerHTML = theme === "dark" ? "☀️ Light" : "🌙 Dark";
  }
}

// ===========================================================================
// 2. SCROLL-SPY & PRESENTATION MODE
// ===========================================================================
function initScrollSpy() {
  const navLinks = document.querySelectorAll(".nav-links a");
  const sectionElements = SECTIONS.map(id => document.getElementById(id)).filter(Boolean);

  window.addEventListener("scroll", () => {
    let currentId = "";
    const scrollPos = window.scrollY + 100;

    sectionElements.forEach(sec => {
      if (sec.offsetTop <= scrollPos && sec.offsetTop + sec.offsetHeight > scrollPos) {
        currentId = sec.id;
      }
    });

    navLinks.forEach(link => {
      link.classList.remove("active");
      if (link.getAttribute("href") === `#${currentId}`) {
        link.classList.add("active");
      }
    });
  });
}

function initPresentationMode() {
  const btn = document.getElementById("btn-presentation-toggle");
  const indicator = document.getElementById("presentation-indicator");

  if (btn) {
    btn.addEventListener("click", togglePresentationMode);
  }

  window.addEventListener("keydown", e => {
    // If typing inside textarea or input, do not trigger global shortcuts
    if (["TEXTAREA", "INPUT"].includes(document.activeElement.tagName)) return;

    if (e.key === "p" || e.key === "P") {
      togglePresentationMode();
    } else if (e.key === "?") {
      toggleShortcutsModal();
    } else if (e.key === "/") {
      e.preventDefault();
      const ed = document.getElementById("sql-editor-input");
      if (ed) ed.focus();
    } else if (e.key >= "1" && e.key <= "8") {
      const idx = parseInt(e.key, 10) - 1;
      if (PRESETS[idx]) {
        loadPreset(PRESETS[idx].id);
      }
    } else if (STATE.presentationMode) {
      if (e.key === "ArrowRight" || e.key === "PageDown" || e.key === " ") {
        e.preventDefault();
        stepPresentation(1);
      } else if (e.key === "ArrowLeft" || e.key === "PageUp") {
        e.preventDefault();
        stepPresentation(-1);
      } else if (e.key === "Escape") {
        togglePresentationMode(false);
      }
    }
  });
}

function togglePresentationMode(force) {
  STATE.presentationMode = typeof force === "boolean" ? force : !STATE.presentationMode;
  const btn = document.getElementById("btn-presentation-toggle");
  const indicator = document.getElementById("presentation-indicator");

  if (STATE.presentationMode) {
    btn.classList.add("active");
    btn.innerHTML = "📺 Exit Pres.";
    if (indicator) indicator.style.display = "block";
    updatePresentationIndicator();
    scrollToSectionIndex(STATE.currentSectionIndex);
  } else {
    btn.classList.remove("active");
    btn.innerHTML = "📺 Present";
    if (indicator) indicator.style.display = "none";
  }
}

function stepPresentation(delta) {
  STATE.currentSectionIndex = Math.max(0, Math.min(SECTIONS.length - 1, STATE.currentSectionIndex + delta));
  updatePresentationIndicator();
  scrollToSectionIndex(STATE.currentSectionIndex);
}

function updatePresentationIndicator() {
  const indicator = document.getElementById("presentation-indicator");
  if (indicator) {
    indicator.innerHTML = `Slide ${STATE.currentSectionIndex + 1} / ${SECTIONS.length} (Use ← / →)`;
  }
}

function scrollToSectionIndex(idx) {
  const targetId = SECTIONS[idx];
  const el = document.getElementById(targetId);
  if (el) {
    el.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

function toggleShortcutsModal(force) {
  const modal = document.getElementById("shortcuts-overlay");
  if (!modal) return;
  const isActive = modal.classList.contains("active");
  const show = typeof force === "boolean" ? force : !isActive;
  if (show) modal.classList.add("active");
  else modal.classList.remove("active");
}

// ===========================================================================
// 3. ANIMATED COUNT-UP NUMBERS (HERO STATS)
// ===========================================================================
function initCountUpNumbers() {
  const counters = document.querySelectorAll(".count-up");
  counters.forEach(counter => {
    const target = parseFloat(counter.getAttribute("data-target"));
    const isDecimal = counter.getAttribute("data-decimal") === "true";
    const duration = 1200;
    const start = 0;
    const startTime = performance.now();

    function update(now) {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // ease-out cubic
      const ease = 1 - Math.pow(1 - progress, 3);
      const current = start + (target - start) * ease;
      counter.textContent = isDecimal ? current.toFixed(2) : Math.round(current);

      if (progress < 1) {
        requestAnimationFrame(update);
      } else {
        counter.textContent = isDecimal ? target.toFixed(2) : target;
      }
    }
    requestAnimationFrame(update);
  });
}

// ===========================================================================
// 4. STEPPER COMPONENT (INDUCTION DEMO)
// ===========================================================================
const STEPPER_DATA = [
  {
    num: "Step 1",
    title: "1. Tokenize Input Query",
    desc: "Lexer decomposes query into typed tokens while recording 1-indexed lines and columns.",
    code: "['SELECT', 'first_name', ',', 'last_name', 'FROM', 'students', 'WHERE', 'state', '=', \"'Karnataka'\"]"
  },
  {
    num: "Step 2",
    title: "2. Mine Clause Skeleton",
    desc: "Extracts clause sequencing and statement archetype (SELECT_STMT, JOIN, WHERE).",
    code: "Statement Type: SELECT_STMT\nSkeleton: SELECT -> FROM -> WHERE"
  },
  {
    num: "Step 3",
    title: "3. Generalize Identifiers & Literals",
    desc: "Abstracts concrete table/column names into syntactic non-terminals (CNAME, literal, condition).",
    code: "select_stmt: \"SELECT\"i select_list from_clause where_clause\ncolumn_ref: [CNAME \".\"] CNAME\nliteral: STRING | NUMBER"
  },
  {
    num: "Step 4",
    title: "4. Emit Valid EBNF Production",
    desc: "Consolidates observed patterns into Lark-compatible grammar rule with optionality & repetition.",
    code: "select_stmt: \"SELECT\"i [distinct_clause] select_list from_clause [where_clause] [groupby_clause]"
  }
];

function initStepper() {
  const container = document.getElementById("stepper-container");
  if (!container) return;

  container.innerHTML = STEPPER_DATA.map(s => `
    <div class="step-card">
      <div class="step-num">${s.num}</div>
      <div class="step-title">${s.title}</div>
      <div class="step-desc">${s.desc}</div>
      <pre class="step-code"><code>${escapeHtml(s.code)}</code></pre>
    </div>
  `).join("");
}

// ===========================================================================
// 5. INTERACTIVE 4-STAGE PIPELINE CARDS
// ===========================================================================
const PIPELINE_DATA = {
  stage0: {
    title: "Stage 0: Pre-Parse Security Gate",
    badge: "AST / Pattern Guardrail",
    catches: "Destructive DDL/DCL commands (DROP, ALTER, TRUNCATE), multi-statement batching (SQL injection vectors), unconstrained UPDATE/DELETE without WHERE.",
    good: "SELECT first_name, state FROM students WHERE class_id = 5;",
    bad: "DROP TABLE students; -- Blocked destructive command"
  },
  stage1: {
    title: "Stage 1: Lexical Analyzer (Lexer)",
    badge: "Regex Tokenizer",
    catches: "Illegal characters, unrecognized special symbols (@, #, $), unclosed literal strings, double operators (> =). Localizes line and column numbers.",
    good: "WHERE marks_obtained >= 85 AND gender = 'Female';",
    bad: "SELECT first_name @#$ last_name FROM students; -- Illegal token @"
  },
  stage2: {
    title: "Stage 2: Syntax Parser",
    badge: "Earley / LALR Context-Free Grammar",
    catches: "Missing mandatory clauses (FROM), unbalanced parentheses, misplaced clauses (WHERE before FROM), unobserved constructs in learned grammar.",
    good: "SELECT class_id, AVG(marks_obtained) FROM marks GROUP BY class_id;",
    bad: "SELECT first_name, last_name WHERE state = 'Delhi'; -- Missing FROM"
  },
  stage3: {
    title: "Stage 3: Semantic Catalog Checker",
    badge: "Relational Schema Verification",
    catches: "Unknown table names, nonexistent column references, ambiguous column references in joins, type mismatches. Generates Levenshtein 'Did you mean ...?' suggestions.",
    good: "SELECT s.first_name, m.marks_obtained FROM students AS s INNER JOIN marks AS m ON s.student_id = m.student_id;",
    bad: "SELECT first_name, blood_group FROM students; -- Unknown column 'blood_group'"
  }
};

function initPipelineCards() {
  const cards = document.querySelectorAll(".pipeline-card");
  const detailBox = document.getElementById("pipeline-detail-box");

  cards.forEach(card => {
    card.addEventListener("click", () => {
      cards.forEach(c => c.classList.remove("active"));
      card.classList.add("active");
      const stageKey = card.getAttribute("data-stage");
      const d = PIPELINE_DATA[stageKey];
      if (detailBox && d) {
        detailBox.innerHTML = `
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <h3 style="margin:0; color:#38bdf8;">${d.title}</h3>
            <span class="badge badge-info">${d.badge}</span>
          </div>
          <p style="color:#cbd5e1; font-size:0.9rem;"><strong>What this stage verifies:</strong> ${d.catches}</p>
          <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-top:10px;">
            <div style="background:#064e3b; padding:10px; border-radius:6px; border:1px solid #059669;">
              <span style="font-size:11px; font-weight:bold; color:#34d399;">✓ PASS EXAMPLE</span>
              <pre style="margin-top:4px; font-family:var(--font-mono); font-size:11px; color:#e2e8f0;">${escapeHtml(d.good)}</pre>
            </div>
            <div style="background:#7f1d1d; padding:10px; border-radius:6px; border:1px solid #dc2626;">
              <span style="font-size:11px; font-weight:bold; color:#fca5a5;">✗ REJECT EXAMPLE</span>
              <pre style="margin-top:4px; font-family:var(--font-mono); font-size:11px; color:#e2e8f0;">${escapeHtml(d.bad)}</pre>
            </div>
          </div>
        `;
      }
    });
  });

  // Activate first card by default
  if (cards.length > 0) cards[0].click();
}

// ===========================================================================
// 6. PLAYGROUND CONTROLLER (PRESETS, EDITOR, VERDICTS, TABS)
// ===========================================================================
function initPlayground() {
  const presetsContainer = document.getElementById("presets-container");
  const editor = document.getElementById("sql-editor-input");
  const btnRun = document.getElementById("btn-run-query");
  const btnCopy = document.getElementById("btn-copy-query");
  const btnClear = document.getElementById("btn-clear-query");

  // 1. Render Preset Buttons
  if (presetsContainer) {
    presetsContainer.innerHTML = PRESETS.map(p => {
      const isAccept = p.tag === "ACCEPT";
      const badgeCls = isAccept ? "badge-accept" : "badge-reject";
      return `
        <button class="preset-btn" data-preset="${p.id}" onclick="loadPreset('${p.id}')">
          <span>${p.name}</span>
          <span class="badge ${badgeCls}">${p.tag}</span>
        </button>
      `;
    }).join("");
  }

  // 2. Clickable Schema Sidebar
  renderSchemaSidebar();

  // 3. Event Listeners
  if (btnRun) {
    btnRun.addEventListener("click", () => {
      runPlaygroundEvaluation();
    });
  }

  if (btnCopy) {
    btnCopy.addEventListener("click", () => {
      if (editor) {
        navigator.clipboard.writeText(editor.value).then(() => {
          btnCopy.innerHTML = "✓ Copied!";
          setTimeout(() => { btnCopy.innerHTML = "📋 Copy Query"; }, 1500);
        });
      }
    });
  }

  if (btnClear) {
    btnClear.addEventListener("click", () => {
      if (editor) {
        editor.value = "";
        editor.focus();
        runPlaygroundEvaluation();
      }
    });
  }

  // Tabs navigation
  const tabBtns = document.querySelectorAll(".tab-btn");
  tabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      tabBtns.forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach(tc => tc.classList.remove("active"));
      btn.classList.add("active");
      const targetId = btn.getAttribute("data-tab");
      const targetContent = document.getElementById(targetId);
      if (targetContent) targetContent.classList.add("active");
    });
  });

  // Load initial preset (Preset 1: Valid Join)
  loadPreset("p1_join");
}

function loadPreset(presetId) {
  const preset = PRESETS.find(p => p.id === presetId);
  if (!preset) return;

  STATE.activePresetId = presetId;
  const editor = document.getElementById("sql-editor-input");
  if (editor) {
    editor.value = preset.sql;
  }

  // Highlight active preset button
  document.querySelectorAll(".preset-btn").forEach(b => {
    b.classList.remove("active");
    if (b.getAttribute("data-preset") === presetId) b.classList.add("active");
  });

  runPlaygroundEvaluation(preset);
}

function renderSchemaSidebar() {
  const container = document.getElementById("schema-sidebar-container");
  if (!container) return;

  let html = `<div style="font-size:0.85rem; font-weight:700; margin-bottom:8px; color:#f8fafc;">school_db Tables</div>`;
  for (const [tbl, tInfo] of Object.entries(SCHEMA)) {
    html += `
      <div class="schema-table-item">
        <div class="schema-tbl-name" onclick="insertTextAtCursor('${tbl}')" title="Click to insert table name">
          <span>📁 ${tbl}</span>
          <span style="font-size:10px; color:#64748b;">${tInfo.columns.length} cols</span>
        </div>
        <ul class="schema-col-list">
          ${tInfo.columns.map(c => `
            <li class="schema-col-item" onclick="insertTextAtCursor('${c.name}')" title="${c.type} - ${c.desc}">
              ${c.pk ? '🔑 ' : (c.fk ? '🔗 ' : '• ')}${c.name}
            </li>
          `).join("")}
        </ul>
      </div>
    `;
  }
  container.innerHTML = html;
}

function insertTextAtCursor(text) {
  const editor = document.getElementById("sql-editor-input");
  if (!editor) return;
  const start = editor.selectionStart;
  const end = editor.selectionEnd;
  const before = editor.value.substring(0, start);
  const after = editor.value.substring(end);
  editor.value = before + text + after;
  editor.selectionStart = editor.selectionEnd = start + text.length;
  editor.focus();
}

// ===========================================================================
// PYTHON COMPILER BACKEND INTEGRATION
// ===========================================================================
let BACKEND_ONLINE = false;
let BACKEND_INFO = null;

function getApiBase() {
  if (window.CUSTOM_API_BASE) return window.CUSTOM_API_BASE;
  const loc = window.location;
  if (loc.protocol.startsWith("http")) {
    return loc.origin;
  }
  return "http://127.0.0.1:8000";
}

async function checkBackendHealth() {
  const indicator = document.getElementById("backend-status-indicator");
  const candidates = [
    getApiBase(),
    "http://127.0.0.1:8000",
    "http://localhost:8000"
  ];
  const uniqueUrls = Array.from(new Set(candidates));

  for (const baseUrl of uniqueUrls) {
    try {
      const res = await fetch(`${baseUrl}/api/health`, {
        method: "GET",
        headers: { "Accept": "application/json" },
        cache: "no-store"
      });
      if (res.ok) {
        const data = await res.json();
        BACKEND_ONLINE = true;
        BACKEND_INFO = data;
        window.CUSTOM_API_BASE = baseUrl;
        if (indicator) {
          indicator.className = "badge badge-accept";
          indicator.innerHTML = "● Python Compiler Online (Lark)";
          indicator.title = `Connected to Python backend at ${baseUrl} with Lark parser.`;
        }
        return data;
      }
    } catch (e) {
      // Continue searching
    }
  }

  BACKEND_ONLINE = false;
  BACKEND_INFO = null;
  if (indicator) {
    indicator.className = "badge badge-warn";
    indicator.innerHTML = "● Compiler Offline (Simulation Mode)";
    indicator.title = "Python backend server (server.py) not detected. Using client-side simulation.";
  }
  return null;
}

async function runPlaygroundEvaluation(preset) {
  const editor = document.getElementById("sql-editor-input");
  if (!editor) return;
  const query = editor.value.trim();

  // Record history
  if (query && !STATE.queryHistory.includes(query)) {
    STATE.queryHistory.unshift(query);
    if (STATE.queryHistory.length > 10) STATE.queryHistory.pop();
    renderQueryHistory();
  }

  let evalResult = null;
  let isBackendResult = false;
  let realExecResult = null;

  // Try real Python backend first
  if (BACKEND_ONLINE) {
    try {
      const resp = await fetch(`${getApiBase()}/api/validate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: query, grammar_choice: "both" })
      });
      if (resp.ok) {
        const data = await resp.json();
        evalResult = {
          isBackend: true,
          source: data.source,
          compiler_valid: data.compiler_valid,
          learned_valid: data.learned_valid,
          grammar_disagreement: data.grammar_disagreement,
          ml_disagreement: data.ml_disagreement,
          ml_override_message: data.ml_override_message,
          baseline: data.baseline,
          learned: data.learned,
          ml: data.ml,
          tokens: data.tokens,
          safe_to_execute: data.safe_to_execute
        };
        isBackendResult = true;

        // If query is valid and read-only SELECT, run safe execution
        if (data.safe_to_execute) {
          try {
            const execResp = await fetch(`${getApiBase()}/api/execute`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ query: query, max_rows: 50 })
            });
            if (execResp.ok) {
              realExecResult = await execResp.json();
            }
          } catch (e) {
            console.warn("Execution request error:", e);
          }
        }
      }
    } catch (e) {
      console.warn("Backend request failed, falling back to offline simulation:", e);
      BACKEND_ONLINE = false;
      const indicator = document.getElementById("backend-status-indicator");
      if (indicator) {
        indicator.className = "badge badge-warn";
        indicator.innerHTML = "● Compiler Offline (Simulation Mode)";
      }
    }
  }

  // Fallback to offline evaluation
  if (!evalResult) {
    evalResult = evaluateQueryMultiSystem(query, STATE.sessionGrammarRefined);
  }

  // 1. Render Verdict Source Tag Banner
  const sourceTagBox = document.getElementById("verdict-source-banner");
  if (sourceTagBox) {
    let mlOverrideBanner = "";
    if (evalResult.ml_override_message) {
      mlOverrideBanner = `<div class="badge badge-warn" style="margin-top:8px; display:block; white-space:normal; line-height:1.4;">ℹ️ ${escapeHtml(evalResult.ml_override_message)}</div>`;
    }

    if (isBackendResult) {
      let disagreeBadge = "";
      if (evalResult.grammar_disagreement) {
        disagreeBadge = `<span class="badge badge-warn" style="margin-left:8px;">⚠️ Disagreement: Baseline accepts, Learned rejects</span>`;
      }
      sourceTagBox.innerHTML = `
        <div>
          <span class="badge badge-accept">Source: Real Python Compiler (Lark Earley Parser &amp; Pipeline)</span>
          ${disagreeBadge}
          <span style="font-size:12px; color:#94a3b8; margin-left:8px;">Validated through Security Gate &rarr; Lexer &rarr; Lark EBNF &rarr; Semantic Checker</span>
        </div>
        ${mlOverrideBanner}
      `;
    } else if (evalResult.isPreset) {
      sourceTagBox.innerHTML = `
        <div>
          <span class="badge badge-info">Source: Precomputed Benchmark (Exact Python/Lark Verdict)</span>
          <span style="font-size:12px; color:#94a3b8; margin-left:8px;">Preset: <strong>${evalResult.presetName}</strong> (${evalResult.presetTag})</span>
        </div>
        ${mlOverrideBanner}
      `;
    } else {
      sourceTagBox.innerHTML = `
        <div>
          <span class="badge badge-warn">Backend Offline (Offline Simulation Mode)</span>
          <span style="font-size:12px; color:#94a3b8; margin-left:8px;">Python backend is offline. Start via <code>python server.py</code> to connect the real Lark compiler. Showing client-side simulation.</span>
        </div>
        ${mlOverrideBanner}
      `;
    }
  }

  // 2. Render Error Caret Display if query failed
  const caretContainer = document.getElementById("error-caret-container");
  if (caretContainer) {
    const activeFailure = (!evalResult.learned.valid ? evalResult.learned : (!evalResult.baseline.valid ? evalResult.baseline : null));
    if (activeFailure && activeFailure.column) {
      const lines = query.split("\n");
      const errLineNum = activeFailure.line || 1;
      const errColNum = activeFailure.column || 1;
      const targetLine = lines[errLineNum - 1] || query;
      const caretIndent = " ".repeat(Math.max(0, errColNum - 1)) + "^";

      caretContainer.style.display = "block";
      caretContainer.innerHTML = `
        <div class="error-caret-line">
          <strong>Location: Line ${errLineNum}, Column ${errColNum}</strong><br>
          <pre style="margin:4px 0; color:#e2e8f0;">${escapeHtml(targetLine)}\n<span style="color:#f87171; font-weight:bold;">${caretIndent}</span></pre>
          <span>${escapeHtml(activeFailure.message)}</span>
        </div>
      `;
    } else {
      caretContainer.style.display = "none";
      caretContainer.innerHTML = "";
    }
  }

  // 3. Render 3 Verdict Columns
  renderVerdictColumn("verdict-col-baseline", evalResult.baseline, "#38bdf8", "Fixed Baseline Grammar");
  renderVerdictColumn("verdict-col-learned", evalResult.learned, "#10b981", `Learned Grammar ${STATE.sessionGrammarRefined ? '(Session Refined)' : '(learned.lark)'}`);
  renderVerdictColumn("verdict-col-ml", evalResult.ml, "#a855f7", `ML Model: ${evalResult.ml ? (evalResult.ml.model_type || 'Statistical') : 'ML'}`);

  // 4. Render Inspection Tabs (Tokens, Parse Tree, Database)
  renderTokensTab(evalResult.tokens || []);
  renderParseTreeTab(evalResult.learned.ascii_tree || evalResult.baseline.ascii_tree || "");
  renderDatabaseTab(evalResult.learned.valid || evalResult.baseline.valid, query, realExecResult);
}

function renderVerdictColumn(containerId, res, accentColor, title) {
  const col = document.getElementById(containerId);
  if (!col) return;

  const isAccept = res.valid;
  const badgeHtml = isAccept ?
    `<span class="badge badge-accept">ACCEPT (Valid)</span>` :
    `<span class="badge badge-reject">REJECT (Invalid)</span>`;

  col.innerHTML = `
    <div class="verdict-header" style="border-top: 3px solid ${accentColor};">
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <h4>${title}</h4>
        ${badgeHtml}
      </div>
    </div>
    <div class="verdict-body">
      <div class="verdict-field">
        <strong>Failing Stage:</strong> <code>${res.stage_reached || 'N/A'}</code>
      </div>
      <div class="verdict-field">
        <strong>Error Location:</strong> ${res.line ? `Line ${res.line}, Col ${res.column}` : 'N/A'}
      </div>
      <div class="verdict-field">
        <strong>Diagnostic Message:</strong><br>
        <span style="color:${isAccept ? '#34d399' : '#f87171'};">${escapeHtml(res.message || 'Validation passed.')}</span>
      </div>
      <div class="verdict-field">
        <strong>Compiler Suggestion:</strong><br>
        <span style="color:${accentColor}; font-size:0.8rem;">💡 ${escapeHtml(res.suggestion || 'Safe for database execution.')}</span>
      </div>
    </div>
  `;
}

function renderTokensTab(tokens) {
  const container = document.getElementById("tokens-tab-container");
  if (!container) return;

  if (!tokens || tokens.length === 0) {
    container.innerHTML = `<p style="color:#64748b; font-size:0.85rem;">No tokens to display (query empty or blocked at Stage 0).</p>`;
    return;
  }

  let html = `<div class="token-chip-container">`;
  tokens.forEach(t => {
    const cat = t.type || t.category || "UNKNOWN";
    html += `
      <div class="token-chip token-chip-${cat}" title="Line ${t.line}, Col ${t.column} [Type: ${cat}]">
        <span style="font-size:9px; opacity:0.7;">${cat}</span><br>
        <strong>${escapeHtml(t.value)}</strong>
      </div>
    `;
  });
  html += `</div>`;
  container.innerHTML = html;
}

function renderParseTreeTab(asciiTree) {
  const container = document.getElementById("tree-tab-container");
  if (!container) return;

  if (asciiTree) {
    container.innerHTML = `<pre style="background:var(--bg-secondary); border:1px solid var(--border-color); padding:1rem; border-radius:6px; font-family:var(--font-mono); font-size:0.82rem; color:#38bdf8; overflow-x:auto;"><code>${escapeHtml(asciiTree)}</code></pre>`;
  } else {
    container.innerHTML = `<p style="color:#f87171; font-size:0.85rem;">⚠️ Parse tree unavailable because syntax or security validation did not pass.</p>`;
  }
}

function renderDatabaseTab(isValid, query, realExecResult) {
  const container = document.getElementById("database-tab-container");
  if (!container) return;

  const upper = query.trim().toUpperCase();
  const isSelect = upper.startsWith("SELECT");

  if (!isValid) {
    container.innerHTML = `
      <div style="background:#7f1d1d; border:1px solid #dc2626; padding:12px; border-radius:6px; color:#fca5a5; font-size:0.85rem;">
        ⛔ Database Execution Blocked: Query failed compiler validation. Rejected queries are strictly forbidden from executing.
      </div>
    `;
    return;
  }

  if (!isSelect) {
    container.innerHTML = `
      <div style="background:#78350f; border:1px solid #d97706; padding:12px; border-radius:6px; color:#fde68a; font-size:0.85rem;">
        ⚠️ Execution Safeguard: Only read-only SELECT queries are executed in the interactive sandbox to protect database integrity.
      </div>
    `;
    return;
  }

  if (realExecResult) {
    if (realExecResult.success) {
      const cols = realExecResult.columns || [];
      const rows = realExecResult.rows || [];
      const engine = realExecResult.engine || "Relational Sandbox";
      const rowCount = realExecResult.row_count || rows.length;

      let tableHtml = `
        <div style="background:#064e3b; border:1px solid #059669; padding:12px; border-radius:6px; color:#a7f3d0; font-size:0.85rem; margin-bottom:12px;">
          ✓ Query Executed Successfully on <strong>${escapeHtml(engine)}</strong> (Returned ${rowCount} rows)
        </div>
      `;

      if (rows.length === 0) {
        tableHtml += `<p style="color:#94a3b8; font-size:0.85rem;">Query executed successfully. 0 rows returned matching criteria.</p>`;
      } else {
        tableHtml += `
          <div style="max-height:350px; overflow-y:auto;">
            <table class="data-table" style="width:100%;">
              <thead>
                <tr>${cols.map(c => `<th>${escapeHtml(c)}</th>`).join("")}</tr>
              </thead>
              <tbody>
                ${rows.slice(0, 50).map(r => `
                  <tr>${cols.map(c => `<td>${escapeHtml(r[c] !== undefined && r[c] !== null ? r[c] : "")}</td>`).join("")}</tr>
                `).join("")}
              </tbody>
            </table>
          </div>
          <div style="font-size:11px; color:#94a3b8; margin-top:8px;">Displaying ${Math.min(rows.length, 50)} of ${rowCount} records returned from active database.</div>
        `;
      }
      container.innerHTML = tableHtml;
      return;
    } else {
      container.innerHTML = `
        <div style="background:#7f1d1d; border:1px solid #dc2626; padding:12px; border-radius:6px; color:#fca5a5; font-size:0.85rem;">
          ❌ Database Execution Error: ${escapeHtml(realExecResult.error || "Execution failed.")}
        </div>
      `;
      return;
    }
  }

  // If backend is offline or execution not run
  container.innerHTML = `
    <div style="background:#1e293b; border:1px solid #334155; padding:12px; border-radius:6px; color:#94a3b8; font-size:0.85rem;">
      ℹ️ Database Execution Sandbox: Start the Python backend (<code>python server.py</code>) to execute read-only queries against the live SQLite relational sandbox (10k records).
    </div>
  `;
}

function renderQueryHistory() {
  const container = document.getElementById("query-history-container");
  if (!container) return;

  if (STATE.queryHistory.length === 0) {
    container.innerHTML = `<span style="color:#64748b; font-size:12px;">No recent queries.</span>`;
    return;
  }

  container.innerHTML = STATE.queryHistory.map((q, idx) => `
    <button class="btn-ctrl" style="font-family:var(--font-mono); font-size:11px; margin-right:4px; margin-bottom:4px;" onclick="loadHistoryQuery(${idx})" title="${escapeHtml(q)}">
      ${idx + 1}. ${escapeHtml(q.slice(0, 32))}...
    </button>
  `).join("");
}

function loadHistoryQuery(idx) {
  const q = STATE.queryHistory[idx];
  if (!q) return;
  const editor = document.getElementById("sql-editor-input");
  if (editor) {
    editor.value = q;
    runPlaygroundEvaluation();
  }
}

// ===========================================================================
// 7. GRAMMAR VIEW & REFINEMENT SANDBOX
// ===========================================================================
function initGrammarSection() {
  const ebnfCodeEl = document.getElementById("ebnf-code-display");
  const searchInput = document.getElementById("grammar-search-input");
  const prodCountEl = document.getElementById("grammar-production-count");

  // Render EBNF
  function updateEbnfDisplay(filter = "") {
    let lines = (STATE.sessionGrammarRefined ? getRefinedEbnf() : LEARNED_EBNF).split("\n");
    if (filter) {
      lines = lines.filter(l => l.toLowerCase().includes(filter.toLowerCase()));
    }
    if (ebnfCodeEl) ebnfCodeEl.textContent = lines.join("\n");
  }

  if (ebnfCodeEl) updateEbnfDisplay();

  if (searchInput) {
    searchInput.addEventListener("input", e => {
      updateEbnfDisplay(e.target.value);
    });
  }

  // Refinement Sandbox Handlers
  const btnApprove = document.getElementById("btn-refine-approve");
  const btnReset = document.getElementById("btn-refine-reset");
  const btnDownloadGrammar = document.getElementById("btn-download-grammar");
  const refStatusBadge = document.getElementById("refinement-status-badge");

  if (btnApprove) {
    btnApprove.addEventListener("click", () => {
      STATE.sessionGrammarRefined = true;
      if (refStatusBadge) {
        refStatusBadge.className = "badge badge-accept";
        refStatusBadge.innerHTML = "STATUS: ACCEPTED (Session Refined)";
      }
      updateEbnfDisplay();
      btnApprove.disabled = true;
      btnApprove.innerHTML = "✓ Approved & Active in Session";
      // Re-run playground if active
      runPlaygroundEvaluation();
    });
  }

  if (btnReset) {
    btnReset.addEventListener("click", () => {
      STATE.sessionGrammarRefined = false;
      if (refStatusBadge) {
        refStatusBadge.className = "badge badge-reject";
        refStatusBadge.innerHTML = "STATUS: REJECTED (Unrefined)";
      }
      if (btnApprove) {
        btnApprove.disabled = false;
        btnApprove.innerHTML = "✅ Approve & Apply to Session Grammar";
      }
      updateEbnfDisplay();
      runPlaygroundEvaluation();
    });
  }

  if (btnDownloadGrammar) {
    btnDownloadGrammar.addEventListener("click", () => {
      const content = STATE.sessionGrammarRefined ? getRefinedEbnf() : LEARNED_EBNF;
      downloadFile(content, "learned.lark", "text/plain");
    });
  }
}

function getRefinedEbnf() {
  return LEARNED_EBNF
    .replace("AGG_FUNC.2: /(?i:AVG|MAX|MIN)/", "AGG_FUNC.2: /(?i:AVG|COUNT|MAX|MIN|SUM)/")
    .concat("\n\n// Session Refinement:\ndelete_stmt: \"DELETE\"i \"FROM\"i CNAME [where_clause]\n");
}

// ===========================================================================
// 8. RESULTS, FALSE-REJECTIONS, & BLOB DOWNLOADS
// ===========================================================================
function initResultsSection() {
  renderBenchmarkTable();
  renderFalseRejectionExplorer();

  // Download buttons
  const btnCsv = document.getElementById("btn-download-csv");
  const btnJson = document.getElementById("btn-download-json");

  if (btnCsv) {
    btnCsv.addEventListener("click", () => {
      const csvContent = convertToCsv(MODEL_COMPARISON);
      downloadFile(csvContent, "model_comparison.csv", "text/csv");
    });
  }

  if (btnJson) {
    btnJson.addEventListener("click", () => {
      const jsonStr = JSON.stringify(MODEL_COMPARISON, null, 2);
      downloadFile(jsonStr, "model_comparison.json", "application/json");
    });
  }
}

function renderBenchmarkTable() {
  const tbody = document.getElementById("benchmark-table-body");
  if (!tbody) return;

  tbody.innerHTML = MODEL_COMPARISON.map(m => `
    <tr>
      <td><strong>${escapeHtml(m["System / Paradigm"])}</strong><br><span style="font-size:11px; color:#94a3b8;">${escapeHtml(m["Technique"])}</span></td>
      <td><strong>${typeof m["Accuracy"] === "number" ? (m["Accuracy"] * 100).toFixed(2) + "%" : m["Accuracy"]}</strong></td>
      <td>${typeof m["Valid Acceptance (Recall)"] === "number" ? (m["Valid Acceptance (Recall)"] * 100).toFixed(2) + "%" : m["Valid Acceptance (Recall)"]}</td>
      <td>${typeof m["Invalid Rejection (Specificity)"] === "number" ? (m["Invalid Rejection (Specificity)"] * 100).toFixed(2) + "%" : m["Invalid Rejection (Specificity)"]}</td>
      <td>${typeof m["False Acceptance (FAR)"] === "number" ? (m["False Acceptance (FAR)"] * 100).toFixed(2) + "%" : m["False Acceptance (FAR)"]}</td>
      <td>${typeof m["False Rejection (FRR)"] === "number" ? (m["False Rejection (FRR)"] * 100).toFixed(2) + "%" : m["False Rejection (FRR)"]}</td>
      <td>${escapeHtml(m["Generates Parse Tree"])}</td>
    </tr>
  `).join("");
}

function renderFalseRejectionExplorer() {
  const container = document.getElementById("false-rejection-table-body");
  const filterSelect = document.getElementById("fr-template-filter");
  const searchInput = document.getElementById("fr-search-input");
  const countBadge = document.getElementById("fr-count-badge");

  if (!container) return;

  // Extract unique templates
  const templates = Array.from(new Set(FALSE_REJECTIONS.map(r => r.template_id))).sort();
  if (filterSelect && filterSelect.options.length <= 1) {
    templates.forEach(t => {
      const opt = document.createElement("option");
      opt.value = t;
      const count = FALSE_REJECTIONS.filter(r => r.template_id === t).length;
      opt.textContent = `${t} (${count} queries)`;
      filterSelect.appendChild(opt);
    });
  }

  function updateTable() {
    const filter = filterSelect ? filterSelect.value : "ALL";
    const search = searchInput ? searchInput.value.toLowerCase() : "";

    let filtered = FALSE_REJECTIONS.filter(r => {
      const matchTpl = filter === "ALL" || r.template_id === filter;
      const matchSearch = !search || r.query_text.toLowerCase().includes(search) || r.error_message.toLowerCase().includes(search);
      return matchTpl && matchSearch;
    });

    if (countBadge) countBadge.textContent = `${filtered.length} of ${FALSE_REJECTIONS.length} queries`;

    container.innerHTML = filtered.slice(0, 50).map(r => `
      <tr>
        <td><code>${escapeHtml(r.query_id)}</code></td>
        <td><span class="badge badge-warn">${escapeHtml(r.template_id)}</span></td>
        <td><code style="font-size:11px;">${escapeHtml(r.query_text)}</code></td>
        <td style="color:#f87171; font-size:11px;">${escapeHtml(r.error_message)}</td>
        <td>
          <button class="btn-ctrl" onclick="sendToPlayground('${escapeHtml(r.query_text)}')">
            Inspect in Demo
          </button>
        </td>
      </tr>
    `).join("");
  }

  if (filterSelect) filterSelect.addEventListener("change", updateTable);
  if (searchInput) searchInput.addEventListener("input", updateTable);
  updateTable();
}

function sendToPlayground(sql) {
  const editor = document.getElementById("sql-editor-input");
  if (editor) {
    editor.value = sql;
    const demoSec = document.getElementById("sec-demo");
    if (demoSec) demoSec.scrollIntoView({ behavior: "smooth" });
    runPlaygroundEvaluation();
  }
}

// Client-Side Blob File Downloader
function downloadFile(content, fileName, mimeType) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = fileName;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function convertToCsv(arr) {
  if (!arr || arr.length === 0) return "";
  const keys = Object.keys(arr[0]);
  const header = keys.join(",");
  const rows = arr.map(row => {
    return keys.map(k => {
      const val = row[k] === null || row[k] === undefined ? "" : String(row[k]);
      return `"${val.replace(/"/g, '""')}"`;
    }).join(",");
  });
  return [header, ...rows].join("\n");
}

// ===========================================================================
// 9. VIVA Q&A ACCORDION
// ===========================================================================
const VIVA_QUESTIONS = [
  {
    q: "1. Why does the Baseline Grammar have 100% accuracy while the Learned Grammar has 89.53%?",
    a: "The Baseline Grammar is an authoritative, hand-written ground truth reference authored by compiler engineers to encode the entire DSL specification. The Learned Grammar is automatically induced from training queries without human intervention. In our zero-leakage split, certain valid constructs (like COUNT aggregates in template V_AGG_02) appeared only in the held-out test split, explaining the difference."
  },
  {
    q: "2. Why is the False Rejection Rate (FRR) exactly 14.29% for the Learned Grammar?",
    a: "The held-out test set contains 840 valid queries. Exactly 120 of them belong to template V_AGG_02, which uses the aggregate function COUNT(*). Because our template-disjoint split placed all COUNT training templates in the test split, the induction engine never observed COUNT during training. 120 / 840 = exactly 14.2857% (14.29%). Once refined in the sandbox, FRR drops to 0%."
  },
  {
    q: "3. What is data leakage and how did AutoGrammar prevent it?",
    a: "Data leakage occurs when an induction model or classifier is evaluated on identical query templates it already memorized during training. AutoGrammar enforces a strict, template-disjoint split: template overlap between Train, Validation, and Test is verified to be 0 templates across all pairs."
  },
  {
    q: "4. Why use Grammar Induction instead of an end-to-end Neural Network / LLM / Classifier?",
    a: "Black-box classifiers (like TF-IDF or Neural Networks) provide probability scores but cannot guarantee 100% security rejection (in our benchmarks, the ML classifier falsely accepted 84% of invalid queries), cannot construct an AST parse tree, and cannot localize syntax errors to exact lines and columns."
  },
  {
    q: "5. What role does MySQL play versus the SQLite relational sandbox?",
    a: "The project is engineered for production deployment over MySQL 8.0+ via PyMySQL. For evaluator convenience, zero-setup environments, and offline testing, DatabaseManager automatically falls back to an in-memory SQLite relational sandbox loaded with all 10,000 synthetic Indian school records."
  },
  {
    q: "6. What Machine Learning techniques are used in AutoGrammar?",
    a: "The project employs: (1) An automatic structural pattern-mining and rule induction engine that discovers grammar skeletons, optionality, repetitions, and recursive subqueries; and (2) A TF-IDF (1–3 n-grams) + Logistic Regression statistical validity classifier used as an empirical comparative baseline."
  },
  {
    q: "7. Why is False Acceptance Rate (FAR) 0.0% for both grammar compilers?",
    a: "Unlike statistical models that produce false positives on malformed inputs, formal Context-Free Grammars are deterministic: invalid syntax cannot derive a parse tree under the grammar productions, guaranteeing that no malformed query ever reaches execution."
  },
  {
    q: "8. Why does the ML Classifier have such a low specificity (TNR = 16.01%)?",
    a: "Statistical n-gram classifiers look at token co-occurrences without understanding grammar structure. Malformed queries like 'SELECT * FROM marks WHERE marks_obtained > = 60' contain common SQL words ('SELECT', 'FROM', 'WHERE'), which fool the linear classifier into predicting high validity likelihood."
  },
  {
    q: "9. How does the Interactive Refinement Sandbox work?",
    a: "When an engineer provides a rejected valid query, the induction engine tokenizes it, extracts newly discovered tokens (e.g. COUNT), updates the candidate EBNF rule, and applies it to an in-memory session copy only upon explicit approval. It never modifies the committed grammar without confirmation."
  },
  {
    q: "10. What is the difference between production precision and production recall?",
    a: "Production precision measures the fraction of learned grammar rules that match the reference baseline (39 / 39 = 100%). Production recall measures the fraction of reference baseline rules successfully discovered by the induction engine (39 / 40 = 97.5%, missing only delete_stmt)."
  },
  {
    q: "11. Why is there a slight discrepancy in the F1 score reported in the README (0.9873 vs 0.961)?",
    a: "README's 0.9873 was computed across normalized rule headers (P=1.0, R=0.975 -> F1=0.9873). When terminal rules are indexed separately (37 shared out of 38 learned vs 39 baseline), raw F1 is 0.961. Both values are disclosed transparently in our documentation."
  },
  {
    q: "12. How does AutoGrammar ensure safe database execution in the playground?",
    a: "Every query must pass all 4 pipeline stages (Stage 0 Security Gate, Stage 1 Lexer, Stage 2 Parser, Stage 3 Semantics). Furthermore, execution is strictly hard-coded to read-only SELECT queries with a limit of 50 rows."
  }
];

function initVivaAccordion() {
  const container = document.getElementById("viva-accordion-container");
  if (!container) return;

  container.innerHTML = VIVA_QUESTIONS.map((item, idx) => `
    <div class="accordion-item" id="accordion-${idx}">
      <div class="accordion-header" onclick="toggleAccordion(${idx})">
        <span>${item.q}</span>
        <span class="acc-icon" style="color:#38bdf8; font-weight:bold;">+</span>
      </div>
      <div class="accordion-body">
        <p>${item.a}</p>
      </div>
    </div>
  `).join("");
}

function toggleAccordion(idx) {
  const item = document.getElementById(`accordion-${idx}`);
  if (!item) return;
  const wasActive = item.classList.contains("active");
  document.querySelectorAll(".accordion-item").forEach(el => {
    el.classList.remove("active");
    const icon = el.querySelector(".acc-icon");
    if (icon) icon.textContent = "+";
  });

  if (!wasActive) {
    item.classList.add("active");
    const icon = item.querySelector(".acc-icon");
    if (icon) icon.textContent = "−";
  }
}

// ===========================================================================
// 10. HELPER UTILITIES
// ===========================================================================
function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// Copy button generic
function copyTextToClipboard(text, btnElement) {
  navigator.clipboard.writeText(text).then(() => {
    const orig = btnElement.innerHTML;
    btnElement.innerHTML = "✓ Copied!";
    setTimeout(() => { btnElement.innerHTML = orig; }, 1500);
  });
}

// ===========================================================================
// INITIALIZATION ON DOM READY
// ===========================================================================
document.addEventListener("DOMContentLoaded", () => {
  // Update header/footer metadata from CONFIG
  const titleEls = document.querySelectorAll(".cfg-project-title");
  titleEls.forEach(el => el.textContent = CONFIG.projectTitle);

  const guideEl = document.getElementById("cfg-guide");
  if (guideEl) guideEl.textContent = CONFIG.guide;

  const teamEl = document.getElementById("cfg-team");
  if (teamEl) teamEl.textContent = CONFIG.teamMembers.join(", ");

  const instEl = document.getElementById("cfg-inst");
  if (instEl) instEl.textContent = CONFIG.institution;

  const yearEl = document.getElementById("cfg-year");
  if (yearEl) yearEl.textContent = CONFIG.academicYear;

  initTheme();
  initScrollSpy();
  initPresentationMode();
  initCountUpNumbers();
  initStepper();
  initPipelineCards();
  initPlayground();
  initGrammarSection();
  initResultsSection();
  initVivaAccordion();

  // Initialize hand-written SVG charts
  if (typeof initAllCharts === "function") {
    initAllCharts();
  }

  // Probe real Python compiler backend status
  checkBackendHealth().then(() => {
    if (BACKEND_ONLINE) {
      runPlaygroundEvaluation();
    }
  });
});
