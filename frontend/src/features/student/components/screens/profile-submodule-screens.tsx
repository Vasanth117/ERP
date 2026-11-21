"use client";

import {
  ProfileDetailGrid,
  ProfileEditDetailsButton,
  ProfileInfoBanner,
  ProfileEmergencyHighlight,
  ProfileGuardianCard,
  ProfilePageHeading,
  ProfilePanel,
  ProfilePreferenceRow,
  ProfileRequestUpdateButton,
  ProfileVerificationPanel,
} from "@/features/student/components/ui/student-profile-ui";
import { QueryState, formatDate } from "@/features/student/components/ui/student-screen-ui";
import { useCommunicationPreferences } from "@/features/student/hooks/use-student-communication";
import { useStudentProfile } from "@/features/student/hooks/use-student-profile";

function religionCommunity(official: NonNullable<ReturnType<typeof useStudentProfile>["data"]>["official_personal"]) {
  if (!official) return "—";
  const parts = [official.religion, official.community].filter(Boolean);
  return parts.length ? parts.join(" - ") : "—";
}

/** Figma ST 01.03 date format (e.g. 14 Mar 2004). */
function formatPersonalDate(value: string | null | undefined) {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}

/** ST 01.03 — Personal Information (node 164:720). */
export function StudentProfilePersonalScreen() {
  const profile = useStudentProfile();

  return (
    <div className="space-y-5" data-figma-node="164:720">
      <ProfilePageHeading
        title="Personal Information"
        description="Read-only. Official details are maintained by the college"
        backHref="/student/profile"
        actions={<ProfileRequestUpdateButton defaultField="display_name" />}
      />
      <QueryState query={profile}>
        {profile.data ? (
          <div className="grid items-start gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2">
              <ProfilePanel title="Personal details" figmaNode="164:750">
                <ProfileDetailGrid
                  variant="personal"
                  rows={[
                    [
                      { label: "Full name", value: profile.data.full_name },
                      {
                        label: "Date of birth",
                        value: formatPersonalDate(profile.data.official_personal?.date_of_birth),
                      },
                    ],
                    [
                      { label: "Gender", value: profile.data.official_personal?.gender ?? "—" },
                      { label: "Blood group", value: profile.data.official_personal?.blood_group ?? "—" },
                    ],
                    [
                      { label: "Nationality", value: profile.data.official_personal?.nationality ?? "—" },
                      {
                        label: "Religion / community",
                        value: religionCommunity(profile.data.official_personal),
                      },
                    ],
                    [
                      { label: "Mother tongue", value: profile.data.official_personal?.mother_tongue ?? "—" },
                      { label: "Aadhaar", value: profile.data.official_personal?.aadhaar_masked ?? "—" },
                    ],
                  ]}
                />
              </ProfilePanel>
            </div>
            <UploadVerificationAside profile={profile.data} />
          </div>
        ) : null}
      </QueryState>
    </div>
  );
}

function UploadVerificationAside({
  profile,
}: {
  profile: NonNullable<ReturnType<typeof useStudentProfile>["data"]>;
}) {
  return (
    <ProfileVerificationPanel
      identityVerified={Boolean(profile.official_personal?.identity_documents_verified)}
      lastUpdated={formatPersonalDate(profile.updated_at)}
    />
  );
}

