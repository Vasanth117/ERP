"use client";

import { useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  DetailRow,
  PageHeading,
  QueryState,
  SectionPanel,
  StatusBadge,
  formatDateTime,
  toneForStatus,
} from "@/features/student/components/ui/student-screen-ui";
import { screenBySlug } from "@/features/student/config/screens";
import {
  useAvailableCourses,
  useCancelRegistration,
  useConfirmedRegistrations,
  useElectiveGroups,
  useElectiveOptions,
  useRegistrationEligibility,
  useRegistrationHistory,
  useSubmitRegistration,
  useValidateRegistration,
} from "@/features/student/hooks/use-student-registration";
import type { RegistrationSelectionInput } from "@/features/student/types/registration";

type RegistrationSlug =
  | "registration"
  | "registration-eligibility"
  | "available-courses"
  | "elective-groups"
  | "my-registrations"
  | "submit-registration"
  | "registration-history";

export function RegistrationScreen({ slug }: { slug: RegistrationSlug }) {
  const def = screenBySlug(slug);
  return (
    <div>
      <PageHeading
        title={def?.title ?? "Registration"}
        description={def?.description}
        figmaPage="ST 04"
      />
      <RegistrationBody slug={slug} />
    </div>
  );
}

function RegistrationBody({ slug }: { slug: RegistrationSlug }) {
  switch (slug) {
    case "registration":
      return <RegistrationHub />;
    case "registration-eligibility":
      return <EligibilityPanel />;
    case "available-courses":
      return <AvailableCoursesPanel />;
    case "elective-groups":
      return <ElectiveGroupsPanel />;
    case "my-registrations":
      return <MyRegistrationsPanel />;
    case "submit-registration":
      return <SubmitRegistrationPanel />;
    case "registration-history":
      return <RegistrationHistoryPanel />;
    default:
      return null;
  }
}

function RegistrationHub() {
  const eligibility = useRegistrationEligibility();
  const confirmed = useConfirmedRegistrations();
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <EligibilityPanel compact />
      <SectionPanel title="Current registrations">
        <QueryState
          isLoading={confirmed.isLoading}
          isError={confirmed.isError}
          error={confirmed.error}
          onRetry={() => void confirmed.refetch()}
          isEmpty={!confirmed.data?.length}
          emptyMessage="No confirmed registrations."
        >
          {confirmed.data ? (
            <ul className="divide-y divide-[#f1f5f9] text-sm">
              {confirmed.data.map((row) => (
                <li key={row.id} className="flex justify-between py-3">
                  <span>
                    {row.course_code} · {row.credit_units} cr
                  </span>
                  <StatusBadge label={row.status} tone={toneForStatus(row.status)} />
                </li>
              ))}
            </ul>
          ) : null}
        </QueryState>
      </SectionPanel>
      {!eligibility.isLoading && eligibility.data && !eligibility.data.window_open ? (
        <p className="text-sm text-[#c2410c] lg:col-span-2">
          Registration window is currently closed. Check eligibility for open dates.
        </p>
      ) : null}
    </div>
  );
}

function EligibilityPanel({ compact = false }: { compact?: boolean }) {
  const eligibility = useRegistrationEligibility();
  const inner = (
    <QueryState
      isLoading={eligibility.isLoading}
      isError={eligibility.isError}
      error={eligibility.error}
      onRetry={() => void eligibility.refetch()}
    >
      {eligibility.data ? (
        <div className="grid gap-0 sm:grid-cols-2">
          <DetailRow
            label="Eligible"
            value={eligibility.data.eligible ? "Yes" : "No"}
          />
          <DetailRow
            label="Window open"
            value={eligibility.data.window_open ? "Yes" : "No"}
          />
          <DetailRow label="Min credits" value={eligibility.data.min_credits ?? "—"} />
          <DetailRow label="Max credits" value={eligibility.data.max_credits ?? "—"} />
          <DetailRow
            label="Opens"
            value={formatDateTime(eligibility.data.registration_open_at)}
          />
          <DetailRow
            label="Closes"
            value={formatDateTime(eligibility.data.registration_close_at)}
          />
          {eligibility.data.reasons.length > 0 ? (
            <ReasonList reasons={eligibility.data.reasons} />
          ) : null}
        </div>
      ) : null}
    </QueryState>
  );

  if (compact) {
    return <SectionPanel title="Eligibility">{inner}</SectionPanel>;
  }
  return <SectionPanel title="Registration eligibility & window">{inner}</SectionPanel>;
}

