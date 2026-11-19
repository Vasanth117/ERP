"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PageHeading } from "@/features/college-admin/components/layout/page-heading";
import {
  QueryState,
  StatCard,
} from "@/features/college-admin/components/ui/query-state";
import {
  useCampuses,
  useConfigurationHistory,
  useCreateCampus,
  useInstitutionProfile,
  useInstitutionSettings,
  useUpdateCampus,
  useUpdateInstitutionProfile,
  useUpdateInstitutionSettings,
} from "@/features/college-admin/hooks/use-institution";
import type { InstitutionProfile } from "@/features/college-admin/types/institution";

export function InstitutionProfileView() {
  const profile = useInstitutionProfile();
  const update = useUpdateInstitutionProfile();
  const form = useForm<Partial<InstitutionProfile>>({
    values: profile.data,
  });

  return (
    <div data-figma-frame="72:5933">
      <PageHeading
        title="Institution profile"
        description="Legal identity, affiliation and primary contact for your college tenant."
        figmaFrame="72:5933"
      />
      <QueryState
        isLoading={profile.isLoading}
        isError={profile.isError}
        error={profile.error}
        onRetry={() => void profile.refetch()}
      >
        <form
          className="max-w-3xl space-y-4 rounded-xl border border-[#dce3ec] bg-white p-6"
          onSubmit={form.handleSubmit((values) => {
            update.mutate({
              legal_name: values.legal_name,
              display_name: values.display_name,
              institution_code: values.institution_code ?? undefined,
              institution_email: values.institution_email ?? undefined,
              contact_phone: values.contact_phone ?? undefined,
              official_website: values.official_website ?? undefined,
              institution_type: values.institution_type ?? undefined,
              affiliation_name: values.affiliation_name ?? undefined,
            });
          })}
        >
          <ProfileField label="Legal name" id="legal_name" register={form.register} />
          <ProfileField label="Display name" id="display_name" register={form.register} />
          <ProfileField
            label="Institution code"
            id="institution_code"
            register={form.register}
          />
          <ProfileField
            label="Institution email"
            id="institution_email"
            register={form.register}
          />
          <ProfileField
            label="Contact phone"
            id="contact_phone"
            register={form.register}
          />
          <ProfileField
            label="Website"
            id="official_website"
            register={form.register}
          />
          <ProfileField
            label="Institution type"
            id="institution_type"
            register={form.register}
          />
          <div className="flex justify-end gap-2 pt-2">
            <Button
              type="submit"
              className="bg-[#245dd8] hover:bg-[#1f4fb8]"
              disabled={update.isPending}
            >
              Save profile
            </Button>
          </div>
        </form>
      </QueryState>
    </div>
  );
}

export function InstitutionInformationView() {
  const profile = useInstitutionProfile();
  const p = profile.data;
  return (
    <div data-figma-frame="72:6332">
      <PageHeading
        title="Institution information"
        figmaFrame="72:6332"
        description="Read-only registry fields and affiliation metadata."
      />
      <QueryState
        isLoading={profile.isLoading}
        isError={profile.isError}
        error={profile.error}
        onRetry={() => void profile.refetch()}
      >
        <dl className="grid gap-4 sm:grid-cols-2">
          <InfoRow label="Tenant code" value={p?.tenant_code} />
          <InfoRow label="Timezone" value={p?.timezone} />
          <InfoRow label="Locale" value={p?.locale} />
          <InfoRow label="Affiliation" value={p?.affiliation_name} />
          <InfoRow label="Affiliation type" value={p?.affiliation_type} />
          <InfoRow label="Affiliation ID" value={p?.affiliation_id} />
          <InfoRow label="Address line 1" value={p?.address?.line1} />
          <InfoRow label="City" value={p?.address?.city} />
        </dl>
      </QueryState>
    </div>
  );
}

