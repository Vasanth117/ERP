"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { onCollegeAdminMutationError } from "@/features/college-admin/context/college-admin-validation-context";
import { toast } from "sonner";

import {
  copyAcademicYearFromPrevious,
  createInstitutionAcademicYear,
  fetchAcademicYearConfigurationPage,
  saveAcademicYearConfiguration,
  fetchInstitutionCalendarSettingsPage,
  createInstitutionHoliday,
  importInstitutionCalendarHolidays,
  saveInstitutionCalendarSettingsPage,
  createInstitutionPolicy,
  fetchInstitutionPoliciesPage,
  fetchAcademicInstitutionSettingsPage,
  resetAcademicInstitutionSettingsPage,
  saveAcademicInstitutionSettingsPage,
  createCampus,
  fetchCampus,
  fetchCampusContactPage,
  fetchCampusDetailPage,
  fetchCampusManagementDashboard,
  fetchCampuses,
  saveCampusContactPage,
  fetchConfigurationHistory,
  fetchConfigurationHistoryPage,
  fetchInstitutionalOverview,
  fetchInstitutionProfile,
  fetchInstitutionBrandingPage,
  fetchInstitutionInformationPage,
  publishInstitutionBranding,
  saveInstitutionBrandingDraft,
  uploadBrandingAsset,
  fetchInstitutionProfilePage,
  publishInstitutionInformation,
  saveInstitutionInformationDraft,
  fetchInstitutionSettings,
  updateCampus,
  updateInstitutionProfile,
  updateInstitutionSettings,
} from "@/features/college-admin/api/institution";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type {
  AcademicInstitutionFormValues,
  AcademicYearSemesterForm,
  InstitutionCalendarFormValues,
  CampusContactPageSave,
  CampusCreate,
  CampusUpdate,
  InstitutionProfileUpdate,
  InstitutionSettingsPatch,
} from "@/features/college-admin/types/institution";

export function useInstitutionProfile() {
  return useQuery({
    queryKey: collegeAdminQueryKeys.profile(),
    queryFn: fetchInstitutionProfile,
  });
}

export function useInstitutionProfilePage() {
  return useQuery({
    queryKey: collegeAdminQueryKeys.profilePage(),
    queryFn: fetchInstitutionProfilePage,
  });
}

export function useInstitutionInformationPage() {
  return useQuery({
    queryKey: collegeAdminQueryKeys.informationPage(),
    queryFn: fetchInstitutionInformationPage,
  });
}

export function useSaveInstitutionInformationDraft() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (values: Record<string, unknown>) => saveInstitutionInformationDraft(values),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.informationPage() });
      toast.success("Draft saved");
    },
    onError: onCollegeAdminMutationError,
  });
}

export function useInstitutionBrandingPage() {
  return useQuery({
    queryKey: collegeAdminQueryKeys.brandingPage(),
    queryFn: fetchInstitutionBrandingPage,
  });
}

export function useSaveInstitutionBrandingDraft() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (values: Record<string, unknown>) => saveInstitutionBrandingDraft(values),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.brandingPage() });
      toast.success("Branding draft saved");
    },
    onError: onCollegeAdminMutationError,
  });
}

export function usePublishInstitutionBranding() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (values: Record<string, unknown>) => publishInstitutionBranding(values),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.brandingPage() });
      void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.profilePage() });
      void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.settings() });
      toast.success("Branding published");
    },
    onError: onCollegeAdminMutationError,
  });
}

export function useUploadBrandingAsset() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ assetKey, file }: { assetKey: string; file: File }) =>
      uploadBrandingAsset(assetKey, file),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.brandingPage() });
      toast.success("File uploaded");
    },
    onError: onCollegeAdminMutationError,
  });
}

export function usePublishInstitutionInformation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (values: Record<string, unknown>) => publishInstitutionInformation(values),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.informationPage() });
      void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.profile() });
      void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.profilePage() });
      toast.success("Institution information saved");
    },
    onError: onCollegeAdminMutationError,
  });
}