function ReasonList({ reasons }: { reasons: string[] }) {
  return (
    <div className="sm:col-span-2">
      <p className="text-xs font-medium text-[#6b7280]">Reasons</p>
      <ul className="mt-1 list-disc pl-5 text-sm text-[#4b5563]">
        {reasons.map((r) => (
          <li key={r}>{r}</li>
        ))}
      </ul>
    </div>
  );
}

function AvailableCoursesPanel() {
  const courses = useAvailableCourses();
  return (
    <SectionPanel title="Open courses">
      <QueryState
        isLoading={courses.isLoading}
        isError={courses.isError}
        error={courses.error}
        onRetry={() => void courses.refetch()}
        isEmpty={!courses.data?.length}
        emptyMessage="No courses available for registration."
      >
        {courses.data ? (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-left text-sm">
              <thead className="text-xs uppercase text-[#9ca3af]">
                <tr>
                  <th className="px-2 py-2">Code</th>
                  <th className="px-2 py-2">Name</th>
                  <th className="px-2 py-2">Credits</th>
                  <th className="px-2 py-2">Type</th>
                  <th className="px-2 py-2">Open</th>
                </tr>
              </thead>
              <tbody>
                {courses.data.map((c) => (
                  <tr key={c.course_id} className="border-t border-[#f1f5f9]">
                    <td className="px-2 py-3 font-medium">{c.course_code}</td>
                    <td className="px-2 py-3">{c.name}</td>
                    <td className="px-2 py-3">{c.credit_units}</td>
                    <td className="px-2 py-3 capitalize">{c.registration_type.replace(/_/g, " ")}</td>
                    <td className="px-2 py-3">{c.is_open_for_registration ? "Yes" : "No"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </QueryState>
    </SectionPanel>
  );
}

function ElectiveGroupsPanel() {
  const groups = useElectiveGroups();
  const [selectedGroup, setSelectedGroup] = useState<string | null>(null);
  const options = useElectiveOptions(selectedGroup);

  return (
    <ElectiveGroupsBlock
      groups={groups}
      selectedGroup={selectedGroup}
      setSelectedGroup={setSelectedGroup}
      options={options}
    />
  );
}

function ElectiveGroupsBlock({
  groups,
  selectedGroup,
  setSelectedGroup,
  options,
}: {
  groups: ReturnType<typeof useElectiveGroups>;
  selectedGroup: string | null;
  setSelectedGroup: (id: string) => void;
  options: ReturnType<typeof useElectiveOptions>;
}) {
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <SectionPanel title="Elective groups">
        <QueryState
          isLoading={groups.isLoading}
          isError={groups.isError}
          error={groups.error}
          onRetry={() => void groups.refetch()}
          isEmpty={!groups.data?.length}
          emptyMessage="No elective groups configured."
        >
          {groups.data ? (
            <ul className="divide-y divide-[#f1f5f9]">
              {groups.data.map((g) => (
                <li key={g.id}>
                  <button
                    type="button"
                    className="flex w-full flex-col items-start py-3 text-left text-sm hover:bg-[#f8fafc]"
                    onClick={() => setSelectedGroup(g.id)}
                  >
                    <span className="font-medium text-[#111827]">
                      {g.group_code} · {g.title}
                    </span>
                    <span className="text-xs text-[#9ca3af]">
                      Pick {g.min_selections}–{g.max_selections} · {g.min_credits}–{g.max_credits} cr
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          ) : null}
        </QueryState>
      </SectionPanel>
      <SectionPanel title="Options">
        <QueryState
          isLoading={options.isLoading}
          isError={options.isError}
          error={options.error}
          onRetry={() => void options.refetch()}
          isEmpty={!selectedGroup}
          emptyMessage="Select an elective group."
        >
          {options.data ? (
            <ul className="divide-y divide-[#f1f5f9] text-sm">
              {options.data.map((o) => (
                <li key={o.course_id} className="flex justify-between py-3">
                  <span>
                    {o.course_code} · {o.course_name}
                  </span>
                  <span className="text-xs text-[#9ca3af]">
                    {o.eligible ? `${o.credit_units} cr` : "Not eligible"}
                  </span>
                </li>
              ))}
            </ul>
          ) : null}
        </QueryState>
      </SectionPanel>
    </div>
  );
}

function MyRegistrationsPanel() {
  const confirmed = useConfirmedRegistrations();
  const cancel = useCancelRegistration();
  return (
    <SectionPanel title="Confirmed registrations">
      <QueryState
        isLoading={confirmed.isLoading}
        isError={confirmed.isError}
        error={confirmed.error}
        onRetry={() => void confirmed.refetch()}
        isEmpty={!confirmed.data?.length}
        emptyMessage="No registrations on record."
      >
        {confirmed.data ? (
          <ul className="divide-y divide-[#f1f5f9]">
            {confirmed.data.map((row) => (
              <li
                key={row.id}
                className="flex flex-wrap items-center justify-between gap-2 py-3 text-sm"
              >
                <ConfirmedLine row={row} cancel={cancel} />
              </li>
            ))}
          </ul>
        ) : null}
      </QueryState>
    </SectionPanel>
  );
}

function ConfirmedLine({
  row,
  cancel,
}: {
  row: { id: string; course_id: string; course_code: string; section_code: string | null; status: string; credit_units: number };
  cancel: ReturnType<typeof useCancelRegistration>;
}) {
  return (
    <>
      <div>
        <p className="font-medium text-[#111827]">{row.course_code}</p>
        <p className="text-xs text-[#9ca3af]">
          Section {row.section_code ?? "—"} · {row.credit_units} credits
        </p>
      </div>
      <StatusRow row={row} cancel={cancel} />
    </>
  );
}

function StatusRow({
  row,
  cancel,
}: {
  row: { course_id: string; status: string };
  cancel: ReturnType<typeof useCancelRegistration>;
}) {
  return (
    <div className="flex items-center gap-2">
      <StatusBadge label={row.status} tone={toneForStatus(row.status)} />
      <Button
        type="button"
        variant="outline"
        size="sm"
        disabled={cancel.isPending}
        onClick={() => cancel.mutate(row.course_id)}
      >
        Cancel
      </Button>
    </div>
  );
}

function SubmitRegistrationPanel() {
  const available = useAvailableCourses();
  const validate = useValidateRegistration();
  const submit = useSubmitRegistration();
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [validationMsg, setValidationMsg] = useState<string | null>(null);

  const selections: RegistrationSelectionInput[] = useMemo(() => {
    if (!available.data) return [];
    return available.data
      .filter((c) => selectedIds.has(c.course_id) && c.is_open_for_registration)
      .map((c) => ({
        course_id: c.course_id,
        course_code: c.course_code,
        registration_type: c.registration_type,
      }));
  }, [available.data, selectedIds]);

  return (
    <SectionPanel title="Build & submit selection">
      <QueryState
        isLoading={available.isLoading}
        isError={available.isError}
        error={available.error}
        onRetry={() => void available.refetch()}
        isEmpty={!available.data?.length}
        emptyMessage="No courses to select."
      >
        {available.data ? (
          <form
            className="space-y-4"
            onSubmit={(e) => {
              e.preventDefault();
              submit.mutate(selections, {
                onSuccess: (data) =>
                  setValidationMsg(`Submitted — status ${data.status.replace(/_/g, " ")}.`),
                onError: (err) =>
                  setValidationMsg(err instanceof Error ? err.message : "Submit failed"),
              });
            }}
          >
            <ul className="divide-y divide-[#f1f5f9] rounded-lg border border-[#e8ecf2]">
              {available.data
                .filter((c) => c.is_open_for_registration)
                .map((c) => (
                  <li key={c.course_id} className="flex items-center gap-3 px-3 py-2 text-sm">
                    <input
                      type="checkbox"
                      checked={selectedIds.has(c.course_id)}
                      onChange={(ev) => {
                        setSelectedIds((prev) => {
                          const next = new Set(prev);
                          if (ev.target.checked) next.add(c.course_id);
                          else next.delete(c.course_id);
                          return next;
                        });
                      }}
                    />
                    <span>
                      {c.course_code} · {c.name} ({c.credit_units} cr)
                    </span>
                  </li>
                ))}
            </ul>
            <ActionButtons
              validate={validate}
              selections={selections}
              setValidationMsg={setValidationMsg}
              submitPending={submit.isPending}
            />
            {validationMsg ? <p className="text-sm text-[#6b7280]">{validationMsg}</p> : null}
          </form>
        ) : null}
      </QueryState>
    </SectionPanel>
  );
}

function ActionButtons({
  validate,
  selections,
  setValidationMsg,
  submitPending,
}: {
  validate: ReturnType<typeof useValidateRegistration>;
  selections: RegistrationSelectionInput[];
  setValidationMsg: (msg: string) => void;
  submitPending: boolean;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      <Button
        type="button"
        variant="outline"
        disabled={validate.isPending || selections.length === 0}
        onClick={() => {
          validate.mutate(selections, {
            onSuccess: (result) => {
              const parts = [
                result.valid ? "Selection is valid." : "Selection has errors.",
                ...result.errors,
                ...result.warnings.map((w) => `Warning: ${w}`),
                `Total credits: ${result.total_credits}`,
              ];
              setValidationMsg(parts.join(" "));
            },
            onError: (err) =>
              setValidationMsg(err instanceof Error ? err.message : "Validation failed"),
          });
        }}
      >
        Validate
      </Button>
      <Button type="submit" className="bg-[#245dd8]" disabled={submitPending || selections.length === 0}>
        {submitPending ? "Submitting…" : "Submit registration"}
      </Button>
    </div>
  );
}

function RegistrationHistoryPanel() {
  const history = useRegistrationHistory(50, 0);
  return (
    <SectionPanel title="History">
      <QueryState
        isLoading={history.isLoading}
        isError={history.isError}
        error={history.error}
        onRetry={() => void history.refetch()}
        isEmpty={!history.data?.items.length}
        emptyMessage="No registration history."
      >
        {history.data ? (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[560px] text-left text-sm">
              <thead className="text-xs uppercase text-[#9ca3af]">
                <tr>
                  <th className="px-2 py-2">Course</th>
                  <th className="px-2 py-2">Action</th>
                  <th className="px-2 py-2">Status change</th>
                  <th className="px-2 py-2">When</th>
                </tr>
              </thead>
              <tbody>
                {history.data.items.map((row) => (
                  <tr key={row.id} className="border-t border-[#f1f5f9]">
                    <td className="px-2 py-3">{row.course_code}</td>
                    <td className="px-2 py-3 capitalize">{row.action.replace(/_/g, " ")}</td>
                    <td className="px-2 py-3 text-xs text-[#607086]">
                      {row.previous_status ?? "—"} → {row.new_status ?? "—"}
                    </td>
                    <td className="px-2 py-3 text-xs text-[#9ca3af]">
                      {formatDateTime(row.occurred_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </QueryState>
    </SectionPanel>
  );
}