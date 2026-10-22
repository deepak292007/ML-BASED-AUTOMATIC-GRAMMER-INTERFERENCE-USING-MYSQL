/**
 * AutoGrammar Hand-Written Inline SVG Chart & Diagram Generator (site/js/charts.js)
 * Standalone vanilla SVG generator for:
 *   1. Template-Disjoint Split Venn / Partition diagram (zero-leakage verification)
 *   2. Relational Entity-Relationship (ER) Diagram for school_db
 *   3. 3-System Metric Bar Charts (Accuracy, TPR, TNR, FAR, FRR)
 *   4. Side-by-side Confusion Matrix Heatmaps
 *   5. Per-category Invalid Rejection Horizontal Bar Chart
 *   6. Induction Learning Curve with interactive SVG tooltips
 */

// ===========================================================================
// 1. TEMPLATE-DISJOINT SPLIT PARTITION DIAGRAM (ZERO LEAKAGE)
// ===========================================================================
function renderSplitDiagram() {
  const container = document.getElementById("split-diagram-container");
  if (!container) return;

  const svg = `
  <svg viewBox="0 0 880 220" width="100%" height="auto" xmlns="http://www.w3.org/2000/svg" style="background:#0f172a; border-radius:8px; border:1px solid #334155;">
    <defs>
      <linearGradient id="trainGrad" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="#0284c7" stop-opacity="0.3"/>
        <stop offset="100%" stop-color="#0369a1" stop-opacity="0.1"/>
      </linearGradient>
      <linearGradient id="valGrad" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="#d97706" stop-opacity="0.3"/>
        <stop offset="100%" stop-color="#b45309" stop-opacity="0.1"/>
      </linearGradient>
      <linearGradient id="testGrad" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="#10b981" stop-opacity="0.3"/>
        <stop offset="100%" stop-color="#059669" stop-opacity="0.1"/>
      </linearGradient>
    </defs>

    <!-- Train Box -->
    <rect x="30" y="30" width="250" height="150" rx="8" fill="url(#trainGrad)" stroke="#38bdf8" stroke-width="2"/>
    <text x="50" y="65" fill="#38bdf8" font-size="16" font-weight="700">TRAIN SPLIT (70%)</text>
    <text x="50" y="95" fill="#f8fafc" font-size="24" font-weight="800">4,826 Queries</text>
    <text x="50" y="125" fill="#94a3b8" font-size="13">29 Distinct Templates</text>
    <text x="50" y="145" fill="#cbd5e1" font-size="12">3,440 Valid • 1,386 Invalid</text>
    <rect x="50" y="155" width="110" height="18" rx="4" fill="#0284c7" opacity="0.3"/>
    <text x="55" y="168" fill="#7dd3fc" font-size="10" font-weight="600">INDUCTION CORPUS</text>

    <!-- Wall 1: Disjoint Barrier -->
    <line x1="300" y1="40" x2="300" y2="170" stroke="#ef4444" stroke-width="2" stroke-dasharray="4,4"/>
    <circle cx="300" cy="105" r="14" fill="#1e293b" stroke="#ef4444" stroke-width="2"/>
    <text x="300" y="110" fill="#ef4444" font-size="12" font-weight="bold" text-anchor="middle">0</text>

    <!-- Val Box -->
    <rect x="320" y="30" width="240" height="150" rx="8" fill="url(#valGrad)" stroke="#f59e0b" stroke-width="2"/>
    <text x="340" y="65" fill="#fbbf24" font-size="16" font-weight="700">VAL SPLIT (15%)</text>
    <text x="340" y="95" fill="#f8fafc" font-size="24" font-weight="800">1,028 Queries</text>
    <text x="340" y="125" fill="#94a3b8" font-size="13">19 Distinct Templates</text>
    <text x="340" y="145" fill="#cbd5e1" font-size="12">720 Valid • 308 Invalid</text>
    <rect x="340" y="155" width="120" height="18" rx="4" fill="#d97706" opacity="0.3"/>
    <text x="345" y="168" fill="#fde68a" font-size="10" font-weight="600">TUNING & SELECTION</text>

    <!-- Wall 2: Disjoint Barrier -->
    <line x1="580" y1="40" x2="580" y2="170" stroke="#ef4444" stroke-width="2" stroke-dasharray="4,4"/>
    <circle cx="580" cy="105" r="14" fill="#1e293b" stroke="#ef4444" stroke-width="2"/>
    <text x="580" y="110" fill="#ef4444" font-size="12" font-weight="bold" text-anchor="middle">0</text>

    <!-- Test Box -->
    <rect x="600" y="30" width="250" height="150" rx="8" fill="url(#testGrad)" stroke="#10b981" stroke-width="2"/>
    <text x="620" y="65" fill="#34d399" font-size="16" font-weight="700">HELD-OUT TEST (15%)</text>
    <text x="620" y="95" fill="#f8fafc" font-size="24" font-weight="800">1,146 Queries</text>
    <text x="620" y="125" fill="#94a3b8" font-size="13">20 Distinct Templates</text>
    <text x="620" y="145" fill="#cbd5e1" font-size="12">840 Valid • 306 Invalid</text>
    <rect x="620" y="155" width="130" height="18" rx="4" fill="#059669" opacity="0.3"/>
    <text x="625" y="168" fill="#a7f3d0" font-size="10" font-weight="600">FINAL BENCHMARK</text>

    <!-- Bottom Banner -->
    <text x="440" y="202" fill="#34d399" font-size="13" font-weight="700" text-anchor="middle">
      ✓ STRICT ZERO-LEAKAGE CONFIRMED: Template Overlap = 0 across Train, Validation, and Test
    </text>
  </svg>
  `;
  container.innerHTML = svg;
}

