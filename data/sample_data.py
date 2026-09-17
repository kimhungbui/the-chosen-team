"""
Appendix B Sample Dataset for FPT Software Europe Proposal Scorer.
Includes NordFrame Client RFP and 4 draft response variants (Weak, Medium, Strong, Overpromising),
plus benchmark reference output.
"""

from typing import Dict

RFP_NORDFRAME_CONTENT = """# Request for Proposal (RFP) — Enterprise Cloud & SAP Modernization
**Client:** NordFrame Logistics & Manufacturing GmbH (Hamburg, Germany)
**RFP Reference:** RFP-2026-NF-089
**Submission Deadline:** April 30, 2026
**Target Project Start:** May 15, 2026
**Target Go-Live:** October 31, 2026

---

## 1. Executive Summary & Problem Statement
NordFrame operates 14 logistics centers across the DACH region. Our core ERP system—an on-premise SAP ECC 6.0 instance hosted in a local Hamburg data center—is reaching end-of-life. Legacy infrastructure bottlenecks cause frequent processing delays during peak shifts, and reporting across logistics hubs is fragmented.

NordFrame seeks a qualified technology partner to migrate our SAP environment to SAP S/4HANA Cloud hosted on AWS, modernize our core supply chain integration APIs, and establish a resilient 24/7 post-migration operational model.

---

## 2. Detailed Scope of Work & Requirements

### REQ-01: SAP S/4HANA & AWS Cloud Migration
- Migrate 12 SAP ECC modules (FI, CO, SD, MM, PP, WM, QM, PM, SD, LE, BW, Basis) and 4TB database to AWS.
- Ensure full data integrity with zero data loss guarantee.
- Maximum allowable cutover downtime window: **4 hours** (over a weekend).

### REQ-02: Security, Governance & Compliance
- Full compliance with EU GDPR regulations.
- The vendor **must hold valid ISO 27001 certification** and provide a recent **SOC 2 Type II audit report**.
- All data at rest and in transit must be encrypted with client-managed keys.

### REQ-03: Post-Go-Live Support (Hypercare)
- Provide **60 days of 24/7 Hypercare support** post-cutover with dedicated Level 2/3 SAP engineers and guaranteed 15-minute response SLA for Critical (Severity 1) incidents.

### REQ-04: Project Timeline & Milestone Constraints
- Mandatory Go-Live Date: **October 31, 2026** (hard deadline prior to Q4 logistics peak).
- Fixed milestone deadlines:
  - **Milestone 1 (Architecture Blueprint & Target Schema):** June 15, 2026
  - **Milestone 2 (Dry Run 1 & Data Validation):** August 15, 2026
  - **Milestone 3 (Dry Run 2 & Dress Rehearsal):** September 30, 2026
  - **Milestone 4 (Final Cutover & Go-Live):** October 31, 2026

### REQ-05: Commercial & Pricing Structure
- **Fixed Price Model** for Phase 1 Migration & Hypercare. Total budget cap is **€850,000 EUR**.
- Time & Materials (T&M) rate card required for optional post-hypercare enhancements.
- Deferred or "to-be-determined post-contract" pricing will result in immediate disqualification.

### REQ-06: Risk Management & Rollback Strategy
- Detailed risk mitigation matrix covering data migration fallback, cutover rollback procedures, and business continuity during dry runs.
"""

RESPONSE_1_WEAK_CONTENT = """# Proposal for NordFrame IT Transformation
**Submitted by:** Global Tech Consultants Inc.
**Date:** April 2026

---

## 1. Executive Summary
Global Tech Consultants is a leading IT services provider. We help enterprise companies modernize their software systems using state-of-the-art cloud solutions. We are excited to submit this proposal for NordFrame.

---

## 2. Our Proposed Solution
We will evaluate your infrastructure and move your servers to the cloud. Our experienced team uses industry best practices to ensure a smooth transition.

- Cloud infrastructure setup.
- Application migration and database transfer.
- General IT support following launch.

---

## 3. Project Timeline
Project activities will commence shortly after contract execution. We estimate the project will take several months to complete depending on discovery findings. Milestones will be finalized during Phase 1.

---

## 4. Pricing & Commercials
Pricing details will be calculated following an initial 4-week paid discovery phase. Daily consultant rates are available upon request.
"""

