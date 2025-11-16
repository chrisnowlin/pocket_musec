## Context
The current system supports processing mode switching (Cloud/Local) but doesn't allow users to select specific models within the Cloud mode. Users want granular control over model selection directly from the chat interface, similar to other AI chat platforms like ChatGPT, Claude, and GitHub Copilot.

## Goals / Non-Goals
- Goals: Enable dynamic model selection from chat UI, add Kimi-K2-Thinking model option, persist model preferences per session
- Non-Goals: Complete model management system, model fine-tuning capabilities, custom model hosting

## Decisions
- Decision: Extend existing ModelRouter rather than create new model management system
- Rationale: Leverages existing infrastructure, maintains consistency with current architecture
- Decision: Store model preference in session data rather than global user settings
- Rationale: Allows per-conversation model selection, simpler implementation for demo mode
- Decision: Add model validation before chat completion
- Rationale: Prevents errors from unavailable models, provides better UX

## Risks / Trade-offs
- Risk: Model switching during active generation could cause state inconsistency
- Mitigation: Disable model switching during generation, queue changes for next message
- Trade-off: Additional API calls for model availability checking vs. stale model information
- Decision: Implement caching with periodic refresh to balance performance and accuracy

## Migration Plan
1. Extend backend ModelRouter with multi-model support
2. Update session schema to include selected_model field
3. Add model selection UI component to frontend
4. Implement model preference persistence
5. Add comprehensive testing for model switching scenarios

## Open Questions
- Should model preferences persist across different chat sessions or be per-conversation?
- How should the system handle model unavailability during an active chat?
- Should there be model-specific configuration (temperature, max_tokens) or use global defaults?