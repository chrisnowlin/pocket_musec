# Implementation Tasks: Remove Legacy Auth Components

**Change ID**: `remove-auth-components`

## 1. Frontend Cleanup
- [x] 1.1 Remove unused login/logout helpers, auth guards, and related hooks from the React app
- [x] 1.2 Delete references to the `Users` navigation item and other admin/auth pages that are not implemented
- [x] 1.3 Prune API client methods/types tied to auth endpoints so only active demo-mode calls remain
- [x] 1.4 Sweep for UI copy or tooltips suggesting sign-in/sign-out flows and replace them with demo-mode messaging

## 2. Backend Cleanup
- [x] 2.1 Remove unused imports (e.g., AuthService, JWT utilities) from API routers that already rely on `get_current_user`
- [x] 2.2 Ensure OpenAPI/docs no longer surface disabled auth routes (hide or comment them out if necessary)
- [x] 2.3 Verify default demo-user dependency remains the single path for request context and document that behavior inline

## 3. Documentation Updates
- [x] 3.1 Update README/onboarding docs to clarify the app runs in single-user demo mode without authentication
- [x] 3.2 Remove instructions for setting auth environment variables or seeding users unless they are still needed for backend-only workflows

## 4. Verification
- [x] 4.1 Manually exercise Dashboard, Workspace, Images, and Settings to confirm nothing references removed auth code
- [x] 4.2 Run lint/tests to ensure no leftover unused imports or type errors remain after the cleanup
