# FIGMA_TO_FRONTEND_IMPLEMENTATION_GUIDE.md

## Purpose
Implement the frontend to match the existing Figma designs as closely as possible across every required page and frame. Figma is the visual source of truth. Do not redesign, simplify, approximate or invent UI when the design already exists. Use the connected Figma MCP to inspect the actual file and retrieve its design details and assets.

This guide covers frontend implementation only.

## 1. Inspect the frontend project first
- Inspect the repository structure, framework, language, package manager and build setup.
- Identify routing, layouts, styling, state management, API client and component conventions.
- Inspect existing reusable components, tokens, fonts, icons and assets.
- Understand current functionality before changing anything.
- Review Git status and preserve existing changes.
- Reuse the existing architecture. Do not replace it or add dependencies without a clear reason.

## 2. Inspect the entire Figma file using MCP
Use the connected Figma MCP tools to inspect the actual file, not just a screenshot or a few sample screens.

Inspect every relevant:
- Figma page and frame.
- Nested frame, section and layer.
- Component, instance, variant and component property.
- Auto Layout setting, constraint and resizing behaviour.
- Text layer, text style and font.
- Fill, stroke, border, radius, shadow and effect.
- Image, logo, illustration and icon.
- Prototype link, overlay and interaction.
- Desktop, tablet and mobile design, when provided.

Do not skip pages or assume similarly named frames are duplicates. Inspect and compare them. If the file is large, work page by page and track inspected and uninspected items. Do not claim the inspection is complete until all relevant pages and frames have been reviewed.

## 3. Create a complete page/frame inventory
Before coding, create a tracking table:

| Figma page | Frame/screen | Node ID | Frontend route | Inspection status | Implementation status |
|---|---|---|---|---|---|

For each frame, record:
- Overall page structure and section order.
- Header, sidebar, navigation, footer and content containers.
- Columns, grids, cards, tables, forms, dialogs and overlays.
- Repeated components and variants.
- Assets, icons, fonts and illustrations.
- Interactive elements and expected behaviour.
- Responsive frames and resizing rules.

Map every required frame to its frontend route. Identify missing or unclear route mappings before implementation.

## 4. Export and use original assets
Use Figma MCP export/access capabilities to retrieve the original assets wherever possible.

### SVG and vector assets
- Export original SVGs for logos, icons, illustrations and vector graphics when available.
- Preserve original paths, viewBox, dimensions, proportions, fills, strokes, stroke widths, gradients, masks and colours.
- Do not replace original icons with emoji, text characters, random icon-library icons or approximate drawings.
- Do not redraw an asset when the original export is available.
- Verify each SVG renders correctly in the frontend.
- Use reusable TSX icon components when useful, preserving the original SVG artwork and paths.
- If an SVG cannot be exported or faithfully converted, report it instead of silently substituting an approximation.

### Other assets
Retrieve and use original raster images, logos, illustrations, backgrounds and font files where available and permitted. Keep meaningful filenames and organize them in the existing assets structure. Preserve aspect ratios and intended dimensions. Avoid duplicate exports.

Do not use a screenshot of a whole Figma frame as the implementation of a page. Build real frontend elements and use exported assets for visual elements.

Maintain an asset map:

| Figma node/component | Asset type | Exported file | Frontend usage | Verified |
|---|---|---|---|---|

## 5. Extract exact design tokens
Use actual Figma values through MCP wherever available. Do not estimate from screenshots when exact values can be retrieved.

Capture:
- Colours: backgrounds, surfaces, primary/secondary/accent, text, muted text, borders, status colours, gradients and opacity.
- Typography: font family, weight, size, line height, letter spacing, alignment and decoration.
- Layout: frame dimensions, content widths, padding, margins, gaps, grid proportions and alignment.
- Components: border widths, radii, shadows, blur, icon sizes, button/input dimensions and interaction states.

Create or update shared CSS variables, theme tokens or the project's existing token system. Reuse consistent values across pages. Do not introduce arbitrary values when an exact Figma or existing project token is available.

