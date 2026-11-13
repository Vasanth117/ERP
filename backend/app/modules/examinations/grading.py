"""Grading helpers using tenant policy."""

from app.modules.examinations.models import GradingPolicy


def letter_grade(percentage: float, policy: GradingPolicy) -> str:
    if policy.grade_bands:
        for band in sorted(policy.grade_bands, key=lambda b: b.get("min", 0), reverse=True):
            if percentage >= float(band.get("min", 0)):
                return str(band.get("grade", "N/A"))
    if percentage >= policy.pass_percentage:
        return "PASS"
    return "FAIL"


async def get_grading_policy(tenant_id) -> GradingPolicy:
    policy = await GradingPolicy.find_one({"tenant_id": tenant_id})
    if policy is None:
        policy = GradingPolicy(tenant_id=tenant_id, grade_bands=[{"min": 90, "grade": "O"}, {"min": 75, "grade": "A"}])
        await policy.insert()
    return policy


def weighted_percentage(marks: float, max_marks: float) -> float:
    if max_marks <= 0:
        return 0.0
    return round((marks / max_marks) * 100, 2)
