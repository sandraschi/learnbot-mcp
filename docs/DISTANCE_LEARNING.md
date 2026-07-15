# Distance Learning Architecture — Master/Slave Language School

**Status**: Draft  
**Date**: 2026-07-15

## Concept

A language teacher runs a **master** learnbot-mcp instance. Students connect via a lightweight **slave** client. The teacher manages rosters, timetables, lesson plans, and progress tracking. Students get a personalized learning interface with chat, lessons, vocabulary review, and speaking practice.

## Architecture

```
MASTER (Teacher — Goliath or cloud VM)
  learnbot-mcp
    ├── REST API + Webapp (serves teacher + all students)
    ├── Lesson depot (all lessons, all classes)
    ├── Student roster (users, classes, groups)
    ├── Timetable (scheduled lessons, assignments)
    ├── Progress tracking (vocab mastery, quiz scores, time spent)
    │
    ├── speech-mcp (Gemini TTS — teacher voice demo)
    ├── Ollama (LLM — shared across all students)
    └── Tailscale Funnel (public HTTPS if students are external)
          │
          ▼
SLAVE (Student — web browser, no install)
  Connects to master URL. Sees only their own assignments.
  Features:
    ├── Chat with teacher's AI persona (language practice)
    ├── Assigned lessons (from teacher's depot)
    ├── Vocabulary review (spaced repetition)
    └── Pronunciation practice (via browser Web Speech API)

  (Optional) Offline mode:
    └── Tauri shell — caches lessons locally
    └── Tiny Ollama — offline vocab drills
```

## Student Management Data Model

```sql
CREATE TABLE students (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    email       TEXT UNIQUE,
    pass_hash   TEXT,              -- bcrypt, optional for simple deployments
    language    TEXT DEFAULT 'ja',
    level       TEXT DEFAULT 'N4',
    timezone    TEXT DEFAULT 'UTC',
    created_at  TEXT NOT NULL
);

CREATE TABLE classes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,     -- "Monday Evening A2"
    language    TEXT DEFAULT 'ja',
    level       TEXT DEFAULT 'N4',
    teacher_id  INTEGER,
    created_at  TEXT NOT NULL
);

CREATE TABLE class_students (
    class_id    INTEGER REFERENCES classes(id),
    student_id  INTEGER REFERENCES students(id),
    PRIMARY KEY (class_id, student_id)
);

CREATE TABLE assignments (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    class_id    INTEGER REFERENCES classes(id),
    lesson_id   INTEGER REFERENCES lessons(id),
    due_at      TEXT,               -- ISO 8601 deadline
    assigned_at TEXT NOT NULL,
    completed   INTEGER DEFAULT 0
);

CREATE TABLE progress (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id  INTEGER REFERENCES students(id),
    lesson_id   INTEGER REFERENCES lessons(id),
    quiz_score  REAL,              -- 0.0 - 1.0
    time_spent  INTEGER,           -- seconds
    completed_at TEXT,
    vocab_mastered INTEGER DEFAULT 0,
    vocab_total   INTEGER DEFAULT 0
);
```

## Deployment Tiers

| Tier | Setup | Cost | Who |
|------|-------|------|-----|
| **1 — Local** | Master on Goliath, students on LAN | Free | Family, friends |
| **2 — Tailscale** | Master + Tailscale Funnel for external access | Free | Remote students |
| **3 — Cloud VM** | Master on $5/mo VPS (Hetzer/Linode) | ~$5-15/mo | Small classes |
| **4 — Managed** | Auth, payments, multiple teachers | Business | Language school |

Tier 1 and 2 require zero additional infrastructure — the code already runs on Goliath.
Tier 3 needs a cloud VM with Ollama + the stack. Tier 4 is a full SaaS product.

## Student "Slave" Options

| Option | Install | Offline | STT | Cost |
|--------|---------|---------|-----|------|
| **Web browser** (PWA) | None | Limited (cached pages) | Web Speech API | Free |
| **Tauri desktop app** | Download 5MB | Full (cached lessons) | speech-mcp | Free |
| **Tiny Ollama on slave** | `ollama pull` | Offline vocab drills | Web Speech | Student's HW |

The PWA is the default — works immediately, no install, no config. The Tauri slave adds offline resilience. Tiny Ollama adds offline LLM for spaced repetition drills when the master is unreachable.

## Teacher Interface (Webapp)

### Roster page
- Add/remove students, assign to classes
- Import via CSV (email, name, level)
- Each student gets a login link (simple: ?student_id=X&token=Y)

### Timetable page  
- Calendar view with lesson assignments per class
- Drag lesson from depot onto a date slot → creates assignment
- Students see "Upcoming: Lesson X — due Friday"

### Progress dashboard
- Grid: students × lessons → completion status + quiz score + time
- Export to CSV for report cards
- Vocab mastery heatmap (which words each student struggles with)

### Lesson planner
- Existing Lessons page + "Assign to class" button
- Scheduled release: lessons become available at a set time

## Implementation Order

| Phase | What | Depends on |
|-------|------|-----------|
| **P1** | Student CRUD + class CRUD + basic auth | — |
| **P2** | Assignment system + timetable | P1 |
| **P3** | Student-facing restricted view (only their assignments) | P2 |
| **P4** | Progress tracking + quiz scoring | P3 |
| **P5** | Export/CSV for report cards | P4 |
| **P6** | Tauri slave client with offline mode | P3 |
| **P7** | Payment tier (Stripe) for multi-teacher | P6 |

## Revenue Model (if applicable)

- **Tier 1-2**: Free (personal use)
- **Tier 3**: €10/teacher/month (cloud hosting included)
- **Tier 4**: €50/school/month (multi-teacher, analytics, priority support)

## Open Questions

- Auth: simple token-based or full OAuth?
- Student isolation: same webapp with role-based views or separate build?
- Real-time: WebSocket for teacher seeing student progress during a lesson?
- Voice: student submits audio for speaking drills → teacher reviews async?

## Related

- [PRD.md](PRD.md)
- [SPEC.md](SPEC.md)
- [TODO.md](../TODO.md)