export function InstitutionBrandingView() {
  const settings = useInstitutionSettings();
  const update = useUpdateInstitutionSettings();
  const branding = settings.data?.branding;

  return (
    <div data-figma-frame="72:6775">
      <PageHeading title="College logo & branding" figmaFrame="72:6775" />
      <QueryState
        isLoading={settings.isLoading}
        isError={settings.isError}
        error={settings.error}
        onRetry={() => void settings.refetch()}
      >
        <form
          className="max-w-xl space-y-4 rounded-xl border border-[#dce3ec] bg-white p-6"
          onSubmit={(e) => {
            e.preventDefault();
            const fd = new FormData(e.currentTarget);
            update.mutate({
              branding: {
                display_name: String(fd.get("display_name") || ""),
                primary_color: String(fd.get("primary_color") || ""),
                secondary_color: String(fd.get("secondary_color") || ""),
                logo_file_id: String(fd.get("logo_file_id") || "") || undefined,
              },
            });
          }}
        >
          <Field name="display_name" label="Portal display name" defaultValue={branding?.display_name ?? ""} />
          <Field name="primary_color" label="Primary colour (#RRGGBB)" defaultValue={branding?.primary_color ?? "#245DD8"} />
          <Field name="secondary_color" label="Secondary colour" defaultValue={branding?.secondary_color ?? "#172B45"} />
          <Field name="logo_file_id" label="Logo file ID" defaultValue={branding?.logo_file_id ?? ""} />
          <Button type="submit" className="bg-[#245dd8]" disabled={update.isPending}>
            Save branding
          </Button>
        </form>
      </QueryState>
    </div>
  );
}

export function CampusesDashboardView() {
  const campuses = useCampuses();
  const create = useCreateCampus();
  const router = useRouter();

  return (
    <div data-figma-frame="72:7199">
      <PageHeading
        title="Campus management"
        figmaFrame="72:7199"
        description="Multi-campus registry for your institution."
        actions={
          <Button
            type="button"
            className="h-9 bg-[#245dd8] text-xs"
            onClick={() => {
              const code = `C${Date.now().toString().slice(-5)}`;
              create.mutate(
                { campus_code: code, name: "New campus", is_main: false },
                {
                  onSuccess: (campus) => {
                    router.push(
                      `/college-admin/institution/campuses/${campus.campus_id}`,
                    );
                  },
                },
              );
            }}
            disabled={create.isPending}
          >
            Add campus
          </Button>
        }
      />
      <QueryState
        isLoading={campuses.isLoading}
        isError={campuses.isError}
        error={campuses.error}
        isEmpty={!campuses.data?.length}
        onRetry={() => void campuses.refetch()}
      >
        <div className="grid gap-4 md:grid-cols-2">
          {campuses.data?.map((c) => (
            <Link
              key={c.campus_id}
              href={`/college-admin/institution/campuses/${c.campus_id}`}
              className="rounded-xl border border-[#dce3ec] bg-white p-4 hover:border-[#245dd8]"
            >
              <p className="font-semibold text-[#172b45]">{c.name}</p>
              <p className="text-xs text-[#607086]">
                {c.campus_code}
                {c.is_main ? " · Main" : ""}
                {!c.is_active ? " · Inactive" : ""}
              </p>
            </Link>
          ))}
        </div>
      </QueryState>
    </div>
  );
}

export function CampusDetailView({ campusId }: { campusId: string }) {
  const campus = useCampuses();
  const record = campus.data?.find((c) => c.campus_id === campusId);
  const update = useUpdateCampus(campusId);

  return (
    <div data-figma-frame="72:7582">
      <PageHeading
        title="Campus details"
        figmaFrame="72:7582"
        actions={
          <Link
            href={`/college-admin/institution/campuses/${campusId}/contact`}
            className="text-xs font-medium text-[#245dd8]"
          >
            Address & contact →
          </Link>
        }
      />
      <QueryState
        isLoading={campus.isLoading}
        isError={campus.isError}
        error={campus.error}
        isEmpty={!record}
        onRetry={() => void campus.refetch()}
      >
        {record ? (
          <form
            className="max-w-xl space-y-4 rounded-xl border border-[#dce3ec] bg-white p-6"
            onSubmit={(e) => {
              e.preventDefault();
              const fd = new FormData(e.currentTarget);
              update.mutate({
                name: String(fd.get("name") || record.name),
                is_main: fd.get("is_main") === "on",
                is_active: fd.get("is_active") === "on",
              });
            }}
          >
            <Field name="name" label="Campus name" defaultValue={record.name} />
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" name="is_main" defaultChecked={record.is_main} />
              Main campus
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" name="is_active" defaultChecked={record.is_active} />
              Active
            </label>
            <Button type="submit" className="bg-[#245dd8]" disabled={update.isPending}>
              Save campus
            </Button>
          </form>
        ) : null}
      </QueryState>
    </div>
  );
}

