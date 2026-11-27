"""Student curriculum and course registration API schemas."""

from datetime import datetime, time
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.modules.academics.curriculum_models import SyllabusUnit, TeachingMaterialRef
from app.modules.students.registration_enums import (
    CourseRegistrationStatus,
    CourseRegistrationType,
    RegistrationRequestStatus,
)


class EnrolledCourseItemRead(BaseModel):
    course_id: str
    course_code: str
    name: str
    section_code: str | None = None
    credit_units: float
    academic_year_label: str
    semester_label: str
    source: str


class SubjectItemRead(BaseModel):
    subject_id: str
    subject_code: str
    name: str
    description: str | None = None
    credit_units: float = 0
    sequence_order: int = 1


class CurriculumRead(BaseModel):
    programme_code: str
    academic_year_label: str
    semester_label: str
    version: str | None = None
    summary: str | None = None
    academic_regulations: list[str] = Field(default_factory=list)
    locked: bool = True


class CurriculumOverviewKpisRead(BaseModel):
    total_credits: float
    total_semesters: int
    total_credits_semester_hint: str | None = None
    core_subjects: int
    electives: int
    elective_credits: float
    elective_credits_hint: str | None = None
    labs: int


class CurriculumOverviewSemesterRowRead(BaseModel):
    semester_number: int
    label: str
    subject_count: int
    credits: float
    status_code: str
    status_label: str
    status_tone: str


class CurriculumOverviewRead(BaseModel):
    page_title: str = "Curriculum Overview"
    programme_headline: str
    programme_code: str
    regulation_label: str | None = None
    kpis: CurriculumOverviewKpisRead
    semesters: list[CurriculumOverviewSemesterRowRead]
    semesters_footer_label: str


class CurriculumSemesterTabRead(BaseModel):
    semester_number: int
    tab_label: str


class CurriculumSemesterCourseRowRead(BaseModel):
    course_id: str
    course_code: str
    course_name: str
    type_label: str
    ltp_label: str
    credits: float
    status_code: str
    status_label: str
    status_tone: str
    syllabus_href: str


class CurriculumSemesterCreditCategoryRead(BaseModel):
    category_key: str
    category_label: str
    credits: float
    share_pct: float | None = None


class CurriculumSubjectFilterOptionRead(BaseModel):
    value: str
    label: str


class CurriculumSubjectListRowRead(BaseModel):
    course_id: str
    course_code: str
    course_name: str
    category_label: str
    ltp_label: str
    credits: float
    status_code: str
    status_label: str
    status_tone: str
    semester_number: int | None = None


class CurriculumSubjectListRead(BaseModel):
    page_title: str = "Subject list"
    page_subtitle: str = "Filter by semester, category or completion"
    filter_semester: int | None = None
    filter_category: str = "all"
    filter_status: str = "all"
    search_query: str | None = None
    semester_options: list[CurriculumSubjectFilterOptionRead]
    category_options: list[CurriculumSubjectFilterOptionRead]
    status_options: list[CurriculumSubjectFilterOptionRead]
    table_headers: list[str] = Field(
        default_factory=lambda: ["Code", "Subject", "Category", "L-T-P", "Credits", "Status"],
    )
    subjects: list[CurriculumSubjectListRowRead]
    footer_label: str
    total_matching: int


class CurriculumSubjectAssessmentRead(BaseModel):
    label: str
    marks_label: str
    kind: str = "assessment"


class CurriculumSubjectResourceRead(BaseModel):
    title: str
    subtitle: str | None = None
    kind: str = "document"


class CurriculumCreditComponentRowRead(BaseModel):
    component_label: str
    hours_per_week: float
    credits: float
    assessed_by: str
    is_total: bool = False


class CurriculumSubjectCreditDetailsRead(BaseModel):
    page_title: str = "Subject credit details"
    page_subtitle: str = "How credits are allocated"
    panel_title: str = "Credits"
    table_headers: list[str] = Field(
        default_factory=lambda: ["Component", "Hours per week", "Credits", "Assessed by"],
    )
    rows: list[CurriculumCreditComponentRowRead]
    footer_label: str


