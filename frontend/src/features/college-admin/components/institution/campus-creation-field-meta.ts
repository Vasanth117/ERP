import type { InstitutionFieldMeta } from "@/features/college-admin/types/institution";

export const CAMPUS_CREATION_FIELD_META_BY_STEP: Record<string, InstitutionFieldMeta[]> = {
  identity: [
    { key: "campus_code", label: "Campus code", required: true },
    { key: "name", label: "Campus name", required: true },
    { key: "is_main", label: "Main campus" },
  ],
  location: [
    { key: "address_line1", label: "Address line 1", required: true },
    { key: "address_line2", label: "Address line 2" },
    { key: "city", label: "City", required: true },
    { key: "district", label: "District" },
    { key: "state", label: "State", required: true },
    { key: "country", label: "Country", required: true },
    { key: "postal_code", label: "Postal code" },
    { key: "latitude", label: "Latitude" },
    { key: "longitude", label: "Longitude" },
  ],
  contact: [
    { key: "contact_email", label: "Contact email", field_type: "email" },
    { key: "contact_phone", label: "Contact phone" },
    { key: "timezone", label: "Timezone" },
    { key: "locale", label: "Locale" },
  ],
  capacity: [
    { key: "area_acres", label: "Campus area (acres)" },
    { key: "built_up_sq_m", label: "Built-up area (sq. m)" },
    { key: "buildings_count", label: "Buildings count" },
    { key: "parking_slots", label: "Parking slots" },
  ],
  facilities: [
    { key: "planned_classrooms", label: "Planned classrooms" },
    { key: "planned_laboratories", label: "Planned laboratories" },
    { key: "hostel_blocks_planned", label: "Hostel blocks (planned)" },
    { key: "library_branches_planned", label: "Library branches (planned)" },
    { key: "facilities_notes", label: "Facilities notes", field_type: "textarea" },
  ],
  review: [],
};