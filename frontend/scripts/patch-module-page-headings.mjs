/**
 * Replaces standard h2 page header blocks with CollegeAdminModulePageHeading
 * in college-admin dashboard TSX files.
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(__dirname, "..", "src", "features", "college-admin", "components");

const IMPORT_LINE =
  'import { CollegeAdminModulePageHeading } from "@/features/college-admin/components/layout/college-admin-module-page-heading";';

const HEADER_RE =
  /<div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">\s*<div>\s*<h2 className="text-\[22px\] font-bold tracking-\[-0\.02em\] text-\[#111827\]">\s*([\s\S]*?)\s*<\/h2>\s*(?:<p className="mt-1 text-\[14px\] text-\[#6b7280\]">\s*([\s\S]*?)\s*<\/p>\s*)?<\/div>\s*<div className="flex shrink-0 flex-wrap(?: items-center)? gap-2">\s*([\s\S]*?)\s*<\/div>\s*<\/div>/g;

function walk(dir, out = []) {
  for (const name of fs.readdirSync(dir)) {
    const full = path.join(dir, name);
    if (fs.statSync(full).isDirectory()) walk(full, out);
    else if (name.endsWith(".tsx")) out.push(full);
  }
  return out;
}

let patched = 0;
let skipped = 0;

for (const file of walk(root)) {
  let text = fs.readFileSync(file, "utf8");
  if (!text.includes('text-[22px] font-bold tracking-[-0.02em]')) {
    skipped++;
    continue;
  }
  if (!HEADER_RE.test(text)) {
    skipped++;
    continue;
  }
  HEADER_RE.lastIndex = 0;
  const asJsxExpr = (chunk) => {
    const t = chunk.trim();
    if (!t) return "";
    if (t.startsWith("{") && t.endsWith("}")) return t;
    return `{${t}}`;
  };

  const next = text.replace(HEADER_RE, (_, title, subtitle, actions) => {
    const sub = subtitle?.trim() ? ` subtitle={${asJsxExpr(subtitle).slice(1, -1)}}` : "";
    const actionsBody = actions.trim();
    const actionsProp = actionsBody ? ` actions={<>${actionsBody}</>}` : "";
    return `<CollegeAdminModulePageHeading title={${asJsxExpr(title).slice(1, -1)}}${sub}${actionsProp} />`;
  });
  if (next === text) {
    skipped++;
    continue;
  }
  if (!next.includes("CollegeAdminModulePageHeading")) {
    skipped++;
    continue;
  }
  let withImport = next;
  if (!withImport.includes(IMPORT_LINE)) {
    const useClient = withImport.match(/^"use client";\s*\n/);
    if (useClient) {
      const rest = withImport.slice(useClient[0].length);
      const firstImport = rest.match(/^import .+;\n/m);
      const insertAt = useClient[0].length + (firstImport ? firstImport.index + firstImport[0].length : 0);
      withImport = withImport.slice(0, insertAt) + IMPORT_LINE + "\n" + withImport.slice(insertAt);
    } else {
      withImport = IMPORT_LINE + "\n" + withImport;
    }
  }
  fs.writeFileSync(file, withImport);
  patched++;
  console.log("patched", path.relative(root, file));
}

console.log({ patched, skipped });