RESPONSE_2_MEDIUM_CONTENT = """# Technical Proposal: SAP S/4HANA Migration to AWS
**Submitted by:** CloudSphere Solutions GmbH
**Client:** NordFrame Logistics GmbH
**Date:** April 22, 2026

---

## 1. Context & Understanding
NordFrame requires the migration of its legacy SAP ECC 6.0 environment to SAP S/4HANA on AWS to improve performance across 14 logistics centers. CloudSphere understands the critical nature of keeping logistics operational.

---

## 2. Technical Scope
- Full migration of 12 SAP modules and 4TB database to AWS Cloud.
- Setup of high-availability AWS architecture in Frankfurt region (eu-central-1).
- 30 days of post-go-live support during business hours (8am - 6pm CET).

---

## 3. Compliance & Security
- CloudSphere complies with GDPR standards.
- ISO 27001 certification is currently in progress (expected completion Q1 2027).

---

## 4. Timeline
- Phase 1 (Blueprint): Months 1-2
- Phase 2 (Build & Test): Months 3-4
- Phase 3 (Cutover): Month 5-6 (target autumn 2026)

---

## 5. Commercials
- Total estimated project cost: €780,000 - €920,000 EUR depending on change requests.
- Payment terms: 30% upfront, 40% at mid-point, 30% upon final signoff.
"""

RESPONSE_3_STRONG_CONTENT = """# Proposal for Enterprise SAP S/4HANA Migration & Hypercare
**Submitted by:** FPT Software Europe GmbH
**RFP Target:** NordFrame Logistics & Manufacturing GmbH (RFP-2026-NF-089)
**Date:** April 25, 2026

---

## 1. Problem Context & Solution Alignment
NordFrame’s 14 logistics centers require zero disruption during peak shifts. The bottleneck created by legacy SAP ECC on-premise infrastructure in Hamburg directly threatens Q4 delivery commitments.

FPT Software Europe proposes a dedicated AWS-certified SAP migration factory approach tailored for SAP S/4HANA Cloud, designed specifically to meet NordFrame's hard October 31, 2026 deadline.

---

## 2. Scope & Technical Deliverables
- **SAP S/4HANA & 4TB DB AWS Migration:** Full migration of all 12 modules (FI, CO, SD, MM, PP, WM, QM, PM, SD, LE, BW, Basis) with zero data loss validation.
- **Cutover Window Guarantee:** Guaranteed maximum **4-hour weekend cutover downtime window** backed by 2 dress rehearsal dry runs.
- **60-Day 24/7 Hypercare Support:** Dedicated Level 2/3 SAP & AWS support engineers stationed in Frankfurt/Hamburg with guaranteed **15-minute SLA** for Severity 1 incidents.

---

## 3. Security, Governance & Compliance
- **ISO 27001 Certification:** FPT Software Europe holds valid ISO 27001:2022 certification (Cert # ISO-2024-8891, copy attached in Annex A).
- **SOC 2 Type II:** Recent SOC 2 Type II audit report attached in Annex B.
- **Data Protection:** Full GDPR compliance with client-managed AWS KMS encryption keys.

---

## 4. Concrete Timeline & Milestone Commitment
We formally commit to NordFrame’s schedule:
- **Milestone 1 (Architecture Blueprint):** Complete by **June 15, 2026**
- **Milestone 2 (Dry Run 1 & Data Validation):** Complete by **August 15, 2026**
- **Milestone 3 (Dry Run 2 & Dress Rehearsal):** Complete by **September 30, 2026**
- **Milestone 4 (Final Cutover & Go-Live):** Complete by **October 31, 2026**

---

## 5. Transparent Fixed Pricing & Commercial Structure
- **Fixed Price (Migration & 60-Day 24/7 Hypercare):** **€795,000 EUR** (Fully within NordFrame's €850,000 budget cap).
- **Optional Post-Hypercare T&M Rate Card:**
  - Lead SAP Architect: €1,200 / day
  - Senior Cloud/DevOps Engineer: €950 / day
  - SAP Functional Specialist: €850 / day

---

## 6. Risk Management & Rollback Strategy
- **Rollback Guarantee:** Dual-stage automated DB snapshotting prior to cutover. If dry run criteria fail at T-2 hours, automated rollback to legacy ECC completes in 30 minutes with zero data corruptions.
- **Risk Matrix:** 12 specific risk vectors detailed in Annex C with mitigation leads.
"""

