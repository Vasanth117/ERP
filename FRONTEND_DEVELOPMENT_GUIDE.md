# FRONTEND_DEVELOPMENT_GUIDE.md

## Purpose

Use this guide when creating or developing the frontend of a web application.

The goal is to build a complete, maintainable, functional and responsive frontend that works properly on desktop, tablet and mobile devices.

This guide is for frontend development. Follow the existing project architecture and requirements. If a Figma design exists, use the separate Figma-to-Frontend guide as the visual reference.

Do not build only static screens. Implement the required pages, navigation, interactions, states and responsive behaviour.

---

## 1. Understand the project before coding

Before making changes:

- Inspect the complete frontend repository.
- Identify the framework, language, build tool and package manager.
- Inspect the existing folder structure, routes, layouts and components.
- Identify the styling approach, UI library and design-token system.
- Understand current API clients, authentication, state management and data-fetching patterns.
- Review existing assets, fonts, icons and reusable components.
- Read available requirements and identify all required modules, pages and user roles.
- Check Git status and preserve existing changes.

Do not replace the existing architecture or install unnecessary dependencies. Reuse existing conventions and working functionality.

## 2. Plan the frontend pages and routes

Create a page inventory before implementation.

For each page, identify:
- Page name and purpose.
- Route/path.
- Parent layout.
- User roles that can access it.
- Main sections and components.
- Required data and API dependencies.
- Main actions and interactions.
- Loading, empty, error and success states.
- Responsive behaviour.

Ensure every required page has a route and that navigation between related pages is clear.

## 3. Manage frontend development properly

Do not follow an arbitrary folder structure just because it appears in a guide. First understand the existing project and continue its established conventions. Organize the implementation around the actual features and responsibilities.

For each feature or page:

- Keep its page-level implementation, feature-specific components, validation and related logic together in a way that fits the existing project.
- Separate reusable application-wide components from components that are only used by one feature.
- Keep API communication in the project's established API/service layer rather than writing request logic differently in every page.
- Keep shared types and interfaces consistent with the actual API contracts.
- Keep business rules out of presentation-only components where practical.
- Keep components focused: a component should have a clear responsibility and should not become a large file containing an entire feature.
- Extract repeated logic into existing project patterns such as hooks or utilities when it genuinely improves reuse.
- Use consistent naming, imports, formatting and error-handling patterns.
- Avoid duplicate implementations, unnecessary abstractions and unnecessary dependencies.
- Before creating a new component or utility, check whether an existing one already performs that job.

### Development workflow

1. Understand the feature requirement and expected user workflow.
2. Identify the page, components, data, API operations and permissions involved.
3. Check whether reusable components or existing logic can be used.
4. Plan the smallest set of files and changes needed.
5. Implement the feature in manageable steps.
6. Verify the normal flow and failure cases.
7. Check that related pages and existing features still work.
8. Record incomplete work and assumptions instead of hiding them.

Do not create placeholder components, duplicate files or unused abstractions just to make the project look organized.

## 4. Build a consistent UI foundation

Create or reuse shared design foundations:

- Colour palette and theme variables.
- Typography scale and font families.
- Spacing scale.
- Breakpoints.
- Container widths.
- Border radii and shadows.
- Button, input and form styles.
- Common card, table, badge and dialog styles.

Use design tokens or CSS variables where appropriate. Avoid random one-off values and inconsistent styling.

Keep visual consistency across pages, including spacing, alignment, typography, icons and component states.

## 5. Create reusable components

Identify repeated UI patterns and build reusable components where useful.

Examples:
- Application header and navigation.
- Sidebar and mobile navigation.
- Page title and breadcrumb.
- Buttons and icon buttons.
- Inputs, selects, checkboxes and radio controls.
- Form fields and validation messages.
- Cards, tables and data lists.
- Search and filter controls.
- Tabs and pagination.
- Dialogs, drawers, dropdowns and popovers.
- Alerts, badges, toasts and loading indicators.
- Empty states and error states.

Requirements:
- Support the variants and states needed by the application.
- Use consistent props and component APIs.
- Keep components accessible and responsive.
- Avoid duplicating identical UI across pages.
- Do not over-generalize components that have genuinely different behaviour.

## 6. Implement all required pages

For every page:

1. Understand its purpose and requirements.
2. Identify the correct route and layout.
3. Break the page into logical sections.
4. Reuse shared components.
5. Implement the content and required data.
6. Implement all required actions and interactions.
7. Add loading, empty, error and success states.
8. Verify permissions and role-specific visibility.
9. Check desktop, tablet and mobile layouts.
10. Test the page before marking it complete.

Do not leave required pages as blank screens, placeholders or static mockups.

## 7. Make the entire website responsive

Responsive design is mandatory. The website must work on mobile phones, tablets, laptops and large desktop screens.

