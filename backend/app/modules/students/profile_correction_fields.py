"""Official profile fields students may request to correct (portal Path B)."""

from __future__ import annotations

ALLOWED_CORRECTION_FIELDS = frozenset(
    {
        # Identity & academic (profile / admission)
        "display_name",
        "roll_number",
        "admission_number",
        "programme_name",
        "programme_code",
        "section_code",
        "batch_label",
        "regulation_label",
        "admission_type",
        # Personal (admission metadata)
        "date_of_birth",
        "gender",
        "nationality",
        "mother_tongue",
        "blood_group",
        "religion",
        "community",
        "aadhaar",
        # Guardians
        "guardian_father_name",
        "guardian_mother_name",
        "guardian_father_phone",
        "guardian_mother_phone",
        "guardian_father_email",
        "guardian_mother_email",
        "guardian_father_occupation",
        "guardian_mother_occupation",
    }
)

# Admission.metadata keys written on approve (first key is primary).
METADATA_FIELD_KEYS: dict[str, tuple[str, ...]] = {
    "date_of_birth": ("date_of_birth", "dob"),
    "gender": ("gender", "sex"),
    "nationality": ("nationality",),
    "mother_tongue": ("mother_tongue", "mother_tongue_name"),
    "blood_group": ("blood_group",),
    "religion": ("religion",),
    "community": ("community", "caste", "category"),
    "aadhaar": ("aadhaar", "aadhaar_number"),
    "regulation_label": ("regulation_label", "regulation"),
    "admission_type": ("admission_type",),
    "batch_label": ("batch_display", "batch_label"),
}

GUARDIAN_CORRECTION_ATTR: dict[str, tuple[str, str]] = {
    "guardian_father_name": ("father", "guardian_name"),
    "guardian_mother_name": ("mother", "guardian_name"),
    "guardian_father_phone": ("father", "phone"),
    "guardian_mother_phone": ("mother", "phone"),
    "guardian_father_email": ("father", "email"),
    "guardian_mother_email": ("mother", "email"),
    "guardian_father_occupation": ("father", "occupation"),
    "guardian_mother_occupation": ("mother", "occupation"),
}