# AGENTS.md — AI Exam Proctoring Software

## Quick Start

```bash
cd backend
uvicorn app.main:app --reload
```

Requires **PostgreSQL** running and **Redis** running. Create database `aiproctor_db` before first run. `.env` in `backend/` supplies `DATABASE_URL`, `SECRET_KEY`, `REDIS_URL`.

Tables are auto-created on startup via `Base.metadata.create_all()` — no migrations.

## Architecture

- **Backend**: FastAPI (Python 3.12) in `backend/app/`. Serves both API and HTML pages via Jinja2.
- **Frontend**: Server-rendered HTML templates (`frontend/templates/`) + static JS (`frontend/static/anticheat.js`). No build step.
- **Database**: PostgreSQL via SQLAlchemy. Multi-tenant by `college_id`.
- **Live state**: Redis stores per-session `penalty_score` and `state` with 24h TTL. Keys: `session:<id>`, `cooldown:<id>:<event>`, `streak:<id>:<event>`, `deesc:<id>`.

## Hardcoded Windows Paths — MUST FIX FOR OTHER OS

`backend/app/main.py:21` and `backend/app/config.py:1` contain absolute Windows paths:
- Static files: `C:\Swayam\Codes\Proctoring Software\frontend\static`
- Templates: `C:\Swayam\Codes\Proctoring Software\frontend\templates`
- Debug frame output: `backend/app/detection.py:237` writes to `C:\Swayam\Codes\Proctoring Software\backend\app\debug_frame.jpg`

These will break on Linux/macOS. Use `os.path` or `pathlib` relative to the project root.

## Detection Pipeline

Backend runs these analyses on each frame (sent every 5s from client):
| Function | Module | Detects |
|---|---|---|
| `analyse_face` | `detection.py` | no face, multiple faces, camera blocked |
| `analyse_eye_gaze` | `detection.py` | gaze_away |
| `analyse_head_pose` | `detection.py` | head_turned (yaw >30°), looking_down (pitch < -20°) |
| `analyse_objects` | `detection.py` | YOLOv8s: phone, keyboard, book, monitor, laptop, earphones, extra person |
| `analyse_audio` | `detection.py` | voice_detected via WebRTC VAD |

YOLO model loaded at import time from `backend/yolov8s.pt`. MediaPipe models also initialized at module load.

Client-side `anticheat.js` detects: tab_switch, keyboard shortcuts, copy/paste, right_click, devtools_open.

## Penalty System (`penalty.py`)

- States: `CLEAR → CAUTION (≤30) → WARNING (≤60) → ALERT (≤85) → CRITICAL (≤99) → TERMINATED (≥100)`
- Score decays by 1 point every 30s via background thread (`decay.py`) when no violations occur
- Cooldown: same violation type ignored for 3s
- Streak multiplier: escalates if multiple violations within 60s window
- State multiplier: 1.5x in ALERT, 2.0x in CRITICAL
- Combined multiplier = streak_m + state_m - 1.0

## API Routes

| Prefix | File | Notes |
|---|---|---|
| `/auth` | `routers/auth.py` | register, login (JWT, 8h expiry), /me, /admin-only |
| `/exams` | `routers/exams.py` | POST /creation (admin only), GET /listings |
| `/session` | `routers/session.py` | POST /start, GET /:id/state, POST /:id/violation_event, POST /:id/frame, POST /:id/audio |
| `/` | `routers/pages.py` | GET /exam/:session_id — serves exam HTML (hardcoded sample questions) |

## Key Gotchas

- **No tests exist** — add tests before making changes to detection or penalty logic
- **No linter/formatter configured** — pick one before committing code
- **`pages.py` hardcodes a JWT token** in template context — not real auth flow for exam page
- **`ExamSession` model has `terminated_at` column but `session.py` sets `ended_at`** — typo/bug on line 160
- **`get_state` is defined in both `penalty.py` and `session.py`** — duplicate, could diverge
- **Venv at repo root** (`.venv/`) but all Python code lives under `backend/` — activate from root
- **`requirement.txt` may have encoding issues** (observed BOM/UTF-16) — use `pip freeze > requirements.txt` to regenerate if needed

## Directory Structure

```
backend/app/
  main.py          — FastAPI app entry, mounts static, includes routers, starts decay thread
  config.py        — Jinja2 templates dir
  database.py      — SQLAlchemy engine, session, Base
  model.py         — ORM: User, Exam, ExamSession, ViolationEvents, StateTransition
  schemas.py       — Pydantic request/response models
  auth.py          — bcrypt passwords, JWT creation/validation, role guard
  detection.py     — MediaPipe + YOLO + WebRTC VAD analysis functions
  penalty.py       — Violation matrix, score calculation, state thresholds
  decay.py         — Background thread that decays Redis scores every 30s
  routers/         — auth.py, exams.py, session.py, pages.py
```