Do not treat mobile responsiveness as a final optional adjustment. Consider responsive behaviour while designing and implementing every page and component.

### Responsive layout

- Use a mobile-first approach where suitable.
- Use CSS Grid, Flexbox and fluid sizing appropriately.
- Use responsive containers and sensible maximum widths.
- Avoid fixed widths that cause horizontal overflow.
- Allow content to wrap and resize naturally.
- Use responsive spacing and typography.
- Ensure images and media scale without distortion.
- Respect safe areas on mobile devices where relevant.
- Prevent content from being hidden behind fixed headers or navigation.
- Avoid relying on hover-only interactions on touch devices.

### Navigation

- Provide suitable desktop navigation.
- Use a mobile navigation pattern such as a menu button, drawer, or bottom navigation when appropriate.
- Ensure the mobile menu opens, closes and navigates correctly.
- Make menus usable with touch and keyboard.
- Close mobile navigation after navigation when appropriate.
- Keep navigation accessible and prevent it from covering important content.

### Tables and wide content

- Do not let tables break the mobile layout.
- Use an appropriate responsive strategy: horizontal scrolling, column prioritization, stacked records or a dedicated mobile layout.
- Keep important information and actions accessible.
- Ensure charts, code blocks and wide content remain usable on small screens.

### Forms and controls

- Make inputs and buttons comfortable to use on touch screens.
- Use suitable input types and mobile-friendly input behaviour.
- Prevent labels, validation messages and controls from overlapping.
- Ensure dropdowns, date pickers, dialogs and popovers fit within the viewport.
- Keep form actions visible and easy to reach.

### Responsive breakpoints

Use the breakpoints already established in the project or design system. If none exist, define a consistent breakpoint strategy appropriate to the application. Do not assume one set of breakpoint values fits every layout.

Verify at least:
- Small mobile: approximately 320–375 px.
- Standard mobile: approximately 390–430 px.
- Tablet: approximately 768–1024 px.
- Desktop: approximately 1280 px and above.

Also test intermediate widths where layout transitions may break. These are verification viewport examples, not a requirement to hardcode every layout to those exact widths.

### Mobile verification checklist

- No unintended horizontal page scrolling.
- No clipped text, buttons, cards or form fields.
- No overlapping sections or fixed elements.
- Navigation and menus work by touch.
- Buttons and controls have usable touch targets.
- Tables and wide content remain usable.
- Images and icons scale correctly.
- Dialogs and dropdowns fit the screen.
- Typography remains readable.
- Content order and hierarchy remain clear.
- Forms can be completed without layout problems.
- Sticky headers/footers do not hide content.
- Portrait and landscape layouts work where relevant.

## 8. Implement real interactions and behaviour

All visible controls should behave as expected.

Implement and test:
- Navigation links and buttons.
- Forms, validation and submission.
- Search, filtering and sorting.
- Tabs and segmented controls.
- Dropdowns and action menus.
- Tables, pagination and row actions.
- Dialogs, drawers and confirmation flows.
- Expand/collapse sections.
- Notifications and feedback messages.
- File upload and download flows, if required.
- Keyboard and touch interactions.

Do not use clickable-looking elements that do nothing. If an action is not defined in the requirements, identify it rather than inventing important business behaviour.

## 9. Connect to backend APIs correctly

When backend APIs are available:

- Inspect the API documentation or actual backend routes.
- Use the correct HTTP methods, URLs, request fields and response structures.
- Use a centralized API client or existing service layer.
- Handle authentication and authorization correctly.
- Keep secrets and private credentials out of frontend code.
- Handle loading, success, empty, validation, authorization, server and network errors.
- Avoid duplicate requests and unnecessary re-fetching.
- Keep frontend types aligned with actual API contracts.
- Do not invent endpoints, fields or response data.
- Do not replace real data with hardcoded values in completed features.

If the backend is not ready, isolate mock data and clearly identify what still needs integration.

## 10. Handle frontend errors properly

Error handling must be consistent across the application. Do not leave errors only in the browser console, show raw backend messages to users, or silently ignore failed operations.

### Centralize API error handling

- Use the existing shared API client or request layer for common error handling.
- Convert different backend/network error responses into a consistent error shape that the UI can understand.
- Handle request timeouts, connection failures, invalid responses and server errors.
- Keep authentication headers and token refresh behaviour in the established authentication flow.
- Do not duplicate slightly different error-handling code in every page.
- Do not expose stack traces, internal server details, database errors, tokens or sensitive information to users.

### Handle errors according to the situation

