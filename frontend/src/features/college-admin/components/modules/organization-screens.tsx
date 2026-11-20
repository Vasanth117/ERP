"use client";

import Link from "next/link";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  createDepartment,
  createOrganizationUnit,
  fetchDepartment,
  fetchDepartmentHistory,
  fetchDepartments,
  fetchOrganizationUnits,
  updateDepartment,
} from "@/features/college-admin/api/organization";
import { AllDepartmentsListDashboard } from "@/features/college-admin/components/organization/all-departments-list-dashboard";
import { CreateEditDepartmentDashboard } from "@/features/college-admin/components/organization/create-edit-department-dashboard";
import { DepartmentDetailsDashboard } from "@/features/college-admin/components/organization/department-details-dashboard";
import { DepartmentHeadAssignmentDashboard } from "@/features/college-admin/components/organization/department-head-assignment-dashboard";
import { OrganizationalHierarchyDashboard } from "@/features/college-admin/components/organization/organizational-hierarchy-dashboard";
import { ProgrammeCourseMappingDashboard } from "@/features/college-admin/components/organization/programme-course-mapping-dashboard";
import { DepartmentFacultyAllocationDashboard } from "@/features/college-admin/components/organization/department-faculty-allocation-dashboard";
import { DepartmentStatusHistoryDashboard } from "@/features/college-admin/components/organization/department-status-history-dashboard";
import { DepartmentResourceManagementDashboard } from "@/features/college-admin/components/organization/department-resource-management-dashboard";
import { DepartmentManagementDashboard } from "@/features/college-admin/components/organization/department-management-dashboard";
import {
  QueryState,
  StatCard,
} from "@/features/college-admin/components/ui/query-state";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function OrganizationScreen({ slug }: { slug: string }) {
  switch (slug) {
    case "department-management-dashboard":
      return <DepartmentManagementDashboard />;
    case "all-departments":
      return <AllDepartmentsListDashboard />;
    case "create-department":
      return <CreateEditDepartmentDashboard />;
    case "department-details":
      return <DepartmentDetailsDashboard />;
    case "department-edit":
      return <CreateEditDepartmentDashboard />;
    case "department-head-assignment":
      return <DepartmentHeadAssignmentDashboard />;
    case "programme-course-mapping":
      return <ProgrammeCourseMappingDashboard />;
    case "department-faculty-allocation":
      return <DepartmentFacultyAllocationDashboard />;
    case "department-status-history":
      return <DepartmentStatusHistoryDashboard />;
    case "department-resource-management":
      return <DepartmentResourceManagementDashboard />;
    case "organizational-hierarchy":
      return <OrganizationalHierarchyDashboard />;
    default:
      return <DepartmentsList />;
  }
}

function DepartmentsList() {
  const q = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "departments"],
    queryFn: fetchDepartments,
  });
  return (
    <QueryState
      isLoading={q.isLoading}
      isError={q.isError}
      error={q.error}
      isEmpty={!q.data?.length}
      onRetry={() => void q.refetch()}
    >
      <ul className="divide-y rounded-xl border border-[#dce3ec] bg-white">
        {q.data?.map((dep) => (
          <li key={dep.department_id} className="flex items-center justify-between px-4 py-3 text-sm">
            <DepartmentLink
              href={`/college-admin/organization/department-details?departmentId=${dep.department_id}`}
              title={dep.name}
              subtitle={dep.department_code}
            />
            <span className="text-[#607086]">{dep.status}</span>
          </li>
        ))}
      </ul>
    </QueryState>
  );
}

function CreateDepartmentForm() {
  const qc = useQueryClient();
  const create = useMutation({
    mutationFn: createDepartment,
    onSuccess: () => {
      toast.success("Department created");
      void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.all });
    },
    onError: (e: Error) => toast.error(e.message),
  });
  return (
    <form
      className="max-w-md space-y-3 rounded-xl border border-[#dce3ec] bg-white p-6"
      onSubmit={(e) => {
        e.preventDefault();
        const fd = new FormData(e.currentTarget);
        create.mutate({
          department_code: String(fd.get("department_code")),
          name: String(fd.get("name")),
        });
      }}
    >
      <Field name="department_code" label="Department code" />
      <Field name="name" label="Name" />
      <Button type="submit" className="bg-[#245dd8]" disabled={create.isPending}>
        Create
      </Button>
    </form>
  );
}

function DepartmentDetailsPicker() {
  const [id, setId] = useState("");
  const q = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "department", id],
    queryFn: () => fetchDepartment(id),
    enabled: id.length > 5,
  });
  return (
    <DepartmentDetailPanel id={id} setId={setId} q={q} />
  );
}

