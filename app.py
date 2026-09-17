"""
Proposal Scorer Web Application — FPT Software Europe (SiviHack 2026).
Interactive Streamlit application for automated proposal evaluation & scoring.
"""

import os
import streamlit as st
from data.sample_data import SAMPLE_DATASETS
from services.scoring_engine import evaluate_proposal, DEFAULT_WEIGHTS
from schema.proposal_models import TrafficLight, RequirementCoverageStatus

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
        background-color: #0F172A;
        color: #F8FAFC;
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

def extract_text_from_file(uploaded_file) -> str:
    """Extracts raw text from uploaded .md, .txt, or .pdf files."""
    if uploaded_file is None:
        return ""
    fname = uploaded_file.name.lower()
    if fname.endswith(".pdf"):
        try:
            import pymupdf
            doc = pymupdf.open(stream=uploaded_file.getvalue(), filetype="pdf")
            return "\n\n".join([page.get_text() for page in doc]).strip()
        except Exception as e:
            st.error(f"Error extracting text from PDF '{uploaded_file.name}': {e}")
            return ""
    else:
        return uploaded_file.getvalue().decode("utf-8", errors="replace").strip()


# Sidebar
with st.sidebar:
    st.markdown("### 📁 Upload Documents")
    st.caption("Upload any client RFP and draft proposal to evaluate compliance and quality.")

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

    if uploaded_rfp and uploaded_proposal:
        rfp_text = extract_text_from_file(uploaded_rfp)
        rfp_title = uploaded_rfp.name
        proposal_text = extract_text_from_file(uploaded_proposal)
        proposal_title = uploaded_proposal.name
        st.success("✅ Both documents loaded successfully.")
    else:
        # Optional quick-loader for instant demo testing
        with st.expander("⚡ Or load a demo sample file"):
            st.caption("Test the engine with pre-bundled sample benchmark files:")
            sample_variant = st.selectbox(
                "Select Proposal Variant:",
                options=list(SAMPLE_DATASETS["proposals"].keys()),
                format_func=lambda k: SAMPLE_DATASETS["proposals"][k]["title"],
                index=0,
            )
            if st.button("📥 Load Sample into Review"):
                st.session_state["loaded_demo_key"] = sample_variant
                st.rerun()

        if "loaded_demo_key" in st.session_state and not (uploaded_rfp or uploaded_proposal):
            d_key = st.session_state["loaded_demo_key"]
            if d_key in SAMPLE_DATASETS["proposals"]:
                selected_prop = SAMPLE_DATASETS["proposals"][d_key]
                proposal_text = selected_prop["content"]
                proposal_title = selected_prop["title"]
                rfp_text = SAMPLE_DATASETS["rfp"]["content"]
                rfp_title = SAMPLE_DATASETS["rfp"]["title"]
                st.info(f"Loaded Demo Variant: **{selected_prop['variant']}**")

    st.markdown("---")
    st.markdown("### ⚙️ Engine Options")
    use_llm_mode = st.toggle("Use Agno Gemini LLM Multi-Agent", value=True)

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

# Run Evaluation if documents are loaded
if rfp_text and proposal_text:
    with st.spinner("🤖 Evaluating Proposal against RFP..."):
        report = evaluate_proposal(
            rfp_text=rfp_text,
            proposal_text=proposal_text,
            proposal_title=proposal_title,
            rfp_title=rfp_title,
            custom_weights=weights,
            force_fallback=not use_llm_mode,
        )

    # Executive Overview Header Card
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.markdown(f"### 📄 {report.proposal_title}")
        st.caption(f"Evaluated against target: **{report.rfp_title}**")

    with col2:
        st.metric("Overall Weighted Score", f"{report.overall_score_pct}%")

    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        if report.overall_traffic_light == TrafficLight.GREEN:
            st.markdown('<span class="badge-green">🟢 ACCEPTABLE / READY</span>', unsafe_allow_html=True)
        elif report.overall_traffic_light == TrafficLight.YELLOW:
            st.markdown('<span class="badge-yellow">🟡 REVISION REQUIRED</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="badge-red">🔴 HIGH RISK / NON-COMPLIANT</span>', unsafe_allow_html=True)

    st.markdown("---")
    if getattr(report, "detected_client_priorities", None):
        st.info(f"🎯 **Detected Client Strategic Priorities (Level 3 Insight):**\n\n{report.detected_client_priorities}")

    st.markdown(f"#### 💡 Executive Verdict\n{report.executive_summary}")
    st.markdown("---")

    # Main Analysis Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 7-Criterion Scorecard",
        "🎯 RFP Requirement Gap Matrix",
        "✍️ Actionable Paragraph Rewrites",
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

    # TAB 2: Requirement Gap Matrix
    with tab2:
        st.markdown("### Mandatory RFP Requirement Coverage Analysis")
        if not report.requirement_gaps:
            st.success("🎉 Excellent! 100% requirement coverage detected with zero missing requirements.")
        else:
            for gap in report.requirement_gaps:
                with st.expander(f"⚠️ {gap.requirement_id}: {gap.requirement_title} — Status: {gap.status.value}", expanded=True):
                    g_col1, g_col2 = st.columns(2)
                    with g_col1:
                        st.markdown(f"**Requested in RFP:**\n> {gap.rfp_snippet}")
                    with g_col2:
                        st.markdown(f"**Current Proposal Statement:**\n> {gap.proposal_snippet if gap.proposal_snippet else '*(Omitted)*'}")
                    st.error(f"**Identified Gap:** {gap.issue_description}")

    # TAB 3: Actionable Paragraph Rewrites
    with tab3:
        st.markdown("### ✍️ Specific & Actionable Paragraph Rewrites")
        st.caption("Copy and paste these pre-formatted rewritten sections directly into your proposal draft.")

        if not report.requirement_gaps:
            st.info("No paragraph rewrites required! The proposal already satisfies all RFP requirements.")
        else:
            for i, gap in enumerate(report.requirement_gaps, 1):
                st.markdown(f"#### Fix #{i}: {gap.requirement_title} (`{gap.requirement_id}`)")
                st.markdown(f"**Problem:** {gap.issue_description}")
                st.code(gap.actionable_rewrite, language="markdown")
                st.markdown("---")

    # TAB 4: Document Inspector
    with tab4:
        st.markdown("### 🔍 Side-by-Side Document Inspector")
        doc_col1, doc_col2 = st.columns(2)
        with doc_col1:
            st.markdown(f"#### Client RFP ({report.rfp_title})")
            st.text_area("RFP Raw Text", value=rfp_text, height=500, key="rfp_view")
        with doc_col2:
            st.markdown(f"#### Draft Proposal ({report.proposal_title})")
            st.text_area("Proposal Raw Text", value=proposal_text, height=500, key="prop_view")

else:
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
