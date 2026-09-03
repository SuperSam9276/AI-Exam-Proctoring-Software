# WADJET - AI Proctor — Intelligent Exam Proctoring System

An AI-powered exam proctoring platform built for colleges and universities. Monitors students in real time during online exams using computer vision, audio analysis, and browser-level detection. Flags violations, escalates threats, and gives invigilators a live dashboard to act on.

---

## What It Does

Students sit exams through a secure browser interface while the system watches for cheating behaviour. Every 5 seconds a webcam frame is analysed by MediaPipe and YOLOv8. Audio is sampled every 2 seconds by WebRTC VAD. Browser events are intercepted by a JavaScript anti-cheat module. Each detected violation adds to a live risk score stored in Redis. As the score rises the student moves through threat states — from CLEAR to TERMINATED. Invigilators watch this happen in real time on their dashboard.

---

## Features

### AI Detection
- **Face detection** — detects face absence, low confidence presence, and camera blocking via MediaPipe
- **Gaze tracking** — detects when a student looks away from the screen using Face Mesh iris landmarks
- **Head pose estimation** — detects sideways head turns and downward gaze via 3D landmark projection
- **Object detection** — detects phones, earphones, books, second keyboards, second monitors, and persons behind the student via YOLOv8 nano
- **Liveness detection** — detects photo spoofing (no blink) and video loop spoofing (robotic blink) via Eye Aspect Ratio
- **Audio VAD** — detects voice activity and multiple voices via WebRTC VAD

### Browser Anti-Cheat
- Tab switching and window blur detection
- Copy, paste, and cut interception and blocking
- Keyboard shortcut blocking (F12, Ctrl+C/V/U/S/A, PrintScreen)
- Right-click blocking
- Real-time violation reporting to backend

### Scoring Engine
- Six threat states: CLEAR → CAUTION → WARNING → ALERT → CRITICAL → TERMINATED
- Per-violation cooldown windows prevent spam scoring
- Streak multipliers escalate repeated violations
- State-aware multipliers increase penalties in high-alert states
- Score decay prevents states from persisting after behaviour improves
- Decay never crosses state boundaries — only invigilator action de-escalates

### Invigilator Dashboard
- Live grid of all active student sessions with colour-coded state badges
- Real-time score updates via FastAPI WebSockets — no polling
- Resume paused sessions, manually escalate, or terminate with reason
- Download PDF violation report per student

### Reporting
- PDF report generated on termination and submission using ReportLab
- Per-student violation log with timestamps, points, multipliers, and state after
- Integrity score (0–100) calculated from violation history at submission
- Integrity bands: Clean / Minor Concerns / Review Recommended / Serious Concerns / Compromised

### Auth and Roles
- JWT authentication with 8-hour expiry
- Four roles: student, invigilator, admin, senior_admin
- Role-based redirect on login — students to exam, invigilators to dashboard, admins to admin panel
- Session token stored in sessionStorage — cleared on tab close

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python 3.12) |
| Database | PostgreSQL 16 + SQLAlchemy |
| Cache / State | Redis 7 |
| Face Detection | MediaPipe FaceDetection + Face Mesh |
| Object Detection | YOLOv8 nano (Ultralytics) |
| Audio | WebRTC VAD |
| Real-time | FastAPI WebSockets |
| Auth | PyJWT + bcrypt |
| PDF Reports | ReportLab |
| Frontend | Jinja2 Templates + Vanilla JS |
| Containerisation | Docker + Docker Compose |
| Deployment | Railway.app |

---

## Project Structure

```
ai-proctor/
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env
│   └── app/
│       ├── main.py              # FastAPI app, router registration, startup
│       ├── database.py          # SQLAlchemy engine and session
│       ├── model.py             # Database models
│       ├── schemas.py           # Pydantic schemas
│       ├── auth.py              # JWT, bcrypt, get_current_user
│       ├── penalty.py           # PENALTY_MATRIX, scoring engine constants
│       ├── detection.py         # MediaPipe + YOLO detection functions
│       ├── decay.py             # Background score decay thread
│       ├── reports.py           # ReportLab PDF generation
│       ├── ws_manager.py        # WebSocket connection manager
│       └── routers/
│           ├── auth.py          # Register, login
│           ├── exams.py         # Exam creation and listing
│           ├── session.py       # Violation events, frames, audio, submission
│           ├── invigilator.py   # Dashboard data, actions, report download
│           ├── ws.py            # WebSocket endpoint
│           └── pages.py         # Jinja2 page routes
├── frontend/
│   ├── static/
│   │   └── anticheat.js         # Browser-side detection and API calls
│   └── templates/
│       ├── login.html
│       ├── exam_template.html
│       ├── invigilator.html
│       └── admin.html
├── docker-compose.yml
└── .gitignore
```

---

## Violation Types

