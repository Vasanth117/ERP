# FRONTEND_BACKEND_INTEGRATION_GUIDE.md

## Purpose

Use this guide when connecting an existing frontend application to an existing backend.

The goal is to make the frontend and backend work together correctly, securely and reliably, using the actual API contracts and project structure.

**Important:** Inspect both projects before making changes. Do not guess API endpoints, request fields, response formats, authentication methods or database behaviour.

---

## 1. Inspect both projects

Before integration, inspect:

### Frontend
- Framework, folder structure and routing.
- Existing pages, components, forms and state management.
- Current API client or HTTP request utilities.
- Environment configuration.
- Authentication and token/session handling.
- Existing loading, success and error handling.

### Backend
- Framework, folder structure and application entry point.
- Available API routes and HTTP methods.
- Request and response schemas.
- Authentication and authorization.
- Validation and error response formats.
- Database models, services and repositories.
- CORS and environment configuration.
- Existing API documentation and tests.

Trace at least one similar feature from the frontend action through the backend to the database and back.

Summarize what already exists, what can be reused and what is missing.

## 2. Define the API contract

Before connecting a feature, confirm the API contract.

For every endpoint, identify:

- HTTP method and exact URL.
- Purpose.
- Authentication requirements.
- Required permissions.
- Path and query parameters.
- Request body and content type.
- Required and optional fields.
- Response structure and data types.
- Success status codes.
- Possible error codes and response format.
- Pagination, filtering and sorting rules.

Use the backend implementation or its OpenAPI documentation as the source of truth. If the frontend and backend contracts disagree, identify the mismatch and agree on the correct contract before changing either side.

Do not invent endpoints or silently rename fields.

## 3. Configure the API connection

- Create or reuse one centralized API client.
- Keep the backend base URL in environment configuration.
- Use the correct development, staging and production URLs.
- Set appropriate request headers and content types.
- Configure request timeouts.
- Handle network errors consistently.
- Avoid hardcoding URLs throughout components.
- Never put backend secrets or private API keys in frontend code.

Keep environment files and examples free of real credentials.

## 4. Connect authentication and authorization

Verify the actual authentication design before implementation.

- Connect login, logout and session restoration.
- Send credentials or tokens using the agreed secure method.
- Handle token expiry and refresh according to backend behaviour.
- Prevent repeated or conflicting refresh requests.
- Clear invalid sessions safely.
- Protect frontend routes for user experience.
- Enforce all permissions again on the backend.
- Handle `401 Unauthorized` and `403 Forbidden` consistently.
- Never rely on frontend role checks as the only security control.
- Do not store sensitive tokens in insecure browser storage without reviewing the security implications.

For cookie-based authentication, configure credentials, CORS, cookie attributes and CSRF protection correctly.

## 5. Connect frontend features to backend APIs

For each feature:

1. Identify the user action.
2. Identify the corresponding backend endpoint.
3. Map frontend fields to the API request schema.
4. Validate inputs on the frontend for usability.
5. Submit the request through the centralized API client.
6. Validate and map the backend response.
7. Update the relevant page or application state.
8. Display the correct success or error feedback.

Keep API communication separate from presentation components where appropriate. Reuse existing hooks, services or data-fetching patterns.

Do not duplicate business rules in the frontend. The backend remains responsible for authoritative validation and business logic.

## 6. Handle application states

Every API-connected feature should handle the relevant states:

- **Loading:** show an appropriate loading indicator.
- **Success:** display or update the returned data.
- **Empty:** show a useful empty state when no records exist.
- **Validation error:** show field-level messages where possible.
- **Unauthorized:** handle expired or missing authentication.
- **Forbidden:** explain that the action is not permitted.
- **Not found:** handle missing resources.
- **Conflict:** handle duplicate or conflicting updates.
- **Server error:** show a safe message and allow appropriate recovery.
- **Network error:** explain connection failure and provide retry where safe.

Prevent duplicate submissions when an operation is in progress. Do not show success before the backend confirms the operation.

## 7. Data mapping and consistency

- Match frontend field names and data types to the API contract.
- Handle nullable and optional values correctly.
- Handle dates and timezones consistently.
- Handle money and numeric precision safely.
- Handle pagination metadata and total counts correctly.
- Do not assume response arrays or objects are always populated.
- Avoid overwriting newer state with stale responses.
- Refresh or invalidate cached data after successful mutations.
- Do not expose internal database fields unnecessarily in the UI.

