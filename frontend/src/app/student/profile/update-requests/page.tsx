import { Suspense } from "react";

import { StudentScreen } from "@/features/student/components/student-screen";

export default function Page() {
  return (
    <Suspense fallback={null}>
      <StudentScreen slug="profile-update-requests" />
    </Suspense>
  );
}