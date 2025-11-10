# Specification: Lesson Generation

## ADDED Requirements

### Requirement: PocketFlow Agent Framework
The system SHALL implement a minimalist agent framework for lesson generation.

#### Scenario: Agent initialization
Given the PocketFlow framework with Node, Flow, and Store components
When a LessonAgent is instantiated
Then it initializes with access to standards repository
And connects to the Chutes LLM client
And maintains conversation state in the Store

#### Scenario: Message processing flow
Given an agent receiving a user message
When the message is processed
Then it flows through the defined nodes in sequence
And each node can access and modify the Store
And the final response is returned to the user

### Requirement: Standards-Aligned Generation
The system MUST generate lesson plans that align with selected NC standards.

#### Scenario: Generate lesson for specific standard
Given a teacher selects grade "K" and strand "CN"
And chooses standard "K.CN.1" with its objectives
When lesson generation is triggered
Then the LLM prompt includes the full standard text
And objectives are incorporated into lesson activities
And the output explicitly references the standard ID

#### Scenario: Multi-standard lesson
Given a teacher selects multiple standards (e.g., "K.CN.1", "K.CN.2")
When generating the lesson
Then activities address all selected standards
And the lesson plan notes which activities align to which standards
And time is appropriately distributed across objectives

### Requirement: Lesson Plan Structure
Generated lessons MUST follow the defined template with required fields.

#### Scenario: Complete lesson output
Given successful generation for a kindergarten Connect strand lesson
When the lesson is created
Then it includes all required fields:
- Title (descriptive and grade-appropriate)
- Grade Level (matching selection)
- Duration (realistic timeframe)
- Objectives (learning goals)
- Materials (required resources)
- Standards Alignment (selected standards)
- Procedure/Steps (detailed activities)
- Assessment (evaluation methods)
- Differentiation (accommodations)
- Extensions (enrichment options)
- References (source citations if RAG used)

#### Scenario: Markdown formatting
Given a generated lesson plan
When output to the teacher
Then it uses clean Markdown formatting
And sections are clearly delineated with headers
And lists and emphasis are properly formatted

### Requirement: LLM Integration
The system SHALL reliably interface with Chutes API for generation.

#### Scenario: Successful API call
Given valid Chutes API credentials in environment
When requesting lesson generation
Then the system constructs a detailed prompt with context
And sends the request to Chutes API
And streams the response in real-time
And handles the complete response

#### Scenario: API error handling
Given a Chutes API request
When the API returns an error or timeout
Then the system retries up to 3 times with exponential backoff
And provides clear error message if all retries fail
And preserves partial work in session

### Requirement: Context Enhancement
The system MUST provide rich context to improve lesson quality.

#### Scenario: Additional context integration
Given a teacher provides additional context (theme, materials, student needs)
When generating the lesson
Then this context is woven into the prompt
And influences activity selection and differentiation
And is reflected in the final lesson plan

#### Scenario: Grade-appropriate content
Given a selected grade level
When generating lesson content
Then vocabulary matches grade-level expectations
And activity complexity is developmentally appropriate
And time allocations reflect attention spans