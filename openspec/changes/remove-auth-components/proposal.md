# Change Proposal: Remove Legacy Auth Components

**Change ID**: `remove-auth-components`
**Status**: DRAFT
**Author**: Codex (via ChatGPT)
**Created**: 2025-01-15

## Why

The frontend contains vestigial navigation items (e.g., "Users") and API helpers that are never exercised, confusing contributors about expected flows. Several components mention or expect authentication states even though the backend hardcodes a demo user, leading to mismatched expectations during UI testing. Maintaining unused auth code increases cognitive load and creates false impressions that security features exist when they do not.

## What Changes

1. **Delete Frontend Auth UI/Logic**
   - Remove any references to login/logout, auth guards, or user management links from the React app.
   - Eliminate unused API client methods and types related to authentication, keeping only the session/image/lesson calls that work with the demo user.
2. **Simplify Navigation & Copy**
   - Update `Layout` navigation to only include supported pages (Dashboard, Images, Settings) and remove "Users" or other admin references.
   - Adjust page copy to clarify that the environment is a single-user demo build.
3. **Prune Backend Hooks**
   - Remove unused auth service imports or dependencies that are no longer exercised now that endpoints rely exclusively on the default user dependency.
   - Remove AuthRateLimitMiddleware and setup endpoint that referenced auth.
4. **Documentation Cleanup**
   - Update README/install docs to explain the auth-free demo mode and remove stale login instructions.

## Impact

- Affected specs: workspace-shell (new capability)
- Affected code: frontend/src/components/Layout.tsx, frontend/src/pages/DashboardPage.tsx, backend/api/main.py, backend/api/middleware.py, backend/api/dependencies.py, README.md
