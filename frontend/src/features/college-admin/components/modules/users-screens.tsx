"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useState } from "react";
import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  activateUser,
  assignUserRoles,
  bulkCreateUsers,
  createRole,
  createUser,
  deactivateUser,
  fetchPermissions,
  fetchRoles,
  fetchUser,
  fetchUserAccessHistory,
  fetchUsers,
  inviteUser,
  suspendUser,
  updateUser,
} from "@/features/college-admin/api/users";
import {
  QueryState,
  StatCard,
} from "@/features/college-admin/components/ui/query-state";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function UsersScreen({ slug }: { slug: string }) {
  switch (slug) {
    case "user-management-dashboard":
      return <UsersDashboard />;
    case "all-users-list":
      return <UsersList />;
    case "user-details":
      return <UserDetailsPicker />;
    case "create-new-user":
      return <CreateUserForm />;
    case "edit-user-information":
      return <EditUserPicker />;
    case "bulk-user-invitation":
      return <BulkInviteForm />;
    case "role-management-dashboard":
      return <RolesDashboard />;
    case "create-edit-role":
      return <CreateRoleForm />;
    case "permission-management":
      return <PermissionsList />;
    case "role-assignment":
      return <RoleAssignmentPicker />;
    case "user-account-activation-suspension":
      return <AccountStatusPicker />;
    case "login-account-activity":
      return <LoginActivityPicker />;
    case "user-access-history":
      return <AccessHistoryPicker />;
    default:
      return <UsersList />;
  }
}

function UsersDashboard() {
  const q = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "users-stats"],
    queryFn: () => fetchUsers(0, 1),
  });
  return (
    <QueryState
      isLoading={q.isLoading}
      isError={q.isError}
      error={q.error}
      onRetry={() => void q.refetch()}
    >
      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard label="Institution users" value={q.data?.total ?? 0} />
        <StatCard label="Listed on this page" value={q.data?.items.length ?? 0} />
        <Link
          href="/college-admin/users/all-users-list"
          className="flex items-center text-sm font-medium text-[#245dd8]"
        >
          Open all users →
        </Link>
      </div>
    </QueryState>
  );
}

function UsersList() {
  const q = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "users-list"],
    queryFn: () => fetchUsers(0, 100),
  });
  return (
    <QueryState
      isLoading={q.isLoading}
      isError={q.isError}
      error={q.error}
      isEmpty={!q.data?.items.length}
      onRetry={() => void q.refetch()}
    >
      <div className="overflow-x-auto rounded-xl border border-[#dce3ec] bg-white">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-[#eceff4] bg-[#f8fafc] text-[11px] uppercase text-[#8a98aa]">
            <tr>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Email</th>
              <th className="px-4 py-3">Role</th>
              <th className="px-4 py-3">Status</th>
            </tr>
          </thead>
          <tbody>
            {q.data?.items.map((u) => (
              <tr key={u.user_id} className="border-b border-[#eceff4]">
                <td className="px-4 py-3">
                  <Link
                    href={`/college-admin/users/user-details?userId=${u.user_id}`}
                    className="font-medium text-[#245dd8]"
                  >
                    {u.full_name}
                  </Link>
                </td>
                <td className="px-4 py-3 text-[#607086]">{u.email}</td>
                <td className="px-4 py-3">{u.role}</td>
                <td className="px-4 py-3">{u.account_status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </QueryState>
  );
}

function UserDetailsPicker() {
  const params = useSearchParams();
  const [userId, setUserId] = useState(params.get("userId") ?? "");
  const q = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "user", userId],
    queryFn: () => fetchUser(userId),
    enabled: userId.length > 10,
  });

  return (
    <div className="space-y-4">
      <UserIdField userId={userId} setUserId={setUserId} />
      <QueryState
        isLoading={Boolean(userId) && q.isLoading}
        isError={q.isError}
        error={q.error}
        isEmpty={Boolean(userId) && !q.isLoading && !q.data}
      >
        {q.data ? (
          <dl className="grid gap-3 sm:grid-cols-2">
            <Info label="Email" value={q.data.email} />
            <Info label="Role" value={q.data.role} />
            <Info label="Status" value={q.data.account_status} />
            <Info
              label="Last login"
              value={
                q.data.last_login_at
                  ? new Date(q.data.last_login_at).toLocaleString()
                  : "—"
              }
            />
          </dl>
        ) : null}
      </QueryState>
    </div>
  );
}

function CreateUserForm() {
  const qc = useQueryClient();
  const create = useMutation({
    mutationFn: createUser,
    onSuccess: () => {
      toast.success("User created");
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
          email: String(fd.get("email")),
          password: String(fd.get("password")),
          full_name: String(fd.get("full_name")),
          role: String(fd.get("role")),
        });
      }}
    >
      <Field name="full_name" label="Full name" />
      <Field name="email" label="Email" type="email" />
      <Field name="password" label="Password" type="password" />
      <Field name="role" label="Role (e.g. college_admin)" />
      <Button type="submit" className="bg-[#245dd8]" disabled={create.isPending}>
        Create user
      </Button>
    </form>
  );
}