class CurriculumSubjectDetailRead(BaseModel):
    page_title: str = "Subject Details"
    headline: str
    course_code: str
    course_name: str
    code: str
    category_label: str
    credits: float
    ltp_label: str
    faculty_label: str
    regulation_label: str | None = None
    objectives: list[str] = Field(default_factory=list)
    assessments: list[CurriculumSubjectAssessmentRead] = Field(default_factory=list)
    resources: list[CurriculumSubjectResourceRead] = Field(default_factory=list)
    syllabus_href: str
    credit_details: CurriculumSubjectCreditDetailsRead


class CurriculumSyllabusTopicRead(BaseModel):
    title: str
    hours: float


class CurriculumSyllabusUnitRowRead(BaseModel):
    unit_no: int
    title: str
    planned_hours: float
    topic_count: int
    progress_code: str
    progress_label: str
    progress_tone: str


class CurriculumSyllabusResourceRead(BaseModel):
    title: str
    subtitle: str | None = None
    url: str | None = None
    kind: str = "document"


class CurriculumSyllabusUnitDetailRead(BaseModel):
    page_title: str = "Unit-wise Syllabus Details"
    unit_no: int
    headline: str
    planned_hours: float
    weightage_pct: float | None = None
    co_mapping_label: str | None = None
    topics: list[CurriculumSyllabusTopicRead] = Field(default_factory=list)
    learning_resources: list[CurriculumSyllabusResourceRead] = Field(default_factory=list)
    open_materials_url: str | None = None
    faculty_label: str | None = None


class CurriculumSyllabusPageRead(BaseModel):
    page_title: str = "Subject Syllabus"
    headline: str
    course_code: str
    course_name: str
    units_panel_title: str = "Units"
    table_headers: list[str] = Field(
        default_factory=lambda: ["Unit", "Title", "Hours", "Topics", "Progress"],
    )
    units: list[CurriculumSyllabusUnitRowRead] = Field(default_factory=list)
    units_footer_label: str
    selected_unit_no: int | None = None
    unit_detail: CurriculumSyllabusUnitDetailRead | None = None


class CurriculumCategoryCourseRowRead(BaseModel):
    course_code: str
    course_name: str
    credits: float


class CurriculumCategoryPanelRead(BaseModel):
    panel_title: str
    table_headers: list[str] = Field(
        default_factory=lambda: ["Code", "Subject", "Credits"],
    )
    rows: list[CurriculumCategoryCourseRowRead] = Field(default_factory=list)
    footer_label: str


class CurriculumElectiveCatalogueRowRead(BaseModel):
    course_code: str
    course_name: str
    group_label: str
    credits: float
    offered_in_label: str


class CurriculumHistoryRowRead(BaseModel):
    version_label: str
    regulation_label: str
    effective_from_label: str
    change_summary: str
    applies_code: str
    applies_label: str
    applies_tone: str


class CurriculumHistoryPageRead(BaseModel):
    page_title: str = "Curriculum History"
    page_subtitle: str = "Versions of your curriculum"
    panel_title: str = "Versions"
    table_headers: list[str] = Field(
        default_factory=lambda: ["Version", "Regulation", "Effective from", "Change", "Applies to you"],
    )
    rows: list[CurriculumHistoryRowRead] = Field(default_factory=list)
    footer_label: str


class CurriculumCategoriesElectivesPageRead(BaseModel):
    categories_page_title: str = "Theory and Practical Subject Categories"
    categories_page_subtitle: str = "Subjects by type"
    theory_panel: CurriculumCategoryPanelRead
    practical_panel: CurriculumCategoryPanelRead
    elective_page_title: str = "Elective Subject Catalogue"
    elective_page_subtitle: str = "Electives offered for your programme"
    elective_table_headers: list[str] = Field(
        default_factory=lambda: ["Code", "Subject", "Group", "Credits", "Offered in"],
    )
    elective_rows: list[CurriculumElectiveCatalogueRowRead] = Field(default_factory=list)
    elective_footer_label: str
    registration_href: str = "/student/registration"