export function useInstitutionalOverview() {
  return useQuery({
    queryKey: collegeAdminQueryKeys.institutionalOverview(),
    queryFn: fetchInstitutionalOverview,
  });
}

export function useUpdateInstitutionProfile() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: InstitutionProfileUpdate) =>
      updateInstitutionProfile(payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.profile() });
      void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.profilePage() });
      toast.success("Institution profile saved");
    },
    onError: onCollegeAdminMutationError,
  });
}

export function useAcademicYearConfigurationPage(selectedYearId?: string) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.academicYearPage(selectedYearId),
    queryFn: () => fetchAcademicYearConfigurationPage(selectedYearId),
  });
}

export function useSaveAcademicYearConfiguration() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ yearId, form }: { yearId: string; form: AcademicYearSemesterForm }) =>
      saveAcademicYearConfiguration(yearId, form),
    onSuccess: (page, variables) => {
      void qc.setQueryData(collegeAdminQueryKeys.academicYearPage(variables.yearId), page);
      if (page.selected_year_id && page.selected_year_id !== variables.yearId) {
        void qc.setQueryData(collegeAdminQueryKeys.academicYearPage(page.selected_year_id), page);
      }
      void qc.invalidateQueries({
        queryKey: [...collegeAdminQueryKeys.all, "institution-academic-year-page"],
      });
      toast.success("Academic year configuration saved");
    },
    onError: onCollegeAdminMutationError,
  });
}

export function useCopyAcademicYearFromPrevious() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => copyAcademicYearFromPrevious(),
    onSuccess: (page) => {
      if (page.selected_year_id) {
        void qc.setQueryData(collegeAdminQueryKeys.academicYearPage(page.selected_year_id), page);
      }
      void qc.invalidateQueries({
        queryKey: [...collegeAdminQueryKeys.all, "institution-academic-year-page"],
      });
      toast.success("Academic year copied");
    },
    onError: onCollegeAdminMutationError,
  });
}

export function useCreateInstitutionAcademicYear() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => createInstitutionAcademicYear(),
    onSuccess: (page) => {
      if (page.selected_year_id) {
        void qc.setQueryData(collegeAdminQueryKeys.academicYearPage(page.selected_year_id), page);
      }
      void qc.invalidateQueries({
        queryKey: [...collegeAdminQueryKeys.all, "institution-academic-year-page"],
      });
      toast.success("Academic year created");
    },
    onError: onCollegeAdminMutationError,
  });
}

export function useInstitutionCalendarSettingsPage(params: {
  page?: number;
  academic_year_id?: string;
} = {}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.calendarSettingsPage(params),
    queryFn: () => fetchInstitutionCalendarSettingsPage(params),
  });
}

export function useSaveInstitutionCalendarSettingsPage(
  context: { page?: number; academic_year_id?: string | null } = {},
) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (form: InstitutionCalendarFormValues) =>
      saveInstitutionCalendarSettingsPage({
        form,
        page: context.page,
        academic_year_id: context.academic_year_id,
      }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["college-admin", "institution-calendar-settings-page"] });
      toast.success("Calendar settings saved");
    },
    onError: onCollegeAdminMutationError,
  });
}

export function useImportInstitutionCalendarHolidays() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => importInstitutionCalendarHolidays(),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["college-admin", "institution-calendar-settings-page"] });
      toast.success("Holidays imported");
    },
    onError: onCollegeAdminMutationError,
  });
}

export function useCreateInstitutionHoliday() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: createInstitutionHoliday,
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["college-admin", "institution-calendar-settings-page"] });
    },
    onError: onCollegeAdminMutationError,
  });
}

export function useInstitutionPoliciesPage(params: {
  search?: string;
  category?: string;
  audience?: string;
  status?: string;
  page?: number;
  selected_policy_id?: string;
}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.policiesPage(params),
    queryFn: () => fetchInstitutionPoliciesPage(params),
  });
}

