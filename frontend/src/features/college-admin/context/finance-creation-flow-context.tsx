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

export const FINANCE_CREATION_STEP_DEFS = [
  { key: "fee_structure", label: "Create fee structure" },
  { key: "assign_fees", label: "Assign fees to students" },
  { key: "fee_demands", label: "Generate fee demands" },
  { key: "monitor_payments", label: "Monitor payments" },
  { key: "reconcile", label: "Reconcile transactions" },
  { key: "reports", label: "Generate finance reports" },
] as const;

type FinanceCreationFlowContextValue = {
  isModalOpen: boolean;
  stepIndex: number;
  structureId: string | undefined;
  openCreation: (options?: { stepIndex?: number; structureId?: string }) => void;
  closeCreation: () => void;
  setStructureId: (structureId: string | undefined) => void;
  goToStep: (index: number) => void;
  goBack: () => void;
  goForward: () => void;
};

const FinanceCreationFlowContext = createContext<FinanceCreationFlowContextValue | null>(null);

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

export function FinanceCreationFlowProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [stepIndex, setStepIndex] = useState(0);
  const [structureId, setStructureId] = useState<string | undefined>(undefined);

  useBodyScrollLock(isModalOpen);

  const openCreation = useCallback((options?: { stepIndex?: number; structureId?: string }) => {
    setStepIndex(options?.stepIndex ?? 0);
    setStructureId(options?.structureId?.trim() || undefined);
    setIsModalOpen(true);
  }, []);

  const closeCreation = useCallback(() => {
    setIsModalOpen(false);
    setStepIndex(0);
    setStructureId(undefined);
  }, []);

  const goToStep = useCallback((index: number) => {
    const next = Math.min(Math.max(0, index), FINANCE_CREATION_STEP_DEFS.length - 1);
    setStepIndex(next);
  }, []);

  const goBack = useCallback(() => {
    setStepIndex((current) => (current <= 0 ? current : current - 1));
  }, []);

  const goForward = useCallback(() => {
    setStepIndex((current) =>
      current >= FINANCE_CREATION_STEP_DEFS.length - 1 ? current : current + 1,
    );
  }, []);

  useEffect(() => {
    const create = searchParams.get("create");
    if (create !== "1" || isModalOpen) return;
    if (!pathname.includes("/college-admin/finance/")) return;

    openCreation({ stepIndex: 0 });
    const params = new URLSearchParams(searchParams.toString());
    params.delete("create");
    const qs = params.toString();
    router.replace(qs ? `${pathname}?${qs}` : pathname, { scroll: false });
  }, [isModalOpen, openCreation, pathname, router, searchParams]);

  const value = useMemo(
    () => ({
      isModalOpen,
      stepIndex,
      structureId,
      openCreation,
      closeCreation,
      setStructureId,
      goToStep,
      goBack,
      goForward,
    }),
    [
      closeCreation,
      goBack,
      goForward,
      goToStep,
      isModalOpen,
      openCreation,
      stepIndex,
      structureId,
    ],
  );

  return <FinanceCreationFlowContext.Provider value={value}>{children}</FinanceCreationFlowContext.Provider>;
}

export function useFinanceCreationFlow() {
  const ctx = useContext(FinanceCreationFlowContext);
  if (!ctx) {
    throw new Error("useFinanceCreationFlow must be used within FinanceCreationFlowProvider");
  }
  return ctx;
}

export function useFinanceCreationFlowOptional() {
  return useContext(FinanceCreationFlowContext);
}

export function useFinanceCreationWorkflowVisible() {
  return useFinanceCreationFlowOptional()?.isModalOpen ?? false;
}