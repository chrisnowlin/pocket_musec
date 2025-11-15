# Model Selection Feature

## Overview
The model selection feature allows users to choose between different AI models when using Cloud processing mode. This enables teachers to select models based on their specific needs for speed, reasoning capability, or cost.

## Available Models

### Qwen3-VL (Default) ⭐
- **ID**: `Qwen/Qwen3-VL-235B-A22B-Instruct`
- **Capabilities**: Text, Vision
- **Description**: High-quality multimodal model with vision capabilities
- **Best for**: Standard lesson planning with image support
- **Speed**: ~30 seconds per lesson

### Kimi K2 Thinking
- **ID**: `moonshotai/Kimi-K2-Thinking`
- **Capabilities**: Text, Reasoning
- **Description**: Advanced reasoning model with step-by-step thinking
- **Best for**: Complex lesson plans requiring deeper pedagogical reasoning
- **Speed**: Variable (depends on complexity)

## Usage

### In the Web Interface

1. **Navigate to Chat**: Open a lesson planning session
2. **Locate Model Selector**: Find the dropdown below the "Lesson Planning Chat" heading
3. **Select Model**: Choose from available models in the dropdown
4. **Confirm Selection**: The model is automatically updated for the session

### Model Selection Display
- **Current Model**: Shows the currently selected model name
- **Description**: Displays model capabilities below the dropdown
- **Capabilities Tags**: Shows what the model can do (text, vision, reasoning)
- **Availability**: Grayed out models are currently unavailable

### Persistence
- Model selection is saved per chat session
- When you return to a session, your model choice is preserved
- Starting a new session uses the default model (Qwen3-VL)

## API Usage

### Get Available Models
```http
GET /api/sessions/{session_id}/models
```

**Response:**
```json
{
  "available_models": [
    {
      "id": "Qwen/Qwen3-VL-235B-A22B-Instruct",
      "name": "Qwen3-VL (Default)",
      "description": "High-quality multimodal model with vision capabilities",
      "capabilities": ["text", "vision"],
      "available": true,
      "recommended": true
    },
    {
      "id": "moonshotai/Kimi-K2-Thinking",
      "name": "Kimi K2 Thinking",
      "description": "Advanced reasoning model with step-by-step thinking",
      "capabilities": ["text", "reasoning"],
      "available": true,
      "recommended": false
    }
  ],
  "current_model": "Qwen/Qwen3-VL-235B-A22B-Instruct",
  "processing_mode": "cloud"
}
```

### Update Selected Model
```http
PUT /api/sessions/{session_id}/models
Content-Type: application/json

{
  "selected_model": "moonshotai/Kimi-K2-Thinking"
}
```

**Response:**
```json
{
  "id": "session-id",
  "grade_level": "Grade 3",
  "strand_code": "Connect",
  "selected_model": "moonshotai/Kimi-K2-Thinking",
  ...
}
```

## Model Selection During Chat

### Behavior
- **During Message Generation**: Model selection is disabled to prevent state inconsistency
- **Between Messages**: Model can be changed freely
- **Model Change Effect**: Next message uses the newly selected model
- **Previous Messages**: Already generated messages are not affected

### Visual Feedback
- **Loading State**: Shows spinner while fetching available models
- **Disabled State**: Dropdown is grayed out during generation
- **Error State**: Displays error message if model fetch/update fails

## Error Handling

### Common Errors

**Model Not Available**
```
Error: Model moonshotai/Kimi-K2-Thinking is not available
```
- **Cause**: Selected model is not in available models list
- **Solution**: Choose a different model from the dropdown

**Model Update Failed**
```
Error: Failed to update model: Network error
```
- **Cause**: Network connectivity issue or server error
- **Solution**: Check internet connection and try again

**No Models Available**
```
Warning: No models available
```
- **Cause**: Not in Cloud mode or API credentials missing
- **Solution**: Verify Cloud mode is enabled and CHUTES_API_KEY is configured

## Processing Mode Considerations

### Cloud Mode Only
- Model selection is only available in Cloud processing mode
- Local mode uses the configured Ollama model (not switchable via UI)
- The model selector is hidden when in Local mode

### Mode Switching
- Switching from Local to Cloud: Default model is used
- Switching from Cloud to Local: Model preference is preserved for when you return to Cloud mode

## Best Practices

1. **Choose the Right Model**:
   - Use Qwen3-VL for standard lessons and when images are involved
   - Use Kimi K2 Thinking for complex pedagogical reasoning

2. **Model Persistence**:
   - Your model choice persists within a session
   - New sessions start with the default model

3. **Performance**:
   - Different models have different response times
   - More capable models may take longer to generate responses

4. **Cost Awareness**:
   - Different models have different API costs
   - Qwen3-VL is the default balanced option
   - Kimi K2 Thinking may incur higher costs for complex reasoning

## Troubleshooting

### Model Selector Not Appearing
- **Check**: Verify you're in Cloud processing mode
- **Check**: Ensure you have an active session
- **Check**: Confirm CHUTES_API_KEY is configured

### Model Changes Not Taking Effect
- **Wait**: Ensure message generation is complete
- **Refresh**: Try refreshing the model list
- **Check**: Verify the session was updated successfully

### Models Show as Unavailable
- **Check**: Verify Chutes API credentials are valid
- **Check**: Ensure internet connectivity
- **Contact**: Administrator if issue persists

## Technical Details

### Database Schema
```sql
ALTER TABLE sessions ADD COLUMN selected_model TEXT;
```

### Session Model
```python
@dataclass
class Session:
    id: str
    user_id: str
    selected_model: Optional[str] = None
    ...
```

### LLM Integration
The selected model is passed to the LLM client during chat completion:
```python
response = self.llm_client.chat_completion(
    messages=messages,
    temperature=temperature,
    max_tokens=max_tokens,
    model=self.selected_model,  # Uses session's selected model
)
```

## Future Enhancements

Potential future improvements:
- Model-specific temperature and token limits
- Model usage statistics and cost tracking
- Custom model configurations
- Model performance comparisons
- Auto-selection based on query complexity
