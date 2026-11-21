"use client";

import { StudentProfileOverviewScreen } from "@/features/student/components/screens/profile-overview-screen";
import { StudentProfileEditScreen } from "@/features/student/components/screens/profile-edit-screen";
import { StudentProfileAcademicScreen } from "@/features/student/components/screens/profile-academic-screen";
import {
  StudentProfileContactScreen,
  StudentProfileGuardianScreen,
  StudentProfilePersonalScreen,
} from "@/features/student/components/screens/profile-submodule-screens";

export {
  StudentProfileActivityScreen,
} from "@/features/student/components/screens/profile-activity-screen";

/** ST 01.02 — `/student/profile` */
export const StudentProfileScreen = StudentProfileOverviewScreen;

export {
  StudentProfilePersonalScreen,
  StudentProfileAcademicScreen,
  StudentProfileContactScreen,
  StudentProfileGuardianScreen,
  StudentProfileEditScreen,
};