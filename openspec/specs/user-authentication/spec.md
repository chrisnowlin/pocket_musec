# user-authentication Specification

## Purpose
TBD - created by archiving change implement-milestone3-advanced-features. Update Purpose after archive.
## Requirements
### Requirement: User Registration and Account Management

The system SHALL support user registration, account management, and role-based access control with Teacher and Admin roles.

#### Scenario: Admin creates teacher account
- **WHEN** an administrator creates a new user account
- **THEN** the admin SHALL provide email, password, full name, and role
- **AND** the system SHALL validate email uniqueness
- **AND** the system SHALL hash the password using bcrypt (cost factor 12)
- **AND** the system SHALL send a welcome email (if email configured)

#### Scenario: Password complexity validation
- **WHEN** creating or changing a password
- **THEN** the password SHALL be at least 8 characters long
- **AND** the password SHALL contain at least one uppercase letter
- **AND** the password SHALL contain at least one lowercase letter
- **AND** the password SHALL contain at least one number
- **AND** the system SHALL reject weak passwords with clear error messages

#### Scenario: Account deactivation
- **WHEN** an administrator deactivates a user account
- **THEN** the user SHALL no longer be able to log in
- **AND** the user's existing sessions SHALL be invalidated
- **AND** the user's lessons SHALL remain in the database
- **AND** the account can be reactivated later

### Requirement: Login and Authentication

The system SHALL authenticate users with email and password, issuing JWT access and refresh tokens upon successful login.

#### Scenario: Successful login
- **WHEN** a teacher enters valid email and password
- **THEN** the system SHALL verify the password against the stored bcrypt hash
- **AND** the system SHALL generate a JWT access token (15-minute expiration)
- **AND** the system SHALL generate a JWT refresh token (7-day expiration)
- **AND** the system SHALL return both tokens to the client
- **AND** the system SHALL update the user's last_login timestamp

#### Scenario: Invalid credentials
- **WHEN** a teacher enters incorrect email or password
- **THEN** the system SHALL return a generic error: "Invalid email or password"
- **AND** the system SHALL not reveal whether email exists
- **AND** the system SHALL log the failed attempt
- **AND** the system SHALL increment failed login counter

#### Scenario: Account lockout after failed attempts
- **WHEN** a user fails login 5 times within 10 minutes
- **THEN** the system SHALL temporarily lock the account for 15 minutes
- **AND** the system SHALL display: "Account temporarily locked due to multiple failed attempts"
- **AND** the system SHALL log the lockout event
- **AND** the account SHALL automatically unlock after 15 minutes

### Requirement: JWT Token Management

The system SHALL use JWT tokens for stateless authentication with access and refresh token rotation.

#### Scenario: JWT token structure
- **WHEN** generating a JWT access token
- **THEN** the token SHALL include claims: sub (user ID), email, role, exp (expiration), iat (issued at)
- **AND** the token SHALL be signed with HS256 algorithm
- **AND** the secret key SHALL be at least 256 bits
- **AND** the token SHALL be transmitted in Authorization header as "Bearer <token>"

#### Scenario: Token validation on requests
- **WHEN** a client makes an authenticated API request
- **THEN** the system SHALL extract the access token from Authorization header
- **AND** the system SHALL verify the token signature
- **AND** the system SHALL check token expiration
- **AND** if valid, the request SHALL proceed with user context
- **AND** if invalid or expired, the system SHALL return 401 Unauthorized

#### Scenario: Token refresh
- **WHEN** an access token expires
- **AND** the client sends a valid refresh token
- **THEN** the system SHALL generate a new access token
- **AND** the system SHALL generate a new refresh token (rotation)
- **AND** the system SHALL invalidate the old refresh token
- **AND** the system SHALL return both new tokens

### Requirement: Role-Based Access Control

The system SHALL enforce role-based permissions with Teacher and Admin roles.

