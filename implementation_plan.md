# ProctorAI — Mobile Companion PWA

Build a production-grade Progressive Web App (PWA) that serves as the **mobile companion** to the existing desktop AI Exam Proctoring backend. The mobile app is used by **students** to take exams on their phones and by **proctors/admins** to monitor sessions in real-time.

## Backend Context (What Your Friend Built)

| Layer | Tech | Details |
|-------|------|---------|
| API | FastAPI | REST endpoints at `/auth`, `/exams`, `/sessions` |
| Auth | JWT + bcrypt | 8-hour tokens, role-based (`student`, `proctor`, `admin`) |
| DB | PostgreSQL (SQLAlchemy) | `users`, `exams`, `exam_sessions` tables |
| Cache | Redis | Live session state (`penalty_score`, `state`) for fast reads |
| State Machine | Python | CLEAR → CAUTION → WARNING → ALERT → CRITICAL → TERMINATED |

The mobile app will connect to the **same backend** — no duplicate APIs needed.

---

## User Review Required

> [!IMPORTANT]
> **PWA vs Native**: Since you mentioned system constraints with Flutter/Android Studio previously, I'm proposing a **PWA (Progressive Web App)**. It installs on any phone like a native app, works offline, uses the camera, and requires zero app store deployment. This is the most powerful approach given the constraints.

> [!IMPORTANT]
> **Mock Data Mode**: The app will ship with a **mock data layer** that can toggle on/off. When the backend isn't running, the entire app functions with realistic fake data — perfect for demos and presentations.

> [!WARNING]
> **Backend URL**: The app will need to know where the FastAPI backend is running. I'll add a settings screen where you can configure the API URL. For now, it defaults to `http://localhost:8000`.

---

## Open Questions

1. **Camera Proctoring on Mobile**: Should the student's front camera feed be analyzed on-device using TensorFlow.js (face detection, gaze tracking, multiple face detection)? This is powerful but adds ~2MB to the bundle.
2. **Push Notifications**: Should proctors receive push notifications when a student's state changes to WARNING or above?
3. **Exam Content**: Does the backend serve actual exam questions, or does the mobile app only handle proctoring (camera monitoring + session state) while questions are displayed elsewhere?

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  ProctorAI PWA                  │
├─────────────────────────────────────────────────┤
│  Service Worker (offline + caching)             │
│  Web App Manifest (installable)                 │
├─────────────────────────────────────────────────┤
│  Pages:                                         │
│  ├── Login / Register                           │
│  ├── Student Dashboard                          │
│  │   ├── Upcoming Exams                         │
│  │   ├── Active Exam Session (Camera + Timer)   │
│  │   └── Session History                        │
│  ├── Proctor Dashboard                          │
│  │   ├── Live Monitoring Grid                   │
│  │   ├── Student Detail View                    │
│  │   └── Alert Feed                             │
│  └── Admin Panel                                │
│      ├── Create Exam                            │
│      ├── Manage Users                           │
│      └── Analytics Overview                     │
├─────────────────────────────────────────────────┤
│  Services:                                      │
│  ├── API Client (fetch wrapper + JWT)           │
│  ├── Mock Data Engine                           │
│  ├── Camera Service (MediaDevices API)          │
│  ├── Face Detection (TensorFlow.js)             │
│  └── State Manager (reactive store)             │
└─────────────────────────────────────────────────┘
```

---

## Proposed Changes

### File Structure

```
mobile/
├── index.html              ← Entry point + PWA meta
├── manifest.json           ← PWA manifest
├── sw.js                   ← Service worker
├── css/
│   ├── design-system.css   ← Tokens, variables, animations
│   ├── components.css      ← Reusable component styles
│   └── pages.css           ← Page-specific layouts
├── js/
│   ├── app.js              ← Router + app shell
│   ├── api.js              ← API client + JWT management
│   ├── mock.js             ← Mock data engine
│   ├── state.js            ← Reactive state manager
│   ├── camera.js           ← Camera + face detection
│   ├── pages/
│   │   ├── login.js        ← Login/Register page
│   │   ├── student.js      ← Student dashboard
│   │   ├── exam-session.js ← Live exam taking view
│   │   ├── proctor.js      ← Proctor monitoring dashboard
│   │   └── admin.js        ← Admin panel
│   └── components/
│       ├── nav.js          ← Bottom navigation bar
│       ├── card.js         ← Exam/session cards
│       ├── modal.js        ← Modal dialogs
│       ├── toast.js        ← Toast notifications
│       ├── chart.js        ← Risk score charts
│       └── camera-feed.js  ← Camera preview component
├── assets/
│   ├── icons/              ← PWA icons (generated)
│   └── sounds/             ← Alert sounds
└── README.md
```

All files are **[NEW]**.

---

### Core: Design System (`css/design-system.css`)

- Dark theme with deep navy/charcoal base (`#0a0e1a`, `#131927`)
- Accent colors: Emerald green (CLEAR), Amber (CAUTION), Orange (WARNING), Red (ALERT/CRITICAL)
- Glassmorphism cards with `backdrop-filter: blur()`
- CSS custom properties for all tokens
- Fluid typography scale
- Keyframe animations: pulse, glow, slide-in, fade, shake (for alerts)
- Mobile-first responsive breakpoints

