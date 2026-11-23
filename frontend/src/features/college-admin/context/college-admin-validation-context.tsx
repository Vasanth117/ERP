"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { toast } from "sonner";

import { CollegeAdminFormValidationDialog } from "@/features/college-admin/components/ui/college-admin-form-validation-dialog";
import {
  parseFormValidationDetails,
  type FormValidationDetail,
} from "@/lib/api/form-validation";

type ValidationState = {
  title: string;
  description: string;
  items: FormValidationDetail[];
} | null;

type CollegeAdminValidationContextValue = {
  onMutationError: (err: Error & { details?: unknown }) => void;
  showValidation: (title: string, description: string, items: FormValidationDetail[]) => void;
};

const CollegeAdminValidationContext = createContext<CollegeAdminValidationContextValue | null>(null);

export function CollegeAdminValidationProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<ValidationState>(null);

  const showValidation = useCallback((title: string, description: string, items: FormValidationDetail[]) => {
    if (!items.length) return;
    setState({ title, description, items });
  }, []);

  const onMutationError = useCallback((err: Error & { details?: unknown }) => {
    const items = parseFormValidationDetails(err.details);
    if (items.length) {
      showValidation("Missing required information", err.message, items);
      return;
    }
    toast.error(err.message);
  }, [showValidation]);

  const value = useMemo(() => ({ onMutationError, showValidation }), [onMutationError, showValidation]);

  useEffect(() => {
    registerCollegeAdminValidationHandler(onMutationError);
    return () => {
      registerCollegeAdminValidationHandler((err) => toast.error(err.message));
    };
  }, [onMutationError]);

  return (
    <CollegeAdminValidationContext.Provider value={value}>
      {children}
      <CollegeAdminFormValidationDialog
        open={Boolean(state)}
        title={state?.title ?? ""}
        description={state?.description ?? ""}
        items={state?.items ?? []}
        onClose={() => setState(null)}
      />
    </CollegeAdminValidationContext.Provider>
  );
}

export function useCollegeAdminValidation() {
  const ctx = useContext(CollegeAdminValidationContext);
  if (!ctx) {
    return {
      onMutationError: onCollegeAdminMutationError,
      showValidation: () => undefined,
    };
  }
  return ctx;
}

/** Use from non-React modules (e.g. legacy callbacks). Prefer the hook when possible. */
let _fallbackError: (err: Error & { details?: unknown }) => void = (err) => toast.error(err.message);

export function registerCollegeAdminValidationHandler(handler: (err: Error & { details?: unknown }) => void) {
  _fallbackError = handler;
}

export function onCollegeAdminMutationError(err: Error & { details?: unknown }) {
  _fallbackError(err);
}