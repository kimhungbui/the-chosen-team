// ==========================================================================
// Proposal Scorer & Reviewer - Frontend Application Logic
// ==========================================================================

let appState = {
  currentVariant: 'response_1_weak.md',
  samples: {},
  report: null,
  activeCitationIndex: 0
};

// Architecture Stage Details
const stageDetails = {
  rfp_extractor: {
    title: "🔍 Stage 1: RFP Requirements Extractor Agent",
    badge: "Agno Agent 1",
    content: `
      <p>The <strong>RFPExtractorAgent</strong> ingests the client's Request for Proposal (RFP) in isolation to eliminate confirmation bias.</p>
      <ul>
        <li><strong>Deliverable Extraction:</strong> Parses core functional requirements (dashboards, low-stock alerts, multi-warehouse scopes).</li>
        <li><strong>Strict Negative Constraints:</strong> Specifically isolates non-negotiable boundaries (e.g. <em>"no migration to new database"</em>).</li>
        <li><strong>Commercial & Timeline Bounds:</strong> Captures budget ceilings (€80k–€120k) and phased deadlines (3-month pilot, 6-month rollout).</li>
        <li><strong>Client Psychology / Focus:</strong> Detects whether the client prioritizes rapid innovation or low operational risk.</li>
      </ul>
      <p><strong>Pydantic Output Schema:</strong> <code>RFPAnalysis(requirements: List[RFPRequirement], detected_client_priority: str)</code></p>
    `
  },
  compliance_auditor: {
    title: "📋 Stage 2: Procurement Compliance Auditor Agent",
    badge: "Agno Agent 2",
    content: `
      <p>The <strong>ComplianceAuditorAgent</strong> performs a systematic, matrix-based cross-audit between the RFP checklist and the draft proposal.</p>
      <ul>
        <li><strong>Requirement-by-Requirement Checklist:</strong> Evaluates every single extracted RFP requirement individually.</li>
        <li><strong>Compliance Classifications:</strong>
          <ul>
            <li><code>MET</code>: Unambiguously addressed with specific deliverables.</li>
            <li><code>PARTIALLY_MET</code>: Mentioned vaguely without operational depth.</li>
            <li><code>MISSING</code>: Omitted entirely from proposal.</li>
            <li><code>CONTRADICTED</code>: Explicitly violates an RFP constraint (e.g. proposes database migration).</li>
            <li><code>DEFERRED</code>: Kicks pricing or timeline down the road ("upon further discussion").</li>
          </ul>
        </li>
      </ul>
      <p><strong>Pydantic Output Schema:</strong> <code>ComplianceMatrix(items: List[RequirementAudit])</code></p>
    `
  },
  scorer_fixer: {
    title: "✍️ Stage 3: Senior Scorer and Fixer Agent",
    badge: "Agno Agent 3",
    content: `
      <p>Acting as an experienced pre-sales director, the <strong>ScorerAndFixerAgent</strong> grades the proposal and drafts concrete revisions.</p>
      <ul>
        <li><strong>7 Appendix A Rubrics:</strong> Scores Problem Understanding, Scope Clarity, Pricing, Timeline, Completeness, Tone, and Risk Transparency.</li>
        <li><strong>Concrete Replacement Drafting:</strong> Instead of generic advice (<em>"improve clarity"</em>), the agent writes the <strong>exact replacement paragraph</strong>, milestone table, or SLA clause.</li>
      </ul>
      <p><strong>Pydantic Output Schema:</strong> <code>ProposalReviewReport(criteria_scores: List[CriterionScore], actionable_fixes: List[SuggestedFix])</code></p>
    `
  },
  guardrails: {
    title: "🛡️ Stage 4: Python Deterministic Guardrail Engine (Method 4 Core)",
    badge: "Deterministic Post-Processing",
    content: `
      <p>The critical difference between Method 2 and Method 4. A non-LLM Python layer verifies outputs before rendering:</p>
      <ul>
        <li><strong>Verbatim Substring Search:</strong> Searches <code>rfp_text</code> and <code>proposal_text</code> for exact quotes, proving citations are 100% grounded and not hallucinated.</li>
        <li><strong>Exact Line Resolution:</strong> Resolves quotes to line numbers (e.g. <code>rfp_nordframe.md:L17</code>) to enable live side-by-side highlighting.</li>
        <li><strong>Mathematical Score Locking:</strong> Binds Completeness scores to exact compliance percentage formula: <code>Score = 1.0 + 4.0 * (Met + 0.5 * Partial) / Total</code>.</li>
        <li><strong>Fix Enforceability:</strong> Programmatically checks that suggested fixes are full, formatted draft paragraphs rather than generic advice.</li>
      </ul>
    `
  },
  dashboard_output: {
    title: "📊 Stage 5: Live Interactive Evaluation Dashboard",
    badge: "Frontend Experience",
    content: `
      <p>Presents an executive dashboard designed for live evaluation during hackathon judging:</p>
      <ul>
        <li><strong>Synchronized Traceability:</strong> Clicking any issue highlights the exact lines in both RFP and Proposal simultaneously.</li>
        <li><strong>One-Click Copy:</strong> Sales reps can copy drafted paragraphs directly into their proposal documents.</li>
        <li><strong>Live Multi-Scenario Testing:</strong> Switch between Weak, Medium, Strong, and Overpromising variants with one click.</li>
      </ul>
    `
  }
};

