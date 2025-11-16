# lesson-presentations Specification

## Purpose
TBD - created by archiving change add-lesson-presentations. Update Purpose after archive.
## Requirements
### Requirement: Presentation Document Schema
The system SHALL define a structured `PresentationDocument` that maps each lesson into ordered slides with teacher scripts and metadata traceable to `LessonDocumentM2` content.

#### Scenario: Build presentation document
Given a completed `LessonDocumentM2`
When a presentation is generated
Then the resulting document includes lesson identifiers, revision, timestamps, and at least the following slides: title/overview, learning objectives, warmup, one per activity, assessment, differentiation/closure
And each slide lists `title`, `key_points`, `teacher_script`, optional `visual_prompt`, and the source activity/section reference.

### Requirement: Presentation Generation Flow
The system SHALL convert lessons into presentations via a deterministic scaffold and MAY optionally refine slide copy using the configured LLM, falling back gracefully when offline.

#### Scenario: Deterministic scaffold
Given LessonDocument content is available
When presentation generation starts
Then the service produces a complete slide deck without external calls by mapping lesson sections to slides and summarizing key details.

#### Scenario: LLM refinement
Given the workspace has LLM access
When the optional refinement step runs
Then the returned JSON-enhanced slides replace the scaffold text while maintaining structure
And if the LLM call fails or times out, the scaffolded slides are preserved without surfacing an error to the user beyond a warning message.

### Requirement: Presentation Storage and Versioning
The system SHALL persist each generated presentation, link it to the originating lesson revision, and detect when the deck becomes stale because the lesson changed.

#### Scenario: Persist and mark stale
Given a lesson is edited after a presentation exists
When the revision increases
Then the previous presentation remains stored but is marked stale/incompatible
And requesting the latest presentation prompts regeneration before exposing updated slides.

### Requirement: Teacher Access to Presentations
The system SHALL expose APIs and UI affordances for teachers to request, view, and export presentations with accompanying scripts.

#### Scenario: Request and preview deck
Given a saved lesson draft
When the teacher selects "Generate presentation"
Then the backend queues generation and the UI reflects progress until a deck is ready
And once available, the teacher can browse slide titles, see key points plus scripts, and copy/download the data (JSON/Markdown at minimum).

#### Scenario: Regenerate on demand
Given a stale or outdated presentation exists for a lesson
When the teacher clicks "Regenerate"
Then the system produces a new deck tied to the latest lesson revision and replaces the previous "stale" indicator in the UI.