// ===========================================================================
// 2. RELATIONAL ER DIAGRAM FOR school_db
// ===========================================================================
function renderErDiagram() {
  const container = document.getElementById("er-diagram-container");
  if (!container) return;

  const svg = `
  <svg viewBox="0 0 960 440" width="100%" height="auto" xmlns="http://www.w3.org/2000/svg" style="background:#0b1120; border-radius:8px; border:1px solid #1e293b;">
    <defs>
      <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1 L 10 5 L 0 9 z" fill="#38bdf8"/>
      </marker>
    </defs>

    <!-- Entity: subjects -->
    <g transform="translate(40, 40)">
      <rect width="180" height="100" rx="6" fill="#1e293b" stroke="#0284c7" stroke-width="2"/>
      <rect width="180" height="28" rx="6" fill="#0284c7"/>
      <text x="10" y="20" fill="#ffffff" font-size="14" font-weight="bold">subjects (6)</text>
      <text x="10" y="52" fill="#fbbf24" font-size="12">🔑 subject_id (INT)</text>
      <text x="10" y="74" fill="#cbd5e1" font-size="12">subject_name (VARCHAR)</text>
    </g>

    <!-- Entity: teachers -->
    <g transform="translate(390, 40)">
      <rect width="180" height="130" rx="6" fill="#1e293b" stroke="#0284c7" stroke-width="2"/>
      <rect width="180" height="28" rx="6" fill="#0284c7"/>
      <text x="10" y="20" fill="#ffffff" font-size="14" font-weight="bold">teachers (40)</text>
      <text x="10" y="52" fill="#fbbf24" font-size="12">🔑 teacher_id (INT)</text>
      <text x="10" y="74" fill="#cbd5e1" font-size="12">first_name, last_name</text>
      <text x="10" y="96" fill="#38bdf8" font-size="12">🔗 subject_id (FK)</text>
    </g>

    <!-- Entity: classes -->
    <g transform="translate(740, 40)">
      <rect width="180" height="130" rx="6" fill="#1e293b" stroke="#0284c7" stroke-width="2"/>
      <rect width="180" height="28" rx="6" fill="#0284c7"/>
      <text x="10" y="20" fill="#ffffff" font-size="14" font-weight="bold">classes (7)</text>
      <text x="10" y="52" fill="#fbbf24" font-size="12">🔑 class_id (INT)</text>
      <text x="10" y="74" fill="#cbd5e1" font-size="12">class_name, year</text>
      <text x="10" y="96" fill="#38bdf8" font-size="12">🔗 class_teacher_id (FK)</text>
    </g>

    <!-- Entity: students -->
    <g transform="translate(740, 250)">
      <rect width="180" height="150" rx="6" fill="#1e293b" stroke="#0284c7" stroke-width="2"/>
      <rect width="180" height="28" rx="6" fill="#0284c7"/>
      <text x="10" y="20" fill="#ffffff" font-size="14" font-weight="bold">students (10,000)</text>
      <text x="10" y="52" fill="#fbbf24" font-size="12">🔑 student_id (INT)</text>
      <text x="10" y="74" fill="#cbd5e1" font-size="12">admission_no, names</text>
      <text x="10" y="96" fill="#38bdf8" font-size="12">🔗 class_id (FK)</text>
      <text x="10" y="118" fill="#cbd5e1" font-size="12">city, state, status</text>
    </g>

    <!-- Entity: marks -->
    <g transform="translate(390, 250)">
      <rect width="180" height="150" rx="6" fill="#1e293b" stroke="#0284c7" stroke-width="2"/>
      <rect width="180" height="28" rx="6" fill="#0284c7"/>
      <text x="10" y="20" fill="#ffffff" font-size="14" font-weight="bold">marks (6,031)</text>
      <text x="10" y="52" fill="#fbbf24" font-size="12">🔑 mark_id (INT)</text>
      <text x="10" y="74" fill="#38bdf8" font-size="12">🔗 student_id (FK)</text>
      <text x="10" y="96" fill="#38bdf8" font-size="12">🔗 subject_id (FK)</text>
      <text x="10" y="118" fill="#cbd5e1" font-size="12">marks_obtained, exam_date</text>
    </g>

    <!-- Entity: attendance -->
    <g transform="translate(40, 250)">
      <rect width="180" height="130" rx="6" fill="#1e293b" stroke="#0284c7" stroke-width="2"/>
      <rect width="180" height="28" rx="6" fill="#0284c7"/>
      <text x="10" y="20" fill="#ffffff" font-size="14" font-weight="bold">attendance (6,000)</text>
      <text x="10" y="52" fill="#fbbf24" font-size="12">🔑 attendance_id (INT)</text>
      <text x="10" y="74" fill="#38bdf8" font-size="12">🔗 student_id (FK)</text>
      <text x="10" y="96" fill="#cbd5e1" font-size="12">attendance_date, status</text>
    </g>

    <!-- Relationship Lines -->
    <!-- teachers -> subjects -->
    <path d="M 390 90 L 220 90" stroke="#38bdf8" stroke-width="2" marker-end="url(#arrow)"/>
    <!-- classes -> teachers -->
    <path d="M 740 90 L 570 90" stroke="#38bdf8" stroke-width="2" marker-end="url(#arrow)"/>
    <!-- students -> classes -->
    <path d="M 830 250 L 830 170" stroke="#38bdf8" stroke-width="2" marker-end="url(#arrow)"/>
    <!-- marks -> students -->
    <path d="M 570 325 L 740 325" stroke="#38bdf8" stroke-width="2" marker-end="url(#arrow)"/>
    <!-- marks -> subjects -->
    <path d="M 450 250 L 450 210 L 130 210 L 130 140" stroke="#38bdf8" stroke-width="2" fill="none" marker-end="url(#arrow)"/>
    <!-- attendance -> students -->
    <path d="M 220 325 L 390 325" stroke="#38bdf8" stroke-width="2" marker-end="url(#arrow)"/>
  </svg>
  `;
  container.innerHTML = svg;
}

