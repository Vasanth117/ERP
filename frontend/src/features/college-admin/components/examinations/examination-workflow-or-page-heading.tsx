"use client";

import {
  ExaminationCreationWorkflowHeader,
  type ExaminationCreationWorkflowHeaderProps,
} from "@/features/college-admin/components/examinations/examination-creation-workflow-header";
import { ExaminationWorkflowHeaderActions } from "@/features/college-admin/components/examinations/examination-workflow-header-actions";
import { CollegeAdminModulePageHeading } from "@/features/college-admin/components/layout/college-admin-module-page-heading";
import {
  EXAMINATION_CREATION_STEP_SLUGS,
  useExaminationCreationFlowOptional,
  useExaminationCreationWorkflowVisible,
} from "@/features/college-admin/context/examination-creation-flow-context";

type Props = Omit<ExaminationCreationWorkflowHeaderProps, "children">;

export function ExaminationWorkflowOrPageHeading(props: Props) {
  const inCreationModal = useExaminationCreationWorkflowVisible();
  const flow = useExaminationCreationFlowOptional();

  if (!inCreationModal) {
    const disabled = Boolean(props.controlsDisabled || props.busy);
    return (
      <CollegeAdminModulePageHeading
        title={props.pageTitle}
        subtitle={props.pageSubtitle}
        forceShowTitle
        actions={
          <ExaminationWorkflowHeaderActions
            headerActions={props.headerActions}
            saveDraftLabel={props.saveDraftLabel}
            continueLabel={props.continueLabel}
            onSaveDraft={props.onSaveDraft}
            onContinue={props.onContinue}
            continueEnabled={props.continueEnabled}
            disabled={disabled}
          />
        }
      />
    );
  }

  const goToStep = (href: string) => {
    const slug = href.split("?")[0]?.split("/").filter(Boolean).pop() ?? "";
    const index = EXAMINATION_CREATION_STEP_SLUGS.indexOf(
      slug as (typeof EXAMINATION_CREATION_STEP_SLUGS)[number],
    );
    if (index >= 0) flow?.goToStep(index);
  };

  return (
    <ExaminationCreationWorkflowHeader
      {...props}
      stepLinkMode="modal"
      onBack={flow?.stepIndex === 0 ? flow.closeCreation : flow?.goBack}
      onStepNavigate={goToStep}
    />
  );
}