## Why
Users want the ability to switch between different AI models directly from the chat interface to have more control over the generation quality, speed, and cost characteristics. Currently, model selection is limited to configuration files and requires restarting the application.

## What Changes
- Add model selection dropdown in the chat interface 
- Extend backend to support dynamic model switching during chat sessions
- Add moonshotai/Kimi-K2-Thinking as an available Chutes API model option
- Implement model preference persistence per user session
- Add model availability checking and validation

## Impact
- Affected specs: processing-mode-toggle (extend), web-interface (modify)
- Affected code: backend/llm/model_router.py, backend/api/routes/sessions.py, frontend chat components
- **BREAKING**: Changes to session model to include selected model