// ===========================================================================
// 3. COMPARATIVE BENCHMARK BAR CHARTS
// ===========================================================================
function renderBenchmarkBarChart() {
  const container = document.getElementById("benchmark-chart-container");
  if (!container) return;

  const data = [
    { label: "Overall Accuracy", baseline: 100.0, learned: 89.53, ml: 66.67 },
    { label: "Valid Acceptance (TPR)", baseline: 100.0, learned: 85.71, ml: 85.12 },
    { label: "Invalid Rejection (TNR)", baseline: 100.0, learned: 100.0, ml: 16.01 },
    { label: "False Acceptance (FAR)", baseline: 0.0, learned: 0.0, ml: 83.99 },
    { label: "False Rejection (FRR)", baseline: 0.0, learned: 14.29, ml: 14.88 }
  ];

  const svgH = 320;
  const svgW = 760;
  const margin = { top: 30, right: 30, bottom: 40, left: 180 };
  const chartW = svgW - margin.left - margin.right;
  const groupH = (svgH - margin.top - margin.bottom) / data.length;

  let barsHtml = "";
  data.forEach((d, idx) => {
    const y0 = margin.top + idx * groupH;
    const barH = 12;

    const wBase = (d.baseline / 100) * chartW;
    const wLearn = (d.learned / 100) * chartW;
    const wMl = (d.ml / 100) * chartW;

    barsHtml += `
      <text x="${margin.left - 12}" y="${y0 + 24}" fill="#cbd5e1" font-size="12" font-weight="600" text-anchor="end">${d.label}</text>
      
      <!-- Baseline Bar -->
      <rect x="${margin.left}" y="${y0 + 2}" width="${wBase}" height="${barH}" rx="3" fill="#38bdf8"/>
      <text x="${margin.left + wBase + 6}" y="${y0 + 12}" fill="#38bdf8" font-size="10" font-weight="bold">${d.baseline.toFixed(1)}%</text>

      <!-- Learned Bar -->
      <rect x="${margin.left}" y="${y0 + 17}" width="${wLearn}" height="${barH}" rx="3" fill="#10b981"/>
      <text x="${margin.left + wLearn + 6}" y="${y0 + 27}" fill="#10b981" font-size="10" font-weight="bold">${d.learned.toFixed(1)}%</text>

      <!-- ML Bar -->
      <rect x="${margin.left}" y="${y0 + 32}" width="${wMl}" height="${barH}" rx="3" fill="#a855f7"/>
      <text x="${margin.left + wMl + 6}" y="${y0 + 42}" fill="#c084fc" font-size="10" font-weight="bold">${d.ml.toFixed(1)}%</text>
    `;
  });

  const svg = `
  <svg viewBox="0 0 ${svgW} ${svgH}" width="100%" height="auto" xmlns="http://www.w3.org/2000/svg" style="background:#0f172a; border-radius:8px; border:1px solid #334155;">
    <!-- Legend -->
    <rect x="${margin.left}" y="10" width="12" height="10" fill="#38bdf8" rx="2"/>
    <text x="${margin.left + 18}" y="19" fill="#cbd5e1" font-size="11">Baseline Grammar</text>

    <rect x="${margin.left + 160}" y="10" width="12" height="10" fill="#10b981" rx="2"/>
    <text x="${margin.left + 178}" y="19" fill="#cbd5e1" font-size="11">Learned Grammar</text>

    <rect x="${margin.left + 310}" y="10" width="12" height="10" fill="#a855f7" rx="2"/>
    <text x="${margin.left + 328}" y="19" fill="#cbd5e1" font-size="11">ML Baseline Classifier</text>

    <!-- Gridlines -->
    ${[0, 25, 50, 75, 100].map(pct => {
      const x = margin.left + (pct / 100) * chartW;
      return `
        <line x1="${x}" y1="${margin.top}" x2="${x}" y2="${svgH - margin.bottom}" stroke="#334155" stroke-dasharray="2,2"/>
        <text x="${x}" y="${svgH - margin.bottom + 18}" fill="#64748b" font-size="10" text-anchor="middle">${pct}%</text>
      `;
    }).join("")}

    ${barsHtml}
  </svg>
  `;
  container.innerHTML = svg;
}

