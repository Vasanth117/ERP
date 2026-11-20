# Student Portal (ST 00–08)

Shared shell and UI primitives for **ST 00 – Student Portal Components** live under `components/layout` and `components/ui`.

All screens call live FastAPI routes under `/api/v1/students/me/*` via `src/features/student/api/*`.

## Routes

62 pages under `/student/...` — regenerate after adding screens:

```bash
py scripts/generate_student_app_routes.py
```

## Entry

- Layout: `src/app/student/layout.tsx`
- Portal home: `/student/home` (all ST 01–08 links)
- Landing cards: `student-academic` and `performance` → `/student/home`