| Situation | Expected frontend behaviour |
|---|---|
| Validation error (400/422) | Show the relevant message beside the field or form |
| Unauthenticated (401) | Follow the application's sign-in/session-expiry flow |
| Forbidden (403) | Show an access-denied state; do not pretend the action succeeded |
| Not found (404) | Show a not-found state or explain that the requested record is unavailable |
| Conflict (409) | Explain the conflict and guide the user to refresh or resolve it |
| Rate limited (429) | Explain that the user should wait before trying again |
| Server error (5xx) | Show a safe message and allow retry when appropriate |
| Network/offline/timeout | Explain that the service could not be reached and provide a retry option when safe |

Use the actual status codes and error contract provided by the backend. Do not assume every API uses the same response format.

### Handle errors at the correct level

- **Field level:** Show validation errors next to the relevant input.
- **Form level:** Show submission errors that apply to the whole form.
- **Component level:** Show a local fallback when a widget or data section fails independently.
- **Page level:** Show a useful error state when the page cannot load its required data.
- **Application level:** Use an error boundary or the framework's equivalent to prevent an unexpected rendering error from crashing the entire application.

Provide a clear recovery action where possible, such as retry, go back, refresh, sign in again or contact support.

### Protect user actions and data

- Do not clear form values when a request fails unless the workflow requires it.
- Prevent accidental duplicate submissions while a request is processing.
- Show a loading state while an operation is in progress.
- Do not show a success message until the backend confirms success.
- If an update fails, keep the UI consistent with the actual server state.
- For destructive actions, show confirmation where required and report failures clearly.
- Retry automatically only when it is safe. Do not automatically repeat payments, record creation, file uploads or other non-idempotent actions without a reliable idempotency mechanism.
- Cancel obsolete requests or ignore stale responses when users navigate or change search/filter input quickly.

### Logging and debugging

- Keep useful technical details in development logs.
- In production, send errors through the project's approved monitoring/logging service if one exists.
- Include useful context such as feature, operation and request/correlation ID when available.
- Never log passwords, access tokens, secrets, private user data or full sensitive request payloads.
- Do not swallow exceptions with empty catch blocks.
- If an error is caught, handle it meaningfully, show appropriate feedback and log safe diagnostic information.
- Avoid exposing internal exception text directly in the UI.

### Verify error scenarios

For each important feature, test:
- Invalid input.
- Missing or expired authentication.
- Insufficient permission.
- Missing or deleted record.
- Duplicate/conflicting request.
- Network disconnection and timeout.
- Backend 5xx response.
- Failed upload or external dependency, if applicable.
- Retry and recovery behaviour.

A feature is not verified just because its success path works. Confirm that failures are understandable, safe and recoverable.

## 11. Manage application state and data

- Use the project's existing state-management approach.
- Keep local UI state local when possible.
- Use shared state only when multiple components need it.
- Keep server data and UI state conceptually separate.
- Handle loading and request failures.
- Avoid stale or inconsistent data after updates.
- Prevent duplicate submissions.
- Preserve appropriate state during navigation.
- Avoid unnecessary global state and complex abstractions.

## 12. Implement forms and validation

- Use clear labels and helpful descriptions.
- Mark required fields appropriately.
- Validate input types, formats and business constraints.
- Show errors near the relevant fields.
- Preserve user input when safe after validation failures.
- Disable or guard duplicate submissions.
- Show progress and success/failure feedback.
- Ensure forms are keyboard accessible and mobile friendly.
- Do not rely only on frontend validation; the backend must validate submitted data too.

## 13. Accessibility and usability

Follow practical accessibility basics:

- Use semantic HTML elements.
- Provide labels for inputs and accessible names for icon-only buttons.
- Maintain sufficient text and control contrast.
- Support keyboard navigation.
- Provide visible focus states.
- Use correct heading hierarchy.
- Add useful alternative text for meaningful images.
- Do not communicate status using colour alone.
- Ensure dialogs and menus support keyboard interaction and focus management.
- Respect reduced-motion preferences where relevant.

Keep the interface understandable, predictable and consistent.

## 14. Performance and code quality

- Avoid unnecessary re-renders and expensive computations.
- Split large routes or features when useful.
- Optimize images and use suitable formats.
- Load assets efficiently.
- Avoid unnecessary dependencies.
- Avoid duplicate API calls.
- Keep bundles and page loading reasonable.
- Use appropriate caching and data-fetching patterns.
- Remove unused imports and dead code.
- Follow the project's linting, formatting and type-checking conventions.
- Avoid suppressing errors without a clear reason.

Do not optimize blindly; investigate measurable or likely bottlenecks.

## 15. Browser and device verification

Test the frontend in supported browsers and realistic viewport sizes.

Verify:
- Routes load and refresh correctly.
- Navigation works.
- Forms and interactions work.
- API requests succeed and failures are handled.
- No major console errors exist.
- No broken asset requests exist.
- Responsive layouts work at mobile, tablet and desktop sizes.
- Keyboard navigation and touch interactions work.
- Existing features remain functional.

