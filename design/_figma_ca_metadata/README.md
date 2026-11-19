# Figma metadata for College Admin (CA 01–24)

Next.js routes are generated from **`college-admin-frames.json`**. That file is built by parsing Figma **`get_metadata`** XML for frames named `CA NN.MM – …`.

## Why many Figma pages are still missing here

| Source | What it contains |
|--------|------------------|
| Cached MCP dump (`agent-tools/*.txt`) | **~62 frames** — mostly **CA 01–CA 06** only |
| This folder (`*.txt` per canvas) | **Empty until you export** — needed for **CA 07–CA 24** and the full **300+** screen list |
| `synthesize_ca_screens.py` | **~111 fallback screens** (API-bound, not every Figma variant/dialog) |

Until you save XML for each CA canvas, the generator **cannot** create one `page.tsx` per Figma frame for modules 07–24.

## Personal access token (REST export)

1. In Figma: **Account menu (avatar) → Settings → Security**.
2. Scroll to **Personal access tokens** → **Generate new token**.
3. Name it e.g. `ERP-college-admin-export`, copy the token once (Figma will not show it again).
4. You need **view** access to file `Hy7qeZdVNmzD6PN0ZkgBfK` (ERP).
5. Add to **`e:\ERPSYSTEM\.env`** (gitignored):

   ```env
   FIGMA_ACCESS_TOKEN=figd_xxxxxxxx
   ```

6. Run:

   ```powershell
   py scripts/export_figma_ca_metadata_rest.py
   py scripts/sync_college_admin_pages.py
   ```

**Do not** commit the token or paste it in public chat. Tell the agent “token is in `.env`” and it can run the scripts locally.

## Export steps (when Figma MCP is available)

For each page in `design/figma-pages.json` under `collegeAdmin.pages` (e.g. `159:2198` = CA 07):

1. Call Figma MCP `get_metadata` with `fileKey` `Hy7qeZdVNmzD6PN0ZkgBfK` and that `nodeId`.
2. Save the full XML response to this folder, e.g. `CA-07-faculty.txt`.
3. Run from repo root:

```powershell
py scripts/sync_college_admin_pages.py
```

That runs: build registry → synthetic gaps → generate all `page.tsx` files.

## Do not run build alone

`build_college_admin_frame_registry.py` **only reads XML**. It used to drop synthetic frames; it now **preserves** them, but you should still use **`sync_college_admin_pages.py`** so routes stay in sync.