### Visual (MediaPipe)
| Violation | Points | Detection |
|---|---|---|
| face_not_visible | 8 | Confidence < 0.7 |
| face_absent | 20 | No face for 10s |
| camera_blocked | 20 | Frame undecodable |
| multiple_faces | 25 | > 1 detection |
| gaze_away | 5 | Iris offset ratio |
| head_turned | 10 | Yaw > 30° |
| looking_down | 8 | Pitch < -20° |
| identity_mismatch | 50 | Embedding mismatch |

### Object Detection (YOLO)
| Violation | Points | Object |
|---|---|---|
| phone_detected | 30 | cell phone |
| earphone_detected | 25 | headphones/earphones |
| book_detected | 20 | book |
| second_keyboard_detected | 25 | keyboard |
| second_monitor_detected | 35 | tv/laptop/monitor |
| person_behind_detected | 40 | second person |

### Audio (WebRTC VAD)
| Violation | Points | Trigger |
|---|---|---|
| voice_detected | 10 | Speech in frame |
| multiple_voices | 25 | Multiple voice patterns |

### Browser (JavaScript)
| Violation | Points | Trigger |
|---|---|---|
| tab_switch | 10 | visibilitychange / blur |
| keyboard_shortcut | 8 | F12, Ctrl+U/S/A |
| print_screen | 10 | PrintScreen key |
| copy_attempt | 5 | Ctrl+C / copy event |
| paste_attempt | 5 | Ctrl+V / paste event |
| right_click | 3 | contextmenu event |
| devtools_open | 15 | F12 / Ctrl+Shift+I |

### Liveness (EAR)
| Violation | Points | Trigger |
|---|---|---|
| liveness_fail_no_blink | 35 | No blink for 30s |
| liveness_fail_robotic_blink | 50 | Interval variance < 0.15 |

---

## Threat States

| State | Score | Action |
|---|---|---|
| CLEAR | 0 | Normal monitoring |
| CAUTION | 1–30 | Silent toast to student |
| WARNING | 31–60 | Full modal, invigilator notified |
| ALERT | 61–85 | Exam paused, invigilator must resume |
| CRITICAL | 86–99 | Locked, senior admin must release |
| TERMINATED | 100+ | Permanent shutdown, PDF generated |

---

## Getting Started

### Prerequisites
- Python 3.12
- PostgreSQL 16
- Redis 7
- Docker (for containerised deployment)

### Local Development

```bash
# Clone the repository
git clone https://github.com/yourusername/ai-proctor.git
cd ai-proctor/backend

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your DATABASE_URL, REDIS_URL, SECRET_KEY

# Start the server
uvicorn app.main:app --reload --host localhost --port 8000
```

### Environment Variables

```env
DATABASE_URL=postgresql://user:password@localhost:5432/aiproctor
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key-minimum-32-characters
```

### Docker

```bash
# Run the full stack
docker compose up --build

# Server available at http://localhost:8000
```

### Railway Deployment

1. Push repository to GitHub
2. Create new Railway project → Deploy from GitHub
3. Add PostgreSQL and Redis services
4. Set `SECRET_KEY` in Variables tab
5. Set Root Directory to `backend`
6. Deploy — Railway provides HTTPS URL automatically

---

## API Overview

| Method | Endpoint | Description |
|---|---|---|
| POST | /auth/register | Register user |
| POST | /auth/login | Login, returns JWT + role |
| POST | /exams/creation | Create exam (admin) |
| GET | /exams/listings | List active exams |
| POST | /session/start | Start exam session |
| POST | /session/{id}/violation_event | Report browser violation |
| POST | /session/{id}/frame | Send webcam frame for AI analysis |
| POST | /session/{id}/audio | Send audio chunk for VAD |
| POST | /session/{id}/submit | Submit exam with answers |
| GET | /session/{id}/state | Get live score and state |
| GET | /invigilator/sessions | All active sessions (invigilator) |
| POST | /invigilator/sessions/{id}/resume | Resume paused session |
| POST | /invigilator/sessions/{id}/terminate | Terminate session |
| GET | /invigilator/sessions/{id}/report | Download PDF report |
| WS | /ws/dashboard | WebSocket for live dashboard updates |

Full interactive docs available at `/docs` when server is running.

---

## Scoring Design Decisions

**Why additive multipliers not multiplicative:** A 7th streak violation in CRITICAL state with multiplicative would reach 6x — a 10pt violation becomes 60pts instantly. Additive (streak + state - 1.0) is fairer and more defensible to institutions reviewing terminations.

**Why decay never crosses state boundaries:** A student in ALERT should not silently drift back to WARNING overnight. Only an invigilator reviewing the situation and hitting Resume should de-escalate. Decay only cleans up noise within a state's score band.

**Why paper_detected was excluded:** YOLOv8 cannot distinguish a cheat sheet from rough working paper. If a college bans rough paper that is an administrative rule enforced before the exam, not a software detection problem.

---

## License

Commercial software — all rights reserved.
Contact for licensing inquiries.

---

## Author

Built by Swayam — solo developer, 5-week build.
