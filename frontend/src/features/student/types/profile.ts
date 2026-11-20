export type EmergencyContact = {
  name: string;
  relationship: string;
  phone: string;
  email?: string | null;
};

export type ProfileDocumentRef = {
  ref: string;
  label: string;
};

export type StudentProfile = {
  user_id: string;
  full_name: string;
  email: string;
  student_id: string | null;
  roll_number: string | null;
  admission_number: string | null;
  admission_date: string | null;
  department_id: string | null;
  department_name: string | null;
  programme_code: string | null;
  programme_name: string | null;
  batch_label: string | null;
  section_code: string | null;
  contact_phone: string | null;
  alternate_email: string | null;
  permanent_address: string | null;
  current_address: string | null;
  emergency_contacts: EmergencyContact[];
  bio: string | null;
  profile_photo_ref: string | null;
  document_refs: ProfileDocumentRef[];
  updated_at: string;
};

export type StudentProfileUpdate = {
  contact_phone?: string | null;
  alternate_email?: string | null;
  permanent_address?: string | null;
  current_address?: string | null;
  emergency_contacts?: EmergencyContact[] | null;
  bio?: string | null;
  profile_photo_ref?: string | null;
};