# Spec Delta: Desktop Auto Update

## ADDED Requirements

### Requirement: Auto-Update Mechanism
The system SHALL automatically check for, download, and install application updates using electron-updater.

#### Scenario: Update check on startup
- **WHEN** the application starts
- **THEN** it checks for updates from GitHub Releases within 5 seconds
- **AND** checks occur silently without blocking the UI
- **AND** update checks respect the user's configured frequency (default: daily)
- **AND** update checks can be disabled in Settings (opt-out)

#### Scenario: Update available notification
- **WHEN** a newer version is available on GitHub Releases
- **THEN** the system shows a notification: "Update available: v0.5.0"
- **AND** clicking the notification opens the update dialog
- **AND** the dialog shows release notes from GitHub Release description
- **AND** options include "Download Update", "Remind Me Later", "Skip This Version"

#### Scenario: Update downloads in background
- **WHEN** user clicks "Download Update"
- **THEN** the update downloads in the background while the app remains usable
- **AND** progress is shown in a subtle UI indicator (e.g., menu bar icon badge)
- **AND** download can be paused and resumed
- **AND** if download fails, it retries up to 3 times

#### Scenario: Update installs on quit (macOS)
- **WHEN** update download completes on macOS
- **THEN** the system shows notification: "Update ready. Will install when you quit."
- **AND** when user quits the app, update installs automatically
- **AND** the new version launches after installation
- **AND** user data and settings are preserved
- **AND** the system re-runs code signing and notarization verification

### Requirement: Update Security and Verification
The system SHALL verify update integrity and authenticity before installation.

#### Scenario: Code signature verification
- **WHEN** an update is downloaded
- **THEN** the system verifies the code signature matches the publisher
- **AND** unsigned or mismatched updates are rejected
- **AND** users see error: "Update verification failed. Your current version is safe."
- **AND** the error is logged with details for debugging

#### Scenario: Checksum verification
- **WHEN** an update is downloaded
- **THEN** the system verifies the file checksum (SHA256) against GitHub Release metadata
- **AND** corrupted downloads are rejected
- **AND** if verification fails, the download retries automatically

#### Scenario: Staged rollout protection
- **WHEN** a new version is released
- **THEN** updates are rolled out gradually (10% day 1, 50% day 2, 100% day 3)
- **AND** if crash rate exceeds threshold, rollout pauses automatically
- **AND** users can opt-in to "Beta" channel for immediate updates

### Requirement: Update Rollback and Recovery
The system SHALL provide rollback mechanisms for failed or problematic updates.

#### Scenario: Automatic rollback on crash loop
- **WHEN** the app crashes on startup 3 times consecutively
- **THEN** the system detects the crash loop
- **AND** automatically rolls back to the previous version
- **AND** shows dialog: "Update caused issues. Rolled back to v0.4.0."
- **AND** logs the crash details for developer investigation

#### Scenario: Manual rollback option
- **WHEN** user experiences issues after update
- **THEN** the Help menu includes "Revert to Previous Version"
- **AND** selecting it restores the backed-up previous version
- **AND** user data and settings are preserved
- **AND** the system shows confirmation: "Reverted to v0.4.0. You can update again later."

#### Scenario: Backup cleanup
- **WHEN** a new update installs successfully and runs without issues for 7 days
- **THEN** the previous version backup is deleted automatically
- **AND** disk space is reclaimed
- **AND** rollback is no longer available (update is considered stable)

### Requirement: Release Notes and Changelog
The system SHALL display release notes and changelog information for available updates.

#### Scenario: Release notes in update dialog
- **WHEN** an update is available
- **THEN** the update dialog shows the GitHub Release description
- **AND** release notes are formatted as Markdown
- **AND** headings, lists, and links render correctly
- **AND** images in release notes are displayed (if included)

#### Scenario: Changelog viewer in Help menu
- **WHEN** user selects "What's New" from Help menu
- **THEN** a dialog shows the changelog for the current version
- **AND** users can scroll through previous versions' changes
- **AND** each entry includes version number, date, and changes
- **AND** links to GitHub Release page work correctly

#### Scenario: Breaking changes highlighted
- **WHEN** release notes contain breaking changes
- **THEN** breaking changes are highlighted in red or with a warning icon
- **AND** users must acknowledge breaking changes before updating
- **AND** migration instructions are provided (if applicable)

### Requirement: Update Settings and Preferences
The system SHALL allow users to configure update behavior via Settings.

#### Scenario: Update frequency setting
- **WHEN** user opens Settings > Updates
- **THEN** options include "Check daily" (default), "Check weekly", "Check manually", "Never check"
- **AND** changing the setting takes effect immediately
- **AND** "Never check" shows warning: "You will not receive important security updates"