export function CampusContactView({ campusId }: { campusId: string }) {
  const { data, isLoading, isError, error, refetch } = useCampuses();
  const record = data?.find((c) => c.campus_id === campusId);
  const update = useUpdateCampus(campusId);

  return (
    <div data-figma-frame="72:7995">
      <PageHeading title="Campus address & contact" figmaFrame="72:7995" />
      <QueryState
        isLoading={isLoading}
        isError={isError}
        error={error}
        isEmpty={!record}
        onRetry={() => void refetch()}
      >
        {record ? (
          <form
            className="max-w-xl space-y-4 rounded-xl border border-[#dce3ec] bg-white p-6"
            onSubmit={(e) => {
              e.preventDefault();
              const fd = new FormData(e.currentTarget);
              update.mutate({
                contact_email: String(fd.get("contact_email") || "") || null,
                contact_phone: String(fd.get("contact_phone") || "") || null,
                address: {
                  line1: String(fd.get("line1") || ""),
                  city: String(fd.get("city") || ""),
                  state: String(fd.get("state") || ""),
                  postal_code: String(fd.get("postal_code") || ""),
                  country: String(fd.get("country") || ""),
                },
              });
            }}
          >
            <Field name="contact_email" label="Contact email" defaultValue={record.contact_email ?? ""} />
            <Field name="contact_phone" label="Contact phone" defaultValue={record.contact_phone ?? ""} />
            <Field name="line1" label="Address line 1" defaultValue={record.address?.line1 ?? ""} />
            <Field name="city" label="City" defaultValue={record.address?.city ?? ""} />
            <Field name="state" label="State" defaultValue={record.address?.state ?? ""} />
            <Field name="postal_code" label="Postal code" defaultValue={record.address?.postal_code ?? ""} />
            <Field name="country" label="Country" defaultValue={record.address?.country ?? ""} />
            <Button type="submit" className="bg-[#245dd8]" disabled={update.isPending}>
              Save contact
            </Button>
          </form>
        ) : null}
      </QueryState>
    </div>
  );
}

export function AcademicSettingsView() {
  const settings = useInstitutionSettings();
  const update = useUpdateInstitutionSettings();
  const s = settings.data?.settings ?? {};

  return (
    <div data-figma-frame="72:8395">
      <PageHeading title="Academic institution settings" figmaFrame="72:8395" />
      <QueryState
        isLoading={settings.isLoading}
        isError={settings.isError}
        error={settings.error}
        onRetry={() => void settings.refetch()}
      >
        <form
          className="max-w-xl space-y-4 rounded-xl border border-[#dce3ec] bg-white p-6"
          onSubmit={(e) => {
            e.preventDefault();
            const fd = new FormData(e.currentTarget);
            update.mutate({
              grade_display_scale: String(fd.get("grade_display_scale") || ""),
              show_department_in_reports: fd.get("show_department_in_reports") === "on",
            });
          }}
        >
          <Field
            name="grade_display_scale"
            label="Grade display scale"
            defaultValue={String(s.grade_display_scale ?? "")}
          />
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              name="show_department_in_reports"
              defaultChecked={Boolean(s.show_department_in_reports)}
            />
            Show department in reports
          </label>
          <Button type="submit" className="bg-[#245dd8]" disabled={update.isPending}>
            Save settings
          </Button>
        </form>
      </QueryState>
    </div>
  );
}

export function InstitutionPoliciesView() {
  const settings = useInstitutionSettings();
  const s = settings.data?.settings ?? {};
  return (
    <div data-figma-frame="72:8805">
      <PageHeading title="Institutional policies" figmaFrame="72:8805" />
      <QueryState
        isLoading={settings.isLoading}
        isError={settings.isError}
        error={settings.error}
        onRetry={() => void settings.refetch()}
      >
        <div className="space-y-3 rounded-xl border border-[#dce3ec] bg-white p-6 text-sm">
          <StatCard
            label="Cross-batch transfer approval"
            value={
              s.inter_batch_section_transfer_requires_college_approval
                ? "Required"
                : "Not required"
            }
          />
          <StatCard
            label="Notification digest"
            value={s.notification_digest_enabled ? "Enabled" : "Disabled"}
          />
        </div>
      </QueryState>
    </div>
  );
}

