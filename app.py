"""
Proposal Scorer Web Application — FPT Software Europe (SiviHack 2026).
Interactive Streamlit application for automated proposal evaluation & scoring.
"""

import os
import importlib
import traceback
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from services.scoring_engine import evaluate_proposal, DEFAULT_WEIGHTS
from data.sample_data import SAMPLE_DATASETS
from schema.proposal_models import TrafficLight, RequirementCoverageStatus, AmbiguousRequirement

# Page Configuration
st.set_page_config(
    page_title="Proposal Scorer — FPT Software Europe",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Styling CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    .stApp {
        background-color: #FFFFFF;
        color: #000000;
    }
    .main-header {
        background: linear-gradient(135deg, #1E1B4B 0%, #312E81 50%, #4338CA 100%);
        padding: 1.5rem 2rem;
        border-radius: 16px;
        box-shadow: 0 10px 25px -5px rgba(67, 56, 202, 0.3);
        margin-bottom: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .badge-green {
        background-color: #064E3B;
        color: #34D399;
        border: 1px solid #059669;
        padding: 0.35rem 0.8rem;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.9rem;
    }
    .badge-yellow {
        background-color: #78350F;
        color: #FBBF24;
        border: 1px solid #D97706;
        padding: 0.35rem 0.8rem;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.9rem;
    }
    .badge-red {
        background-color: #7F1D1D;
        color: #FCA5A5;
        border: 1px solid #DC2626;
        padding: 0.35rem 0.8rem;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.9rem;
    }
    .citation-box {
        background: #1E293B;
        border: 1px dashed #475569;
        padding: 0.75rem 1rem;
        border-radius: 8px;
        font-size: 0.875rem;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Application Header
st.markdown("""
<div class="main-header">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <h1 style="color: #FFFFFF; font-size: 2.1rem; font-weight: 800; margin: 0;">🎯 Proposal Scorer</h1>
            <p style="color: #C7D2FE; font-size: 1.05rem; margin-top: 0.4rem; margin-bottom: 0;">
                FPT Software Europe — Automated Pre-Sales Quality & RFP Compliance Auditor
            </p>
        </div>
        <div style="text-align: right;">
            <span style="background: rgba(255,255,255,0.15); padding: 0.5rem 1rem; border-radius: 20px; font-weight: 600; color: #EEF2FF;">
                SiviHack 2026 Challenge
            </span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

def extract_text_from_file(uploaded_file) -> tuple:
    """
    Extracts raw text and document metrics from uploaded .md, .txt, or .pdf files.
    Preserves block reading order and detects PowerPoint-to-PDF slide decks.
    """
    if uploaded_file is None:
        return "", {}
    fname = uploaded_file.name.lower()
    if fname.endswith(".pdf"):
        try:
            import pymupdf
            doc = pymupdf.open(stream=uploaded_file.getvalue(), filetype="pdf")
            page_count = len(doc)

            is_slide_deck = False
            if page_count > 0:
                rect = doc[0].rect
                if rect.width > rect.height:
                    is_slide_deck = True

            extracted_pages = []
            for i, page in enumerate(doc):
                page_text = page.get_text("text", sort=True).strip()
                if page_text:
                    label = f"Slide {i+1}" if is_slide_deck else f"Page {i+1}"
                    extracted_pages.append(f"=== [{label}] ===\n{page_text}")

            full_text = "\n\n".join(extracted_pages)
            word_count = len(full_text.split())

            metrics = {
                "format": "PowerPoint Slide Deck (PDF)" if is_slide_deck else "Multi-Page PDF Document",
                "units_label": "slides" if is_slide_deck else "pages",
                "count": page_count,
                "word_count": word_count,
            }
            return full_text, metrics
        except Exception as e:
            st.error(f"Error extracting text from PDF '{uploaded_file.name}': {e}")
            return "", {}
    else:
        text = uploaded_file.getvalue().decode("utf-8", errors="replace").strip()
        lines = len(text.splitlines())
        word_count = len(text.split())
        metrics = {
            "format": "Markdown / Text Document",
            "units_label": "lines",
            "count": lines,
            "word_count": word_count,
        }
        return text, metrics


# Sidebar
with st.sidebar:
    st.markdown("### 📁 Upload Documents")
    st.caption("Upload client RFPs & draft proposals (supports `.md`, `.txt`, `.pdf`, and PPT-to-PDF).")

    uploaded_rfp = st.file_uploader(
        "1. Client RFP (.md, .txt, .pdf)",
        type=["md", "txt", "pdf"],
        help="The official client request for proposal document.",
    )
    uploaded_proposal = st.file_uploader(
        "2. Draft Proposal (.md, .txt, .pdf)",
        type=["md", "txt", "pdf"],
        help="Your draft response proposal to be evaluated.",
    )

    rfp_text = ""
    proposal_text = ""
    rfp_title = ""
    proposal_title = ""
    rfp_metrics = {}
    proposal_metrics = {}

    has_custom_upload = bool(uploaded_rfp or uploaded_proposal)

    # 1. Inspect custom uploads
    rfp_is_blank = False
    proposal_is_blank = False

    if uploaded_rfp:
        rfp_text, rfp_metrics = extract_text_from_file(uploaded_rfp)
        rfp_title = uploaded_rfp.name
        if not rfp_text.strip():
            rfp_is_blank = True
            st.error(f"❌ **Uploaded RFP '{uploaded_rfp.name}' is empty (0 words).**")
        else:
            st.success(f"✅ **Custom RFP Loaded:** {rfp_metrics.get('format', 'Document')} ({rfp_metrics.get('count', 0)} {rfp_metrics.get('units_label', '')}, {rfp_metrics.get('word_count', 0):,} words)")

    if uploaded_proposal:
        proposal_text, proposal_metrics = extract_text_from_file(uploaded_proposal)
        proposal_title = uploaded_proposal.name
        if not proposal_text.strip():
            proposal_is_blank = True
            st.error(f"❌ **Uploaded Proposal '{uploaded_proposal.name}' is empty (0 words).**")
        else:
            st.success(f"✅ **Custom Proposal Loaded:** {proposal_metrics.get('format', 'Document')} ({proposal_metrics.get('count', 0)} {proposal_metrics.get('units_label', '')}, {proposal_metrics.get('word_count', 0):,} words)")

    # 2. Benchmark Pre-bundled Datasets (ONLY shown and loaded when user has NOT uploaded custom files)
    if not has_custom_upload:
        benchmark_domains = {
            "logistics": {
                "name": "📦 NordFrame Logistics (Logistics / Warehouse)",
                "rfp_path": "sample_data/rfp_nordframe.md",
                "rfp_title": "NordFrame Warehouse Inventory Dashboard RFP",
                "proposals_dir": "sample_data",
            },
            "healthcare": {
                "name": "🏥 MediCare Systems (Clinical Telehealth / Epic EHR)",
                "rfp_path": "sample_data/healthcare_telehealth/rfp.md",
                "rfp_title": "MediCare Telehealth & EHR Integration RFP",
                "proposals_dir": "sample_data/healthcare_telehealth",
            },
            "fintech": {
                "name": "💳 Global Payments (Fraud Prevention / FinTech)",
                "rfp_path": "sample_data/fintech_fraud/rfp.md",
                "rfp_title": "Global Payments Fraud Engine RFP",
                "proposals_dir": "sample_data/fintech_fraud",
            },
            "retail_ambiguous": {
                "name": "🛍️ Apex Commerce (Unclear & Ambiguous Client Requirements)",
                "rfp_path": "sample_data/retail_ambiguous/rfp.md",
                "rfp_title": "Apex Commerce Personalization Suite RFP",
                "proposals_dir": "sample_data/retail_ambiguous",
            },
        }

        with st.expander("⚡ Or load a pre-bundled benchmark domain dataset", expanded=True):
            st.caption("Select a business domain and test variant:")
            selected_domain_key = st.selectbox(
                "Benchmark Domain:",
                options=list(benchmark_domains.keys()),
                format_func=lambda k: benchmark_domains[k]["name"],
                index=0,
            )
            domain_info = benchmark_domains[selected_domain_key]
            
            variant_options = [
                ("response_3_strong", "Variant: Strong (Comprehensive & Grounded)"),
                ("response_2_medium", "Variant: Medium (Competent but Deferred Pricing)"),
                ("response_4_overpromise", "Variant: Overpromising (Violates Constraints)"),
                ("response_1_weak", "Variant: Weak (Generic Boilerplate)"),
            ]
            selected_var_key = st.selectbox(
                "Proposal Test Variant:",
                options=[v[0] for v in variant_options],
                format_func=lambda k: next(v[1] for v in variant_options if v[0] == k),
                index=0,
            )
            if st.button("📥 Load Benchmark Files into Review"):
                st.session_state["benchmark_domain"] = selected_domain_key
                st.session_state["benchmark_variant"] = selected_var_key
                st.rerun()

        b_dom = st.session_state.get("benchmark_domain", "logistics")
        b_var = st.session_state.get("benchmark_variant", "response_3_strong")
        dom_meta = benchmark_domains.get(b_dom, benchmark_domains["logistics"])

        if os.path.exists(dom_meta["rfp_path"]):
            with open(dom_meta["rfp_path"], "r", encoding="utf-8") as f:
                rfp_text = f.read()
            rfp_title = dom_meta["rfp_title"]
            rfp_metrics = {"format": "Markdown", "units_label": "lines", "count": len(rfp_text.splitlines()), "word_count": len(rfp_text.split())}

        var_path = os.path.join(dom_meta["proposals_dir"], f"{b_var}.md")
        if os.path.exists(var_path):
            with open(var_path, "r", encoding="utf-8") as f:
                proposal_text = f.read()
            proposal_title = f"{dom_meta['name'].split()[1]} — {b_var.replace('_', ' ').title()}"
            proposal_metrics = {"format": "Markdown", "units_label": "lines", "count": len(proposal_text.splitlines()), "word_count": len(proposal_text.split())}



    st.markdown("---")
    st.markdown("### ⚙️ Engine Options")
    use_llm_mode = st.toggle("Use Agno Gemini LLM Multi-Agent", value=True)
    fallback_on_error = st.toggle(
        "Auto-fallback to Rule Engine on Error",
        value=True,
        help="When enabled (recommended), errors during AI agent execution (e.g. 429 quota exhaustion) will gracefully switch to the dynamic rule engine with an explanatory notice."
    )
    has_api_key = bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))
    if has_api_key:
        st.caption("🟢 **Gemini AI Engine:** Connected & Active")
    else:
        st.warning("⚠️ No Gemini API Key found in `.env`.")

    st.markdown("---")
    st.markdown("### ⚖️ Rubric Criteria Weights")
    
    weights = {}
    weights["problem_understanding"] = st.slider("Problem Understanding", 0.0, 40.0, 15.0, 5.0)
    weights["scope_deliverables_clarity"] = st.slider("Scope & Deliverables Clarity", 0.0, 40.0, 20.0, 5.0)
    weights["pricing_clarity"] = st.slider("Pricing Clarity", 0.0, 40.0, 15.0, 5.0)
    weights["timeline_clarity"] = st.slider("Timeline Clarity", 0.0, 40.0, 15.0, 5.0)
    weights["completeness_vs_rfp"] = st.slider("Completeness vs RFP", 0.0, 40.0, 20.0, 5.0)
    weights["tone_persuasiveness"] = st.slider("Tone & Persuasiveness", 0.0, 20.0, 5.0, 5.0)
    weights["risk_transparency"] = st.slider("Risk & Assumptions", 0.0, 30.0, 10.0, 5.0)

    total_w = sum(weights.values())
    if abs(total_w - 100.0) > 0.1:
        st.warning(f"⚠️ Total Weight: {total_w}% (Adjust to equal 100%)")
    else:
        st.success("✅ Total Weight: 100%")

    if st.button("🔄 Reset Weights"):
        weights = DEFAULT_WEIGHTS
        st.rerun()

# Validation before running evaluation
if uploaded_rfp and rfp_is_blank:
    st.error(f"🚨 **Evaluation Blocked:** The uploaded RFP file **'{uploaded_rfp.name}'** is completely blank (0 bytes). Please upload a valid document containing text.")
    st.stop()

if uploaded_proposal and proposal_is_blank:
    st.error(f"🚨 **Evaluation Blocked:** The uploaded Proposal file **'{uploaded_proposal.name}'** is completely blank (0 bytes). Please upload a valid document containing text.")
    st.stop()

if uploaded_rfp and not uploaded_proposal:
    st.warning("⚠️ **Proposal Required:** You uploaded an RFP, but have not uploaded a draft Proposal yet. Please upload a proposal in the sidebar to evaluate.")
    st.stop()

if uploaded_proposal and not uploaded_rfp:
    st.warning("⚠️ **RFP Required:** You uploaded a Proposal, but have not uploaded an RFP yet. Please upload a client RFP in the sidebar to evaluate.")
    st.stop()

if not rfp_text.strip() or not proposal_text.strip():
    st.info("👈 Please upload an RFP and Proposal in the sidebar, or load a benchmark dataset to begin evaluation.")
    st.markdown("""
    <div style="background: #1E293B; padding: 2.5rem 2rem; border-radius: 16px; border: 1px dashed #475569; text-align: center; margin-top: 1.5rem;">
        <h2 style="color: #FFFFFF; font-weight: 800; margin-bottom: 0.5rem; font-size: 1.8rem;">Ready to Audit Your Proposal</h2>
        <p style="color: #94A3B8; font-size: 1.05rem; max-width: 640px; margin: 0 auto 2rem auto;">
            Upload your <b>Client RFP</b> and <b>Draft Proposal</b> in the sidebar (supports <code>.md</code>, <code>.txt</code>, and <code>.pdf</code>) to run the 2-Stage Multi-Agent quality audit.
        </p>
        <div style="display: flex; justify-content: center; gap: 1.2rem; flex-wrap: wrap;">
            <div style="background: rgba(255,255,255,0.04); padding: 1.2rem 1.5rem; border-radius: 12px; border: 1px solid rgba(255,255,255,0.08); width: 240px; text-align: left;">
                <div style="font-size: 1.8rem;">🎯</div>
                <div style="font-weight: 700; color: #EEF2FF; margin-top: 0.5rem; font-size: 1rem;">7 Rubrics Scored</div>
                <div style="font-size: 0.85rem; color: #94A3B8; margin-top: 0.2rem;">Detailed scores with explicit 'Why High' and 'Why Penalized' factor breakdowns.</div>
            </div>
            <div style="background: rgba(255,255,255,0.04); padding: 1.2rem 1.5rem; border-radius: 12px; border: 1px solid rgba(255,255,255,0.08); width: 240px; text-align: left;">
                <div style="font-size: 1.8rem;">📍</div>
                <div style="font-weight: 700; color: #EEF2FF; margin-top: 0.5rem; font-size: 1rem;">Exact Citations</div>
                <div style="font-size: 0.85rem; color: #94A3B8; margin-top: 0.2rem;">Direct side-by-side quotes from the RFP and proposal with omission detection.</div>
            </div>
            <div style="background: rgba(255,255,255,0.04); padding: 1.2rem 1.5rem; border-radius: 12px; border: 1px solid rgba(255,255,255,0.08); width: 240px; text-align: left;">
                <div style="font-size: 1.8rem;">✍️</div>
                <div style="font-weight: 700; color: #EEF2FF; margin-top: 0.5rem; font-size: 1rem;">Actionable Rewrites</div>
                <div style="font-size: 0.85rem; color: #94A3B8; margin-top: 0.2rem;">Pre-written, copy-pasteable paragraph rewrites for all detected gaps.</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Run Evaluation
report = None
try:
    with st.spinner("🤖 Evaluating Proposal against RFP (2-Stage Multi-Agent Analysis)..."):
        report = evaluate_proposal(
            rfp_text=rfp_text,
            proposal_text=proposal_text,
            proposal_title=proposal_title,
            rfp_title=rfp_title,
            custom_weights=weights,
            force_fallback=not use_llm_mode,
            rfp_metrics=rfp_metrics,
            proposal_metrics=proposal_metrics,
            allow_fallback_on_error=fallback_on_error,
        )
except Exception as e:
    st.error(f"🚨 **Evaluation Error:** {e}")
    with st.expander("🔍 Diagnostic Error Details & Traceback", expanded=True):
        st.code(traceback.format_exc())
    st.info(
        "💡 **Troubleshooting & Remediation:**\n"
        "- Check that your Gemini API key in `.env` is valid and active.\n"
        "- Verify that the uploaded files contain readable text.\n"
        "- If you want to view offline heuristic scores despite the LLM error, turn ON **'Auto-fallback to Rule Engine on Error'** in the sidebar."
    )
    st.stop()

if getattr(report, "llm_error", None):
    st.error(f"🚨 **AI Multi-Agent Pipeline Encountered an Error:** `{report.llm_error}`")
    with st.expander("🔍 View Technical LLM Error Details"):
        st.code(report.llm_error_traceback or report.llm_error)
    st.warning("⚠️ **Fallback Activated:** Displaying evaluation results generated by the Dynamic Algorithmic Rule Engine.")

# Executive Overview Header Card
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    st.markdown(f"### 📄 {report.proposal_title}")
    st.caption(f"Evaluated against target: **{report.rfp_title}**")
    if report.rfp_metrics or report.proposal_metrics:
        r_fmt = report.rfp_metrics.get("format", "RFP Document")
        r_cnt = f"{report.rfp_metrics.get('count', '')} {report.rfp_metrics.get('units_label', '')}" if report.rfp_metrics.get('count') else ""
        p_fmt = report.proposal_metrics.get("format", "Proposal Document")
        p_cnt = f"{report.proposal_metrics.get('count', '')} {report.proposal_metrics.get('units_label', '')}" if report.proposal_metrics.get('count') else ""
        st.caption(f"📊 **Telemetry:** RFP ({r_fmt}, {r_cnt}) ⟷ Proposal ({p_fmt}, {p_cnt})")
    if getattr(report, "engine_mode", "") == "agno_llm":
        st.caption("🤖 **Engine:** 2-Stage Multi-Agent AI (Agno Gemini)")
    elif getattr(report, "engine_mode", ""):
        st.caption("⚙️ **Engine:** Dynamic Algorithmic Rule Engine (Offline / Local)")

    notice_txt = getattr(report, "engine_notice", "")
    if notice_txt and str(notice_txt).strip().lower() not in ["", "null", "none"]:
        st.warning(f"ℹ️ {notice_txt}")

with col2:
    st.metric("Overall Weighted Score", f"{report.overall_score_pct}%")

with col3:
    st.markdown("<br>", unsafe_allow_html=True)
    if report.overall_score_pct == 0.0:
        st.markdown('<span class="badge-red">🚨 0% DISQUALIFIED</span>', unsafe_allow_html=True)
    elif report.overall_traffic_light == TrafficLight.GREEN:
        st.markdown('<span class="badge-green">🟢 ACCEPTABLE / READY</span>', unsafe_allow_html=True)
    elif report.overall_traffic_light == TrafficLight.YELLOW:
        st.markdown('<span class="badge-yellow">🟡 REVISION REQUIRED</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge-red">🔴 HIGH RISK / NON-COMPLIANT</span>', unsafe_allow_html=True)

if report.overall_score_pct == 0.0:
    st.error(
        "🚨 **FATAL DISQUALIFICATION (Overall Score: 0%): Target Company Mismatch**\n\n"
        "The proposal targets a different client company than the issuing RFP client. "
        "In commercial procurement, submitting a proposal for the wrong client organization results in immediate disqualification."
    )

st.markdown("---")
if getattr(report, "detected_client_priorities", None):
    st.info(f"🎯 **Detected Client Strategic Priorities (Level 3 Insight):**\n\n{report.detected_client_priorities}")

st.markdown(f"#### 💡 Executive Verdict\n{report.executive_summary}")
st.markdown("---")

# Main Analysis Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 7-Criterion Scorecard",
    "🎯 RFP Requirement Traceability Matrix",
    "✍️ Actionable Paragraph Rewrites",
    "❓ Customer Ambiguity & RFI Tracker",
    "🔍 Side-by-Side Document Inspector"
])

# TAB 1: 7-Criterion Scorecard
with tab1:
    st.markdown("### 7 Core Scoring Rubrics (Appendix A)")
    for crit in report.rubric_scores:
        with st.container():
            c_col1, c_col2, c_col3 = st.columns([3, 1, 1])
            with c_col1:
                st.markdown(f"#### {crit.criterion_name}")
            with c_col2:
                st.markdown(f"**Score:** `{crit.score_1_to_5} / 5.0` (Weight: `{crit.weight}%`)")
            with c_col3:
                if crit.traffic_light == TrafficLight.GREEN:
                    st.markdown('<span class="badge-green">GREEN</span>', unsafe_allow_html=True)
                elif crit.traffic_light == TrafficLight.YELLOW:
                    st.markdown('<span class="badge-yellow">YELLOW</span>', unsafe_allow_html=True)
                else:
                    st.markdown('<span class="badge-red">RED</span>', unsafe_allow_html=True)

            st.progress(crit.score_1_to_5 / 5.0)
            st.markdown(f"**Score Rationale:** {crit.rationale}")

            # Why High / Why Low Breakdown
            if crit.score_factors_high or crit.score_factors_low:
                f_col1, f_col2 = st.columns(2)
                with f_col1:
                    if crit.score_factors_high:
                        st.markdown("🟢 **Why Score is High (Strengths):**")
                        for h in crit.score_factors_high:
                            st.markdown(f"- {h}")
                with f_col2:
                    if crit.score_factors_low:
                        st.markdown("🔴 **Why Score is Penalized (Weaknesses / Gaps):**")
                        for l in crit.score_factors_low:
                            st.markdown(f"- {l}")

            if crit.citations:
                with st.expander("📍 View Document Citations (RFP vs Proposal)"):
                    for cit in crit.citations:
                        st.markdown(f"""
                        <div class="citation-box">
                            📌 <b>RFP ({cit.rfp_section}):</b> <i>"{cit.rfp_quote}"</i><br>
                            📄 <b>Proposal ({cit.proposal_section}):</b> <i>"{cit.proposal_quote}"</i>
                        </div>
                        """, unsafe_allow_html=True)

            if crit.suggested_fixes:
                st.caption("🔧 **Action Items:** " + " | ".join(crit.suggested_fixes))

            st.markdown("---")

# TAB 2: Requirement Traceability Matrix
with tab2:
    st.markdown("### 🎯 Mandatory RFP Requirement Traceability & Compliance Matrix")
    st.caption("Detailed audit verifying how the proposal addresses each explicit client requirement and constraint from the RFP.")

    if not report.requirement_gaps:
        st.success("🎉 Excellent! 100% requirement coverage detected with zero missing requirements.")
    else:
        crit_count = sum(1 for g in report.requirement_gaps if getattr(g, "priority_level", "HIGH") == "CRITICAL")
        high_count = sum(1 for g in report.requirement_gaps if getattr(g, "priority_level", "HIGH") == "HIGH")
        med_count = sum(1 for g in report.requirement_gaps if getattr(g, "priority_level", "HIGH") == "MEDIUM")

        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        m_col1.metric("Total Identified Gaps", len(report.requirement_gaps))
        m_col2.metric("Critical Gaps (Disqualifiers)", crit_count)
        m_col3.metric("High Priority Gaps", high_count)
        m_col4.metric("Medium Polish Items", med_count)

        st.markdown("---")

        for gap in report.requirement_gaps:
            p_level = getattr(gap, "priority_level", "HIGH")
            p_badge = "🚨 CRITICAL" if p_level == "CRITICAL" else ("⚠️ HIGH" if p_level == "HIGH" else "ℹ️ MEDIUM")
            
            with st.expander(f"{p_badge} | {gap.requirement_id}: {gap.requirement_title} — Status: {gap.status.value}", expanded=True):
                g_col1, g_col2 = st.columns(2)
                with g_col1:
                    st.markdown(f"**📌 Demanded in Client RFP:**\n> {gap.rfp_snippet}")
                with g_col2:
                    st.markdown(f"**📄 Stated in Proposal Draft:**\n> {gap.proposal_snippet if gap.proposal_snippet else '*(Omitted / No mention in document)*'}")
                
                st.error(f"**Gap Analysis:** {gap.issue_description}")
                if getattr(gap, "placement_anchor", None):
                    st.info(f"**📍 Suggested Proposal Placement Anchor:** {gap.placement_anchor}")

# TAB 3: Actionable Paragraph Rewrites
with tab3:
    st.markdown("### ✍️ Specific & Actionable Paragraph Rewrites")
    st.caption("Copy and paste these pre-formatted rewritten sections directly into your proposal draft at the indicated section locations.")

    if not report.requirement_gaps:
        st.info("No paragraph rewrites required! The proposal already satisfies all RFP requirements.")
    else:
        for i, gap in enumerate(report.requirement_gaps, 1):
            p_level = getattr(gap, "priority_level", "HIGH")
            p_badge = "🔴 CRITICAL" if p_level == "CRITICAL" else ("🟡 HIGH" if p_level == "HIGH" else "🔵 MEDIUM")
            st.markdown(f"#### Fix #{i}: {gap.requirement_title} (`{gap.requirement_id}`) — {p_badge}")
            st.markdown(f"**Issue Description:** {gap.issue_description}")
            if getattr(gap, "placement_anchor", None):
                st.markdown(f"📍 **Where to Insert in Proposal:** `{gap.placement_anchor}`")
            st.code(gap.actionable_rewrite, language="markdown")
            st.markdown("---")

# TAB 4: Customer Requirement Ambiguity & Pre-Bid RFI Tracker
with tab4:
    st.markdown("### ❓ Customer Requirement Ambiguity & Pre-Bid RFI Tracker")
    st.caption("Audits unclear, vague, or unquantified customer requirements in the RFP. Highlights scope creep risks, pre-bid clarification questions, and defensive baseline assumptions.")

    if not getattr(report, "ambiguous_requirements", None):
        st.success("🎉 **Crystal-Clear Client Requirements:** All customer requirements contain specific, measurable boundaries and acceptance criteria.")
    else:
        amb_list = report.ambiguous_requirements
        handled_cnt = sum(1 for a in amb_list if a.proposal_handling == "HANDLED_WITH_ASSUMPTIONS")
        vague_cnt = sum(1 for a in amb_list if a.proposal_handling == "REPEATED_VAGUELY")
        unaddressed_cnt = sum(1 for a in amb_list if a.proposal_handling == "UNADDRESSED")

        ac1, ac2, ac3, ac4 = st.columns(4)
        ac1.metric("Ambiguous Requirements Detected", len(amb_list))
        ac2.metric("Mitigated with Assumptions", handled_cnt)
        ac3.metric("Repeated Vaguely (Risk)", vague_cnt)
        ac4.metric("Unaddressed in Proposal", unaddressed_cnt)

        st.markdown("---")

        for amb in amb_list:
            if amb.proposal_handling == "HANDLED_WITH_ASSUMPTIONS":
                p_badge = "🟢 MITIGATED WITH ASSUMPTIONS"
                p_desc = "The proposal author proactively bounded this ambiguity by stating explicit sizing, latency SLAs, or discovery gates."
            elif amb.proposal_handling == "REPEATED_VAGUELY":
                p_badge = "🟡 REPEATED VAGUELY (SCOPE CREEP RISK)"
                p_desc = "The proposal author echoed the customer's vague terms without defining quantitative boundaries or baseline assumptions."
            else:
                p_badge = "🔴 UNADDRESSED IN PROPOSAL"
                p_desc = "The proposal completely ignored this ambiguous requirement, leaving project scope completely open."

            with st.expander(f"⚠️ {amb.requirement_title} (`{amb.requirement_id}`) — {p_badge}", expanded=True):
                st.markdown(f"**📌 Customer's Unclear RFP Statement:**\n> *\"{amb.rfp_snippet}\"*")
                st.error(f"**⚠️ Ambiguity & Scope Creep Risk:** {amb.ambiguity_reason}")
                st.info(f"**🔍 Proposal Handling Status ({p_badge}):** {p_desc}")

                q_col, a_col = st.columns(2)
                with q_col:
                    st.markdown("#### ❓ Pre-Bid Clarification Question (RFI to Client)")
                    st.caption("Submit this exact question to the customer during pre-bid Q&A:")
                    st.code(amb.clarification_question, language="markdown")
                with a_col:
                    st.markdown("#### 🛡️ Recommended Baseline Assumption (For Proposal)")
                    st.caption("Insert this protective assumption text into your proposal draft:")
                    st.code(amb.recommended_assumption, language="markdown")

# TAB 5: Document Inspector
with tab5:
    st.markdown("### 🔍 Side-by-Side Document Inspector")
    doc_col1, doc_col2 = st.columns(2)
    with doc_col1:
        st.markdown(f"#### Client RFP ({report.rfp_title})")
        st.text_area("RFP Raw Text", value=rfp_text, height=500, key="rfp_view")
    with doc_col2:
        st.markdown(f"#### Draft Proposal ({report.proposal_title})")
        st.text_area("Proposal Raw Text", value=proposal_text, height=500, key="prop_view")


