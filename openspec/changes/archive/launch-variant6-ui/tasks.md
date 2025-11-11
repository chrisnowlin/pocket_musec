## 1. Implementation
- [ ] Add a dedicated `WorkspaceShell` component that renders the Variant 6 workspace and provides a gateway to the legacy layout.
- [ ] Update `App.tsx` so `/` renders the new shell, `/workspace` redirects if needed, and `/classic` hosts the legacy dashboard/images/settings routes.
- [ ] Adjust the classic layout/navigation links to point at `/classic/*` so users stay within the legacy flow when they deliberately switch.
- [ ] Run the frontend build/license checks and confirm the new shell works; document any follow-up verification in this change.