// ===========================================================================
// 4. CONFUSION MATRIX HEATMAPS (SIDE-BY-SIDE)
// ===========================================================================
function renderConfusionMatrices() {
  const container = document.getElementById("confusion-matrices-container");
  if (!container) return;

  const matrices = [
    { title: "1. Baseline Grammar (Reference)", tp: 840, tn: 306, fp: 0, fn: 0, color: "#38bdf8" },
    { title: "2. Learned Grammar (AutoGrammar)", tp: 720, tn: 306, fp: 0, fn: 120, color: "#10b981" },
    { title: "3. ML Classifier (TF-IDF + LogReg)", tp: 715, tn: 49, fp: 257, fn: 125, color: "#a855f7" }
  ];

  let html = `<div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap:16px;">`;

  matrices.forEach(m => {
    html += `
    <div style="background:#1e293b; border:1px solid #334155; border-radius:8px; padding:14px; text-align:center;">
      <div style="font-size:13px; font-weight:700; color:${m.color}; margin-bottom:10px;">${m.title}</div>
      <table style="width:100%; border-collapse:collapse; font-size:12px; color:#e2e8f0;">
        <thead>
          <tr style="border-bottom:1px solid #475569;">
            <th style="padding:6px;">Actual \\ Pred</th>
            <th style="padding:6px; color:#34d399;">ACCEPT</th>
            <th style="padding:6px; color:#f87171;">REJECT</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td style="padding:8px; font-weight:600; text-align:left;">Valid (840)</td>
            <td style="background:#064e3b; color:#34d399; font-weight:bold; padding:8px; border-radius:4px;">
              TP: ${m.tp}<br><span style="font-size:10px; font-weight:normal;">(${(m.tp / 840 * 100).toFixed(1)}%)</span>
            </td>
            <td style="background:#7f1d1d; color:#fca5a5; font-weight:bold; padding:8px; border-radius:4px;">
              FN: ${m.fn}<br><span style="font-size:10px; font-weight:normal;">(${(m.fn / 840 * 100).toFixed(1)}%)</span>
            </td>
          </tr>
          <tr>
            <td style="padding:8px; font-weight:600; text-align:left;">Invalid (306)</td>
            <td style="background:${m.fp > 0 ? '#7f1d1d' : '#0f172a'}; color:${m.fp > 0 ? '#fca5a5' : '#64748b'}; font-weight:bold; padding:8px; border-radius:4px;">
              FP: ${m.fp}<br><span style="font-size:10px; font-weight:normal;">(${(m.fp / 306 * 100).toFixed(1)}%)</span>
            </td>
            <td style="background:#064e3b; color:#34d399; font-weight:bold; padding:8px; border-radius:4px;">
              TN: ${m.tn}<br><span style="font-size:10px; font-weight:normal;">(${(m.tn / 306 * 100).toFixed(1)}%)</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    `;
  });

  html += `</div>`;
  container.innerHTML = html;
}