class CurriculumSemesterPageRead(BaseModel):
    page_title: str = "Semester-wise curriculum"
    programme_headline: str
    programme_code: str
    selected_semester: int
    total_semesters: int
    semester_tabs: list[CurriculumSemesterTabRead]
    courses_panel_title: str
    courses_panel_meta: str
    table_headers: list[str] = Field(
        default_factory=lambda: ["Course", "Type", "L-T-P", "Credits", "Status"],
    )
    courses: list[CurriculumSemesterCourseRowRead]
    credit_categories: list[CurriculumSemesterCreditCategoryRead]
    semester_status_code: str
    semester_status_label: str
    semester_status_tone: str
    courses_footer_label: str


class SyllabusRevisionRead(BaseModel):
    version: str
    effective_at: datetime
    summary: str | None = None


class SyllabusDetailRead(BaseModel):
    course_id: str
    subject_id: str | None = None
    academic_year_label: str
    semester_label: str
    units: list[SyllabusUnit]
    objectives: list[str]
    teaching_materials: list[TeachingMaterialRef]
    revision_history: list[SyllabusRevisionRead]
    locked: bool = True


class LearningOutcomesDetailRead(BaseModel):
    course_id: str
    academic_year_label: str
    semester_label: str
    outcomes: list[str]
    locked: bool = True


class PrerequisiteRead(BaseModel):
    course_id: str
    course_code: str
    prerequisite_course_ids: list[str]
    corequisite_course_ids: list[str]
    min_cgpa: float | None = None
    notes: str | None = None


class FacultyInfoRead(BaseModel):
    faculty_user_id: str
    display_name: str
    section: str
    subject_code: str | None = None


class CourseInfoRead(BaseModel):
    course_id: str
    course_code: str
    name: str
    description: str | None = None
    credit_units: float
    faculty: list[FacultyInfoRead] = Field(default_factory=list)


class SemesterSubjectsRead(BaseModel):
    academic_year_label: str
    semester_label: str
    subjects: list[SubjectItemRead]


class AvailableCourseRead(BaseModel):
    course_id: str
    course_code: str
    name: str
    credit_units: float
    registration_type: CourseRegistrationType
    is_open_for_registration: bool
    prerequisites_met: bool | None = None
    max_capacity: int | None = None


class ElectiveGroupRead(BaseModel):
    id: str
    group_code: str
    title: str
    description: str | None = None
    min_selections: int
    max_selections: int
    min_credits: float
    max_credits: float


class ElectiveOptionRead(BaseModel):
    course_id: str
    course_code: str
    course_name: str
    credit_units: float
    seats_available: int | None = None
    eligible: bool = True


class RegistrationEligibilityRead(BaseModel):
    eligible: bool
    reasons: list[str] = Field(default_factory=list)
    min_credits: float | None = None
    max_credits: float | None = None
    registration_open_at: datetime | None = None
    registration_close_at: datetime | None = None
    modification_deadline: datetime | None = None
    window_open: bool = False


class RegistrationSelectionInput(BaseModel):
    course_id: str
    course_code: str
    section_code: str | None = None
    registration_type: CourseRegistrationType = CourseRegistrationType.ELECTIVE
    elective_group_id: str | None = None

    model_config = {"extra": "forbid"}


class RegistrationValidationRead(BaseModel):
    valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    total_credits: float = 0
    timetable_conflicts: list[str] = Field(default_factory=list)


class RegistrationSubmitRead(BaseModel):
    request_id: str
    status: RegistrationRequestStatus
    selections: list[RegistrationSelectionInput]
    submitted_at: datetime | None = None


class CourseRegistrationRead(BaseModel):
    id: str
    course_id: str
    course_code: str
    section_code: str | None = None
    registration_type: CourseRegistrationType
    credit_units: float
    status: CourseRegistrationStatus
    academic_year_label: str
    semester_label: str


