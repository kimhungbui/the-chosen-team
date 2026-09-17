"""
Interactive Streamlit Web Dashboard for FPT Software Europe Proposal Scorer (SiviHack 2026).
Features live proposal evaluation, 7-criterion rubric scoring, RFP requirement gap matrix,
exact document citations, dynamic criteria weighting, and actionable paragraph rewrites.
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

# Custom Enterprise Modern CSS Styling
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
    
    .score-card {
        background: #1E293B;
        border-radius: 16px;
        padding: 1.5rem;
        border: 1px solid #334155;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
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
    
    .rewrite-box {
        background: #0F172A;
        border-left: 4px solid #6366F1;
        padding: 1rem 1.25rem;
        border-radius: 8px;
        margin-top: 0.5rem;
        font-family: monospace;
        color: #E2E8F0;
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

# Sidebar Configuration Controls
with st.sidebar:
    st.image("https://img.shields.io/badge/FPT_Software-Europe_HQ-blue?style=for-the-badge", use_container_width=True)
    st.markdown("### 📋 Evaluation Settings")

    # Document Selection Mode
    data_source = st.radio(
        "Select Document Source:",
        ["Official Appendix B Dataset", "Upload Custom RFP & Proposal"],
        index=0,
    )

    rfp_text = ""
    proposal_text = ""
    proposal_title = ""
    rfp_title = ""

    if data_source == "Official Appendix B Dataset":
        sample_key = st.selectbox(
            "Select Draft Proposal Variant:",
            options=list(SAMPLE_DATASETS["proposals"].keys()),
            format_func=lambda k: SAMPLE_DATASETS["proposals"][k]["title"],
            index=0,
        )
        selected_prop = SAMPLE_DATASETS["proposals"][sample_key]
        proposal_text = selected_prop["content"]
        proposal_title = selected_prop["title"]
        rfp_text = SAMPLE_DATASETS["rfp"]["content"]
        rfp_title = SAMPLE_DATASETS["rfp"]["title"]

        st.info(f"**Loaded Variant:** {selected_prop['variant']}\n\n**RFP Target:** NordFrame Logistics")
    else:
        st.markdown("#### Upload Custom Files")
        uploaded_rfp = st.file_uploader("Upload Client RFP (.md or .txt)", type=["md", "txt"])
        uploaded_proposal = st.file_uploader("Upload Draft Proposal (.md or .txt)", type=["md", "txt"])

        if uploaded_rfp and uploaded_proposal:
            rfp_text = uploaded_rfp.getvalue().decode("utf-8")
            rfp_title = uploaded_rfp.name
            proposal_text = uploaded_proposal.getvalue().decode("utf-8")
            proposal_title = uploaded_proposal.name
        else:
            st.warning("Please upload both RFP and Proposal files to run analysis.")

    st.markdown("---")
    st.markdown("### ⚙️ Engine Options")
    use_llm_mode = st.toggle("Use Agno Gemini LLM Multi-Agent", value=True, help="Leverages Google Gemini 2.5 Flash if GEMINI_API_KEY is available.")
    
    st.markdown("---")
    st.markdown("### ⚖️ Rubric Criteria Weights")
    st.caption("Adjust weightings to reflect client priorities (must sum to 100%).")

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

# Run Evaluation if documents are available
if rfp_text and proposal_text:
    with st.spinner("🤖 Analyzing Proposal against RFP across 7 criteria..."):
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
        st.metric("Overall Weighted Score", f"{report.overall_score_pct}%", delta=None)

    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        if report.overall_traffic_light == TrafficLight.GREEN:
            st.markdown('<span class="badge-green">🟢 ACCEPTABLE / READY</span>', unsafe_allow_html=True)
        elif report.overall_traffic_light == TrafficLight.YELLOW:
            st.markdown('<span class="badge-yellow">🟡 REVISION REQUIRED</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="badge-red">🔴 HIGH RISK / NON-COMPLIANT</span>', unsafe_allow_html=True)

    st.markdown("---")

    # Executive Verdict Banner
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
                st.write(f"**Rationale:** {crit.rationale}")

                if crit.citations:
                    with st.expander("📍 View Source Citations"):
                        for cit in crit.citations:
                            st.markdown(f"""
                            <div class="citation-box">
                                📌 <b>RFP ({cit.rfp_section}):</b> <i>"{cit.rfp_quote}"</i><br>
                                📄 <b>Proposal ({cit.proposal_section}):</b> <i>"{cit.proposal_quote}"</i>
                            </div>
                            """, unsafe_allow_html=True)

                if crit.suggested_fixes:
                    st.caption("🔧 **Quick Action Items:** " + " | ".join(crit.suggested_fixes))

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
        st.caption("Copy and paste these pre-formatted rewritten sections directly into your proposal draft to fix identified gaps.")

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
        st.markdown("### 🔍 Document Inspector")
        doc_col1, doc_col2 = st.columns(2)
        with doc_col1:
            st.markdown(f"#### Client RFP ({report.rfp_title})")
            st.text_area("RFP Raw Text", value=rfp_text, height=500, key="rfp_view")
        with doc_col2:
            st.markdown(f"#### Draft Proposal ({report.proposal_title})")
            st.text_area("Proposal Raw Text", value=proposal_text, height=500, key="prop_view")

else:
    st.info("👈 Please select or upload an RFP and Proposal in the sidebar to begin analysis.")
