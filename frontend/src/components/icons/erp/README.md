# ERP icon library (from Figma)

Source: Figma page **ERP Icon Library (Lucide)** (`354:213`).

- Per-icon components live in `generated/*.tsx` (kebab-case filenames, PascalCase exports).
- Regenerate after Figma updates: `py -3 scripts/export_figma_erp_icon_library.py` from repo root.

```tsx
// Preferred in nav / lists (tree-shaken):
import { CircleUserIcon } from "@/components/icons/erp/generated/circle-user";

// By slug (lazy load, one icon per request):
import { ErpIcon } from "@/components/icons/erp/erp-icon";
<ErpIcon name="circle-user" className="size-5" />;
```

`registry.ts` maps every slug to a component — avoid importing it in client bundles; use direct `generated/*` imports or `ErpIcon`.

College Admin maps legacy Figma asset ids to ERP slugs in `features/college-admin/components/layout/college-admin-erp-icons.ts`; render with `CollegeAdminIcon` or `ErpIcon`.

Custom product marks (not from Figma export): `generated/backend-logo.tsx`, `generated/benchlogo_name.tsx` (+ matching `.svg` files).
