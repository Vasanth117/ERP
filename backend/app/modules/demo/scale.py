"""Volume targets for showcase demo generation."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DemoScaleProfile:
    name: str
    students: int
    faculty: int
    non_faculty_staff: int
    admission_applications: int
    library_catalog_titles: int
    generator_version: str = "2.0.0"


DEMO_SCALE_PROFILES: dict[str, DemoScaleProfile] = {
    "quick": DemoScaleProfile(
        name="quick",
        students=2_400,
        faculty=820,
        non_faculty_staff=140,
        admission_applications=500,
        library_catalog_titles=200,
    ),
    "standard": DemoScaleProfile(
        name="standard",
        students=6_000,
        faculty=550,
        non_faculty_staff=350,
        admission_applications=2_000,
        library_catalog_titles=1_000,
    ),
    "enterprise": DemoScaleProfile(
        name="enterprise",
        students=12_000,
        faculty=650,
        non_faculty_staff=400,
        admission_applications=4_000,
        library_catalog_titles=5_000,
    ),
}

DEFAULT_DEMO_SCALE_PROFILE = "enterprise"


def resolve_demo_scale(profile_name: str | None) -> DemoScaleProfile:
    key = (profile_name or DEFAULT_DEMO_SCALE_PROFILE).strip().lower()
    if key not in DEMO_SCALE_PROFILES:
        known = ", ".join(sorted(DEMO_SCALE_PROFILES))
        raise ValueError(f"Unknown demo profile {profile_name!r}. Choose one of: {known}")
    return DEMO_SCALE_PROFILES[key]