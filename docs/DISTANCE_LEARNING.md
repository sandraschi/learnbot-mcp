# Distance Learning Architecture — Courses, Teaching Agents, Courseware

**Status**: Draft  
**Date**: 2026-07-15

## Concept

Two servers split the distance learning domain:

- **classroom-mcp** (:11105) — students, classes, courses, courseware, timetables, progress, billing
- **learnbot-mcp** (:11104) — lesson content, conversation, TTS, robot, emotion, vocabulary SR

A teacher or institution runs both. Students connect to classroom-mcp's webapp to see their courses, assignments, and progress. The actual learning interaction happens through learnbot-mcp's chat interface or dedicated **teaching agents**.

## Teaching Agents — New Concept

A teaching agent is an AI-driven course instructor. It is not a generic chatbot — it has:

- **Subject expertise** — knows the course curriculum, prerequisites, learning objectives
- **Courseware access** — can reference the course's lecture notes, readings, problem sets
- **Pedagogical role** — lecturer, tutor, grader, or curriculum designer
- **Personality** — configured per course (enthusiastic STEM prof, strict economics lecturer, patient language tutor)
- **Institutional knowledge** — knows the class roster, due dates, past performance

Multiple teaching agents can collaborate on the same course:

```
Economics 101
  ├── Lecturer Agent (prepares lectures, records video scripts)
  ├── Tutor Agent (answers student questions, runs office hours)
  ├── Grader Agent (evaluates assignments, provides rubric feedback)
  └── Curriculum Designer Agent (plans syllabus, adjusts pacing)
```

A teaching agent is different from a learnbot persona — it has persistent access to course materials, can grade work, track curriculum progress, and communicate with other agents.

## Architecture

```
classroom-mcp (:11105)
  ├── REST API + Teacher Webapp
  ├── Courses and modules
  ├── Courseware depot (lectures, readings, problem sets)
  ├── Student roster + classes
  ├── Teaching agent registry (which agent for which course)
  ├── Timetable + assignments
  ├── Progress + grades
  └── Billing (future)
        │
        ├── learnbot-mcp (:11104)  — lesson delivery, chat, TTS, robot
        │
        └── teaching agents (LLM-driven)
              ├── Lecturer — creates course materials
              ├── Tutor — answers student questions
              ├── Grader — evaluates submissions
              └── Designer — plans curriculum
```

## Courseware Data Model

```sql
CREATE TABLE courses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    code        TEXT NOT NULL UNIQUE,        -- "ECON101", "CS201"
    title       TEXT NOT NULL,
    description TEXT,
    subject     TEXT,                        -- "economics", "cs", "mathematics"
    level       TEXT,                        -- "undergraduate", "graduate", "professional"
    credits     INTEGER DEFAULT 3,
    total_modules INTEGER DEFAULT 0,
    created_at  TEXT NOT NULL
);

CREATE TABLE modules (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id   INTEGER REFERENCES courses(id),
    title       TEXT NOT NULL,
    sequence    INTEGER NOT NULL,            -- module number within course
    description TEXT,
    learning_objectives TEXT                 -- JSON array of objectives
);

CREATE TABLE courseware (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    module_id   INTEGER REFERENCES modules(id),
    type        TEXT NOT NULL,               -- "lecture", "reading", "problem_set", "quiz", "project"
    title       TEXT NOT NULL,
    content     TEXT,                        -- markdown body or external reference
    source      TEXT DEFAULT 'ai_generated', -- ai_generated, imported, purchased, teacher_written
    duration_min INTEGER DEFAULT 0,
    sequence    INTEGER DEFAULT 0,
    created_at  TEXT NOT NULL
);

CREATE TABLE teaching_agents (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id   INTEGER REFERENCES courses(id),
    role        TEXT NOT NULL,               -- "lecturer", "tutor", "grader", "designer"
    name        TEXT NOT NULL,
    persona     TEXT,                        -- system prompt / personality
    model       TEXT DEFAULT 'llama3.2:3b',
    active      INTEGER DEFAULT 1,
    created_at  TEXT NOT NULL
);
```

## Courseware Sources

| Source | Method | Quality | Cost |
|--------|--------|---------|------|
| **AI-generated** | LLM produces lectures, problem sets, quizzes from curriculum | Good for drafts, needs review | Free |
| **Imported** | Teacher uploads PDF, Markdown, LaTeX, slides | Teacher's existing materials | Free |
| **Fleet-sourced** | Shared courseware depot across classroom-mcp instances | Varies | Free |
| **Published OER** | Imported from OpenStax, MIT OCW, etc. | High | Free |
| **Purchased** | Publisher packs (McGraw-Hill, Pearson, etc.) | High | €€€ |

The courseware table tracks the source so a teacher can see what was AI-generated (needs review) vs imported (ready to use).

## Teaching Agent Workflow

### Course preparation
```
1. Teacher creates course → "ECON101: Microeconomics"
2. Agent Designer generates syllabus (modules, objectives, readings)
3. Agent Lecturer generates lectures for each module
4. Agent Tutor creates practice problems and FAQs
5. Teacher reviews AI-generated courseware, edits as needed
6. Teacher assigns agents to class
```

### Course delivery
```
1. Module becomes available on schedule (timetable)
2. Agent Lecturer introduces the module via chat or recorded lecture
3. Students work through readings and problem sets
4. Agent Tutor answers questions and runs office hours
5. Agent Grader evaluates submissions against rubric
6. Progress recorded to classroom-mcp
```

### Course iteration
```
1. End-of-module survey (student feedback on materials)
2. Agents propose improvements based on common student mistakes
3. Curriculum designer adjusts pacing for next cohort
```

## Deployment Tiers

| Tier | Setup | Courses | Students | Cost |
|------|-------|---------|----------|------|
| **1 — Personal** | Goliath + Tailscale | 1-3 | 1-10 | Free |
| **2 — Small class** | $10/mo VPS | 1-5 | 10-50 | ~$15/mo |
| **3 — Institution** | $50/mo VPS or dedicated | 10-50 | 50-500 | ~$60/mo |
| **4 — Multi-tenant** | Cloud autoscale | Unlimited | Unlimited | Custom |

## Revenue Model

€3/student/month for Tier 2+. At 30 students = €90/mo. Covers hosting + your time.
Optional: €10 flat per course for AI-generated courseware packs (microeconomics, python, etc.).

## Open Questions

- Should teaching agents be MCP servers themselves (agent-mcp)? Or just personas in learnbot-mcp with additional tools?
- Courseware marketplace — share AI-generated courses between classroom-mcp instances?
- Student-facing mobile app for offline courseware access?

## Related

- [PRD.md](PRD.md)
- [classroom-mcp](https://github.com/sandraschi/classroom-mcp) — scaffold repo