Where possible, test both portrait and landscape mobile orientations and at least one real or emulated touch-device environment.

## 16. Run project checks

Inspect available scripts and run the relevant commands, such as:
- Development server startup.
- Lint.
- Type check.
- Unit/component tests.
- Integration tests.
- Production build.

Use the actual scripts configured in the repository. Record exact commands and results. Fix relevant failures and rerun checks. Do not claim success if a check was not run.

## 17. Keep implementation progress and gaps visible

Maintain a page checklist:

| Page/feature | Route | Implementation | API connection | Desktop | Mobile | Tests | Status |
|---|---|---|---|---|---|---|---|

Use clear statuses such as Not started, In progress, Implemented, Verified, Blocked and Not applicable.

Record:
- Missing pages or features.
- Unconnected API calls.
- Incomplete interactions.
- Responsive issues.
- Temporary mock data.
- Accessibility issues.
- Build/test failures.
- Requirements needing clarification.

Do not silently leave incomplete work or claim the entire frontend is complete when some pages or viewport sizes have not been checked.

---

## Required final development report

### A. Project summary
- Frontend stack and structure.
- Pages and features implemented.
- Existing functionality preserved or changed.

### B. Page and feature completion

| Page/feature | Route | Status | Notes |
|---|---|---|---|

### C. Component and design system report
List reusable components, shared layouts, tokens and styling conventions created or reused.

### D. API and data connection report
List connected APIs, temporary mock data, missing endpoints and integration gaps.

### E. Responsive verification report

| Page | Mobile | Tablet | Desktop | Issues remaining |
|---|---|---|---|---|

Include viewport sizes tested and any layout problems.

### F. Interaction and accessibility report
List working interactions, incomplete controls and accessibility gaps.

### G. Quality checks
List exact lint, type-check, test and build commands with their results. Include browser console and network issues.

### H. Remaining work
List missing features, bugs, blockers and recommended next steps.

### I. Final status
State whether the frontend is:
- Not started.
- Partially implemented.
- Implemented but not fully tested.
- Verified on desktop but not fully responsive.
- Verified on mobile, tablet and desktop with known gaps.
- Complete against the available requirements and verified on supported viewports.

Be honest about what was actually tested.

---

## Master Prompt for Cursor

Read and follow `FRONTEND_DEVELOPMENT_GUIDE.md` completely.

Develop the frontend for this project using the existing repository, requirements and design references. Build all required pages and features with clean, reusable and maintainable code. The website must be fully responsive on mobile, tablet and desktop.

### Workflow

1. Inspect the existing frontend repository, framework, dependencies, routes and conventions.
2. Read the available requirements and identify all modules, pages, user roles and workflows.
3. Create a page and feature inventory with routes and dependencies.
4. Inspect and reuse existing layouts, components, styles, assets and state-management patterns.
5. Plan the implementation structure before making large changes.
6. Build shared layouts, navigation, design tokens and reusable components.
7. Implement every required page and all specified interactions.
8. Connect to actual backend APIs using the existing API contract. Do not invent endpoints or response fields.
9. Implement loading, empty, error, validation and success states.
10. Make every page responsive for mobile, tablet and desktop. Do not postpone mobile responsiveness until the end.
11. Verify navigation, forms, controls, touch interactions, keyboard access and accessibility basics.
12. Test pages at small mobile, standard mobile, tablet and desktop viewport sizes. Fix horizontal overflow, clipping, overlap and unusable controls.
13. Run the project's lint, type-check, tests and production build where available.
14. Produce the complete final development report from this guide, including responsive verification and remaining gaps.

### Strict requirements

- Inspect before coding; do not blindly replace existing code.
- Follow the existing project architecture and conventions.
- Implement real pages and functionality, not only static mockups.
- Reuse components where appropriate without over-generalizing.
- Mobile, tablet and desktop responsiveness is mandatory.
- Use touch-friendly controls and do not rely on hover-only behaviour.
- Do not allow unintended horizontal overflow on mobile.
- Do not hide important content or actions on smaller screens.
- Do not invent backend endpoints, response fields or business rules.
- Do not leave visible controls inactive.
- Do not leave unintended mock data in completed features.
- Preserve existing working functionality and user changes.
- Do not claim a page or feature is verified unless it has actually been tested.
- Record anything blocked, missing or requiring clarification.

### Project details

- Frontend repository/path: [Specify frontend folder]
- Requirements/documentation: [Specify files]
- Backend API documentation/base URL: [Specify if available]
- Figma/design reference: [Specify if available]
- Frontend stack: [Discover from repository or specify]
- Supported browsers/devices: [Specify if required]
- Additional instructions: [Specify]

Start by inspecting the repository and preparing the page/feature inventory and implementation plan. Then develop the frontend systematically and verify every page on mobile, tablet and desktop.