## 6. Understand layout and responsive behaviour
- Use Auto Layout information to understand direction, alignment, gaps, padding and sizing.
- Translate Figma constraints into suitable CSS Flexbox, Grid, responsive sizing or positioning.
- Understand fixed, flexible, sticky, scrollable and overflow regions.
- Preserve proportions and hierarchy.
- Avoid absolute positioning for entire layouts when responsive layout behaviour is intended.
- Inspect supplied desktop/tablet/mobile frames and implement each required version.
- If responsive behaviour is not specified, adapt sensibly without changing the supplied design; record the adaptation as an implementation decision.

## 7. Plan reusable components
Identify repeated headers, sidebars, navigation, buttons, inputs, cards, tables, badges, dialogs and other patterns. Reuse Figma components and variants where possible. Build shared frontend components where the same design repeats. Preserve differences between variants such as size, colour and state. Do not force visually different designs into one generic component or duplicate shared components unnecessarily.

## 8. Implement every page frame by frame
For each frame:
1. Open the exact Figma frame using its node ID.
2. Inspect its full structure and nested elements.
3. Confirm its frontend route and layout.
4. Identify shared and page-specific components.
5. Export and map its original assets.
6. Apply exact available tokens and styles.
7. Implement structure, layout and responsive behaviour.
8. Implement specified interactions.
9. Compare the page with the exact Figma frame.
10. Fix visual differences and verify again.

Match:
- Page dimensions, content width and alignment.
- Header, sidebar and navigation position.
- Section hierarchy and order.
- Spacing, gaps, dimensions and proportions.
- Fonts, text sizes, weights and wrapping.
- Colours, borders, radii, gradients and shadows.
- Original SVGs, images, logos and illustrations.
- Tables, forms, cards, dialogs and overlays.
- Hover, focus, active, selected and disabled states.

Do not skip small details such as icons, dividers, labels, borders or text styles.

## 9. Implement specified interactions
Inspect prototype interactions and component states. Implement the relevant navigation, buttons, menus, tabs, dropdowns, forms, validation, search, filters, sorting, pagination, dialogs, drawers, popovers, expand/collapse, tooltips and notifications.

A control should not remain decorative if its intended action is specified. Do not invent complex behaviour when Figma or requirements do not define it; record unclear behaviour for clarification.

## 10. Preserve application functionality
- Follow existing frontend architecture and conventions.
- Reuse established API clients, authentication and state management.
- Do not replace real data with hardcoded sample values.
- Do not invent backend endpoints or response fields.
- Keep design code appropriately separated from business logic.
- If backend integration is unavailable, isolate and label temporary mock data.
- Preserve existing working features.

## 11. Visually verify every implemented page
Visual verification is mandatory. Do not mark a page complete immediately after coding.

For each frame:
- Open the matching frontend route.
- Use the same viewport dimensions as the Figma frame where possible.
- Capture a frontend screenshot.
- Compare it with the exact Figma frame.
- Check layout, alignment, dimensions, spacing, typography, colours and text wrapping.
- Check every SVG, icon, image and font.
- Check borders, shadows, radii and component states.
- Check responsive behaviour for provided viewports.
- Check console errors and failed network requests.
- Fix differences and compare again.

Use screenshot comparison or overlays when available; do not rely only on memory or visual impressions.

Track verification:

| Figma page/frame | Viewport | Layout | Styles/type | Assets/SVGs | Interactions | Screenshot compared | Status |
|---|---|---|---|---|---|---|---|

A page is **Verified** only after comparison with its correct Figma frame and checking its required interactions.

## 12. Audit frontend completeness
After implementation, confirm:
- Every required page and frame is accounted for.
- Every required route exists and opens.
- Navigation connects pages correctly.
- No sections or nested elements were skipped.
- All required SVGs and assets are present and render correctly.
- No broken asset or font paths remain.
- No unintended placeholder or mock content remains.
- Buttons, links and controls work.
- Forms and states behave correctly.
- Responsive layouts work at required sizes.
- No major console errors or failed requests remain.
- Existing application functionality is not broken.

Run available lint, type-check, test and build commands. Record exact commands and results. Never claim a check passed if it was not run.

