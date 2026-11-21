# ENGINEERING_GUIDE.md

## Simple Universal Base Guide for AI-Assisted Software Development

Use this guide as the starting point for any software project, including web applications, mobile applications, APIs and backend systems.

**Important:** First understand the actual project and its requirements. Do not assume a language, framework, database, architecture or folder structure. Use only what the project needs.

---

## 1. Understand the project first

Before writing or changing code:

- Inspect the repository structure, README, dependencies and configuration.
- Identify the languages, frameworks, application entry points and existing architecture.
- Understand the frontend, backend, database, APIs and external services, if present.
- Check existing modules, components, services, repositories, schemas and tests.
- Trace a similar existing feature from request to database and response.
- Check current git changes and do not overwrite the user's work.
- Never expose secrets or assume files and functions exist without checking.

Summarize what the project does, how it is structured, what can be reused and what needs to change.

## 2. Understand the requirement

For every feature, identify:

- What needs to be built or fixed.
- Who will use it.
- Expected inputs and outputs.
- Main workflow and business rules.
- Required data and related modules.
- Permissions and security requirements.
- Error cases and edge cases.
- Acceptance criteria: how we know it works.

Clearly separate confirmed requirements from assumptions. Ask a question only if missing information blocks a safe implementation.

## 3. Keep code organized

Separate responsibilities clearly, using the structure that fits the project.

Typical responsibilities:

- **Routes / Controllers:** receive requests and return responses.
- **Schemas / DTOs:** validate input and format output.
- **Services / Use cases:** implement and coordinate business logic.
- **Repositories / Data access:** communicate with the database.
- **Models / Entities:** represent application or persisted data.
- **Components:** reusable UI or application building blocks.
- **Core / Infrastructure:** configuration, database connections, security, logging and external integrations.

Do not put all logic in one file. Avoid unnecessary files, classes and abstractions. Reuse good existing project conventions.

## 4. Database and schema design

Before creating or changing database structures:

- Understand the data and how the application will read and update it.
- Define fields, data types, required values, defaults and validation.
- Define relationships, ownership and unique constraints.
- Decide whether related data should be embedded or referenced when using MongoDB.
- Use indexes that support actual queries, filters and sorting.
- Avoid unnecessary indexes because they increase storage and write cost.
- Use migrations or controlled schema changes.
- Handle timestamps, money, deletion and concurrent updates consistently.
- Never accept raw database queries or operators directly from users.

For MongoDB, verify important indexes and queries with `explain()` where possible. For SQL, use constraints, transactions and query plans appropriately.

## 5. API and service design

For every API or service operation, define:

- Method and endpoint or operation name.
- Purpose and expected behaviour.
- Authentication and permission requirements.
- Input and output schemas.
- Validation rules.
- Success and error responses.
- Pagination, filtering and sorting, if needed.
- Retry and duplicate-request behaviour, if relevant.

Use consistent API conventions. Do not expose database internals, passwords, tokens or unnecessary private data. Keep controllers thin and business logic in the appropriate layer.

## 6. Security requirements

Apply security from the beginning:

- Authenticate users where required.
- Authorize every protected action on the server.
- Apply least privilege and deny access by default.
- Validate all user input.
- Use safe database queries to prevent SQL/NoSQL injection.
- Prevent unauthorized access to records and files (IDOR/BOLA).
- Protect passwords with a suitable password-hashing algorithm.
- Store secrets in environment configuration or a secrets manager, never in source code.
- Use HTTPS in production.
- Configure CORS, cookies and CSRF protections appropriately.
- Apply rate limits to sensitive or expensive endpoints.
- Protect file uploads and external webhooks.
- Avoid logging passwords, tokens or sensitive personal data.
- Review applicable OWASP guidance and test security-sensitive behaviour.

## 7. Testing and verification

Add tests appropriate to the change:

- Unit tests for business logic and validation.
- Integration tests for database and service interactions.
- API or contract tests for interfaces.
- End-to-end tests for important user workflows.
- Security tests for permissions, unauthorized access and invalid input.

Run the project's available tests, formatter, linter and type checker. Fix regressions. Never claim a test passed unless it was actually run.

## 8. Error handling and monitoring

- Use consistent error responses.
- Do not expose stack traces or secrets to users.
- Log useful diagnostic information safely.
- Use request or correlation IDs where appropriate.
- Monitor errors, latency and important dependencies.
- Handle database, network and external-service failures.
- Use bounded retries and timeouts where appropriate.

## 9. Documentation and delivery

For each completed feature, update relevant documentation:

- What the feature does.
- Important files and responsibilities.
- API changes.
- Database/schema/index changes.
- Configuration requirements.
- Security and permission behaviour.
- Tests and how to run them.
- Migration or deployment steps, if needed.

Before finishing, review the changed files and ensure there are no unrelated edits, debug statements or committed secrets.

---

## Master Prompt

Read and follow `ENGINEERING_GUIDE.md` before working on my task.

1. Inspect and understand the existing project and its code structure.
2. Understand the requirement and expected functionality.
3. Identify the modules, components and files involved.
4. Plan the required schemas, database changes, APIs, services and repositories where applicable.
5. Check validation, security and error-handling requirements.
6. Present a clear implementation plan before making changes.
7. Implement the task using the existing project conventions.
8. Test the implementation and fix any issues.
9. Update relevant documentation.
10. Summarize the files changed, functionality completed and tests actually run.

Do not guess existing functionality, overwrite unrelated work, expose secrets or add unnecessary complexity. Ask me if an essential requirement is unclear.

**Task:**
[Describe the project, module or feature you want to build here.]
