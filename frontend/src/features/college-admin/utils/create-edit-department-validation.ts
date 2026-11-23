import type { CreateEditDepartmentFormValues, CreateEditDepartmentPage } from "@/features/college-admin/types/create-edit-department";
import type { FormValidationDetail } from "@/lib/api/form-validation";

function detailForField(
  fieldKey: string,
  metaLabel: string,
  schoolSelectable: number,
  campusSelectable: number,
): FormValidationDetail {
  if (fieldKey === "organization_unit_id") {
    if (schoolSelectable <= 0) {
      return {
        field_key: fieldKey,
        label: metaLabel,
        message: "No schools or faculties are set up yet. Add one before creating a department.",
        action_type: "navigate",
        action_label: "Open organization hierarchy",
        action_href: "/college-admin/organization/organizational-hierarchy",
      };
    }
    return {
      field_key: fieldKey,
      label: metaLabel,
      message: "Select which school or faculty this department belongs to.",
      action_type: "scroll",
      action_label: "Go to School / faculty",
    };
  }
  if (fieldKey === "campus_id") {
    if (campusSelectable <= 0) {
      return {
        field_key: fieldKey,
        label: metaLabel,
        message: "No campuses are configured for this institution.",
        action_type: "navigate",
        action_label: "Manage campuses",
        action_href: "/college-admin/institution/campuses",
      };
    }
    return {
      field_key: fieldKey,
      label: metaLabel,
      message: "Select the campus where this department is located.",
      action_type: "scroll",
      action_label: "Go to Campus",
    };
  }
  const copy: Record<string, { message: string; action_label: string }> = {
    name: { message: "Enter the full display name of the department.", action_label: "Go to Department name" },
    department_code: { message: "Enter a unique department code (e.g. CSE, MBA).", action_label: "Go to Department code" },
    establishment_year: {
      message: "Enter the year the department was established.",
      action_label: "Go to Year of establishment",
    },
  };
  const row = copy[fieldKey] ?? {
    message: `Complete the required field: ${metaLabel}.`,
    action_label: `Go to ${metaLabel}`,
  };
  return {
    field_key: fieldKey,
    label: metaLabel,
    message: row.message,
    action_type: "scroll",
    action_label: row.action_label,
  };
}

export function validateCreateEditDepartmentForm(
  values: CreateEditDepartmentFormValues,
  page: CreateEditDepartmentPage,
  mode: "create" | "draft",
): FormValidationDetail[] {
  const schoolSelectable = page.school_options.filter((opt) => opt.value).length;
  const campusSelectable = page.campus_options.filter((opt) => opt.value).length;
  const labelByKey = new Map(page.details_field_meta.map((row) => [row.key, row.label]));

  const missing: string[] = [];
  if (mode === "create") {
    if (!values.name.trim()) missing.push("name");
    if (!values.department_code.trim()) missing.push("department_code");
    if (!values.organization_unit_id) missing.push("organization_unit_id");
    if (!values.campus_id) missing.push("campus_id");
    if (values.establishment_year == null) missing.push("establishment_year");
  } else {
    if (!values.name.trim()) missing.push("name");
    if (!values.department_code.trim()) missing.push("department_code");
  }

  return missing.map((key) =>
    detailForField(key, labelByKey.get(key) ?? key, schoolSelectable, campusSelectable),
  );
}