function EditUserPicker() {
  const [userId, setUserId] = useState("");
  const qc = useQueryClient();
  const update = useMutation({
    mutationFn: (name: string) => updateUser(userId, { full_name: name }),
    onSuccess: () => {
      toast.success("User updated");
      void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.all });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  return (
    <div className="max-w-md space-y-3">
      <UserIdField userId={userId} setUserId={setUserId} />
      <form
        className="rounded-xl border border-[#dce3ec] bg-white p-6"
        onSubmit={(e) => {
          e.preventDefault();
          const fd = new FormData(e.currentTarget);
          update.mutate(String(fd.get("full_name")));
        }}
      >
        <Field name="full_name" label="New full name" />
        <Button
          type="submit"
          className="mt-3 bg-[#245dd8]"
          disabled={!userId || update.isPending}
        >
          Save
        </Button>
      </form>
    </div>
  );
}

function BulkInviteForm() {
  const invite = useMutation({
    mutationFn: inviteUser,
    onSuccess: () => toast.success("Invitation sent"),
    onError: (e: Error) => toast.error(e.message),
  });
  const bulk = useMutation({
    mutationFn: bulkCreateUsers,
    onSuccess: (rows) => toast.success(`Created ${rows.length} users`),
    onError: (e: Error) => toast.error(e.message),
  });

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <form
        className="space-y-3 rounded-xl border border-[#dce3ec] bg-white p-6"
        onSubmit={(e) => {
          e.preventDefault();
          const fd = new FormData(e.currentTarget);
          invite.mutate({
            email: String(fd.get("email")),
            full_name: String(fd.get("full_name")),
            role: String(fd.get("role")),
          });
        }}
      >
        <p className="text-sm font-semibold text-[#172b45]">Invite user</p>
        <Field name="full_name" label="Full name" />
        <Field name="email" label="Email" />
        <Field name="role" label="Role" />
        <Button type="submit" className="bg-[#245dd8]" disabled={invite.isPending}>
          Send invite
        </Button>
      </form>
      <form
        className="space-y-3 rounded-xl border border-[#dce3ec] bg-white p-6"
        onSubmit={(e) => {
          e.preventDefault();
          const fd = new FormData(e.currentTarget);
          bulk.mutate({
            users: [
              {
                email: String(fd.get("email")),
                password: String(fd.get("password")),
                full_name: String(fd.get("full_name")),
                role: String(fd.get("role")),
              },
            ],
          });
        }}
      >
        <p className="text-sm font-semibold text-[#172b45]">Bulk create (1 row)</p>
        <Field name="full_name" label="Full name" />
        <Field name="email" label="Email" />
        <Field name="password" label="Password" />
        <Field name="role" label="Role" />
        <Button type="submit" className="bg-[#245dd8]" disabled={bulk.isPending}>
          Bulk create
        </Button>
      </form>
    </div>
  );
}

function RolesDashboard() {
  const q = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "roles"],
    queryFn: fetchRoles,
  });
  return (
    <QueryState
      isLoading={q.isLoading}
      isError={q.isError}
      error={q.error}
      onRetry={() => void q.refetch()}
    >
      <StatCard label="Custom roles" value={q.data?.length ?? 0} />
    </QueryState>
  );
}

function CreateRoleForm() {
  const create = useMutation({
    mutationFn: createRole,
    onSuccess: () => toast.success("Role created"),
    onError: (e: Error) => toast.error(e.message),
  });
  return (
    <form
      className="max-w-md space-y-3 rounded-xl border border-[#dce3ec] bg-white p-6"
      onSubmit={(e) => {
        e.preventDefault();
        const fd = new FormData(e.currentTarget);
        const perms = String(fd.get("permissions") || "")
          .split(",")
          .map((p) => p.trim())
          .filter(Boolean);
        create.mutate({
          role_code: String(fd.get("role_code")),
          name: String(fd.get("name")),
          description: String(fd.get("description") || ""),
          permissions: perms,
        });
      }}
    >
      <Field name="role_code" label="Role code" />
      <Field name="name" label="Name" />
      <Field name="description" label="Description" />
      <Field name="permissions" label="Permissions (comma-separated)" />
      <Button type="submit" className="bg-[#245dd8]" disabled={create.isPending}>
        Create role
      </Button>
    </form>
  );
}