function DepartmentEditPicker() {
  const [id, setId] = useState("");
  const qc = useQueryClient();
  const update = useMutation({
    mutationFn: (name: string) => updateDepartment(id, { name }),
    onSuccess: () => {
      toast.success("Department updated");
      void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.all });
    },
    onError: (e: Error) => toast.error(e.message),
  });
  return (
    <div className="space-y-3 max-w-md">
      <IdField id={id} setId={setId} label="Department ID" />
      <form
        className="rounded-xl border border-[#dce3ec] bg-white p-6"
        onSubmit={(e) => {
          e.preventDefault();
          update.mutate(String(new FormData(e.currentTarget).get("name")));
        }}
      >
        <Field name="name" label="New name" />
        <Button
          type="submit"
          className="mt-3 bg-[#245dd8]"
          disabled={!id || update.isPending}
        >
          Save
        </Button>
      </form>
    </div>
  );
}

function OrgUnitsList() {
  const q = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "org-units"],
    queryFn: fetchOrganizationUnits,
  });
  const create = useMutation({
    mutationFn: createOrganizationUnit,
    onSuccess: () => toast.success("Unit created"),
    onError: (e: Error) => toast.error(e.message),
  });
  return (
    <div className="space-y-4">
      <QueryState
        isLoading={q.isLoading}
        isError={q.isError}
        error={q.error}
        onRetry={() => void q.refetch()}
      >
        <ul className="divide-y rounded-xl border border-[#dce3ec] bg-white">
          {q.data?.map((unit) => (
            <li key={unit.unit_id} className="px-4 py-2 text-sm">
              {unit.name} <span className="text-[#607086]">({unit.unit_type})</span>
            </li>
          ))}
        </ul>
      </QueryState>
      <form
        className="max-w-md space-y-2 rounded-xl border border-dashed border-[#dce3ec] bg-white p-4"
        onSubmit={(e) => {
          e.preventDefault();
          const fd = new FormData(e.currentTarget);
          create.mutate({
            unit_code: String(fd.get("unit_code")),
            name: String(fd.get("name")),
            unit_type: String(fd.get("unit_type")),
          });
        }}
      >
        <p className="text-xs font-semibold text-[#172b45]">Quick add unit</p>
        <Field name="unit_code" label="Unit code" />
        <Field name="name" label="Name" />
        <Field name="unit_type" label="Type (school/faculty/division)" />
        <Button type="submit" size="sm" disabled={create.isPending}>
          Add
        </Button>
      </form>
    </div>
  );
}

function DepartmentDetailPanel({
  id,
  setId,
  q,
}: {
  id: string;
  setId: (v: string) => void;
  q: ReturnType<typeof useQuery>;
}) {
  const history = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "dept-history", id],
    queryFn: () => fetchDepartmentHistory(id),
    enabled: id.length > 5,
  });
  return (
    <div className="space-y-4">
      <IdField id={id} setId={setId} label="Department ID" />
      <QueryState
        isLoading={Boolean(id) && q.isLoading}
        isError={q.isError}
        error={q.error as Error}
      >
        {q.data ? (
          <dl className="grid gap-2 sm:grid-cols-2 text-sm">
            <Info label="Code" value={(q.data as { department_code: string }).department_code} />
            <Info label="Name" value={(q.data as { name: string }).name} />
            <Info label="Status" value={(q.data as { status: string }).status} />
          </dl>
        ) : null}
      </QueryState>
      {history.data ? (
        <ul className="text-xs text-[#607086]">
          {(history.data as unknown[]).slice(0, 5).map((_, i) => (
            <li key={i}>History event #{i + 1}</li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}

function DepartmentLink({
  href,
  title,
  subtitle,
}: {
  href: string;
  title: string;
  subtitle: string;
}) {
  return (
    <Link href={href} className="font-medium text-[#245dd8]">
      {title}
      <span className="block text-xs text-[#607086]">{subtitle}</span>
    </Link>
  );
}

function IdField({
  id,
  setId,
  label,
}: {
  id: string;
  setId: (v: string) => void;
  label: string;
}) {
  return (
    <div className="space-y-1 max-w-md">
      <Label htmlFor="recordId">{label}</Label>
      <Input
        id="recordId"
        value={id}
        onChange={(e) => setId(e.target.value)}
        className="border-[#dce3ec]"
      />
    </div>
  );
}

function Field({ name, label }: { name: string; label: string }) {
  return (
    <div className="space-y-1">
      <Label htmlFor={name}>{label}</Label>
      <Input id={name} name={name} className="border-[#dce3ec]" />
    </div>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-[#dce3ec] bg-white p-3">
      <dt className="text-[11px] font-semibold uppercase text-[#8a98aa]">{label}</dt>
      <dd className="text-[#172b45]">{value}</dd>
    </div>
  );
}