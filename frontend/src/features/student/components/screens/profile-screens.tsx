"use client";

import { useState, type ChangeEvent, type ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  DetailRow,
  PageHeading,
  QueryState,
  SectionPanel,
  formatDate,
  formatDateTime,
} from "@/features/student/components/ui/student-screen-ui";
import {
  useProfileActivities,
  useStudentProfile,
  useUpdateStudentProfile,
} from "@/features/student/hooks/use-student-profile";
import type { StudentProfileUpdate } from "@/features/student/types/profile";

export function StudentProfileScreen() {
  const profile = useStudentProfile();
  const update = useUpdateStudentProfile();
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState<StudentProfileUpdate>({});
  const [message, setMessage] = useState<string | null>(null);

  return (
    <div>
      <PageHeading
        title="My Profile"
        description="Read-only official fields plus contact details you may update."
        figmaPage="ST 01"
      />
      <QueryState
        isLoading={profile.isLoading}
        isError={profile.isError}
        error={profile.error}
        onRetry={() => void profile.refetch()}
      >
        {profile.data ? (
          <div className="grid gap-6 lg:grid-cols-2">
            <SectionPanel title="Identity (read-only)">
              <DetailRow label="Full name" value={profile.data.full_name} />
              <DetailRow label="Email" value={profile.data.email} />
              <DetailRow label="Student ID" value={profile.data.student_id} />
              <DetailRow label="Roll number" value={profile.data.roll_number} />
              <DetailRow label="Admission number" value={profile.data.admission_number} />
              <DetailRow label="Admission date" value={formatDate(profile.data.admission_date)} />
              <DetailRow label="Department" value={profile.data.department_name} />
              <DetailRow label="Programme" value={profile.data.programme_name} />
              <DetailRow label="Batch / Section" value={`${profile.data.batch_label ?? "—"} / ${profile.data.section_code ?? "—"}`} />
            </SectionPanel>

            <SectionPanel title="Contact details">
              {!editing ? (
                <>
                  <DetailRow label="Phone" value={profile.data.contact_phone} />
                  <DetailRow label="Alternate email" value={profile.data.alternate_email} />
                  <DetailRow label="Current address" value={profile.data.current_address} />
                  <DetailRow label="Permanent address" value={profile.data.permanent_address} />
                  <DetailRow label="Bio" value={profile.data.bio} />
                  <Button
                    type="button"
                    className="mt-4 bg-[#245dd8] hover:bg-[#1f4fb8]"
                    onClick={() => {
                      setForm({
                        contact_phone: profile.data!.contact_phone,
                        alternate_email: profile.data!.alternate_email,
                        current_address: profile.data!.current_address,
                        permanent_address: profile.data!.permanent_address,
                        bio: profile.data!.bio,
                      });
                      setEditing(true);
                      setMessage(null);
                    }}
                  >
                    Edit contact details
                  </Button>
                </>
              ) : (
                <form
                  className="space-y-3"
                  onSubmit={(e) => {
                    e.preventDefault();
                    update.mutate(form, {
                      onSuccess: () => {
                        setEditing(false);
                        setMessage("Profile updated.");
                      },
                      onError: (err) =>
                        setMessage(err instanceof Error ? err.message : "Update failed"),
                    });
                  }}
                >
                  <Field label="Phone">
                    <Input
                      value={form.contact_phone ?? ""}
                      onChange={(ev) =>
                        setForm((f) => ({ ...f, contact_phone: ev.target.value }))
                      }
                    />
                  </Field>
                  <Field label="Alternate email">
                    <Input
                      type="email"
                      value={form.alternate_email ?? ""}
                      onChange={(ev) =>
                        setForm((f) => ({ ...f, alternate_email: ev.target.value }))
                      }
                    />
                  </Field>
                  <Field label="Current address">
                    <textarea
                      className="min-h-20 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      value={form.current_address ?? ""}
                      onChange={(ev: ChangeEvent<HTMLTextAreaElement>) =>
                        setForm((f) => ({ ...f, current_address: ev.target.value }))
                      }
                    />
                  </Field>
                  <Field label="Permanent address">
                    <textarea
                      className="min-h-20 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      value={form.permanent_address ?? ""}
                      onChange={(ev: ChangeEvent<HTMLTextAreaElement>) =>
                        setForm((f) => ({ ...f, permanent_address: ev.target.value }))
                      }
                    />
                  </Field>
                  <Field label="Bio">
                    <textarea
                      className="min-h-20 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      value={form.bio ?? ""}
                      onChange={(ev: ChangeEvent<HTMLTextAreaElement>) =>
                        setForm((f) => ({ ...f, bio: ev.target.value }))
                      }
                    />
                  </Field>
                  <div className="flex gap-2 pt-2">
                    <Button type="submit" disabled={update.isPending} className="bg-[#245dd8]">
                      {update.isPending ? "Saving…" : "Save"}
                    </Button>
                    <Button type="button" variant="outline" onClick={() => setEditing(false)}>
                      Cancel
                    </Button>
                  </div>
                  {message ? <p className="text-sm text-[#6b7280]">{message}</p> : null}
                </form>
              )}
            </SectionPanel>
          </div>
        ) : null}
      </QueryState>
    </div>
  );
}

export function StudentProfileActivityScreen() {
  const activities = useProfileActivities(50, 0);

  return (
    <div>
      <PageHeading
        title="Profile Activity"
        description="Activity trail from GET /students/me/profile/activities."
        figmaPage="ST 01"
      />
      <SectionPanel title="Activity log">
        <QueryState
          isLoading={activities.isLoading}
          isError={activities.isError}
          error={activities.error}
          onRetry={() => void activities.refetch()}
          isEmpty={!activities.data?.items.length}
          emptyMessage="No activity recorded yet."
        >
          {activities.data ? (
            <ul className="divide-y divide-[#f1f5f9]">
              {activities.data.items.map((row) => (
                <li key={row.id} className="flex justify-between gap-4 py-3 text-sm">
                  <div>
                    <p className="font-medium text-[#111827]">{row.title}</p>
                    <p className="text-xs capitalize text-[#9ca3af]">{row.activity_type.replace(/_/g, " ")}</p>
                    {row.description ? (
                      <p className="mt-1 text-xs text-[#6b7280]">{row.description}</p>
                    ) : null}
                  </div>
                  <time className="shrink-0 text-xs text-[#9ca3af]">
                    {formatDateTime(row.created_at)}
                  </time>
                </li>
              ))}
            </ul>
          ) : null}
        </QueryState>
      </SectionPanel>
    </div>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block text-sm">
      <span className="mb-1 block text-xs font-medium text-[#6b7280]">{label}</span>
      {children}
    </label>
  );
}