function PermissionsList() {
  const q = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "permissions"],
    queryFn: fetchPermissions,
  });
  return (
    <QueryState
      isLoading={q.isLoading}
      isError={q.isError}
      error={q.error}
      onRetry={() => void q.refetch()}
    >
      <ul className="max-h-[480px] overflow-y-auto rounded-xl border border-[#dce3ec] bg-white divide-y">
        {q.data?.map((p) => (
          <li key={p.permission_code} className="px-4 py-2 text-sm">
            <span className="font-medium text-[#172b45]">{p.permission_code}</span>
            <span className="text-[#607086]"> — {p.description ?? p.category}</span>
          </li>
        ))}
      </ul>
    </QueryState>
  );
}

function RoleAssignmentPicker() {
  const [userId, setUserId] = useState("");
  const assign = useMutation({
    mutationFn: (role: string) => assignUserRoles(userId, { primary_role: role }),
    onSuccess: () => toast.success("Roles assigned"),
    onError: (e: Error) => toast.error(e.message),
  });
  return (
    <div className="max-w-md space-y-3">
      <UserIdField userId={userId} setUserId={setUserId} />
      <form
        className="rounded-xl border border-[#dce3ec] bg-white p-6"
        onSubmit={(e) => {
          e.preventDefault();
          assign.mutate(String(new FormData(e.currentTarget).get("role")));
        }}
      >
        <Field name="role" label="Primary role" />
        <Button
          type="submit"
          className="mt-3 bg-[#245dd8]"
          disabled={!userId || assign.isPending}
        >
          Assign
        </Button>
      </form>
    </div>
  );
}

function AccountStatusPicker() {
  const [userId, setUserId] = useState("");
  const qc = useQueryClient();
  const run = (fn: () => Promise<unknown>) => () => {
    void fn().then(() => {
      toast.success("Updated");
      void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.all });
    });
  };
  return (
    <div className="space-y-3">
      <UserIdField userId={userId} setUserId={setUserId} />
      <div className="flex flex-wrap gap-2">
        <Button
          type="button"
          variant="outline"
          disabled={!userId}
          onClick={run(() => activateUser(userId))}
        >
          Activate
        </Button>
        <Button
          type="button"
          variant="outline"
          disabled={!userId}
          onClick={run(() => suspendUser(userId, "Manual"))}
        >
          Suspend
        </Button>
        <Button
          type="button"
          variant="outline"
          disabled={!userId}
          onClick={run(() => deactivateUser(userId))}
        >
          Deactivate
        </Button>
      </div>
    </div>
  );
}

function LoginActivityPicker() {
  return (
    <p className="text-sm text-[#607086]">
      Select a user on{" "}
      <Link href="/college-admin/users/user-access-history" className="text-[#245dd8]">
        User access history
      </Link>{" "}
      to view login-related events from institution access history.
    </p>
  );
}

function AccessHistoryPicker() {
  const [userId, setUserId] = useState("");
  const q = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "access-history", userId],
    queryFn: () => fetchUserAccessHistory(userId),
    enabled: userId.length > 10,
  });
  return (
    <div className="space-y-4">
      <UserIdField userId={userId} setUserId={setUserId} />
      <QueryState
        isLoading={Boolean(userId) && q.isLoading}
        isError={q.isError}
        error={q.error}
        isEmpty={Boolean(userId) && !q.data?.length}
      >
        <ul className="divide-y rounded-xl border border-[#dce3ec] bg-white">
          {q.data?.map((row, i) => (
            <li key={i} className="px-4 py-2 text-sm text-[#607086]">
              {row.event_type} · {new Date(row.occurred_at).toLocaleString()}
            </li>
          ))}
        </ul>
      </QueryState>
    </div>
  );
}

function UserIdField({
  userId,
  setUserId,
}: {
  userId: string;
  setUserId: (v: string) => void;
}) {
  return (
    <div className="max-w-md space-y-1">
      <Label htmlFor="userId">User ID</Label>
      <Input
        id="userId"
        value={userId}
        onChange={(e) => setUserId(e.target.value)}
        placeholder="Paste user_id from list"
        className="border-[#dce3ec]"
      />
    </div>
  );
}

function Field({
  name,
  label,
  type = "text",
}: {
  name: string;
  label: string;
  type?: string;
}) {
  return (
    <div className="space-y-1">
      <Label htmlFor={name}>{label}</Label>
      <Input id={name} name={name} type={type} className="border-[#dce3ec]" />
    </div>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-[#dce3ec] bg-white p-3">
      <dt className="text-[11px] font-semibold uppercase text-[#8a98aa]">{label}</dt>
      <dd className="text-sm text-[#172b45]">{value}</dd>
    </div>
  );
}