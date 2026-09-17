# Proposal Scorer: System Design, Methods & Comparison

> **Challenge**: SiviHack 2026 — FPT Software Europe Sponsor Challenge (Track 1)  
> **Topic**: AI-Powered Proposal Scorer & Reviewer  
> **Framework**: Agno + Google Gemini

---

## 1. Executive Summary & Problem Overview

In enterprise sales and pre-sales, proposals often undergo manual, inconsistent, and rushed reviews right before client deadlines. The goal of the **Proposal Scorer** is to act as an objective, automated second reviewer that evaluates draft proposals against the client's Request for Proposal (RFP).

Rather than writing proposals from scratch, the system evaluates an existing draft, scoring it across standard rubrics, detecting compliance gaps, highlighting missed constraints, and providing concrete, copy-pasteable rewrites.

---

## 2. System Inputs & Outputs

### 2.1. System Inputs
* **Client RFP / Project Brief (Markdown/PDF)**: Contains client requirements, technical constraints, budget range, deadlines, and delivery expectations (e.g., [`rfp_nordframe.md`](sample_data/rfp_nordframe.md)).
* **Draft Proposal (Markdown/PDF)**: The vendor's draft response to be reviewed (e.g., [`response_1_weak.md`](sample_data/response_1_weak.md) to [`response_4_overpromise.md`](sample_data/response_4_overpromise.md)).
* **Configuration (Optional)**: User-adjustable criteria weights, custom rubrics, or AI-suggested client priorities.

### 2.2. System Outputs
* **Level 1 — Rubric Scores (1–5)**:
  1. *Problem Understanding*
  2. *Scope & Deliverables Clarity*
  3. *Pricing Clarity*
  4. *Timeline Clarity*
  5. *Completeness vs. RFP Requirements*
  6. *Tone & Persuasiveness*
  7. *Risk/Assumptions Transparency*
  * Overall aggregated score & Go/No-Go readiness verdict.
* **Level 2 — Gap Analysis & Actionable Fixes**:
  * Categorized issue flags: `MISSING_REQUIREMENT`, `VAGUE_SPECIFICATION`, `CONTRADICTION/OVERPROMISING`, `DEFERRED_PRICING_TIMELINE`.
  * Concrete suggested fixes (drafted replacement paragraphs, concrete milestone tables, SLA clauses).
* **Level 3 — Citations & Grounding**:
  * Exact bidirectional citations pointing back to the specific RFP requirement and proposal section.
  * Detected client priorities inferred from the RFP.

---

## 3. Four Key Quality Assurance Pillars

| Pillar | Requirement | Failure Mode to Prevent |
| :--- | :--- | :--- |
| **1. Specific & Actionable** | Every flagged issue must link to an exact section and include a drafted fix. | Vague advice like *"improve clarity"* or *"elaborate on pricing"*. |
| **2. True RFP Grounding** | The proposal must be cross-referenced against extracted RFP requirements. | Scoring the proposal in isolation as a generic standalone essay. |
| **3. Traceability & No Hallucinations** | Citations must be factually grounded in real source text. | Inventing non-existent RFP section numbers or misquoting. |
| **4. Interactive Reliability** | Fast, deterministic execution during live judge demos. | Crashing on unseen documents, broken JSON parsing, or timeout latency. |

---

## 4. Architectural Methods to Solve the Problem

```
+-------------------------------------------------------------------------+
|                  METHOD COMPARISON ARCHITECTURES                        |
+-------------------------------------------------------------------------+

Method 1: Single-Prompt Mega-Agent
[RFP + Proposal] ---> (Single LLM Prompt + Pydantic Schema) ---> [Scorecard + Fixes]

Method 2: Sequential Multi-Agent Pipeline (Agno Team)
[RFP] --------------> [Agent 1: RFP Extractor] ---> Requirement Checklist
                                                            |
[Proposal] ---------> [Agent 2: Compliance Auditor] <-------+
                                   |
                             Audit Matrix (Pass/Fail/Vague)
                                   |
                      [Agent 3: Scorer & Fixer] ---> [Scorecard + Fixes]

Method 3: Vector RAG (Chunk & Cross-Match)
[Proposal Chunks] ---> [Vector Search vs RFP] ---> [Chunk Evaluation] ---> [Merge]

Method 4: Multi-Agent + Deterministic Python Guardrail (Recommended)
[Method 2 Pipeline] ---> [Raw Structured Output with Verbatim Quotes]
                                   |
                        {Python Substring Verifier}
                         /                        \
           [Valid: Render UI]         [Mismatch: Auto-Correct / Fallback]
```

---

