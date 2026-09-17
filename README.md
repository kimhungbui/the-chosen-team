# The Chosen Team — Proposal Scorer & Reviewer

> **SiviHack 2026 — FPT Software Europe Sponsor Challenge (Track 1)**  
> Built with **Agno Multi-Agent Framework** + **Google Gemini (gemini-2.5-flash)** + **Deterministic Python Guardrails (Method 4)**.

---

## 🏗️ System Architecture (Method 4)

Instead of relying on a single prompt or fine-tuning weights, the system chains **3 specialized Agno agents** with strict Pydantic schemas and a **deterministic Python guardrail**:

1. **Agent 1 (`RFPExtractorAgent`)**: Ingests the client RFP to build an unambiguous checklist of explicit deliverables, commercial caps (€80k–€120k), delivery dates, and negative constraints (*"no database migration"*).
2. **Agent 2 (`ComplianceAuditorAgent`)**: Performs a systematic matrix audit against the proposal, categorizing each requirement as `MET`, `PARTIAL`, `MISSING`, `CONTRADICTED`, or `DEFERRED`.
3. **Agent 3 (`ScorerAndFixerAgent`)**: Scores the 7 Appendix A criteria and writes concrete, copy-pasteable replacement paragraphs/tables.
4. **Deterministic Python Guardrail**: Verifies citations verbatim against the source markdown, resolves exact line numbers (e.g. `rfp.md:L17`), and locks mathematical score consistency.

---

## 🐳 How to Run in Docker

### 1. Prerequisites
Ensure Docker is installed and running on your machine:
* Docker Desktop or OrbStack
* `docker --version` and `docker compose version`

---

### 2. Configure Environment (Optional for Live Mode)
If you want to use live Google Gemini agents, set your API key in `.env`:
```bash
cp .env.ex .env
# Edit .env:
# GEMINI_API_KEY=your_gemini_api_key_here
```
> **Note:** If no API key is provided, the system **automatically switches to Offline Mock Mode**, allowing you to test the full container build, UI, guardrails, and line resolvers without an API key!

---

### 3. Option A: Launch Interactive Web UI (Recommended)

Start the containerized Web UI with Docker Compose:

```bash
docker compose up --build
```

Once running, open your browser:
👉 **[http://localhost:8080](http://localhost:8080)**

**What you can do in the Web UI:**
* **Dashboard Tab**: Select between the 4 benchmark scenarios (`Weak`, `Medium`, `Strong`, `Overpromising`) or paste custom documents, run evaluation, view 7-criteria scorecard, compliance table, and copy drafted fixes with one click.
* **Side-by-Side Inspector Tab**: Synchronized dual document viewer highlighting the exact RFP requirement and proposal lines simultaneously.
* **Architecture Deep Dive Tab**: Visual pipeline diagram explaining the 3 agents and Python guardrails.

To stop the web UI:
```bash
docker compose down
```

---

### 4. Option B: Run CLI Evaluation in Docker

First, build the Docker image once:
```bash
docker build -t proposal-scorer .
```

Then run the evaluation on any proposal draft:

#### Test on Weak Proposal (`response_1_weak.md`):
```bash
docker run --rm -v $(pwd):/app proposal-scorer python main.py \
  --rfp sample_data/rfp_nordframe.md \
  --proposal sample_data/response_1_weak.md
```
*(Outputs the scorecard, flags missing PostgreSQL/SLAs, and saves `eval_report.md`)*

#### Test on Strong Proposal (`response_3_strong.md` - Contrast Benchmark):
```bash
docker run --rm -v $(pwd):/app proposal-scorer python main.py \
  --rfp sample_data/rfp_nordframe.md \
  --proposal sample_data/response_3_strong.md
```

#### Test with Live Gemini API Key:
```bash
docker run --rm --env-file .env -v $(pwd):/app proposal-scorer python main.py \
  --rfp sample_data/rfp_nordframe.md \
  --proposal sample_data/response_1_weak.md
```

---

### 5. Option C: Run Automated Unit Tests in Docker (Zero API Key Needed)

Execute the deterministic guardrail and schema test suite inside the container:
```bash
docker run --rm -v $(pwd):/app proposal-scorer python -m unittest discover tests -v
```

Expected output:
```text
test_end_to_end_mock_evaluation (test_guardrails.TestGuardrailsOffline.test_end_to_end_mock_evaluation) ... ok
test_find_snippet_line_range (test_guardrails.TestGuardrailsOffline.test_find_snippet_line_range) ... ok
test_mathematical_consistency_guardrail (test_guardrails.TestGuardrailsOffline.test_mathematical_consistency_guardrail) ... ok

----------------------------------------------------------------------
Ran 3 tests in 0.002s

OK
```

---

## 💻 Running Locally without Docker (Optional)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run web UI locally
python web/server.py 8080

# 3. Run CLI evaluation
python main.py --rfp sample_data/rfp_nordframe.md --proposal sample_data/response_1_weak.md

# 4. Run unit tests
python -m unittest discover tests -v
```

---

## 📁 Repository Structure

```text
├── Dockerfile                  # Container build instructions (Python 3.11-slim)
├── docker-compose.yml          # Docker Compose configuration (maps port 8080)
├── requirements.txt            # Pinned dependencies (agno, google-genai, pydantic, rich)
├── README.md                   # Project documentation & run guide
├── PROPOSAL_SCORER_DESIGN.md   # Architecture analysis & comparison of 4 methods
├── pipeline.py                 # Multi-agent orchestrator & report formatter
├── main.py                     # CLI entrypoint supporting live & mock evaluation
├── agents/                     # Specialized Agno Gemini agents
│   ├── rfp_extractor.py        # Agent 1: RFP requirements & negative constraints
│   ├── compliance_auditor.py   # Agent 2: Requirement-by-requirement compliance auditor
│   └── scorer_and_fixer.py     # Agent 3: 7-criteria scorer & draft replacement writer
├── guardrails/                 # Deterministic Python Guardrails
│   └── verifier.py             # Verbatim quote checker, line resolver & math score lock
├── models/                     # Data contracts & Pydantic schemas
│   └── schemas.py              # RFPRequirement, ComplianceMatrix, SuggestedFix, etc.
├── sample_data/                # Hackathon benchmark test datasets
│   ├── rfp_nordframe.md        # Client RFP
│   ├── response_1_weak.md      # Weak proposal (omitted items)
│   ├── response_2_medium.md    # Medium proposal (vague pricing/timeline)
│   ├── response_3_strong.md    # Strong proposal (adheres to all requirements)
│   ├── response_4_overpromise.md # Overpromising proposal (violates constraint)
│   └── scoring_example.md      # Reference benchmark output from challenge
├── tests/                      # Automated test suite
│   └── test_guardrails.py      # Unit tests for guardrails, line mapping & schemas
└── web/                        # Web UI (Interactive live demonstration)
    ├── index.html              # Dashboard, Side-by-Side Inspector & Architecture tabs
    ├── style.css               # Modern dark glassmorphism styling
    ├── app.js                  # Interactive scenario switching & document highlighting
    └── server.py               # Lightweight server with REST API
```