RESPONSE_4_OVERPROMISE_CONTENT = """# Proposal: Next-Gen AI-Powered SAP Autonomous Cloud Transformation
**Submitted by:** HyperQuantum AI Systems
**Client:** NordFrame Logistics
**Date:** April 2026

---

## 1. Executive Summary
Why spend 6 months migrating SAP when HyperQuantum AI can perform an autonomous zero-downtime migration in 14 days? We present a revolutionary proposal that completely supersedes traditional IT migration methods.

---

## 2. Advanced Scope & Deliverables
- Autonomous AI-driven migration of SAP to cloud within **14 days** with **0 seconds downtime**.
- Mandated inclusion of HyperQuantum AI Real-time Supply Chain Analytics Suite (License fee: €450,000).
- Quantum-safe encryption layer (Proprietary tech).

---

## 3. Timeline
- **Go-Live:** May 30, 2026 (5 months ahead of NordFrame's target).

---

## 4. Pricing & Commercials
- Base SAP AI Migration: €890,000 EUR
- Mandatory AI Analytics Suite: €450,000 EUR
- **Total Project Fixed Price:** **€1,340,000 EUR** (Exceeds NordFrame budget cap of €850,000, but ROI is guaranteed within 3 months).
"""

SCORING_EXAMPLE_CONTENT = """# Benchmark Evaluation Output — Response 1 (Weak)

### Overall Score: 24.5% (Traffic Light: RED)

---

### Rubric Breakdown:

1. **Problem Understanding: 1.5 / 5.0 (RED)**
   - *Rationale:* The proposal contains generic IT consulting pitch text. It fails to mention NordFrame's specific SAP ECC 6.0 legacy system, 14 logistics centers, or the Q4 peak deadline.
   - *Citation:* RFP Section 1 vs Proposal Section 1.

2. **Scope & Deliverables Clarity: 2.0 / 5.0 (RED)**
   - *Rationale:* Deliverables are stated as bullet points like "Application migration". Missing 12 SAP modules, 4TB DB spec, 60-day 24/7 hypercare, and 4-hour cutover SLA.

3. **Pricing Clarity: 1.0 / 5.0 (RED)**
   - *Rationale:* Pricing is completely deferred to a paid discovery phase ("Pricing details will be calculated following an initial 4-week paid discovery phase"). Direct violation of RFP REQ-05.

4. **Timeline Clarity: 1.0 / 5.0 (RED)**
   - *Rationale:* Vague timeline ("estimate several months"). No milestone dates provided (Blueprint June 15, Go-live Oct 31 missing).

5. **Completeness vs RFP: 1.5 / 5.0 (RED)**
   - *Rationale:* Fails 5 out of 6 explicit RFP requirements (ISO 27001 missing, SOC 2 missing, Hypercare missing, Pricing missing).

6. **Tone & Persuasiveness: 2.5 / 3.0 (YELLOW)**
   - *Rationale:* Standard corporate tone, but lacks client focus or convincing domain expertise.

7. **Risk Transparency: 1.0 / 5.0 (RED)**
   - *Rationale:* Zero risk matrix, rollback strategy, or SLA commitments included.
"""

SAMPLE_DATASETS: Dict[str, Dict[str, str]] = {
    "rfp": {
        "title": "NordFrame Enterprise Cloud & SAP Modernization (RFP-2026-NF-089)",
        "content": RFP_NORDFRAME_CONTENT,
    },
    "proposals": {
        "response_3_strong": {
            "title": "Response 3 — Strong (FPT Software Europe)",
            "variant": "Strong",
            "content": RESPONSE_3_STRONG_CONTENT,
        },
        "response_2_medium": {
            "title": "Response 2 — Medium (CloudSphere Solutions)",
            "variant": "Medium",
            "content": RESPONSE_2_MEDIUM_CONTENT,
        },
        "response_4_overpromise": {
            "title": "Response 4 — Overpromising (HyperQuantum AI)",
            "variant": "Overpromising",
            "content": RESPONSE_4_OVERPROMISE_CONTENT,
        },
        "response_1_weak": {
            "title": "Response 1 — Weak (Global Tech Consultants)",
            "variant": "Weak",
            "content": RESPONSE_1_WEAK_CONTENT,
        },
    },
    "benchmark": {
        "title": "Scoring Example (Benchmark for Response 1)",
        "content": SCORING_EXAMPLE_CONTENT,
    }
}
