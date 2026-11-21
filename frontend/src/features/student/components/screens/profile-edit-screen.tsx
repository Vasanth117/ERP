"use client";

import Link from "next/link";
import { useEffect, useState, type ChangeEvent } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  ProfileDetailGrid,
  ProfileFieldSwitch,
  ProfileFormField,
  ProfileInfoBanner,
  ProfilePageHeading,
  ProfilePanel,
} from "@/features/student/components/ui/student-profile-ui";
import { QueryState } from "@/features/student/components/ui/student-screen-ui";
import {
  useCommunicationPreferences,
  useUpdateCommunicationPreferences,
} from "@/features/student/hooks/use-student-communication";
import { useStudentProfile, useUpdateStudentProfile } from "@/features/student/hooks/use-student-profile";
import type { EmergencyContact, StudentProfileUpdate } from "@/features/student/types/profile";

const INPUT_CLASS =
  "h-10 w-full rounded-md border border-[#e8ecf2] bg-white px-3 text-[13px] font-medium text-[#172b45] shadow-[0_1px_2px_rgba(15,23,42,0.04)]";

const TEXTAREA_CLASS =
  "min-h-20 w-full rounded-md border border-[#e8ecf2] bg-white px-3 py-2 text-[13px] text-[#172b45] shadow-[0_1px_2px_rgba(15,23,42,0.04)]";