/** ST 01.05 — Contact Information (node 164:1327). */
export function StudentProfileContactScreen() {
  const profile = useStudentProfile();
  const prefs = useCommunicationPreferences();

  return (
    <div className="space-y-5" data-figma-node="164:1327">
      <ProfilePageHeading
        title="Contact Information"
        description="Phone, email and address"
        backHref="/student/profile"
        actions={<ProfileEditDetailsButton hash="contact" />}
      />
      <ProfileInfoBanner
        title="Self-service contact updates"
        description="Mobile, alternate email and addresses are saved immediately via Edit details (PATCH /students/me/profile). Institution email is official and cannot be edited here."
        actionHref="/student/profile/edit#contact"
        actionLabel="Edit details →"
      />
      <QueryState query={profile}>
        {profile.data ? (
          <div className="grid items-start gap-6 lg:grid-cols-3">
            <div className="space-y-5 lg:col-span-2">
              <ProfilePanel title="Contact">
                <ProfileDetailGrid
                  rows={[
                    [
                      { label: "Mobile", value: profile.data.contact_phone ?? "—" },
                      { label: "Alternate mobile", value: profile.data.alternate_contact_phone ?? "—" },
                    ],
                    [
                      { label: "Institution email", value: profile.data.email },
                      {
                        label: "Personal email",
                        value:
                          profile.data.alternate_email ??
                          profile.data.official_personal?.personal_email ??
                          "—",
                      },
                    ],
                  ]}
                />
              </ProfilePanel>
              <ProfilePanel title="Address">
                <ProfileDetailGrid
                  rows={[
                    [{ label: "Permanent address", value: profile.data.permanent_address ?? "—" }],
                    [{ label: "Communication address", value: profile.data.current_address ?? "—" }],
                  ]}
                />
              </ProfilePanel>
            </div>
            <QueryState query={prefs}>
              {prefs.data ? (
                <ProfilePanel title="Preferences">
                  <ProfilePreferenceRow icon="phone" label="SMS alerts" enabled={prefs.data.push_enabled} />
                  <ProfilePreferenceRow icon="mail" label="Email alerts" enabled={prefs.data.email_enabled} />
                </ProfilePanel>
              ) : null}
            </QueryState>
          </div>
        ) : null}
      </QueryState>
    </div>
  );
}

/** ST 01.06 — Guardian Information (node 164:1634). */
export function StudentProfileGuardianScreen() {
  const profile = useStudentProfile();

  const guardians = profile.data?.guardians ?? [];
  const father = guardians.find((g) => g.relationship.toLowerCase() === "father");
  const mother = guardians.find((g) => g.relationship.toLowerCase() === "mother");
  const emergency = profile.data?.emergency_contacts[0];

  return (
    <div className="space-y-5" data-figma-node="164:1634">
      <ProfilePageHeading
        title="Guardian Information"
        description="Parent and guardian details"
        backHref="/student/profile"
        actions={<ProfileRequestUpdateButton />}
      />
      <ProfileInfoBanner
        title="Emergency vs official guardian data"
        description="Emergency contacts update immediately on Edit permitted fields. Father and mother records are official — use Update requests for guardian name, phone, email, or occupation."
        actionHref="/student/profile/update-requests?field=guardian_father_name"
        actionLabel="Update requests →"
      />
      <QueryState query={profile}>
        {profile.data ? (
          <div className="grid items-start gap-6 lg:grid-cols-3">
            <div className="space-y-5 lg:col-span-2">
              <ProfileGuardianCard
                title="Father"
                rows={father ? guardianRows(father) : emptyGuardianRows("Father")}
              />
              <ProfileGuardianCard
                title="Mother"
                rows={mother ? guardianRows(mother) : emptyGuardianRows("Mother")}
              />
            </div>
            <div>
              {emergency ? (
                <ProfileEmergencyHighlight
                  name={emergency.name}
                  relationship={emergency.relationship ?? "Emergency contact"}
                  phone={emergency.phone}
                />
              ) : father ? (
                <ProfileEmergencyHighlight
                  name={father.name}
                  relationship="Father"
                  phone={father.phone}
                />
              ) : (
                <ProfilePanel title="Emergency contact">
                  <p className="text-sm text-[#607086]">No emergency contact on file.</p>
                </ProfilePanel>
              )}
            </div>
          </div>
        ) : null}
      </QueryState>
    </div>
  );
}

function guardianRows(guardian: {
  name: string;
  occupation?: string | null;
  phone: string;
  email?: string | null;
}) {
  return [
    { label: "Name", value: guardian.name },
    { label: "Occupation", value: guardian.occupation ?? "—" },
    { label: "Mobile", value: guardian.phone },
    { label: "Email", value: guardian.email ?? "—" },
  ];
}

function emptyGuardianRows(role: string) {
  return [
    { label: "Name", value: `No ${role.toLowerCase()} record` },
    { label: "Occupation", value: "—" },
    { label: "Mobile", value: "—" },
    { label: "Email", value: "—" },
  ];
}