// Tab Switching
function switchTab(tabId) {
  document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

  const activeBtn = document.getElementById(`tab-btn-${tabId}`);
  const activeContent = document.getElementById(`tab-${tabId}`);

  if (activeBtn) activeBtn.classList.add('active');
  if (activeContent) activeContent.classList.add('active');

  if (tabId === 'inspector') {
    renderInspectorView();
  }
}

// Show Architecture Stage Details
function showStageDetails(stageKey) {
  const detail = stageDetails[stageKey];
  if (!detail) return;

  const titleEl = document.getElementById('stage-detail-title');
  const bodyEl = document.getElementById('stage-detail-content');

  titleEl.textContent = detail.title;
  bodyEl.innerHTML = detail.content;

  document.querySelectorAll('.diagram-stage').forEach(el => el.classList.remove('active'));
  const clicked = event.currentTarget;
  if (clicked) clicked.classList.add('active');
}

// Load Predefined Scenario
function loadScenario(variantFilename) {
  appState.currentVariant = variantFilename;

  // Update Scenario Buttons
  document.querySelectorAll('.btn-scenario').forEach(btn => btn.classList.remove('active'));
  if (variantFilename.includes('weak')) document.getElementById('btn-weak').classList.add('active');
  else if (variantFilename.includes('medium')) document.getElementById('btn-medium').classList.add('active');
  else if (variantFilename.includes('strong')) document.getElementById('btn-strong').classList.add('active');
  else if (variantFilename.includes('overpromise')) document.getElementById('btn-overpromise').classList.add('active');

  const proposalInput = document.getElementById('proposal-input');
  const proposalMeta = document.getElementById('proposal-meta');

  if (appState.samples && appState.samples.variants && appState.samples.variants[variantFilename]) {
    proposalInput.value = appState.samples.variants[variantFilename];
    proposalMeta.textContent = variantFilename;
  }

  // Auto run evaluation on scenario switch
  runEvaluation();
}

