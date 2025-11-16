# Model Selector UI Documentation

## Overview

The Model Selector dropdown in the chat interface dynamically reflects the backend model configuration. It automatically updates when the backend model list changes, requiring no frontend code changes.

## How It Works

### Backend Configuration

The model list is defined in `backend/llm/model_router.py`:

```python
AVAILABLE_CLOUD_MODELS = [
    {
        "id": "moonshotai/Kimi-K2-Thinking",
        "name": "Kimi K2 Thinking (Default)",
        "description": "Advanced reasoning model with step-by-step thinking",
        "capabilities": ["text", "reasoning", "detailed-planning"],
        "recommended": True,  # Shows ⭐ in dropdown
    },
    {
        "id": "Qwen/Qwen3-VL-235B-A22B-Instruct",
        "name": "Qwen3-VL",
        "description": "High-quality multimodal model with vision capabilities",
        "capabilities": ["text", "vision"],
        "recommended": False,
    },
]
```

### Frontend Component

The Model Selector (`frontend/src/components/unified/ModelSelector.tsx`) fetches models from the API:

```typescript
const response = await fetch(`/api/sessions/${sessionId}/models`);
const data: ModelAvailability = await response.json();
```

### API Endpoint

**Endpoint**: `GET /api/sessions/{session_id}/models`

**Response**:
```json
{
  "available_models": [
    {
      "id": "moonshotai/Kimi-K2-Thinking",
      "name": "Kimi K2 Thinking (Default)",
      "description": "...",
      "capabilities": ["text", "reasoning", "detailed-planning"],
      "recommended": true,
      "available": true
    },
    {
      "id": "Qwen/Qwen3-VL-235B-A22B-Instruct",
      "name": "Qwen3-VL",
      "description": "...",
      "capabilities": ["text", "vision"],
      "recommended": false,
      "available": true
    }
  ],
  "current_model": "moonshotai/Kimi-K2-Thinking",
  "processing_mode": "cloud"
}
```

## UI Behavior

### Dropdown Display

The dropdown shows models in the order returned by the API:

```
┌─────────────────────────────────────┐
│ Select a model...                   │
│ Kimi K2 Thinking (Default) ⭐       │ ← Recommended
│ Qwen3-VL                            │
└─────────────────────────────────────┘
```

### Features

1. **Recommended Badge**: Models with `recommended: true` show a ⭐
2. **Default Label**: The default model includes "(Default)" in its name
3. **Availability Status**: Unavailable models show "(Unavailable)" and are disabled
4. **Current Selection**: The selected model is highlighted in the dropdown

## Updating Models

To change the model list or default:

### 1. Update Backend Configuration

Edit `backend/llm/config.py`:

```python
default_model: str = field(
    default_factory=lambda: os.getenv(
        "DEFAULT_MODEL", "moonshotai/Kimi-K2-Thinking"  # Change here
    )
)
```

### 2. Update Model List

Edit `backend/llm/model_router.py`:

```python
AVAILABLE_CLOUD_MODELS = [
    {
        "id": "your-new-model-id",
        "name": "Your Model Name (Default)",
        "description": "Description here",
        "capabilities": ["text", "reasoning"],
        "recommended": True,  # Set to True for ⭐
    },
    # ... other models
]
```

### 3. Update Environment Variable (Optional)

Edit `.env`:

```bash
DEFAULT_MODEL=your-new-model-id
```

### 4. Restart Backend

The frontend will automatically fetch and display the updated model list - **no frontend changes needed**.

## State Management

### Session Model Selection

When a user selects a model:

1. **Optimistic Update**: UI immediately updates for responsiveness
2. **API Call**: `PUT /api/sessions/{session_id}/models` updates the session
3. **Confirmation**: Server response confirms the change
4. **Persistence**: Model selection is saved to the session in the database

### Model Persistence

- Each session stores its selected model in `sessions.selected_model`
- If no model is selected, the default model is used
- Model selection persists across page reloads
- Different sessions can use different models

## Testing Model Selection

### Manual Testing

1. **Start a new conversation**
2. **Check dropdown** - Should show Kimi K2 first with ⭐
3. **Select a different model** - UI should update immediately
4. **Refresh page** - Selection should persist
5. **Start new session** - Should default to Kimi K2

### API Testing

```bash
# Get available models
curl http://localhost:8000/api/sessions/{session_id}/models \
  -H "Authorization: Bearer {token}"

# Update selected model
curl -X PUT http://localhost:8000/api/sessions/{session_id}/models \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"selected_model": "moonshotai/Kimi-K2-Thinking"}'
```

## Current Configuration (as of Nov 16, 2025)

- **Default Model**: `moonshotai/Kimi-K2-Thinking`
- **Recommended**: Kimi K2 Thinking ⭐
- **Also Available**: Qwen3-VL (for vision tasks)
- **Processing Mode**: Cloud

## Troubleshooting

### Dropdown shows old models

**Solution**: Restart the backend server to reload configuration

### Model selection doesn't persist

**Solution**: Check database `sessions` table has `selected_model` column

### "No models available" message

**Solution**: 
- Verify `CHUTES_API_KEY` is set in `.env`
- Check backend logs for API connection errors
- Ensure `model_router.get_available_cloud_models()` returns data

### Wrong model marked as recommended

**Solution**: Update `recommended: true` in `AVAILABLE_CLOUD_MODELS` list

## Related Files

- **Backend Configuration**: `backend/config.py`
- **Model Router**: `backend/llm/model_router.py`
- **API Endpoint**: `backend/api/routes/sessions.py`
- **Frontend Component**: `frontend/src/components/unified/ModelSelector.tsx`
- **Frontend Hook**: `frontend/src/hooks/useSession.ts`
- **Type Definitions**: `frontend/src/types/unified.ts`

## Best Practices

1. **Always update both config.py and model_router.py** when changing defaults
2. **Mark only one model as recommended** to avoid confusion
3. **Include "(Default)" in the name** of the default model
4. **Test model selection** after configuration changes
5. **Document model capabilities** in the description field
6. **Update .env** if changing the default for deployment

---

*Last Updated: November 16, 2025*  
*Current Default: Kimi K2 Thinking*
