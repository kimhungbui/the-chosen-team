import os
import sys
import json
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline import evaluate_proposal, get_mock_evaluation_report
from models.schemas import ProposalReviewReport, RequirementAudit, SuggestedFix, CriterionScore, ComplianceMatrix
from guardrails.verifier import verify_citations_and_lines, enforce_mathematical_consistency

STATIC_DIR = Path(__file__).resolve().parent

def get_sample_datasets():
    sample_dir = PROJECT_ROOT / "sample_data"
    rfp_text = (sample_dir / "rfp_nordframe.md").read_text(encoding="utf-8") if (sample_dir / "rfp_nordframe.md").exists() else ""
    
    variants = {}
    for filename in ["response_1_weak.md", "response_2_medium.md", "response_3_strong.md", "response_4_overpromise.md"]:
        path = sample_dir / filename
        if path.exists():
            variants[filename] = path.read_text(encoding="utf-8")
            
    return {
        "rfp": rfp_text,
        "variants": variants
    }

def get_variant_mock_report(rfp_text: str, proposal_text: str, variant_name: str) -> ProposalReviewReport:
    """Provides benchmark mock data for all 4 variants if offline."""
    if "response_3_strong" in variant_name:
        compliance_items = [
            RequirementAudit(requirement_id="REQ-1", requirement_title="Web-based inventory dashboard across 6 warehouses", status="MET", rfp_quote="web-based dashboard showing real-time inventory levels", proposal_quote="Live inventory levels across all 6 warehouses, refreshed continuously", proposal_section="1. Real-Time Dashboard", gap_analysis="Fully addressed with real-time updates and multi-site coverage."),
            RequirementAudit(requirement_id="REQ-2", requirement_title="Automated low-stock alerts", status="MET", rfp_quote="Automated low-stock alerts sent to warehouse managers", proposal_quote="Configurable per-item thresholds; alerts sent by email/SMS", proposal_section="2. Low-Stock Alerts", gap_analysis="Fully addressed with configurable thresholds."),
            RequirementAudit(requirement_id="REQ-3", requirement_title="Existing PostgreSQL database integration", status="MET", rfp_quote="existing PostgreSQL inventory database — no migration", proposal_quote="no migration or schema changes required", proposal_section="1. Real-Time Dashboard", gap_analysis="Explicitly confirms zero migration and read-only connector."),
            RequirementAudit(requirement_id="REQ-4", requirement_title="Role-based access", status="MET", rfp_quote="warehouse managers should only see their own site; HQ staff should see all sites", proposal_quote="Warehouse managers see only their own site's inventory; HQ staff have company-wide visibility", proposal_section="3. Role-Based Access", gap_analysis="Database-level enforcement across all 6 sites."),
            RequirementAudit(requirement_id="REQ-5", requirement_title="Rollout & Onboarding plan", status="MET", rfp_quote="data migration / onboarding plan for rolling this out across all 6 sites", proposal_quote="Pilot (Weeks 1-10) -> Validation -> Phased rollout (Weeks 13-24)", proposal_section="4. Rollout / Onboarding Plan", gap_analysis="Clear phased rollout table adhering to 3-month and 6-month milestones."),
            RequirementAudit(requirement_id="REQ-6", requirement_title="Support & Maintenance SLAs", status="MET", rfp_quote="Support & maintenance terms after go-live", proposal_quote="24-hour response time for critical issues, 3-business-day for minor issues", proposal_section="5. Support & Maintenance", gap_analysis="Clear response-time SLAs and CET business hours specified."),
            RequirementAudit(requirement_id="REQ-7", requirement_title="Assumptions & Risk Disclosure", status="MET", rfp_quote="assumptions, limitations, or risks", proposal_quote="PostgreSQL connection access, Site manager availability, Data quality risks", proposal_section="6. Assumptions & Risk Management", gap_analysis="Transparent disclosure of dependencies and mitigation."),
        ]
        scores = [
            CriterionScore(criterion="Problem Understanding", score=4.8, comment="Strong grasp of operational context and disruption constraints."),
            CriterionScore(criterion="Scope & Deliverables Clarity", score=4.7, comment="Detailed functional specs and clear scope boundaries."),
            CriterionScore(criterion="Pricing Clarity", score=4.9, comment="Transparent fixed pricing itemized (€98,500 within €80k-€120k budget)."),
            CriterionScore(criterion="Timeline Clarity", score=4.8, comment="Clear milestone table with pilot in 10 weeks and full rollout in 24 weeks."),
            CriterionScore(criterion="Completeness vs. RFP Requirements", score=5.0, comment="All 7 RFP requirements addressed comprehensively."),
            CriterionScore(criterion="Tone & Persuasiveness", score=4.7, comment="Professional, tailored, confident, and client-centric."),
            CriterionScore(criterion="Risk/Assumptions Transparency", score=4.8, comment="Honest disclosure of database access and warehouse manager availability dependencies."),
        ]
        fixes = []
        verdict = "READY_TO_SUBMIT"
        summary = "Outstanding proposal. Exceeds standard RFP requirements with clear SLAs, transparent pricing, and zero-migration compliance."
        overall = 4.8
    elif "response_4_overpromise" in variant_name:
        compliance_items = [
            RequirementAudit(requirement_id="REQ-1", requirement_title="Web-based inventory dashboard across 6 warehouses", status="MET", rfp_quote="web-based dashboard showing real-time inventory levels", proposal_quote="Real-time dashboard across all 6 warehouses", proposal_section="Proposed Solution", gap_analysis="Dashboard promised, but bundled with unrequested features."),
            RequirementAudit(requirement_id="REQ-2", requirement_title="Automated low-stock alerts", status="MET", rfp_quote="Automated low-stock alerts", proposal_quote="Real-time alerts across all locations simultaneously", proposal_section="Proposed Solution", gap_analysis="Alerting promised."),
            RequirementAudit(requirement_id="REQ-3", requirement_title="Existing PostgreSQL database integration (NO migration)", status="CONTRADICTED", rfp_quote="existing PostgreSQL inventory database — no migration to a new database", proposal_quote="migrating away from your current PostgreSQL database to our proprietary cloud data platform", proposal_section="Proposed Solution", gap_analysis="DIRECT VIOLATION: RFP strictly forbade migration; proposal insists on migrating database."),
            RequirementAudit(requirement_id="REQ-4", requirement_title="Role-based access", status="PARTIALLY_MET", rfp_quote="warehouse managers should only see their own site", proposal_quote=None, proposal_section=None, gap_analysis="No mention of site-specific access partitioning."),
            RequirementAudit(requirement_id="REQ-5", requirement_title="Rollout & Onboarding plan", status="MISSING", rfp_quote="data migration / onboarding plan", proposal_quote=None, proposal_section=None, gap_analysis="No multi-site transition or onboarding strategy."),
            RequirementAudit(requirement_id="REQ-6", requirement_title="Support & Maintenance SLAs", status="PARTIALLY_MET", rfp_quote="response times, SLAs", proposal_quote="one year of support", proposal_section="Pricing", gap_analysis="Mentions 1 year support but gives zero SLA metrics or response times."),
            RequirementAudit(requirement_id="REQ-7", requirement_title="Assumptions & Risk Disclosure", status="MISSING", rfp_quote="assumptions, limitations, or risks", proposal_quote=None, proposal_section=None, gap_analysis="Fails to disclose high operational risks of migrating legacy database."),
        ]
        scores = [
            CriterionScore(criterion="Problem Understanding", score=2.0, comment="Ignores NordFrame's need for minimal disruption and simple visibility."),
            CriterionScore(criterion="Scope & Deliverables Clarity", score=2.5, comment="Massive scope creep (predictive AI, supplier scoring) not requested."),
            CriterionScore(criterion="Pricing Clarity", score=2.5, comment="Lump sum €98,000 without itemization; unrealistic for scope proposed."),
            CriterionScore(criterion="Timeline Clarity", score=1.5, comment="8 weeks for full database migration and AI platform is highly unrealistic."),
            CriterionScore(criterion="Completeness vs. RFP Requirements", score=2.0, comment="Contradicts core database constraint and adds unasked complexity."),
            CriterionScore(criterion="Tone & Persuasiveness", score=2.0, comment="Over-promising, vendor-centric buzzword pitch."),
            CriterionScore(criterion="Risk/Assumptions Transparency", score=1.0, comment="Hides immense risk of forced database cutover."),
        ]
        fixes = [
            SuggestedFix(category="CONTRADICTION", title="Violates Constraint: Database Migration Prohibited", rfp_citation="existing PostgreSQL inventory database — no migration to a new database", proposal_citation="Proposed Solution", issue_description="The proposal demands replacing PostgreSQL with a proprietary cloud platform, violating the client's non-negotiable constraint.", suggested_fix="Remove proprietary data platform migration. Confirm that the dashboard connects to NordFrame's existing PostgreSQL database using standard SQLAlchemy/connector interfaces with zero schema disruption."),
            SuggestedFix(category="VAGUE", title="Unrealistic Delivery Timeline (8 Weeks)", rfp_citation="Working pilot within 3 months; full rollout within 6 months", proposal_citation="Timeline", issue_description="Claiming full delivery including migration in 8 weeks reads as untrustworthy and unrealistic to enterprise buyers.", suggested_fix="Adopt NordFrame's phased timeline: Deliver single-site pilot in Month 3, followed by phased site onboarding across Months 4–6."),
        ]
        verdict = "MAJOR_REWORK_REQUIRED"
        summary = "Dangerous proposal. Contradicts explicit RFP constraint prohibiting database migration and promises an unrealistic 8-week timeline."
        overall = 1.9
    elif "response_2_medium" in variant_name:
        compliance_items = [
            RequirementAudit(requirement_id="REQ-1", requirement_title="Web-based inventory dashboard across 6 warehouses", status="MET", rfp_quote="web-based dashboard showing real-time inventory levels across all 6 warehouses", proposal_quote="real-time inventory levels across all 6 warehouses", proposal_section="Proposed Solution", gap_analysis="Addressed."),
            RequirementAudit(requirement_id="REQ-2", requirement_title="Automated low-stock alerts", status="MET", rfp_quote="Automated low-stock alerts sent to warehouse managers", proposal_quote="configurable thresholds per item, notifying warehouse managers automatically", proposal_section="Proposed Solution", gap_analysis="Addressed with configurable thresholds."),
            RequirementAudit(requirement_id="REQ-3", requirement_title="Existing PostgreSQL database integration", status="MET", rfp_quote="existing PostgreSQL inventory database — no migration", proposal_quote="built on top of your existing PostgreSQL database — no database migration required", proposal_section="Proposed Solution", gap_analysis="Properly respects no-migration constraint."),
            RequirementAudit(requirement_id="REQ-4", requirement_title="Role-based access", status="MET", rfp_quote="warehouse managers should only see their own site; HQ staff should see all sites", proposal_quote="warehouse managers see only their own site's data; HQ staff have visibility across all sites", proposal_section="Proposed Solution", gap_analysis="Correctly addresses role boundaries."),
            RequirementAudit(requirement_id="REQ-5", requirement_title="Rollout & Onboarding plan", status="PARTIALLY_MET", rfp_quote="data migration / onboarding plan for rolling this out across all 6 sites", proposal_quote="onboard warehouses in phases rather than all at once", proposal_section="Proposed Solution", gap_analysis="Mentions phased onboarding but lacks specific site batches or timeline commitments."),
            RequirementAudit(requirement_id="REQ-6", requirement_title="Support & Maintenance SLAs", status="MISSING", rfp_quote="Support & maintenance terms after go-live", proposal_quote=None, proposal_section=None, gap_analysis="Completely omitted support terms and response times."),
            RequirementAudit(requirement_id="REQ-7", requirement_title="Assumptions & Risk Disclosure", status="MISSING", rfp_quote="assumptions, limitations, or risks", proposal_quote=None, proposal_section=None, gap_analysis="No risks or operational assumptions disclosed."),
        ]
        scores = [
            CriterionScore(criterion="Problem Understanding", score=3.5, comment="Accurately captures the multi-warehouse inventory problem."),
            CriterionScore(criterion="Scope & Deliverables Clarity", score=4.0, comment="Solid functional feature scope respecting PostgreSQL constraint."),
            CriterionScore(criterion="Pricing Clarity", score=2.5, comment="Broad range (€70k–€110k) with firm quote deferred until after discovery."),
            CriterionScore(criterion="Timeline Clarity", score=2.5, comment="Vaguely promises 'within your timeframe' without concrete milestones."),
            CriterionScore(criterion="Completeness vs. RFP Requirements", score=3.0, comment="Covers functional requirements but omits SLAs and risk disclosure."),
            CriterionScore(criterion="Tone & Persuasiveness", score=3.5, comment="Competent tone and relevant DACH region credentials."),
            CriterionScore(criterion="Risk/Assumptions Transparency", score=1.0, comment="Zero risk or dependency transparency."),
        ]
        fixes = [
            SuggestedFix(category="MISSING_REQUIREMENT", title="Missing: Support & Maintenance Terms", rfp_citation="Support & maintenance terms after go-live (response times, SLAs)", proposal_citation="Proposed Solution", issue_description="RFP explicitly requested post-launch SLA terms; none are mentioned.", suggested_fix="Add a Support & Maintenance section: 'Year 1 support includes 2-hour response for critical system outages and 24-hour response for standard tickets, with CET business hours support.'"),
            SuggestedFix(category="DEFERRED", title="Vague Pricing Range (€70k–€110k)", rfp_citation="€80,000–€120,000 total, including first year of support", proposal_citation="Pricing", issue_description="Deferring firm quote creates pricing uncertainty.", suggested_fix="Replace vague range with firm phased structure: 'Base integration & dashboard: €75,000; Year 1 Support & SLA: €15,000. Total fixed commitment: €90,000.'"),
        ]
        verdict = "MINOR_REVISIONS_NEEDED"
        summary = "Good functional proposal respecting key technical constraints, but weakened by vague pricing, missing SLAs, and omitted risk disclosures."
        overall = 2.9
    else:
        # Default weak proposal
        return get_mock_evaluation_report(rfp_text, proposal_text)

    report = ProposalReviewReport(
        proposal_title=f"Evaluation: {variant_name.replace('.md', '')}",
        client_name="NordFrame Logistics GmbH",
        overall_score=overall,
        readiness_verdict=verdict,
        verdict_summary=summary,
        detected_client_priorities="Low operational risk, business continuity across 6 sites, and zero database migration disruption.",
        criteria_scores=scores,
        compliance_matrix=compliance_items,
        actionable_fixes=fixes,
    )
    report = verify_citations_and_lines(report, rfp_text, proposal_text)
    report = enforce_mathematical_consistency(report, ComplianceMatrix(items=compliance_items, compliance_summary="Test"))
    return report