## 13. Record blockers honestly
Report pages/frames MCP could not access, assets that could not be exported, SVGs that could not be preserved, missing fonts, unclear interactions, unspecified responsive behaviour, missing route mappings, remaining visual differences and build failures.

Do not silently guess or substitute. Do not claim full completion while relevant frames remain uninspected or unverified.

---

## Required final report

### A. Figma inspection summary
Figma file, pages/frames discovered, inspected items, uninspected items and MCP limitations.

### B. Page implementation matrix

| Page | Frame | Node ID | Frontend route | Implementation status | Verification status |
|---|---|---|---|---|---|

Include every relevant frame.

### C. Asset and SVG report
List original assets, export paths, frontend usage and verification. Separately list inaccessible or substituted assets and explain why.

### D. Design token report
Summarize extracted colours, typography, spacing, dimensions, radii, shadows and any values that were unavailable or approximated.

### E. Component and interaction report
List shared components, variants, page-specific components and interactions marked implemented, partial, missing or unclear.

### F. Visual verification report
For each page, list viewport, screenshot comparison result, visual differences and remaining work.

### G. Quality checks
List exact lint, type-check, test and build commands and results, plus console/network issues.

### H. Missing items and prioritized action plan
List missing pages, broken assets, visual mismatches, inactive controls, responsive issues and other blockers with exact frame/file references and next steps.

### I. Final completion decision
Choose one:
- Not started.
- Partially implemented.
- Implemented but not visually verified.
- Visually verified with known gaps.
- All required pages implemented and verified.

Explain the evidence and remaining gaps. Do not claim pixel-perfect completion if any relevant frame has not been compared.

---

## Master Prompt for Cursor

Read and follow `FIGMA_TO_FRONTEND_IMPLEMENTATION_GUIDE.md` completely.

I have an existing Figma file containing many pages and frames. Figma MCP is connected. Implement the frontend so every required page matches its corresponding Figma design as closely as possible.

1. Inspect the existing frontend repository, framework, routes, components and conventions.
2. Use Figma MCP to discover and inspect all relevant pages, frames, nested elements, components, variants and prototype interactions.
3. Build a complete page/frame inventory with node IDs and map each frame to a frontend route.
4. Extract actual layout, Auto Layout, constraints, dimensions, spacing, colours, typography, borders, radii, shadows and component states.
5. Export and use original SVG icons, logos and vector assets wherever available. Retrieve raster images, illustrations and fonts too.
6. Preserve SVG paths, viewBox, fills, strokes, gradients and proportions. Use reusable TSX icon components when appropriate without approximating the artwork.
7. Create or reuse design tokens and shared components based on the actual Figma design.
8. Implement every required page and specified interaction, one frame at a time.
9. Compare each frontend page with its exact Figma frame at the same viewport. Capture screenshots, identify differences and correct them.
10. Run available frontend checks and produce the complete report above.

### Strict requirements
- Figma is the visual source of truth. Do not redesign or approximate existing designs unnecessarily.
- Inspect every relevant page and frame, not only the first few screens.
- Do not assume similar-looking frames are duplicates.
- Do not replace original SVGs with emoji, text symbols or approximate icons.
- Do not use whole-page screenshots instead of implementing actual frontend elements.
- Do not guess values when MCP can provide the actual values.
- Do not silently skip inaccessible frames or assets.
- Do not invent unspecified interactions or responsive rules; record assumptions.
- Do not unnecessarily change the project architecture or break existing functionality.
- Keep inspected, implemented and verified status separate.
- If the file is too large, proceed page by page and track progress. Never claim full inspection without completing it.
- Preserve existing user changes.
- Do not mark a page complete until it has been visually compared with its corresponding Figma frame.

### Project details
- Figma file/link: [Provide Figma file]
- Frontend repository/path: [Provide frontend folder]
- Pages/sections: [All pages / specify]
- Frontend stack: [Discover from repository or specify]
- Target viewports: [Specify or inspect responsive Figma frames]
- Additional instructions: [Specify]

Start by inspecting the frontend project and discovering the complete Figma page/frame inventory. Present the inventory and implementation plan before large code changes. Then implement and verify every required page systematically.