export function AcademicYearView() {
  const settings = useInstitutionSettings();
  const update = useUpdateInstitutionSettings();
  return (
    <div data-figma-frame="72:9235">
      <PageHeading title="Academic year configuration" figmaFrame="72:9235" />
      <QueryState
        isLoading={settings.isLoading}
        isError={settings.isError}
        error={settings.error}
        onRetry={() => void settings.refetch()}
      >
        <form
          className="max-w-xl space-y-4 rounded-xl border border-[#dce3ec] bg-white p-6"
          onSubmit={(e) => {
            e.preventDefault();
            const fd = new FormData(e.currentTarget);
            update.mutate({
              academic_year_display: String(fd.get("academic_year_display") || ""),
              semester_display: String(fd.get("semester_display") || ""),
            });
          }}
        >
          <Field
            name="academic_year_display"
            label="Academic year display"
            defaultValue={String(settings.data?.settings.academic_year_display ?? "")}
          />
          <Field
            name="semester_display"
            label="Semester display"
            defaultValue={String(settings.data?.settings.semester_display ?? "")}
          />
          <Button type="submit" className="bg-[#245dd8]" disabled={update.isPending}>
            Save
          </Button>
        </form>
      </QueryState>
    </div>
  );
}

export function CalendarSettingsView() {
  const settings = useInstitutionSettings();
  const update = useUpdateInstitutionSettings();
  return (
    <div data-figma-frame="72:9653">
      <PageHeading title="Institutional calendar settings" figmaFrame="72:9653" />
      <QueryState
        isLoading={settings.isLoading}
        isError={settings.isError}
        error={settings.error}
        onRetry={() => void settings.refetch()}
      >
        <form
          className="max-w-xl space-y-4 rounded-xl border border-[#dce3ec] bg-white p-6"
          onSubmit={(e) => {
            e.preventDefault();
            const fd = new FormData(e.currentTarget);
            update.mutate({
              date_format: String(fd.get("date_format") || ""),
              time_format: String(fd.get("time_format") || ""),
            });
          }}
        >
          <Field
            name="date_format"
            label="Date format"
            defaultValue={String(settings.data?.settings.date_format ?? "")}
          />
          <Field
            name="time_format"
            label="Time format"
            defaultValue={String(settings.data?.settings.time_format ?? "")}
          />
          <Button type="submit" className="bg-[#245dd8]" disabled={update.isPending}>
            Save
          </Button>
        </form>
      </QueryState>
    </div>
  );
}

export function ConfigurationHistoryView() {
  const history = useConfigurationHistory();
  return (
    <div data-figma-frame="72:10042">
      <PageHeading title="Campus configuration history" figmaFrame="72:10042" />
      <QueryState
        isLoading={history.isLoading}
        isError={history.isError}
        error={history.error}
        isEmpty={!history.data?.length}
        onRetry={() => void history.refetch()}
      >
        <ul className="divide-y rounded-xl border border-[#dce3ec] bg-white">
          {history.data?.map((row) => (
            <li key={`${row.scope}-${row.version_number}`} className="px-4 py-3 text-sm">
              <p className="font-medium text-[#172b45]">
                {row.scope} · v{row.version_number}
              </p>
              <p className="text-[#607086]">
                {row.changed_keys.join(", ")} ·{" "}
                {new Date(row.created_at).toLocaleString()}
              </p>
            </li>
          ))}
        </ul>
      </QueryState>
    </div>
  );
}

function ProfileField({
  label,
  id,
  register,
}: {
  label: string;
  id: keyof InstitutionProfile;
  register: ReturnType<typeof useForm<Partial<InstitutionProfile>>>["register"];
}) {
  return (
    <div className="space-y-1.5">
      <Label htmlFor={id}>{label}</Label>
      <Input id={id} {...register(id)} className="border-[#dce3ec]" />
    </div>
  );
}

function Field({
  label,
  name,
  defaultValue,
}: {
  label: string;
  name: string;
  defaultValue?: string;
}) {
  return (
    <div className="space-y-1.5">
      <Label htmlFor={name}>{label}</Label>
      <Input
        id={name}
        name={name}
        defaultValue={defaultValue}
        className="border-[#dce3ec]"
      />
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value?: string | null }) {
  return (
    <div className="rounded-lg border border-[#dce3ec] bg-white p-4">
      <dt className="text-[11px] font-semibold uppercase text-[#8a98aa]">
        {label}
      </dt>
      <dd className="mt-1 text-sm text-[#172b45]">{value ?? "—"}</dd>
    </div>
  );
}