## 8. CORS, files and external requests

- Configure backend CORS for the actual frontend origins.
- Do not use permissive wildcard CORS with credentials.
- Use the correct content type for JSON, forms and multipart uploads.
- Enforce file type and size rules on both frontend and backend.
- Show upload progress when appropriate.
- Handle upload failures and retries safely.
- Authorize file downloads on the backend.
- Do not expose private storage locations or long-lived public links.
- Ensure webhooks are verified by the backend, not trusted from frontend requests.

## 9. Verify the integration

Test the complete flow, not just whether the API returns a response.

### Basic checks
- Frontend can reach the correct backend environment.
- API base URL and routes are correct.
- Requests contain the expected headers and body.
- Responses are parsed and displayed correctly.
- CORS works from the actual frontend origin.

### Functional checks
- Create, read, update and delete operations work where applicable.
- Forms send the correct data.
- Search, filters, sorting and pagination work.
- Navigation and page state update correctly.
- Empty, loading and success states work.
- Refreshing the page preserves the expected session and data behaviour.

### Security checks
- Unauthenticated requests are rejected where required.
- Users without permission cannot perform protected actions.
- Users cannot access another user's or tenant's data.
- Protected fields cannot be changed through manipulated requests.
- Tokens, secrets and sensitive information are not exposed in frontend code, logs or responses.
- Backend validation remains effective even when frontend validation is bypassed.

### Failure checks
- Invalid input is handled correctly.
- Missing records are handled correctly.
- Server errors do not break the application.
- Network disconnection is handled.
- Expired authentication is handled.
- Duplicate submissions do not create unintended duplicate records.
- Safe retry behaviour is verified.

Use browser developer tools, network inspection, backend logs, API tests and automated tests as appropriate.

## 10. Review and document

Before completing:

- Review frontend and backend changes.
- Check that the API contract matches on both sides.
- Check environment configuration.
- Check CORS and authentication settings.
- Remove temporary debugging code.
- Confirm no secrets were committed.
- Run relevant frontend and backend tests.
- Run lint, type-check and build commands where available.
- Update API documentation if the contract changed.

Report:
- Features integrated.
- Endpoints connected.
- Frontend and backend files changed.
- Authentication and permission behaviour.
- Environment variables or configuration required.
- Tests and exact results.
- Known issues or incomplete integration work.

---

## Master Prompt

Read and follow `FRONTEND_BACKEND_INTEGRATION_GUIDE.md`.

I want to integrate the existing frontend with the existing backend. Make the integration work according to the real project implementation and API contracts.

Follow these steps:

1. Inspect the frontend and backend repositories and understand their structure.
2. Identify the frontend framework, backend framework, API client, routes, schemas, authentication and database flow.
3. Trace existing features end-to-end and identify reusable patterns.
4. List the APIs required for each frontend feature.
5. Verify every endpoint, method, request field, response field, status code and permission from the backend implementation or API documentation.
6. Identify mismatches between frontend expectations and backend contracts.
7. Present an integration plan, including the files to create or modify.
8. Configure the centralized API client and environment-specific base URLs.
9. Integrate authentication, session handling and permissions using the existing backend design.
10. Connect each page, form and action to the correct API.
11. Implement loading, success, empty, validation, unauthorized, forbidden, network and server-error states.
12. Handle pagination, filtering, sorting, file uploads and data mapping where required.
13. Verify CORS and other cross-origin settings.
14. Test complete user workflows and security boundaries.
15. Run relevant frontend and backend tests, linting, type checks and builds.
16. Review all changes and update relevant API documentation.
17. Report connected features, endpoints, changed files, configuration, actual test results and remaining issues.

Important:
- Do not invent API endpoints or response fields.
- Do not assume the frontend and backend contracts match.
- Do not bypass backend validation or authorization.
- Do not expose secrets in frontend code.
- Do not hardcode environment-specific URLs.
- Do not show success before the backend confirms the operation.
- Do not modify unrelated functionality.
- Do not claim integration is complete without testing the actual request/response flow.
- If an API is missing or incomplete, report it and propose the required backend change rather than creating a fake integration.

**Project details:**
Frontend location: [Frontend folder or repository]
Backend location: [Backend folder or repository]
Backend API base URL: [Development URL, if known]
Task/features to integrate: [Describe the required integration]