class ProposalScorerServer(SimpleHTTPRequestHandler):
    def serve_file(self, filepath: Path, content_type: str):
        if filepath.exists() and filepath.is_file():
            content = filepath.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/samples":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            data = get_sample_datasets()
            encoded = json.dumps(data).encode("utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)
            return

        # Serve static assets
        clean_path = parsed.path.lstrip("/")
        if not clean_path or clean_path == "/":
            clean_path = "index.html"

        target = STATIC_DIR / clean_path
        if clean_path.endswith(".html"):
            self.serve_file(target, "text/html; charset=utf-8")
        elif clean_path.endswith(".css"):
            self.serve_file(target, "text/css; charset=utf-8")
        elif clean_path.endswith(".js"):
            self.serve_file(target, "application/javascript; charset=utf-8")
        elif clean_path.endswith(".json"):
            self.serve_file(target, "application/json")
        else:
            self.serve_file(target, "text/plain; charset=utf-8")

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/evaluate":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            payload = json.loads(body)

            rfp_text = payload.get("rfp", "")
            proposal_text = payload.get("proposal", "")
            variant_name = payload.get("variant", "response_1_weak.md")

            gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            
            try:
                if gemini_key:
                    report = evaluate_proposal(
                        rfp_content=rfp_text,
                        proposal_content=proposal_text,
                        rfp_filename="rfp.md",
                        proposal_filename="proposal.md",
                        verbose=False
                    )
                else:
                    report = get_variant_mock_report(rfp_text, proposal_text, variant_name)

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(report.model_dump_json().encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

def run_server(port=8080):
    server = HTTPServer(("0.0.0.0", port), ProposalScorerServer)
    print(f"🚀 Proposal Scorer UI running at http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        server.server_close()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run_server(port)