class RegistrationRequestRead(BaseModel):
    id: str
    status: RegistrationRequestStatus
    academic_year_label: str
    semester_label: str
    selections: list[RegistrationSelectionInput]
    reviewer_note: str | None = None
    submitted_at: datetime | None = None
    resolved_at: datetime | None = None


class RegistrationHistoryRead(BaseModel):
    id: str
    course_code: str
    action: str
    previous_status: str | None = None
    new_status: str | None = None
    occurred_at: datetime


class RegistrationOverviewStepRead(BaseModel):
    key: str
    label: str
    state: str = Field(description="completed | current | upcoming")


class RegistrationOverviewKpisRead(BaseModel):
    window_label: str
    window_hint: str | None = None
    credit_limit_label: str
    selected_count: str
    status_label: str


class RegistrationOverviewCourseRowRead(BaseModel):
    course_code: str
    course_name: str
    category_label: str
    credit_units: float
    prerequisite_label: str
    seats_label: str


class RegistrationPrerequisiteCheckRead(BaseModel):
    key: str
    title: str
    detail: str
    status_label: str
    status_tone: str


class RegistrationClosedPanelRead(BaseModel):
    page_title: str
    page_subtitle: str
    banner_title: str
    banner_body: str
    raise_request_href: str
    window_opened_label: str
    window_closed_label: str
    student_status_label: str
    show_late_registration_banner: bool = False
    show_raise_request_action: bool = False


class RegistrationOverviewPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    registration_semester_number: int | None = None
    window_open: bool = False
    show_start_registration: bool = False
    start_registration_href: str = "/student/registration/courses"
    contact_department_href: str = "/student/academics/programme-department"
    kpis: RegistrationOverviewKpisRead
    steps: list[RegistrationOverviewStepRead]
    active_step_index: int = 0
    available_courses: list[RegistrationOverviewCourseRowRead]
    courses_footer_label: str
    prerequisite_checks: list[RegistrationPrerequisiteCheckRead]
    closed_panel: RegistrationClosedPanelRead | None = None


class RegistrationFilterOptionRead(BaseModel):
    value: str
    label: str


class RegistrationCourseListRowRead(BaseModel):
    course_id: str
    course_code: str
    course_name: str
    category_label: str
    credit_units: float
    prerequisite_label: str
    seats_label: str
    is_selectable: bool = True


class RegistrationCoursesPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    go_to_selection_href: str
    semester_options: list[RegistrationFilterOptionRead]
    category_options: list[RegistrationFilterOptionRead]
    selected_semester: str
    selected_category: str
    search_placeholder: str
    courses: list[RegistrationCourseListRowRead]
    courses_footer_label: str
    default_course_code: str | None = None


class RegistrationCourseDetailPageRead(BaseModel):
    page_title: str
    headline: str
    course_code: str
    course_name: str
    category_label: str
    credit_units: float
    faculty_label: str
    seats_label: str
    slot_label: str
    description: str
    eligibility: list[RegistrationPrerequisiteCheckRead]
    add_to_selection_href: str
    show_add_to_selection: bool
    back_href: str


class RegistrationElectiveOptionChoiceRead(BaseModel):
    course_id: str
    course_code: str
    course_name: str
    choice_label: str
    credit_units: float
    eligible: bool = True


class RegistrationElectiveGroupSelectionRead(BaseModel):
    group_id: str
    title: str
    choose_label: str
    selected_course_id: str | None = None
    alternate_course_id: str | None = None
    primary_options: list[RegistrationElectiveOptionChoiceRead]
    alternate_options: list[RegistrationElectiveOptionChoiceRead]


class RegistrationElectiveCreditCheckRead(BaseModel):
    selected_detail: str
    allowed_range: str
    status_label: str
    status_tone: str
    min_credits: float | None = None
    max_credits: float | None = None


class RegistrationElectiveSelectionSectionRead(BaseModel):
    page_title: str
    page_subtitle: str
    steps: list[RegistrationOverviewStepRead]
    active_step_index: int
    cancel_href: str
    review_href: str
    draft_request_id: str | None = None
    groups: list[RegistrationElectiveGroupSelectionRead]
    credit_check: RegistrationElectiveCreditCheckRead


