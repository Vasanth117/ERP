"""Seed the full SVIET demo college (CLI — run from backend directory)."""

import argparse
import asyncio
import json

from app.core.database import close_mongo, connect_to_mongo
from app.core.logging import configure_logging
from app.modules.demo.seed.orchestrator import seed_demo_college


async def _run(reset: bool, students: int, faculty: int) -> None:
    configure_logging()
    await connect_to_mongo()
    try:
        summary = await seed_demo_college(student_count=students, faculty_count=faculty, reset=reset)
        print(json.dumps(summary, indent=2))
        print()
        print("--- Demo college ready ---")
        print(f"College code: {summary['tenant_code']}")
        print(f"Admin login:  {summary['admin_email']} / {summary['default_password']}")
        print("All demo accounts use the same password.")
        print("Client users cannot modify data (read-only guard).")
        print("-------------------------")
    finally:
        await close_mongo()


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the SVIET showcase demo college")
    parser.add_argument("--reset", action="store_true", help="Purge and rebuild the demo tenant")
    parser.add_argument("--students", type=int, default=180)
    parser.add_argument("--faculty", type=int, default=36)
    args = parser.parse_args()
    asyncio.run(_run(args.reset, args.students, args.faculty))


if __name__ == "__main__":
    main()