/** ST 01.07 — Edit permitted profile details (node 164:1934). */
export function StudentProfileEditScreen() {
  const profile = useStudentProfile();
  const updateProfile = useUpdateStudentProfile();
  const prefs = useCommunicationPreferences();
  const updatePrefs = useUpdateCommunicationPreferences();

  const [form, setForm] = useState<StudentProfileUpdate>({});
  const [message, setMessage] = useState<string | null>(null);
  const [editPhone, setEditPhone] = useState(true);
  const [editAltPhone, setEditAltPhone] = useState(true);
  const [editAltEmail, setEditAltEmail] = useState(true);
  const [editCurrentAddress, setEditCurrentAddress] = useState(true);
  const [editEmergency, setEditEmergency] = useState(true);

  useEffect(() => {
    if (!profile.data) return;
    setForm({
      contact_phone: profile.data.contact_phone,
      alternate_contact_phone: profile.data.alternate_contact_phone,
      alternate_email: profile.data.alternate_email,
      current_address: profile.data.current_address,
      permanent_address: profile.data.permanent_address,
      bio: profile.data.bio,
      emergency_contacts: profile.data.emergency_contacts,
    });
  }, [profile.data]);

  async function handleSave() {
    setMessage(null);
    const payload: StudentProfileUpdate = {};
    if (editPhone) payload.contact_phone = form.contact_phone;
    if (editAltPhone) payload.alternate_contact_phone = form.alternate_contact_phone;
    if (editAltEmail) payload.alternate_email = form.alternate_email;
    if (editCurrentAddress) {
      payload.current_address = form.current_address;
      payload.permanent_address = form.permanent_address;
    }
    if (form.bio !== undefined) payload.bio = form.bio;
    if (editEmergency) payload.emergency_contacts = form.emergency_contacts;

    if (Object.keys(payload).length === 0) {
      setMessage("Turn on at least one field switch to save.");
      return;
    }

    updateProfile.mutate(payload, {
      onSuccess: () => setMessage("Profile updated successfully."),
      onError: (err) => setMessage(err instanceof Error ? err.message : "Update failed"),
    });
  }

  return (
    <div className="space-y-5" data-figma-node="164:1934">
      <ProfilePageHeading
        title="Edit permitted profile details"
        description="You can change only these fields. Other changes need approval."
        backHref="/student/profile"
        actions={
          <>
            <Link
              href="/student/profile"
              className="inline-flex h-[33px] items-center rounded-md border border-[#e8ecf2] bg-white px-3.5 text-[12px] font-semibold text-[#374151] hover:bg-[#f8fafc]"
            >
              Cancel
            </Link>
            <Button
              type="button"
              className="h-[33px] bg-[#245dd8] px-3.5 text-[12px] font-semibold hover:bg-[#1f4fb8]"
              disabled={updateProfile.isPending || !profile.data}
              onClick={() => void handleSave()}
            >
              {updateProfile.isPending ? "Saving…" : "Save changes"}
            </Button>
          </>
        }
      />

      <ProfileInfoBanner
        title="Official fields are locked"
        description="Name, date of birth, programme and register number can only be changed through an update request."
        actionHref="/student/profile/update-requests"
        actionLabel="Request update →"
      />

      <QueryState query={profile}>
        {profile.data ? (
          <div className="grid items-start gap-6 lg:grid-cols-5">
            <div className="space-y-6 lg:col-span-3" id="contact">
              <ProfilePanel title="Editable fields" figmaNode="164:1934">
                <p className="mb-4 text-[12px] text-[#607086]">
                  Choose which fields to include in this save, then edit the values below.
                </p>
                <div className="mb-6 grid gap-x-8 gap-y-5 border-b border-[#eef2f6] pb-6 sm:grid-cols-2">
                  <ProfileFieldSwitch label="Personal phone" checked={editPhone} onChange={setEditPhone} />
                  <ProfileFieldSwitch label="Alternate mobile" checked={editAltPhone} onChange={setEditAltPhone} />
                  <ProfileFieldSwitch label="Alternate email" checked={editAltEmail} onChange={setEditAltEmail} />
                  <ProfileFieldSwitch
                    label="Communication address"
                    checked={editCurrentAddress}
                    onChange={setEditCurrentAddress}
                  />
                  <ProfileFieldSwitch label="Emergency contact" checked={editEmergency} onChange={setEditEmergency} />
                </div>

                <div className="grid gap-5 sm:grid-cols-2">
                  {editPhone ? (
                    <ProfileFormField label="Mobile">
                      <Input
                        className={INPUT_CLASS}
                        value={form.contact_phone ?? ""}
                        onChange={(e) => setForm((f) => ({ ...f, contact_phone: e.target.value }))}
                      />
                    </ProfileFormField>
                  ) : null}
                  {editAltPhone ? (
                    <ProfileFormField label="Alternate mobile">
                      <Input
                        className={INPUT_CLASS}
                        value={form.alternate_contact_phone ?? ""}
                        onChange={(e) =>
                          setForm((f) => ({ ...f, alternate_contact_phone: e.target.value }))
                        }
                      />
                    </ProfileFormField>
                  ) : null}
                  {editAltEmail ? (
                    <ProfileFormField label="Alternate email">
                      <Input
                        type="email"
                        className={INPUT_CLASS}
                        value={form.alternate_email ?? ""}
                        onChange={(e) => setForm((f) => ({ ...f, alternate_email: e.target.value }))}
                      />
                    </ProfileFormField>
                  ) : null}
                </div>

                {editCurrentAddress ? (
                  <div className="mt-5 grid gap-5 sm:grid-cols-2">
                    <ProfileFormField label="Current address" className="sm:col-span-2">
                      <textarea
                        className={TEXTAREA_CLASS}
                        value={form.current_address ?? ""}
                        onChange={(e: ChangeEvent<HTMLTextAreaElement>) =>
                          setForm((f) => ({ ...f, current_address: e.target.value }))
                        }
                      />
                    </ProfileFormField>
                    <ProfileFormField label="Permanent address" className="sm:col-span-2">
                      <textarea
                        className={TEXTAREA_CLASS}
                        value={form.permanent_address ?? ""}
                        onChange={(e: ChangeEvent<HTMLTextAreaElement>) =>
                          setForm((f) => ({ ...f, permanent_address: e.target.value }))
                        }
                      />
                    </ProfileFormField>
                  </div>
                ) : null}

                <div className="mt-5">
                  <ProfileFormField label="Bio">
                    <textarea
                      className={TEXTAREA_CLASS}
                      value={form.bio ?? ""}
                      onChange={(e: ChangeEvent<HTMLTextAreaElement>) =>
                        setForm((f) => ({ ...f, bio: e.target.value }))
                      }
                    />
                  </ProfileFormField>
                </div>

                {editEmergency ? (
                  <div className="mt-5 border-t border-[#eef2f6] pt-5">
                    <EmergencyContactEditor
                      contacts={form.emergency_contacts ?? []}
                      onChange={(next) => setForm((f) => ({ ...f, emergency_contacts: next }))}
                    />
                  </div>
                ) : null}

                {message ? (
                  <p
                    className={`mt-4 text-sm ${message.includes("success") ? "text-[#047857]" : "text-[#607086]"}`}
                  >
                    {message}
                  </p>
                ) : null}
              </ProfilePanel>

              <ProfilePanel title="Locked fields">
                <ProfileDetailGrid
                  variant="personal"
                  rows={[
                    [
                      { label: "Full name", value: profile.data.full_name },
                      { label: "Register number", value: profile.data.roll_number ?? "—" },
                    ],
                    [
                      { label: "Programme", value: profile.data.programme_name ?? "—" },
                      { label: "Institutional email", value: profile.data.email },
                    ],
                  ]}
                />
              </ProfilePanel>
            </div>

            <div className="lg:col-span-2">
              <QueryState query={prefs}>
                {prefs.data ? (
                  <ProfilePanel title="Communication preferences">
                    <p className="mb-4 text-[12px] text-[#607086]">
                      Saved immediately to your account (PATCH communication preferences).
                    </p>
                    <div className="grid gap-x-8 gap-y-5 sm:grid-cols-2">
                      <ProfileFieldSwitch
                        label="Email alerts"
                        description="Results, notices"
                        checked={prefs.data.email_enabled}
                        onChange={(v) => updatePrefs.mutate({ email_enabled: v })}
                        disabled={updatePrefs.isPending}
                      />
                      <ProfileFieldSwitch
                        label="SMS / push alerts"
                        description="Attendance, fees"
                        checked={prefs.data.push_enabled}
                        onChange={(v) => updatePrefs.mutate({ push_enabled: v })}
                        disabled={updatePrefs.isPending}
                      />
                      <ProfileFieldSwitch
                        label="Academic updates"
                        checked={prefs.data.academic_enabled}
                        onChange={(v) => updatePrefs.mutate({ academic_enabled: v })}
                        disabled={updatePrefs.isPending}
                      />
                      <ProfileFieldSwitch
                        label="Examination updates"
                        checked={prefs.data.examination_enabled}
                        onChange={(v) => updatePrefs.mutate({ examination_enabled: v })}
                        disabled={updatePrefs.isPending}
                      />
                      <ProfileFieldSwitch
                        label="Finance updates"
                        checked={prefs.data.finance_enabled}
                        onChange={(v) => updatePrefs.mutate({ finance_enabled: v })}
                        disabled={updatePrefs.isPending}
                      />
                      <ProfileFieldSwitch
                        label="Library updates"
                        checked={prefs.data.library_enabled}
                        onChange={(v) => updatePrefs.mutate({ library_enabled: v })}
                        disabled={updatePrefs.isPending}
                      />
                    </div>
                  </ProfilePanel>
                ) : null}
              </QueryState>
            </div>
          </div>
        ) : null}
      </QueryState>
    </div>
  );
}