#### Scenario: Auto-download setting
- **WHEN** user opens Settings > Updates
- **THEN** toggle exists: "Automatically download updates" (default: ON)
- **AND** if OFF, updates are announced but not downloaded automatically
- **AND** user must click "Download Update" manually

#### Scenario: Update channel setting
- **WHEN** user opens Settings > Updates
- **THEN** dropdown shows "Stable" (default) and "Beta" channels
- **AND** switching to Beta channel shows warning about instability
- **AND** Beta channel receives updates before Stable (for testing)
- **AND** switching back to Stable channel requires confirmation

#### Scenario: Manual update check
- **WHEN** user selects "Check for Updates" from Help menu
- **THEN** the system checks for updates immediately
- **AND** shows result: "You're up to date" or "Update available: v0.5.0"
- **AND** bypasses the configured frequency setting (force check)

### Requirement: Update Build and Publishing
The system SHALL automate the build and publishing of updates via CI/CD.

#### Scenario: Automated builds on release
- **WHEN** a new Git tag is pushed (e.g., v0.5.0)
- **THEN** GitHub Actions builds the app for macOS, Windows, and Linux
- **AND** code signs the builds with certificates from GitHub Secrets
- **AND** uploads artifacts to GitHub Releases (draft)
- **AND** generates release notes from commit messages (template)

#### Scenario: macOS release artifacts structure
- **WHEN** a release is published on GitHub for macOS
- **THEN** it includes:
  - `PocketMusec-0.5.0.dmg` (DMG installer for direct download)
  - `PocketMusec-0.5.0-mac.zip` (ZIP for universal binary distribution)
  - `latest-mac.yml` (metadata for electron-updater auto-update)
- **AND** all artifacts are code signed and notarized
- **AND** release is marked as "latest" for auto-update discovery
- **AND** release includes notarization status confirmation

#### Scenario: Delta updates for efficiency
- **WHEN** an update is available
- **THEN** electron-updater downloads only changed files (delta update)
- **AND** download size is minimized (e.g., 5MB instead of 200MB for small changes)
- **AND** delta updates are generated automatically during build
- **AND** if delta fails, falls back to full update download

### Requirement: Update Error Handling
The system SHALL handle update failures gracefully and provide recovery options.

#### Scenario: Network error during update check
- **WHEN** update check fails due to network error
- **THEN** the system logs the error silently
- **AND** no error notification is shown to user (avoid spam)
- **AND** next update check is scheduled according to frequency setting

#### Scenario: Download interrupted
- **WHEN** update download is interrupted (network loss, app quit)
- **THEN** the download resumes from where it left off on next launch
- **AND** partial download is not discarded
- **AND** if download fails 3 times, user is notified and can retry manually

#### Scenario: Installation fails
- **WHEN** update installation fails (permissions error, disk full)
- **THEN** the system shows error dialog with specific reason
- **AND** provides troubleshooting steps (e.g., "Free up disk space")
- **AND** previous version remains intact (rollback not needed)
- **AND** user can retry installation or download manually from website

#### Scenario: Update server unreachable
- **WHEN** GitHub Releases is unreachable (outage, firewall)
- **THEN** the system shows notification: "Unable to check for updates. Will retry later."
- **AND** retries automatically on next scheduled check
- **AND** provides option to "Check Now" for manual retry
- **AND** logs the error for debugging

### Requirement: Update Notifications and UX
The system SHALL provide non-intrusive update notifications that don't disrupt workflow.

#### Scenario: Subtle update notification
- **WHEN** an update is available
- **THEN** a badge appears on the Help menu or system tray icon
- **AND** a banner appears at the top of the window (dismissible)
- **AND** no modal dialog blocks the user unless explicitly opened
- **AND** notifications can be snoozed for 24 hours

#### Scenario: Update during active work (macOS)
- **WHEN** user is actively generating a lesson and update finishes downloading on macOS
- **THEN** the system does NOT interrupt the workflow
- **AND** waits until lesson generation completes
- **AND** shows notification: "Update ready. Install when you're done."
- **AND** installation is deferred until app quit
- **AND** the red close button (traffic light) shows notification badge

#### Scenario: Critical security update
- **WHEN** a critical security update is available (marked in release metadata)
- **THEN** the system shows a modal dialog immediately
- **AND** the dialog emphasizes urgency: "Critical security update available"
- **AND** strongly encourages immediate installation
- **AND** provides "Update Now" (recommended) and "Remind Me in 1 Hour" options
