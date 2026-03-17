# Frontend instructions

Apply these instructions when working on web UI, components, dashboards, design system, routing, or state handling.

## UI strategy
Build the interface as a workspace shell with widgets, not as a collection of rigid pages.

## Widget rules
Each widget should have:
- stable id
- clear title and purpose
- permission requirements
- explicit filters and inputs
- predictable API contract
- reusable internal structure

## UX rules
- tenant/location context must always be visible
- navigation must be grouped logically
- widget visibility must follow permissions
- dark mode and layout persistence should be supported cleanly
- design should favor operational clarity over decoration
