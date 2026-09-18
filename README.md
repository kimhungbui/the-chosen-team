# Proposal Scorer — FPT Software Europe (SiviHack 2026)

AI reviewer/evaluator chấm điểm draft proposal đối chiếu với RFP khách hàng: điểm 7 tiêu chí, phát hiện gap, trích dẫn bằng chứng, gợi ý sửa cụ thể.

## Kiến trúc

```
Frontend (React + Vite)          Backend (FastAPI)
app/                             api/
└── Upload RFP + Proposal  ───►  POST /evaluate
                                 ├── 2-stage Agno Gemini agents
                                 ├── Rule-engine fallback
                                 └── SQLite history (data/history.db)
```

## Setup

**1. Tạo virtual environment và cài dependencies:**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**2. Thêm Gemini API key** — copy `.env.ex` thành `.env`:

```bash
cp .env.ex .env
```

```env
GEMINI_API_KEY=your key here
```

Không có key → backend tự chạy rule engine (offline).

## Khởi động

**1. Backend:**

```bash
python -m uvicorn api.server:app --host 0.0.0.0 --port 8000 --reload
```

**2. Frontend** (terminal khác):

```bash
cd app
npm run dev
# hoặc
bun dev
```

Frontend dev server proxy sẵn `/evaluate`, `/history`, `/stats` sang `http://localhost:8000`.

## API

- Swagger UI: `http://localhost:8000/docs`
- Chi tiết endpoints & schemas: [`API_CONTRACT.md`](API_CONTRACT.md)