// ===========================================================================
// 5. PER-CATEGORY REJECTION HORIZONTAL BARS
// ===========================================================================
function renderCategoryBreakdownChart() {
  const container = document.getElementById("category-chart-container");
  if (!container) return;

  const categories = [
    { name: "Double Operator (Lexical/Syntax)", count: 77, compilerRej: 100.0, mlRej: 16.0 },
    { name: "Missing Table Name (Syntax)", count: 77, compilerRej: 100.0, mlRej: 15.6 },
    { name: "Missing SET in UPDATE (Syntax)", count: 77, compilerRej: 100.0, mlRej: 15.6 },
    { name: "Unsupported CTE (Syntax/Dialect)", count: 75, compilerRej: 100.0, mlRej: 16.0 }
  ];

  let rowsHtml = "";
  categories.forEach(c => {
    rowsHtml += `
    <div style="margin-bottom:14px;">
      <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:4px;">
        <span style="font-weight:600; color:#e2e8f0;">${c.name} (${c.count} queries)</span>
        <span>
          <strong style="color:#10b981;">Compilers: 100% Rejection</strong> &nbsp;|&nbsp; 
          <strong style="color:#f87171;">ML: ${c.mlRej.toFixed(1)}% Rejection (${(100 - c.mlRej).toFixed(1)}% bypassed!)</strong>
        </span>
      </div>
      <div style="background:#1e293b; height:18px; border-radius:4px; overflow:hidden; position:relative;">
        <div style="width:100%; height:100%; background:#10b981; opacity:0.35;"></div>
        <div style="width:${c.mlRej}%; height:100%; background:#ef4444; position:absolute; top:0; left:0;"></div>
      </div>
    </div>
    `;
  });

  container.innerHTML = rowsHtml;
}

