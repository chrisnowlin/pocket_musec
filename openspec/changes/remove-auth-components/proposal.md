# Change Proposal: Remove Legacy Auth Components

**Change ID**: `remove-auth-components`
**Status**: DRAFT
**Author**: Codex (via ChatGPT)
**Created**: 2025-01-15

## Summary

Strip the unused authentication scaffolding from both the frontend and backend so the product intentionally operates in demo mode. We will remove login/logout UI hooks, unused auth API helpers, dead navigation links (e.g., “Users”), and redundant backend dependencies that were only supporting the unreleased auth surface. The simplified system will rely on the existing demo user wiring in `backend/api/dependencies.py`, making the UI easier to reason about while avoiding confusion about non-functional auth features.

## Problem

- The frontend still contains vestigial navigation items (e.g., “Users”) and API helpers (`login`, `logout`, token handling) that are never exercised, confusing contributors about expected flows.
- Several components mention or expect authentication states even though the backend hardcodes a demo user, leading to mismatched expectations during UI testing.
- Maintaining unused auth code increases cognitive load and creates false impressions that security features exist when they do not.
- The presence of dead auth endpoints in the API client causes lint noise and complicates future refactors.

## Proposal

1. **Delete Frontend Auth UI/Logic**
   - Remove any references to login/logout, auth guards, or user management links from the React app.
   - Eliminate unused API client methods and types related to authentication, keeping only the session/image/lesson calls that work with the demo user.
2. **Simplify Navigation & Copy**
   - Update `Layout` navigation to only include supported pages (Dashboard, Images, Settings, Workspace) and remove “Users” or other admin references.
   - Adjust page copy to clarify that the environment is a single-user demo build.
3. **Prune Backend Hooks**
   - Remove unused auth service imports or dependencies that are no longer exercised now that endpoints rely exclusively on the default user dependency.
   - Ensure the API documentation and OpenAPI output no longer advertises disabled auth endpoints (or mark them as admin-only behind flags).
4. **Documentation Cleanup**
   - Update README/install docs to explain the auth-free demo mode and remove stale login instructions.

## Scope

In scope:
- Frontend navigation updates, removal of dead auth UI/components, and API client cleanup.
- Backend cleanup limited to eliminating unused imports/config tied to the abandoned auth flow.
- Documentation updates reflecting the demo-only auth-less experience.

Out of scope:
- Implementing new auth features or changing how the demo user is injected.
- Modifying role/permission logic in repositories (they will simply continue receiving the default user).
- Any database migrations related to user tables (they remain for future milestones but are not used by the demo UI).

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Removing code that future milestones might need | Gate deletions to UI-only components and keep backend auth modules for later; document how to re-enable when required. |
| Confusing existing docs | Update README and onboarding docs in the same change. |
| Accidentally breaking demo flows when removing hooks | Add smoke tests or manual checklist covering Dashboard/Workspace/Images/Settings after cleanup. |

## Success Criteria

- No references to login/logout/auth guards remain in the frontend codebase.
- The navigation reflects only supported pages and no longer links to nonexistent “Users” admin screens.
- API client bundles only the endpoints actually used in demo mode.
- Documentation clearly states that the Milestone 3 UI runs with a built-in demo user and does not require authentication.