// Run Evaluation Pipeline
async function runEvaluation() {
  const rfpText = document.getElementById('rfp-input').value;
  const proposalText = document.getElementById('proposal-input').value;
  const loader = document.getElementById('eval-loader');
  const resultsWrapper = document.getElementById('results-wrapper');
  const runBtn = document.getElementById('run-eval-btn');

  loader.classList.remove('hidden');
  resultsWrapper.style.opacity = '0.3';
  runBtn.disabled = true;

  // Animate steps
  const steps = [
    document.getElementById('step-1'),
    document.getElementById('step-2'),
    document.getElementById('step-3'),
    document.getElementById('step-4')
  ];

  let currentStep = 0;
  const stepInterval = setInterval(() => {
    steps.forEach((s, i) => {
      s.classList.toggle('active', i === currentStep);
    });
    currentStep = (currentStep + 1) % steps.length;
  }, 400);

  try {
    const response = await fetch('/api/evaluate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        rfp: rfpText,
        proposal: proposalText,
        variant: appState.currentVariant
      })
    });

    if (!response.ok) {
      throw new Error(`Server returned ${response.status}`);
    }

    const report = await response.json();
    appState.report = report;
    renderResults(report);
  } catch (err) {
    console.warn('API call failed or running in static mode, using fallback handler:', err);
    // If backend unavailable, render fallback client-side
    renderFallbackData();
  } finally {
    clearInterval(stepInterval);
    steps.forEach(s => s.classList.remove('active'));
    loader.classList.add('hidden');
    resultsWrapper.style.opacity = '1';
    runBtn.disabled = false;
  }
}