#### Scenario: Teacher role permissions
- **WHEN** a user has the "teacher" role
- **THEN** they SHALL access lesson generation, standards search, image upload
- **AND** they SHALL view and edit only their own lessons
- **AND** they SHALL view only their own session history
- **AND** they SHALL NOT access user management or admin functions

#### Scenario: Admin role permissions
- **WHEN** a user has the "admin" role
- **THEN** they SHALL have all teacher permissions
- **AND** they SHALL create, edit, and delete user accounts
- **AND** they SHALL view aggregate usage statistics
- **AND** they SHALL configure system-wide settings
- **AND** they SHALL NOT view other teachers' lesson content (privacy)

#### Scenario: Unauthorized access attempt
- **WHEN** a teacher attempts to access an admin-only endpoint
- **THEN** the system SHALL return 403 Forbidden
- **AND** the system SHALL log the unauthorized attempt
- **AND** the system SHALL display: "You do not have permission to access this resource"

### Requirement: Session Isolation and Data Privacy

The system SHALL isolate user sessions and ensure teachers can only access their own data.

#### Scenario: Lesson query filtering by user
- **WHEN** a teacher requests their lesson history
- **THEN** the system SHALL filter lessons by user_id
- **AND** the system SHALL NOT return lessons from other teachers
- **AND** the SQL query SHALL include WHERE user_id = <current_user_id>

#### Scenario: Session isolation
- **WHEN** a teacher views active sessions
- **THEN** the system SHALL show only sessions created by that teacher
- **AND** the system SHALL NOT show sessions from other teachers
- **AND** session IDs SHALL be UUIDs to prevent enumeration attacks

#### Scenario: Cross-user access prevention
- **WHEN** a teacher attempts to access another teacher's lesson by ID
- **THEN** the system SHALL check lesson ownership
- **AND** if not owned by current user and not admin, return 404 Not Found
- **AND** the system SHALL NOT reveal that the lesson exists

### Requirement: Logout and Session Termination

The system SHALL support secure logout with token invalidation and automatic session timeout.

#### Scenario: Manual logout
- **WHEN** a teacher clicks the logout button
- **THEN** the client SHALL discard access and refresh tokens
- **AND** the system SHALL add the refresh token to a revocation list
- **AND** the user SHALL be redirected to the login page
- **AND** any in-progress generations SHALL be stopped

#### Scenario: Automatic session timeout
- **WHEN** a user is inactive for 2 hours
- **THEN** the access token SHALL expire naturally (15 min)
- **AND** the refresh token SHALL not be used automatically
- **AND** the user SHALL be prompted to log in again
- **AND** the system SHALL preserve unsaved work in browser storage

#### Scenario: Token revocation check
- **WHEN** validating a refresh token
- **THEN** the system SHALL check if the token is in the revocation list
- **AND** if revoked, the system SHALL return 401 Unauthorized
- **AND** the user SHALL be required to log in again

### Requirement: Password Management

The system SHALL allow users to change passwords and administrators to reset passwords for other users.

#### Scenario: User password change
- **WHEN** a teacher changes their own password
- **THEN** the system SHALL require the current password
- **AND** the system SHALL validate the new password complexity
- **AND** the system SHALL hash the new password with bcrypt
- **AND** the system SHALL invalidate all existing tokens for that user
- **AND** the system SHALL require immediate re-login

#### Scenario: Admin password reset
- **WHEN** an administrator resets a user's password
- **THEN** the admin SHALL set a temporary password
- **AND** the system SHALL mark the account as "password_must_change"
- **AND** the user SHALL be forced to change password on next login
- **AND** the system SHALL notify the user via email (if configured)

#### Scenario: Forgot password (future)
- **WHEN** a teacher forgets their password
- **THEN** the system SHALL display a message to contact administrator
- **NOTE**: Self-service password reset requires email configuration, defer to Milestone 4

### Requirement: Security Hardening

The system SHALL implement security best practices including HTTPS enforcement, rate limiting, and CSRF protection.

