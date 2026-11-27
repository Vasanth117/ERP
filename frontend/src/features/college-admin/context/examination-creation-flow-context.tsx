"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

export const EXAMINATION_CREATION_STEP_SLUGS = [
  "examination-configuration",
  "internal-external-assessment",
  "exam-timetable-management",
  "examination-hall-seating-management",
  "marks-entry-management",
  "result-approval",
] as const;

export type ExaminationCreationStepSlug = (typeof EXAMINATION_CREATION_STEP_SLUGS)[number];

export function examinationStepIndexFromHref(href: string | undefined): number | null {
  if (!href) return null;
  const path = href.split("?")[0] ?? "";
  const slug = path.split("/").filter(Boolean).pop() ?? "";
  const index = EXAMINATION_CREATION_STEP_SLUGS.indexOf(slug as ExaminationCreationStepSlug);
  return index >= 0 ? index : null;
}

type ExaminationCreationFlowContextValue = {
  isModalOpen: boolean;
  stepIndex: number;
  stepSlug: ExaminationCreationStepSlug;
  sessionId: string | undefined;
  openCreation: (options?: { sessionId?: string; stepIndex?: number }) => void;
  closeCreation: () => void;
  setSessionId: (sessionId: string | undefined) => void;
  goToStep: (index: number) => void;
  goBack: () => void;
  advanceFromHref: (continueHref: string | undefined) => void;
};

const ExaminationCreationFlowContext = createContext<ExaminationCreationFlowContextValue | null>(null);

function useBodyScrollLock(locked: boolean) {
  useEffect(() => {
    if (!locked) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, [locked]);
}

export function ExaminationCreationFlowProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [stepIndex, setStepIndex] = useState(0);
  const [sessionId, setSessionId] = useState<string | undefined>(undefined);

  useBodyScrollLock(isModalOpen);

  const stepSlug = EXAMINATION_CREATION_STEP_SLUGS[stepIndex] ?? EXAMINATION_CREATION_STEP_SLUGS[0];

  const openCreation = useCallback((options?: { sessionId?: string; stepIndex?: number }) => {
    setStepIndex(options?.stepIndex ?? 0);
    setSessionId(options?.sessionId?.trim() || undefined);
    setIsModalOpen(true);
  }, []);

  const closeCreation = useCallback(() => {
    setIsModalOpen(false);
    setStepIndex(0);
    setSessionId(undefined);
  }, []);

  const goToStep = useCallback((index: number) => {
    const next = Math.min(Math.max(0, index), EXAMINATION_CREATION_STEP_SLUGS.length - 1);
    setStepIndex(next);
  }, []);

  const goBack = useCallback(() => {
    setStepIndex((current) => (current <= 0 ? current : current - 1));
  }, []);

  const advanceFromHref = useCallback(
    (continueHref: string | undefined) => {
      const next = examinationStepIndexFromHref(continueHref);
      if (next === null) return;
      goToStep(next);
    },
    [goToStep],
  );

  useEffect(() => {
    const mode = searchParams.get("mode");
    if (mode !== "new" || isModalOpen) return;
    if (!pathname.includes("/examinations/examination-configuration")) return;

    openCreation({ stepIndex: 0 });
    router.replace("/college-admin/examinations/examination-dashboard", { scroll: false });
  }, [isModalOpen, openCreation, pathname, router, searchParams]);

  const value = useMemo(
    () => ({
      isModalOpen,
      stepIndex,
      stepSlug,
      sessionId,
      openCreation,
      closeCreation,
      setSessionId,
      goToStep,
      goBack,
      advanceFromHref,
    }),
    [
      advanceFromHref,
      closeCreation,
      goBack,
      goToStep,
      isModalOpen,
      openCreation,
      sessionId,
      stepIndex,
      stepSlug,
    ],
  );

  return (
    <ExaminationCreationFlowContext.Provider value={value}>{children}</ExaminationCreationFlowContext.Provider>
  );
}

export function useExaminationCreationFlow() {
  const ctx = useContext(ExaminationCreationFlowContext);
  if (!ctx) {
    throw new Error("useExaminationCreationFlow must be used within ExaminationCreationFlowProvider");
  }
  return ctx;
}

export function useExaminationCreationFlowOptional() {
  return useContext(ExaminationCreationFlowContext);
}

export function useExaminationCreationWorkflowVisible() {
  return useExaminationCreationFlowOptional()?.isModalOpen ?? false;
}