# Student Portal (ST 00–08)

Shared shell and UI primitives for **ST 00 – Student Portal Components** live under `components/layout` and `components/ui`.

The student portal shell matches **Figma ST 00** (`ST / Sidebar` + `ST / Top header`) and College Admin content patterns (module chrome, KPI cards, panels).

- Sidebar hub nav (Figma): `config/sidebar-navigation.ts`
- Workspace routes / sitemap: `config/navigation.ts` + `config/screens.ts`
- Module chrome + horizontal tabs: `config/section-tabs.ts` + `StudentPortalChrome`

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