### Core: App Shell & Router (`js/app.js`)

- Hash-based SPA router (`#/login`, `#/student`, `#/exam/:id`, `#/proctor`, `#/admin`)
- Route guards based on JWT role
- Smooth page transitions with CSS animations
- App shell with bottom navigation for authenticated users

### Core: API Client (`js/api.js`)

- Fetch wrapper with automatic JWT header injection
- Token storage in `localStorage` with expiry checking
- Request/response interceptors
- Automatic redirect to login on 401
- Base URL configurable via settings

### Core: Mock Data Engine (`js/mock.js`)

- Toggle via `localStorage.getItem('MOCK_MODE')`
- Generates realistic students, exams, sessions
- Simulates real-time state changes (penalty scores increasing over time)
- Fake camera violation events (face not detected, multiple faces, tab switch)
- Randomized but deterministic data for consistent demos

### Core: Reactive State (`js/state.js`)

- Lightweight observable store pattern
- Subscribe/notify for UI updates
- Persists critical state to `localStorage`

---

### Page: Login & Register (`js/pages/login.js`)

- Animated logo + branding
- Toggle between Login / Register forms
- Role selector (student/proctor/admin) on register
- College ID field
- JWT stored on successful auth
- Form validation with animated error states
- Biometric-style animation on the login button

### Page: Student Dashboard (`js/pages/student.js`)

- **Header**: Welcome message + avatar + risk score badge
- **Upcoming Exams**: Cards with exam name, date, duration, countdown timer
- **Active Session Banner**: Prominent banner if exam is in progress
- **Session History**: Past exams with final state (color-coded)
- **Quick Stats**: Total exams taken, average risk score, clean sessions count
- Pull-to-refresh gesture support

### Page: Exam Session (`js/pages/exam-session.js`)

- **Full-screen mode** with camera preview (picture-in-picture style)
- **Live Timer**: Countdown with animated ring
- **Risk Score Gauge**: Animated circular gauge showing current penalty score
- **State Badge**: Real-time state indicator (CLEAR → TERMINATED) with color + pulse
- **Violation Log**: Scrollable list of detected violations with timestamps
- **Camera Feed**: Front camera with face detection overlay (bounding box on detected face)
- **Lock Controls**: Cannot leave the page without triggering a violation
- **End Exam** button with confirmation modal

### Page: Proctor Dashboard (`js/pages/proctor.js`)

- **Monitoring Grid**: Card grid showing all active students
  - Each card: student name, risk score bar, current state badge, mini camera feed
  - Cards sorted by risk score (highest first)
  - Click to expand to full detail view
- **Alert Feed**: Real-time scrolling feed of state changes across all sessions
- **Filters**: Filter by state (CLEAR, CAUTION, WARNING, etc.)
- **Stats Bar**: Total active sessions, students at risk, terminated count
- **Quick Actions**: Terminate session, send warning, flag for review

### Page: Admin Panel (`js/pages/admin.js`)

- **Create Exam Form**: Title, description, date/time picker, duration
- **Exam List**: All exams with active/archived toggle
- **User Management**: List users, filter by role
- **Analytics Cards**: Total exams, total sessions, average risk score, violation rate

---

### Components

| Component | Description |
|-----------|-------------|
| `nav.js` | Bottom tab bar with icons (Home, Monitor, Admin, Settings), role-based visibility |
| `card.js` | Glassmorphism card factory with variants (exam, session, student, stat) |
| `modal.js` | Animated modal with backdrop blur |
| `toast.js` | Auto-dismissing toast notifications with severity levels |
| `chart.js` | Canvas-based mini charts (risk score timeline, pie charts) |
| `camera-feed.js` | Camera stream with face detection overlay |

---

### PWA Features

#### `manifest.json`
- App name: "ProctorAI"
- Theme color: `#0a0e1a`
- Display: `standalone`
- Orientation: `portrait`
- Icons at 192x192 and 512x512

#### `sw.js`
- Cache-first strategy for static assets
- Network-first for API calls
- Offline fallback page
- Background sync for queued violation reports

---

## Verification Plan

### Automated Tests
- Open the PWA in the browser tool and verify:
  - Login flow works with mock data
  - Student dashboard renders with upcoming exams
  - Exam session page shows camera feed and timer
  - Proctor dashboard shows monitoring grid
  - Navigation between pages is smooth
  - PWA installs correctly (manifest check)

### Manual Verification
- Test on actual mobile phone by serving over local network
- Verify camera access works on mobile browsers
- Check responsive layouts at various screen sizes
- Test offline mode with service worker