export function useCreateInstitutionPolicy() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: createInstitutionPolicy,
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: [...collegeAdminQueryKeys.all, "policies-page"] });
    },
    onError: onCollegeAdminMutationError,
  });
}

export function useAcademicInstitutionSettingsPage() {
  return useQuery({
    queryKey: collegeAdminQueryKeys.academicSettingsPage(),
    queryFn: fetchAcademicInstitutionSettingsPage,
  });
}

export function useSaveAcademicInstitutionSettingsPage() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (form: AcademicInstitutionFormValues) =>
      saveAcademicInstitutionSettingsPage(form),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.academicSettingsPage() });
      toast.success("Academic settings saved");
    },
    onError: onCollegeAdminMutationError,
  });
}

export function useResetAcademicInstitutionSettingsPage() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => resetAcademicInstitutionSettingsPage(),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.academicSettingsPage() });
      toast.success("Academic settings reset to defaults");
    },
    onError: onCollegeAdminMutationError,
  });
}

export function useCampusManagementDashboard() {
  return useQuery({
    queryKey: collegeAdminQueryKeys.campusesDashboard(),
    queryFn: fetchCampusManagementDashboard,
  });
}

export function useCampusDetailPage(campusId: string) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.campusDetailPage(campusId),
    queryFn: () => fetchCampusDetailPage(campusId),
    enabled: Boolean(campusId),
  });
}

export function useCampusContactPage(campusId: string) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.campusContactPage(campusId),
    queryFn: () => fetchCampusContactPage(campusId),
    enabled: Boolean(campusId),
  });
}

export function useSaveCampusContactPage(campusId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CampusContactPageSave) =>
      saveCampusContactPage(campusId, payload),
    onSuccess: () => {
      void qc.invalidateQueries({
        queryKey: collegeAdminQueryKeys.campusContactPage(campusId),
      });
      void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.campuses() });
      void qc.invalidateQueries({
        queryKey: collegeAdminQueryKeys.campusesDashboard(),
      });
      toast.success("Campus contact information saved");
    },
    onError: onCollegeAdminMutationError,
  });
}

export function useCampuses(activeOnly = false) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.campuses(activeOnly),
    queryFn: () => fetchCampuses(activeOnly),
  });
}

export function useCampus(campusId: string) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.campus(campusId),
    queryFn: () => fetchCampus(campusId),
    enabled: Boolean(campusId),
  });
}

export function useCreateCampus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CampusCreate) => createCampus(payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.all });
      void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.campusesDashboard() });
      toast.success("Campus created");
    },
    onError: onCollegeAdminMutationError,
  });
}

export function useUpdateCampus(campusId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CampusUpdate) => updateCampus(campusId, payload),
    onSuccess: () => {
      void qc.invalidateQueries({
        queryKey: collegeAdminQueryKeys.campus(campusId),
      });
      void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.campuses() });
      toast.success("Campus updated");
    },
    onError: onCollegeAdminMutationError,
  });
}

export function useInstitutionSettings() {
  return useQuery({
    queryKey: collegeAdminQueryKeys.settings(),
    queryFn: fetchInstitutionSettings,
  });
}

export function useUpdateInstitutionSettings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: InstitutionSettingsPatch) =>
      updateInstitutionSettings(payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.settings() });
      toast.success("Settings saved");
    },
    onError: onCollegeAdminMutationError,
  });
}

export function useConfigurationHistory() {
  return useQuery({
    queryKey: collegeAdminQueryKeys.configHistory(),
    queryFn: fetchConfigurationHistory,
  });
}

export function useConfigurationHistoryPage(params: {
  page?: number;
  date_range?: string;
  setting_area?: string;
  actor_id?: string;
  search?: string;
  selected_change_id?: string;
}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.configurationHistoryPage(params),
    queryFn: () => fetchConfigurationHistoryPage(params),
  });
}