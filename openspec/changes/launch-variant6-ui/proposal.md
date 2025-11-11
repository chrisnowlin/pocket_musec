## Why
- Variant 6 (Dashboard Chat Hybrid) has the most complete, usable workspace for lesson planning and should become our primary web experience.
- The existing dashboard/images/settings layout is useful for legacy workflows and content, so it should remain available but logically separated.

## What Changes
- Replace `/` with a dedicated Variant 6 workspace shell that hosts the existing workspace page, includes a toggle to the legacy view, and encapsulates the entire dashboard/chat layout as the official entrypoint.
- Push the legacy dashboard/images/settings routes under `/classic` so they remain accessible without interrupting the new experience, and adjust navigation to keep those routes self-contained.
- Update the spec to call out the Variant 6 shell as the default UI while keeping the classic flow for comparison/testing.

## Impact
- Users land directly in the Variant 6 experience when opening the app, delivering the new UI design as intended.
- QA and documentation can still point to `/classic` when verifying the previous layout.
- The codebase gains two clear entrypoints (workspace shell + classic layout) for better isolation when evolving each UI.