### Method 1: Single-Prompt Mega-Agent (Direct Structured Output)
* **Description**: Passes both documents into a single prompt with strict Pydantic constraints and few-shot examples taken from [`scoring_example.md`](sample_data/scoring_example.md).
* **Pros**:
  * Fastest runtime (~2–4s latency).
  * Simplest code implementation (~50 lines).
  * Minimal token consumption.
* **Cons**:
  * Prone to cognitive overload: LLM can miss negative constraints (e.g., *"no database migration"*).
  * Weaker adherence to requirement-by-requirement cross-referencing.

---

### Method 2: Sequential Multi-Agent Pipeline (`agno.team.Team`)
* **Description**: Separates responsibilities across a team of specialized agents:
  1. **RFP Extractor Agent**: Analyzes the RFP to build a structured requirement matrix (deliverables, constraints, SLA, budget, timeline).
  2. **Compliance Auditor Agent**: Evaluates each requirement against the proposal, classifying each as `MET`, `PARTIAL`, `MISSING`, or `VIOLATED`.
  3. **Scorer & Fixer Agent**: Derives scores based strictly on the audit matrix and writes concrete paragraph replacements.
* **Pros**:
  * Strongest RFP grounding: prevents evaluating the proposal in isolation.
  * Highly explainable: intermediate audit matrix can be visualized in the UI.
  * Accurate and objective scoring.
* **Cons**:
  * 3 sequential LLM inferences increase latency (~6–9s).

---

### Method 3: RAG with Vector Retrieval (Chunk & Cross-Match)
* **Description**: Indexes the RFP into vector embeddings, performs semantic similarity searches against proposal sections, and evaluates retrieved pairs.
* **Pros**:
  * Scales to hundreds of pages or multi-document repositories.
* **Cons**:
  * **Harmful for hackathon scope**: Sample documents are 2–5 pages and fit comfortably in Gemini's 1M+ token context window.
  * **Negative Constraint Blindness**: Vector retrieval struggles to catch omissions (e.g. noticing that a database constraint was never mentioned).
  * Adds unnecessary complexity and points of failure (embedding model latency, vector database setup).

---

### Method 4: Multi-Agent + Deterministic Python Guardrail (Recommended)
* **Description**: Builds on Method 2 with an automated, non-LLM Python verification step:
  * Pydantic schema mandates `rfp_verbatim_quote: str` and `proposal_verbatim_quote: str`.
  * Python post-processing verifies whether the exact quote exists in the source text:
    ```python
    def verify_citation(quote: str, source_text: str) -> bool:
        return quote.strip().lower() in source_text.lower()
    ```
  * Guarantees 0% hallucinated citations.
* **Pros**:
  * 100% citation traceability.
  * Directly fulfills all 4 hackathon judging criteria.
  * Impressive technical differentiator for live judging.
* **Cons**:
  * Requires explicit prompting to ensure verbatim quotations.

---

## 5. Comparative Trade-Off Matrix

| Dimension | Method 1: Single Mega-Agent | Method 2: Multi-Agent Pipeline | Method 3: Vector RAG | Method 4: Multi-Agent + Python Guardrail |
| :--- | :---: | :---: | :---: | :---: |
| **True RFP Grounding** | Moderate | **Very High** | Moderate | **Very High** |
| **Specific & Actionable Fixes** | High | **Very High** | Moderate | **Very High** |
| **Citation Traceability** | Moderate | High | Moderate | **100% Guaranteed** |
| **Hallucination Resistance** | Moderate | High | Moderate | **Highest** |
| **Live Demo Latency** | **Fastest (2–4s)** | Good (6–8s) | Slower (8–12s) | Good (6–8s) |
| **Implementation Complexity** | Lowest | Moderate | High (Unnecessary) | Moderate–High |
| **Suitability for SiviHack 2026** | Good Baseline / MVP | **Strong Competitor** | Not Recommended | **Winning Architecture** |

---

## 6. Implementation Roadmap for the Hackathon

1. **Phase 1: Working MVP (Method 1)**
   * Define Pydantic output schema for scores, issues, and suggested fixes.
   * Connect Agno Agent with `gemini-2.5-flash`.
   * Validate against `response_1_weak.md` and benchmark against `scoring_example.md`.

2. **Phase 2: Multi-Agent Decomposition (Method 2)**
   * Split into `RFPExtractor` $\rightarrow$ `ComplianceAuditor` $\rightarrow$ `ProposalScorer`.
   * Validate against all 4 benchmark datasets (`weak`, `medium`, `strong`, `overpromise`).

3. **Phase 3: Python Guardrails & Traceability (Method 4)**
   * Add exact quote verification and section mapping.
   * Implement automated rubric scoring calculation based on compliance percentages.

4. **Phase 4: Live Interactive UI**
   * Build a fast Streamlit or web UI allowing judges to paste/upload unseen RFPs and proposals.
   * Render side-by-side scorecard, compliance checklist, and copyable suggested fixes.
