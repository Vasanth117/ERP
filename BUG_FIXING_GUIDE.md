# BUG_FIXING_GUIDE.md

## Simple Universal Guide for Finding, Fixing and Verifying Bugs

Use this guide whenever you investigate or fix a bug in any software project.

**Important:** Do not change code immediately. First understand the problem, reproduce it, find the root cause and verify the fix. Do not assume the cause from the error message alone.

---

## 1. Understand the bug

Before changing code, identify:

- What is not working?
- What did the user expect to happen?
- What actually happened?
- Which page, module, API, service or component is affected?
- When did the issue start?
- Does it happen every time or only sometimes?
- Which users, environments or data are affected?
- What steps are needed to reproduce it?

Check the bug report, screenshots, error messages, logs and relevant user steps. If important information is missing, ask for it instead of guessing.

## 2. Reproduce the issue

- Inspect the relevant code and existing project structure.
- Follow the reported steps in a safe development or test environment.
- Use the same kind of input, account permissions and conditions where possible.
- Check browser console, network requests, server logs and database errors as relevant.
- Identify whether the issue is in the frontend, backend, database, configuration or an external service.
- Record the exact steps and result.

If the issue cannot be reproduced, investigate the available evidence and clearly report what is still unknown. Do not claim the bug is fixed without verification.

## 3. Find the root cause

Trace the affected functionality through the relevant code:

- Identify the entry point and execution flow.
- Check related components, routes, controllers, schemas, services and repositories.
- Inspect database queries, stored data and indexes when relevant.
- Check validation, permissions, state changes and error handling.
- Review recent code changes or configuration changes if available.
- Check dependencies and external service responses where relevant.

Determine the actual root cause, not just the visible symptom. Explain why the bug happens and which conditions trigger it.

## 4. Plan the fix

Before editing code:

- State the confirmed or most likely root cause.
- Identify the exact files and functions that need changes.
- Describe the proposed fix.
- Check whether the fix could affect other features.
- Identify required tests and regression checks.
- Consider data changes, migrations or configuration changes if needed.

Prefer the smallest safe fix. Do not rewrite working code or make unrelated changes. If the cause is uncertain, explain the uncertainty before proceeding.

## 5. Implement the fix

- Follow the existing project conventions.
- Fix the root cause rather than hiding the error.
- Handle invalid input and failure cases correctly.
- Preserve existing functionality and API behaviour unless a change is required.
- Do not hardcode temporary values or add unnecessary dependencies.
- Do not remove validation, permissions or security checks to make the error disappear.
- Do not expose secrets or sensitive information in logs.
- Keep the code readable and maintainable.

## 6. Verify the fix

After implementation, verify all relevant points:

- The original reproduction steps now work.
- The expected result is produced.
- The previous incorrect behaviour no longer occurs.
- Valid inputs still work.
- Invalid and missing inputs are handled correctly.
- Boundary values and empty data are handled correctly.
- Loading, success and error states work where applicable.
- Permissions and unauthorized access are still enforced.
- Database records are correct and no unintended data is changed.
- Related APIs, modules and integrations still work.
- The issue does not reappear after refresh, retry or repeated execution, where relevant.

Use the appropriate browser, API client, logs, database inspection and test tools for the project.

## 7. Run tests and regression checks

- Add a test that reproduces the bug where practical.
- Run the relevant unit tests.
- Run integration or API tests for affected flows.
- Run end-to-end tests for important user journeys where available.
- Run security tests if access control, input handling or sensitive data is involved.
- Run related existing tests to detect regressions.
- Run the project's formatter, linter, type checker or build checks as appropriate.

If a test cannot be run, state why. Never say a test passed unless it was actually executed and passed.

## 8. Review the changes

Before completing the task:

- Review the complete code diff.
- Confirm only relevant files were changed.
- Check for temporary debugging statements and test data.
- Check that no secrets or personal data were added to logs or code.
- Check that existing validation and security controls remain in place.
- Check whether documentation, configuration or migrations need updates.
- Confirm there are no new warnings or errors caused by the fix.

## 9. Report the result

Provide a short report containing:

- **Bug:** What was not working?
- **Root cause:** Why did it happen?
- **Fix:** What was changed?
- **Files changed:** Which files were modified?
- **Verification:** Which steps were tested?
- **Test results:** Which commands/tests ran and their actual results?
- **Remaining issues:** Anything not verified or still unresolved?

Do not claim the bug is completely fixed if some relevant scenario remains untested.

---

## Master Prompt

Read and follow `BUG_FIXING_GUIDE.md`.

I will describe a bug in the existing project. Your job is to investigate it carefully and fix it without breaking other functionality.

Follow this process:

1. Understand the reported behaviour and expected behaviour.
2. Inspect the relevant project files and existing implementation.
3. Reproduce the issue in a safe environment where possible.
4. Check logs, errors, network requests, database behaviour and related code as applicable.
5. Trace the execution flow and identify the root cause.
6. Explain the root cause and proposed fix before making significant changes.
7. Modify only the code necessary to fix the issue.
8. Preserve existing functionality, validation and security controls.
9. Add or update a regression test for the bug.
10. Test the original scenario, related scenarios and possible edge cases.
11. Run relevant existing tests and quality checks.
12. Review the final code changes for unintended effects.
13. Report the root cause, files changed, fix, tests run and any remaining risks.

Important:
- Do not guess the root cause.
- Do not make random code changes.
- Do not hide errors just to make the screen or API appear successful.
- Do not remove security checks or validation.
- Do not overwrite unrelated user changes.
- Do not claim success without verification.
- If the bug cannot be reproduced, explain what evidence is available and what remains uncertain.
- Ask for clarification when essential information is missing.

**Bug report:**
[Describe the issue, expected behaviour, actual behaviour and steps to reproduce.]

**Available evidence:**
[Paste error messages, logs, screenshots or API responses if available.]
