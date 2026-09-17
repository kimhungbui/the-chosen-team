# The Chosen Team — Proposal Scorer & Reviewer

> **SiviHack 2026 — FPT Software Europe Sponsor Challenge (Track 1)**  
> Built with **Agno Multi-Agent Framework** + **Google Gemini (gemini-2.5-flash)** + **Deterministic Python Guardrails (Method 4)**.

---

## 🏗️ Architecture (Method 4)

1. **Agent 1 (`RFPExtractorAgent`)**: Ingests client RFP to build a structured checklist of functional requirements, negative constraints, commercial limits, and client priorities.
2. **Agent 2 (`ComplianceAuditorAgent`)**: Performs a requirement-by-requirement audit against the draft proposal, categorizing each as `MET`, `PARTIAL`, `MISSING`, `CONTRADICTED`, or `DEFERRED`.
3. **Agent 3 (`ScorerAndFixerAgent`)**: Scores the 7 Appendix A criteria and writes concrete, copy-pasteable replacement paragraphs/tables.
4. **Deterministic Python Guardrail**: Verifies citations against source documents, resolves exact line numbers, and mathematically enforces scoring consistency.

---

## 🐳 Running with Docker (Containerized)

### 1. Configure Environment
Copy `.env.ex` to `.env` and insert your Gemini API key:
```bash
cp .env.ex .env
# Edit .env to add your key:
# GEMINI_API_KEY=your_gemini_api_key_here
```

### 2. Run with Docker Compose
```bash
docker compose up --build
```
This builds the container image and runs the evaluation against `sample_data/rfp_nordframe.md` and `sample_data/response_1_weak.md`, outputting the scorecard and saving `eval_report.md`.

### 3. Run with Docker CLI
```bash
# Build image
docker build -t proposal-scorer .

# Run container (passing .env)
docker run --rm --env-file .env -v $(pwd):/app proposal-scorer python main.py --rfp sample_data/rfp_nordframe.md --proposal sample_data/response_1_weak.md
```

---

## 💻 Running Locally (Optional)

```bash
# Install dependencies
pip install -r requirements.txt

# Run evaluation on weak proposal
python main.py --rfp sample_data/rfp_nordframe.md --proposal sample_data/response_1_weak.md

# Run evaluation on strong proposal (contrast)
python main.py --rfp sample_data/rfp_nordframe.md --proposal sample_data/response_3_strong.md
```