// ===========================================================================
// 6. INDUCTION LEARNING CURVE LINE CHART (SVG WITH HOVER TOOLTIPS)
// ===========================================================================
function renderLearningCurveChart() {
  const container = document.getElementById("learning-curve-container");
  if (!container) return;

  const data = LEARNING_CURVE || [
    { template_percentage: 10, accuracy: 0.7906, tpr: 0.7143, frr: 0.2857 },
    { template_percentage: 25, accuracy: 0.7906, tpr: 0.7143, frr: 0.2857 },
    { template_percentage: 50, accuracy: 0.7906, tpr: 0.7143, frr: 0.2857 },
    { template_percentage: 75, accuracy: 0.7906, tpr: 0.7143, frr: 0.2857 },
    { template_percentage: 100, accuracy: 0.8953, tpr: 0.8571, frr: 0.1429 }
  ];

  const svgW = 760;
  const svgH = 280;
  const margin = { top: 30, right: 40, bottom: 40, left: 60 };
  const plotW = svgW - margin.left - margin.right;
  const plotH = svgH - margin.top - margin.bottom;

  // Scales
  const getX = pct => margin.left + ((pct - 10) / (100 - 10)) * plotW;
  const getY = val => margin.top + (1 - val) * plotH;

  // Polyline points
  const accPoints = data.map(d => `${getX(d.template_percentage)},${getY(d.accuracy)}`).join(" ");
  const frrPoints = data.map(d => `${getX(d.template_percentage)},${getY(d.frr)}`).join(" ");

  let circlesHtml = "";
  data.forEach(d => {
    const cx = getX(d.template_percentage);
    const cyAcc = getY(d.accuracy);
    const cyFrr = getY(d.frr);

    circlesHtml += `
      <!-- Accuracy Dot -->
      <circle cx="${cx}" cy="${cyAcc}" r="5" fill="#38bdf8" stroke="#0f172a" stroke-width="2">
        <title>Templates: ${d.template_percentage}%\nAccuracy: ${(d.accuracy * 100).toFixed(2)}%</title>
      </circle>
      <text x="${cx}" y="${cyAcc - 10}" fill="#38bdf8" font-size="10" font-weight="bold" text-anchor="middle">
        ${(d.accuracy * 100).toFixed(1)}%
      </text>

      <!-- FRR Dot -->
      <circle cx="${cx}" cy="${cyFrr}" r="5" fill="#ef4444" stroke="#0f172a" stroke-width="2">
        <title>Templates: ${d.template_percentage}%\nFRR: ${(d.frr * 100).toFixed(2)}%</title>
      </circle>
      <text x="${cx}" y="${cyFrr + 16}" fill="#f87171" font-size="10" font-weight="bold" text-anchor="middle">
        ${(d.frr * 100).toFixed(1)}%
      </text>
    `;
  });

  const svg = `
  <svg viewBox="0 0 ${svgW} ${svgH}" width="100%" height="auto" xmlns="http://www.w3.org/2000/svg" style="background:#0f172a; border-radius:8px; border:1px solid #334155;">
    <!-- Grid -->
    ${[0, 20, 40, 60, 80, 100].map(v => {
      const y = getY(v / 100);
      return `
        <line x1="${margin.left}" y1="${y}" x2="${svgW - margin.right}" y2="${y}" stroke="#1e293b" stroke-dasharray="2,2"/>
        <text x="${margin.left - 8}" y="${y + 4}" fill="#64748b" font-size="10" text-anchor="end">${v}%</text>
      `;
    }).join("")}

    <!-- X Axis labels -->
    ${data.map(d => {
      const x = getX(d.template_percentage);
      return `<text x="${x}" y="${svgH - 12}" fill="#94a3b8" font-size="11" font-weight="600" text-anchor="middle">${d.template_percentage}%</text>`;
    }).join("")}
    <text x="${svgW / 2}" y="${svgH - 2}" fill="#64748b" font-size="10" text-anchor="middle">% of Training Templates Included</text>

    <!-- Legend -->
    <line x1="${margin.left}" y1="14" x2="${margin.left + 24}" y2="14" stroke="#38bdf8" stroke-width="2.5"/>
    <circle cx="${margin.left + 12}" cy="14" r="3.5" fill="#38bdf8"/>
    <text x="${margin.left + 32}" y="18" fill="#cbd5e1" font-size="11">Overall Generalization Accuracy (%)</text>

    <line x1="${margin.left + 260}" y1="14" x2="${margin.left + 284}" y2="14" stroke="#ef4444" stroke-width="2" stroke-dasharray="4,4"/>
    <circle cx="${margin.left + 272}" cy="14" r="3.5" fill="#ef4444"/>
    <text x="${margin.left + 292}" y="18" fill="#cbd5e1" font-size="11">False Rejection Rate (FRR %)</text>

    <!-- Lines -->
    <polyline points="${accPoints}" fill="none" stroke="#38bdf8" stroke-width="2.5"/>
    <polyline points="${frrPoints}" fill="none" stroke="#ef4444" stroke-width="2" stroke-dasharray="4,4"/>

    ${circlesHtml}
  </svg>
  `;
  container.innerHTML = svg;
}

// Global initialization for all charts
function initAllCharts() {
  renderSplitDiagram();
  renderErDiagram();
  renderBenchmarkBarChart();
  renderConfusionMatrices();
  renderCategoryBreakdownChart();
  renderLearningCurveChart();
}