function EmergencyContactEditor({
  contacts,
  onChange,
}: {
  contacts: EmergencyContact[];
  onChange: (next: EmergencyContact[]) => void;
}) {
  const rows = contacts.length ? contacts : [{ name: "", relationship: "", phone: "", email: "" }];

  return (
    <div className="space-y-3">
      <p className="text-[12px] font-normal text-[#607086]">Emergency contact</p>
      {rows.map((row, index) => (
        <div
          key={`ec-${index}`}
          className="grid gap-3 rounded-lg border border-[#e8ecf2] bg-[#fafbfc] p-4 sm:grid-cols-2"
        >
          <ProfileFormField label="Name">
            <Input
              className={INPUT_CLASS}
              value={row.name}
              onChange={(e) => {
                const next = [...rows];
                next[index] = { ...row, name: e.target.value };
                onChange(next);
              }}
            />
          </ProfileFormField>
          <ProfileFormField label="Relationship">
            <Input
              className={INPUT_CLASS}
              value={row.relationship}
              onChange={(e) => {
                const next = [...rows];
                next[index] = { ...row, relationship: e.target.value };
                onChange(next);
              }}
            />
          </ProfileFormField>
          <ProfileFormField label="Phone">
            <Input
              className={INPUT_CLASS}
              value={row.phone}
              onChange={(e) => {
                const next = [...rows];
                next[index] = { ...row, phone: e.target.value };
                onChange(next);
              }}
            />
          </ProfileFormField>
          <ProfileFormField label="Email (optional)">
            <Input
              className={INPUT_CLASS}
              value={row.email ?? ""}
              onChange={(e) => {
                const next = [...rows];
                next[index] = { ...row, email: e.target.value };
                onChange(next);
              }}
            />
          </ProfileFormField>
        </div>
      ))}
      <Button
        type="button"
        variant="outline"
        className="h-8 border-[#e8ecf2] text-xs"
        onClick={() => onChange([...rows, { name: "", relationship: "", phone: "", email: "" }])}
      >
        Add contact
      </Button>
    </div>
  );
}