#### Scenario: HTTPS enforcement in production
- **WHEN** deploying to production
- **THEN** the system SHALL reject HTTP requests
- **AND** the system SHALL redirect HTTP to HTTPS automatically
- **AND** the system SHALL set HSTS header (max-age=31536000)

#### Scenario: Rate limiting on auth endpoints
- **WHEN** processing login requests
- **THEN** the system SHALL limit to 5 attempts per minute per IP
- **AND** the system SHALL limit to 20 attempts per hour per IP
- **AND** rate-limited requests SHALL return 429 Too Many Requests
- **AND** the response SHALL include Retry-After header

#### Scenario: CSRF protection
- **WHEN** processing state-changing requests (POST, PUT, DELETE)
- **THEN** the system SHALL validate CSRF tokens
- **AND** tokens SHALL be generated per-session
- **AND** tokens SHALL be included in forms and AJAX requests
- **AND** invalid tokens SHALL result in 403 Forbidden

### Requirement: Audit Logging

The system SHALL log security-relevant events for compliance and troubleshooting.

#### Scenario: Login event logging
- **WHEN** a user logs in (successfully or failed attempt)
- **THEN** the system SHALL log: timestamp, user email, IP address, user agent, result
- **AND** logs SHALL NOT contain passwords
- **AND** logs SHALL be stored securely with limited access

#### Scenario: Privilege escalation logging
- **WHEN** an administrator performs an admin action
- **THEN** the system SHALL log: timestamp, admin user, action, target user (if applicable)
- **AND** actions SHALL include: user creation, role change, password reset, account deactivation

#### Scenario: Security event logging
- **WHEN** security-relevant events occur
- **THEN** the system SHALL log: unauthorized access attempts, rate limit hits, suspicious activity
- **AND** administrators SHALL be able to review security logs
- **AND** logs SHALL be retained for at least 90 days

### Requirement: Multi-User UI Components

The system SHALL provide user interface components for login, user management, and profile settings.

#### Scenario: Login page
- **WHEN** an unauthenticated user accesses the application
- **THEN** they SHALL be redirected to the login page
- **AND** the page SHALL include email and password fields
- **AND** the page SHALL include a "Remember Me" option (uses refresh token)
- **AND** the page SHALL show clear error messages on failed login

#### Scenario: User profile page
- **WHEN** a teacher accesses their profile
- **THEN** they SHALL view their email, full name, role, and account creation date
- **AND** they SHALL be able to change their password
- **AND** they SHALL be able to update their full name
- **AND** they SHALL view their processing mode preference

#### Scenario: Admin user management page
- **WHEN** an administrator accesses user management
- **THEN** they SHALL see a list of all users with email, name, role, status
- **AND** they SHALL be able to create new users
- **AND** they SHALL be able to edit existing users (name, role, status)
- **AND** they SHALL be able to deactivate/reactivate accounts
- **AND** they SHALL be able to reset passwords

### Requirement: Backward Compatibility and Migration

The system SHALL support migration from single-user (Milestone 2) to multi-user (Milestone 3) deployments.

#### Scenario: First-time setup
- **WHEN** the system is started for the first time in Milestone 3
- **AND** no users exist in the database
- **THEN** the system SHALL prompt to create an initial admin account
- **AND** the admin SHALL set email, password, and full name
- **AND** this admin SHALL be able to create additional users

#### Scenario: Migration from Milestone 2
- **WHEN** upgrading from Milestone 2 to Milestone 3
- **AND** existing lessons and sessions exist without user_id
- **THEN** the migration script SHALL create a default admin account
- **AND** all existing lessons SHALL be assigned to the default admin
- **AND** the system SHALL notify the admin to create proper accounts

#### Scenario: Single-user mode (optional)
- **WHEN** deploying for a single teacher
- **THEN** the system SHALL support a "single-user mode" configuration flag
- **AND** in single-user mode, login SHALL be skipped
- **AND** all operations SHALL use the default user account
- **AND** multi-user features SHALL be hidden from UI

