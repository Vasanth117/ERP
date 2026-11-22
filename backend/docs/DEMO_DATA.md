# Grand Horizon Institute of Technology (GHIT) — Demo Data

## Overview

The showcase demo tenant is **Grand Horizon Institute of Technology** (`ghit-demo`, institution code `GHIT`). All records are fictional and isolated with `Tenant.is_demo = true`. Demo Mode in College Admin sends `X-Demo-College-View: 1` so any logged-in college user can **read** this tenant without switching accounts.

## Scale profiles

| Profile | Students | Faculty | Non-teaching staff |
|---------|----------|---------|-------------------|
| `quick` | 2,400 | 820 | 140 |
| `standard` | 6,000 | 550 | 350 |
| `enterprise` | **12,000** | **650** | **400** |

Default CLI profile: **enterprise**.

## Initialize / reset

From `backend/` (set `PYTHONPATH` to backend root on Windows):

```bash
py -3 scripts/seed_demo_college.py --reset --profile enterprise
```

Optional overrides:

```bash
py -3 scripts/seed_demo_college.py --reset --students 15000 --faculty 700
```

## Demo logins (password for all: `DemoCollege123!`)

| Role | Email |
|------|-------|
| College Admin | admin@ghit-demo.edu |
| Department Admin | deptadmin@ghit-demo.edu |
| Finance | finance@ghit-demo.edu |
| Examination Cell | examcell@ghit-demo.edu |
| Faculty (bulk) | faculty00001@ghit-demo.edu … |
| Student (bulk) | student00001@ghit-demo.edu … |

## Generation pipeline

1. `seed_foundation` — tenant, 3 campuses, 18 departments, academic year, subscription, role accounts  
2. `seed_people` — staff users, batched faculty & students  
3. `seed_operations` — timetable, exams shell, hostel, library, finance COA  
4. `seed_showcase_analytics` — faculty profiles, employees, finance, attendance at scale, exams, calendar, approvals  
5. `validate_showcase_tenant` — count & integrity report stored on `DemoGenerationRun`

## Modules with rich demo data today

- Institution profile & campuses  
- Departments (18)  
- Students, faculty, employees (profiles + snapshots)  
- Enrollments, academic records, fee demands & payments  
- Attendance sessions & records  
- Examination schedules & pending evaluations  
- Hostel & library (from operations seed)  
- Dashboard KPIs (via `OperationalDataReader`)

## Modules planned for deeper volume (not fully generated yet)

- Dedicated admission application entities (3k–5k) — pending dedicated admission collections in ERP  
- Full examination marks → GPA/CGPA pipelines  
- Transport fleet at scale, library 5k+ titles bulk catalogue  
- Payroll months history  
- Parent/guardian population at scale  

Extend `app/modules/demo/seed/` in dependency order when those modules’ authoritative models are wired.

## Safety

- Mutations on demo tenant are blocked for non-platform users (`DemoMutationGuardMiddleware`).  
- No live payment/SMS/email.  
- `--reset` purges only the demo tenant via `purge_tenant_completely`.