class RegistrationElectiveCatalogueRowRead(BaseModel):
    course_code: str
    course_name: str
    seats_label: str


class RegistrationElectiveCatalogueGroupRead(BaseModel):
    title: str
    courses: list[RegistrationElectiveCatalogueRowRead]
    footer_label: str


class RegistrationElectiveCatalogueSectionRead(BaseModel):
    page_title: str
    page_subtitle: str
    groups: list[RegistrationElectiveCatalogueGroupRead]


class RegistrationElectivesPageRead(BaseModel):
    selection: RegistrationElectiveSelectionSectionRead
    catalogue: RegistrationElectiveCatalogueSectionRead


class RegistrationReviewSelectedRowRead(BaseModel):
    course_id: str
    course_code: str
    course_name: str
    category_label: str
    credit_units: float
    registration_type: CourseRegistrationType
    elective_group_id: str | None = None


class RegistrationReviewTotalsRead(BaseModel):
    course_count: int
    credit_units: float
    fees_label: str


class RegistrationReviewSummarySectionRead(BaseModel):
    page_title: str
    page_subtitle: str
    steps: list[RegistrationOverviewStepRead]
    active_step_index: int
    back_href: str
    submit_enabled: bool
    selected_rows: list[RegistrationReviewSelectedRowRead]
    footer_label: str
    totals: RegistrationReviewTotalsRead
    declaration_label: str
    draft_request_id: str | None = None


class RegistrationReviewValidationCheckRead(BaseModel):
    check_key: str
    check_label: str
    course_label: str
    result_label: str
    result_tone: str


class RegistrationReviewValidationSectionRead(BaseModel):
    page_title: str
    page_subtitle: str
    steps: list[RegistrationOverviewStepRead]
    active_step_index: int
    fix_selection_href: str
    alert_title: str | None = None
    alert_body: str | None = None
    checks: list[RegistrationReviewValidationCheckRead]
    checks_footer_label: str
    is_valid: bool


class RegistrationReviewConfirmationDetailRead(BaseModel):
    key: str
    label: str
    value: str


class RegistrationReviewConfirmationSectionRead(BaseModel):
    page_title: str
    page_subtitle: str
    steps: list[RegistrationOverviewStepRead]
    active_step_index: int
    is_submitted: bool = False
    success_title: str
    success_body: str
    pending_title: str | None = None
    pending_body: str | None = None
    download_slip_href: str | None = None
    view_status_href: str
    details: list[RegistrationReviewConfirmationDetailRead]


class RegistrationReviewPageRead(BaseModel):
    summary: RegistrationReviewSummarySectionRead
    validation: RegistrationReviewValidationSectionRead
    confirmation: RegistrationReviewConfirmationSectionRead
    default_sub_panel: Literal["confirmation", "validation"] = "validation"


class RegistrationStatusCourseRowRead(BaseModel):
    course_code: str
    course_name: str
    status_label: str
    status_tone: str
    credit_units: float


class RegistrationApprovalStepRead(BaseModel):
    key: str
    label: str
    detail: str
    state: str
    tone: str


class RegistrationStatusSectionRead(BaseModel):
    page_title: str
    page_subtitle: str
    courses: list[RegistrationStatusCourseRowRead]
    courses_footer_label: str
    approval_steps: list[RegistrationApprovalStepRead]


class RegistrationHistorySemesterRowRead(BaseModel):
    reference_label: str
    semester_label: str
    course_count: int
    credit_units: float
    submitted_at_label: str
    status_label: str
    status_tone: str


class RegistrationHistorySectionRead(BaseModel):
    page_title: str
    page_subtitle: str
    rows: list[RegistrationHistorySemesterRowRead]
    footer_label: str


class RegistrationStatusPageRead(BaseModel):
    status: RegistrationStatusSectionRead
    history: RegistrationHistorySectionRead


class TimetableSlotCheck(BaseModel):
    course_code: str
    day_of_week: int
    start_time: time
    end_time: time