// Render Results on Dashboard
function renderResults(report) {
  // Score & Verdict
  const scoreNumEl = document.getElementById('score-number');
  const verdictPillEl = document.getElementById('verdict-pill');
  const scoreRingEl = document.querySelector('.score-ring');

  scoreNumEl.textContent = report.overall_score.toFixed(1);

  let verdictText = report.readiness_verdict.replace(/_/g, ' ');
  let verdictClass = 'badge-danger';
  let ringColor = 'var(--color-danger)';

  if (report.overall_score >= 4.0) {
    verdictText = '🟢 ' + verdictText;
    verdictClass = 'badge-success';
    ringColor = 'var(--color-success)';
  } else if (report.overall_score >= 2.5) {
    verdictText = '🟡 ' + verdictText;
    verdictClass = 'badge-warning';
    ringColor = 'var(--color-warning)';
  } else {
    verdictText = '🔴 ' + verdictText;
    verdictClass = 'badge-danger';
    ringColor = 'var(--color-danger)';
  }

  verdictPillEl.textContent = verdictText;
  verdictPillEl.className = `verdict-pill ${verdictClass}`;
  scoreRingEl.style.borderColor = ringColor;
  scoreRingEl.style.boxShadow = `0 0 25px ${ringColor}44`;

  // Priorities & Summary
  document.getElementById('detected-priorities').textContent = report.detected_client_priorities || 'Low operational risk & continuity.';
  document.getElementById('verdict-summary').textContent = report.verdict_summary || 'Evaluation completed.';

  // 7 Core Criteria Cards
  const criteriaGrid = document.getElementById('criteria-grid');
  criteriaGrid.innerHTML = '';

  report.criteria_scores.forEach(item => {
    const card = document.createElement('div');
    card.className = 'criterion-card';

    let scoreColor = 'var(--color-danger)';
    if (item.score >= 4.0) scoreColor = 'var(--color-success)';
    else if (item.score >= 2.5) scoreColor = 'var(--color-warning)';

    const percent = Math.min(100, (item.score / 5.0) * 100);

    card.innerHTML = `
      <div class="criterion-top">
        <span class="criterion-name">${item.criterion}</span>
        <span class="criterion-score-badge" style="color: ${scoreColor}; background: ${scoreColor}22; border: 1px solid ${scoreColor}55;">
          ${item.score.toFixed(1)} / 5.0
        </span>
      </div>
      <div class="meter-track">
        <div class="meter-fill" style="width: ${percent}%; background: ${scoreColor};"></div>
      </div>
      <p class="criterion-comment">${item.comment}</p>
    `;
    criteriaGrid.appendChild(card);
  });

  // Compliance Matrix Table
  const tbody = document.getElementById('compliance-table-body');
  tbody.innerHTML = '';

  const metCount = report.compliance_matrix.filter(i => i.status === 'MET').length;
  const totalCount = report.compliance_matrix.length;
  document.getElementById('compliance-stats').innerHTML = `
    <span class="badge badge-tech">Total Requirements: ${totalCount}</span>
    <span class="badge badge-guardrail">Requirements Met: ${metCount}/${totalCount}</span>
  `;

  report.compliance_matrix.forEach((item, index) => {
    const tr = document.createElement('tr');

    let statusPillClass = 'missing';
    let statusLabel = '❌ Missing';
    if (item.status === 'MET') { statusPillClass = 'met'; statusLabel = '✅ Met'; }
    else if (item.status === 'PARTIALLY_MET') { statusPillClass = 'partial'; statusLabel = '⚠️ Partial'; }
    else if (item.status === 'CONTRADICTED') { statusPillClass = 'contradicted'; statusLabel = '🚫 Contradicted'; }
    else if (item.status === 'DEFERRED') { statusPillClass = 'deferred'; statusLabel = '⏳ Deferred'; }

    tr.innerHTML = `
      <td><strong>${item.requirement_id}</strong></td>
      <td>${item.requirement_title}</td>
      <td><span class="status-pill ${statusPillClass}">${statusLabel}</span></td>
      <td>${item.gap_analysis}</td>
      <td>
        <button class="source-link-btn" onclick="jumpToGrounding(${index})">
          Trace Quote ➔
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });

  // Actionable Fixes
  const fixesContainer = document.getElementById('fixes-container');
  fixesContainer.innerHTML = '';

  if (!report.actionable_fixes || report.actionable_fixes.length === 0) {
    fixesContainer.innerHTML = `
      <div class="fix-card" style="text-align: center; color: var(--color-success);">
        <h3>🎉 No Critical Flaws Detected!</h3>
        <p>This proposal comprehensively addresses the client RFP requirements and respects all stated constraints.</p>
      </div>
    `;
  } else {
    report.actionable_fixes.forEach((fix, idx) => {
      const card = document.createElement('div');
      card.className = 'fix-card';

      let pillClass = 'badge-danger';
      if (fix.category === 'DEFERRED') pillClass = 'badge-warning';
      else if (fix.category === 'VAGUE') pillClass = 'badge-warning';

      const severity = fix.severity || 'MAJOR';
      let sevClass = 'badge-danger';
      let sevIcon = '🔴';
      if (severity === 'MAJOR') { sevClass = 'badge-warning'; sevIcon = '🟡'; }
      else if (severity === 'MINOR') { sevClass = 'badge-tech'; sevIcon = '⚪'; }

      card.innerHTML = `
        <div class="fix-card-header">
          <div class="fix-title-group">
            <span class="fix-category-pill ${sevClass}">${sevIcon} ${severity}</span>
            <span class="fix-category-pill ${pillClass}">${fix.category}</span>
            <h3 class="fix-title">${fix.title}</h3>
          </div>
          ${fix.line_reference ? `<span class="citation-chip">📍 ${fix.line_reference}</span>` : ''}
        </div>

        <div class="fix-citations-row">
          <div><strong>RFP Citation:</strong> <em>"${fix.rfp_citation}"</em></div>
          <div><strong>Proposal Section:</strong> <em>${fix.proposal_citation}</em></div>
        </div>

        <p class="fix-problem-text">${fix.issue_description}</p>

        <div class="suggested-fix-box">
          <div class="fix-box-header">
            <span class="fix-label">Suggested Replacement (Ready to Insert)</span>
            <button class="btn-copy-fix" onclick="copyFixText(this, 'fix-code-${idx}')">
              📋 Copy Fix
            </button>
          </div>
          <pre class="fix-content" id="fix-code-${idx}">${fix.suggested_fix}</pre>
        </div>
      `;
      fixesContainer.appendChild(card);
    });
  }
}

// Copy Fix Text to Clipboard
function copyFixText(buttonEl, codeId) {
  const codeEl = document.getElementById(codeId);
  if (!codeEl) return;

  navigator.clipboard.writeText(codeEl.textContent).then(() => {
    const originalText = buttonEl.innerHTML;
    buttonEl.innerHTML = '✅ Copied!';
    buttonEl.style.background = 'var(--color-success)';
    buttonEl.style.color = '#000';
    setTimeout(() => {
      buttonEl.innerHTML = originalText;
      buttonEl.style.background = '';
      buttonEl.style.color = '';
    }, 2000);
  });
}

// Side-by-Side Grounding Inspector
function renderInspectorView() {
  const rfpText = document.getElementById('rfp-input').value;
  const proposalText = document.getElementById('proposal-input').value;

  renderNumberedLines('rfp-viewer-body', rfpText);
  renderNumberedLines('proposal-viewer-body', proposalText);

  // Populate finding list in sidebar
  const selectorList = document.getElementById('citation-selector-list');
  selectorList.innerHTML = '';

  if (!appState.report || !appState.report.actionable_fixes || appState.report.actionable_fixes.length === 0) {
    selectorList.innerHTML = `<p style="font-size:0.85rem; color:var(--text-muted);">No issues flagged in this proposal.</p>`;
    return;
  }

  appState.report.actionable_fixes.forEach((fix, index) => {
    const btn = document.createElement('button');
    btn.className = `citation-select-btn ${index === appState.activeCitationIndex ? 'active' : ''}`;
    btn.onclick = () => selectCitation(index);
    btn.innerHTML = `
      <strong>${fix.title}</strong>
      <span style="font-family:var(--font-mono); font-size:0.75rem; color:var(--color-primary);">${fix.line_reference || 'Match'}</span>
    `;
    selectorList.appendChild(btn);
  });

  // Select first item by default
  selectCitation(appState.activeCitationIndex || 0);
}

function renderNumberedLines(containerId, text) {
  const container = document.getElementById(containerId);
  container.innerHTML = '';

  const lines = text.split('\n');
  lines.forEach((line, idx) => {
    const lineNum = idx + 1;
    const lineDiv = document.createElement('div');
    lineDiv.className = 'doc-line';
    lineDiv.id = `${containerId}-L${lineNum}`;
    lineDiv.innerHTML = `
      <span class="line-num">${lineNum}</span>
      <span class="line-content">${escapeHtml(line || ' ')}</span>
    `;
    container.appendChild(lineDiv);
  });
}

function selectCitation(index) {
  appState.activeCitationIndex = index;
  document.querySelectorAll('.citation-select-btn').forEach((btn, idx) => {
    btn.classList.toggle('active', idx === index);
  });

  if (!appState.report || !appState.report.actionable_fixes[index]) return;
  const fix = appState.report.actionable_fixes[index];

  // Remove previous highlights
  document.querySelectorAll('.doc-line.highlight-line').forEach(el => el.classList.remove('highlight-line'));

  // Highlight RFP Quote
  highlightSnippetInViewer('rfp-viewer-body', fix.rfp_citation);

  // Highlight Proposal Quote
  highlightSnippetInViewer('proposal-viewer-body', fix.proposal_citation);
}

function highlightSnippetInViewer(viewerId, snippet) {
  if (!snippet) return;
  const viewer = document.getElementById(viewerId);
  const normSnippet = snippet.trim().toLowerCase();

  const lines = viewer.querySelectorAll('.doc-line');
  let firstMatch = null;

  lines.forEach(lineEl => {
    const content = lineEl.querySelector('.line-content').textContent.toLowerCase();
    // Check match
    const words = normSnippet.split(' ').filter(w => w.length > 3);
    const hasMatch = words.some(word => content.includes(word));

    if (hasMatch) {
      lineEl.classList.add('highlight-line');
      if (!firstMatch) firstMatch = lineEl;
    }
  });

  if (firstMatch) {
    firstMatch.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }
}

function jumpToGrounding(complianceItemIndex) {
  switchTab('inspector');
  selectCitation(0);
}

function escapeHtml(str) {
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

// Initial Data Fetch
async function initApp() {
  try {
    const res = await fetch('/api/samples');
    if (res.ok) {
      const data = await res.json();
      appState.samples = data;
      document.getElementById('rfp-input').value = data.rfp;
      if (data.variants && data.variants['response_1_weak.md']) {
        document.getElementById('proposal-input').value = data.variants['response_1_weak.md'];
      }
    }
  } catch (e) {
    console.log('Using static sample fallback');
  }

  // Run initial evaluation
  runEvaluation();
}

document.addEventListener('DOMContentLoaded', initApp);
