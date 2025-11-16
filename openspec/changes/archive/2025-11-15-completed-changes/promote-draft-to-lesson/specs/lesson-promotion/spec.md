# Spec: Lesson Promotion

## ADDED Requirements

### Requirement: Draft Promotion Endpoint
The backend API MUST provide an endpoint to promote a draft lesson to a permanent lesson.

#### Scenario: Successful Promotion
**Given** a draft lesson with `id="draft-123"` owned by the authenticated user
**When** the user calls `POST /api/lessons/draft-123/promote`
**Then** the response status is 200 OK
**And** the returned lesson has `is_draft=false`
**And** the `updated_at` timestamp is refreshed
**And** the lesson remains in the database with the same `id`

#### Scenario: Promote Non-Existent Draft
**Given** no lesson exists with `id="missing-draft"`
**When** the user calls `POST /api/lessons/missing-draft/promote`
**Then** the response status is 404 Not Found
**And** the response body contains an error message "Lesson not found"

#### Scenario: Promote Another User's Draft
**Given** a draft lesson with `id="other-draft"` owned by a different user
**When** the authenticated user calls `POST /api/lessons/other-draft/promote`
**Then** the response status is 404 Not Found
**And** the response body contains an error message "Lesson not found"

### Requirement: Lesson Demotion Endpoint
The backend API MUST provide an endpoint to demote a permanent lesson back to a draft.

#### Scenario: Successful Demotion
**Given** a permanent lesson with `id="lesson-456"` and `is_draft=false` owned by the authenticated user
**When** the user calls `POST /api/lessons/lesson-456/demote`
**Then** the response status is 200 OK
**And** the returned lesson has `is_draft=true`
**And** the `updated_at` timestamp is refreshed
**And** the lesson remains in the database with the same `id`

#### Scenario: Demote Non-Existent Lesson
**Given** no lesson exists with `id="missing-lesson"`
**When** the user calls `POST /api/lessons/missing-lesson/demote`
**Then** the response status is 404 Not Found
**And** the response body contains an error message "Lesson not found"

### Requirement: Permanent Lessons List
The frontend MUST provide a view to browse all permanent lessons (where `is_draft=false`) for the authenticated user.

#### Scenario: View Permanent Lessons
**Given** the user has 3 permanent lessons and 5 drafts
**When** the user navigates to the "My Lessons" tab in MusecDB
**Then** the UI displays exactly 3 lesson cards
**And** each lesson card shows title, grade, strand, and last updated timestamp
**And** no draft lessons appear in this list

#### Scenario: Empty Lessons Library
**Given** the user has no permanent lessons (only drafts)
**When** the user navigates to the "My Lessons" tab
**Then** the UI displays an empty state message "No permanent lessons yet"
**And** the message suggests "Promote a draft to create your first lesson"

### Requirement: Promote Action in Drafts UI
The drafts interface MUST include a "Promote to Lesson" action for each draft.

#### Scenario: Promote Draft from UI
**Given** the user is viewing their saved drafts
**When** the user clicks "Promote to Lesson" on a draft card
**Then** the system calls `POST /api/lessons/{id}/promote`
**And** the draft disappears from the drafts list
**And** a success notification appears: "Draft promoted to lesson"
**And** the promoted lesson now appears in the "My Lessons" tab

#### Scenario: Promotion Failure Handling
**Given** the user clicks "Promote to Lesson" on a draft
**When** the API returns an error (500 Internal Server Error)
**Then** the draft remains in the drafts list
**And** an error notification appears: "Failed to promote draft. Please try again."
**And** the draft's state is unchanged

### Requirement: Demote Action in Lessons UI
The permanent lessons interface MUST include a "Move to Drafts" action for each lesson.

#### Scenario: Demote Lesson from UI
**Given** the user is viewing their permanent lessons
**When** the user clicks "Move to Drafts" on a lesson card
**Then** the system calls `POST /api/lessons/{id}/demote`
**And** the lesson disappears from the lessons list
**And** a success notification appears: "Lesson moved to drafts"
**And** the demoted lesson now appears in the "Saved Drafts" tab

#### Scenario: Demotion Confirmation
**Given** the user clicks "Move to Drafts" on a lesson
**When** the confirmation is required (future enhancement)
**Then** a modal appears asking "Move this lesson to drafts?"
**And** the user can confirm or cancel
**And** only upon confirmation does the demotion occur

### Requirement: Lesson State Persistence
Promotion and demotion MUST preserve all lesson data except the `is_draft` flag and `updated_at` timestamp.

#### Scenario: Data Preservation on Promotion
**Given** a draft lesson with specific title, content, metadata, grade, and strand
**When** the draft is promoted to a permanent lesson
**Then** the lesson retains identical values for title, content, metadata, grade, and strand
**And** only `is_draft` changes from `true` to `false`
**And** `updated_at` is set to the current timestamp
**And** `created_at` remains unchanged

#### Scenario: Data Preservation on Demotion
**Given** a permanent lesson with specific title, content, metadata, grade, and strand
**When** the lesson is demoted to a draft
**Then** the lesson retains identical values for title, content, metadata, grade, and strand
**And** only `is_draft` changes from `false` to `true`
**And** `updated_at` is set to the current timestamp
**And** `created_at` remains unchanged

### Requirement: Search and Filter Parity
The "My Lessons" tab MUST provide search and filter capabilities equivalent to the "Saved Drafts" tab.

#### Scenario: Search Permanent Lessons
**Given** the user has 10 permanent lessons with varying titles
**When** the user types "rhythm" into the search box on the "My Lessons" tab
**Then** only lessons with "rhythm" in the title or content are displayed
**And** the count updates to reflect the filtered results

#### Scenario: Filter by Grade and Strand
**Given** the user has lessons for multiple grades and strands
**When** the user selects "Grade 3" and "Create (CR)" from the filter dropdowns
**Then** only lessons matching both Grade 3 and Create strand are displayed
**And** the filters can be cleared to show all lessons again
