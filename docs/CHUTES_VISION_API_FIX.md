# Chutes Vision API PDF Processing - Issue Resolution

## Problem Summary

The Chutes API vision models cannot directly process PDF files. They require images to be passed as base64-encoded data with proper multimodal message formatting.

## Root Cause Analysis

### 1. **Message Format Incompatibility**

**Issue**: The `Message` dataclass in `chutes_client.py` only supported string content:

```python
@dataclass
class Message:
    role: str
    content: str  # ❌ Cannot handle multimodal content
```

**Impact**: When trying to send vision requests with images, the code attempted to pass a list of content parts (text + image_url), but the Message class rejected it.

### 2. **Authorization Header Missing "Bearer" Prefix**

**Issue**: The authorization header was set incorrectly:

```python
headers["Authorization"] = self.api_key  # ❌ Missing "Bearer"
```

**Impact**: API returned 404 errors because requests weren't properly authenticated.

### 3. **PDF Files Cannot Be Sent Directly to Vision Models**

**Key Finding**: Vision models require:
- PDFs must be converted to images first (using `pdf2image`)
- Images must be base64-encoded
- Content must be formatted as multimodal message parts

**Your existing code** already does the PDF→Image conversion correctly in:
- `backend/ingestion/nc_standards_unified_parser.py`
- `backend/ingestion/complex_layout_parser.py`

But the `Message` class couldn't handle the multimodal format.

## Solution Implemented

### Step 1: Updated Message Dataclass

**File**: `backend/llm/chutes_client.py` (line 17-24)

**Change**:
```python
@dataclass
class Message:
    """Chat message - supports both text and multimodal content"""
    role: str
    content: Union[str, List[Dict[str, Any]]]  # ✅ Now supports both!
```

This allows passing either:
- Simple string messages: `Message(role="user", content="Hello")`
- Multimodal messages: `Message(role="user", content=[{...}, {...}])`

### Step 2: Fixed Authorization Header

**File**: `backend/llm/chutes_client.py` (line 81-85)

**Change**:
```python
# Before (incorrect):
headers["Authorization"] = self.api_key

# After (correct):
headers["Authorization"] = f"Bearer {self.api_key}"
```

**Why this matters**: The Chutes API requires Bearer token authentication format.

### Step 3: Updated Payload Building

**File**: `backend/llm/chutes_client.py` (line 149-156)

**Change**:
```python
# Build messages payload - handle both string and multimodal content
formatted_messages: List[Dict[str, Any]] = []
for msg in messages:
    formatted_msg: Dict[str, Any] = {"role": msg.role}
    # If content is a list (multimodal), pass it directly
    # If content is a string, pass it as is
    formatted_msg["content"] = msg.content  # type: ignore
    formatted_messages.append(formatted_msg)
```

**Why this works**: The API payload builder now preserves the structure of `content`:
- If it's a string → passes as string
- If it's a list of content parts → passes as list

### Step 4: Use Correct Model Name

**Important**: Use the vision model `Qwen/Qwen3-VL-235B-A22B-Instruct` (not Qwen2-VL-7B-Instruct)

## How to Use Vision Models Correctly

### For PDF Processing:

```python
from pdf2image import convert_from_path
import base64
import io
from backend.llm.chutes_client import ChutesClient, Message

# 1. Convert PDF to images
images = convert_from_path("document.pdf", dpi=150)

# 2. Process each page
for page_num, image in enumerate(images):
    # Convert image to base64
    buffered = io.BytesIO()
    image.save(buffered, format="PNG", optimize=True)
    img_base64 = base64.b64encode(buffered.getvalue()).decode()
    
    # 3. Create multimodal message
    message = Message(
        role="user",
        content=[
            {
                "type": "text",
                "text": "Extract all text from this page"
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{img_base64}"
                }
            }
        ]
    )
    
    # 4. Call vision model (use correct model name!)
    client = ChutesClient()
    response = client.chat_completion(
        messages=[message],
        model="Qwen/Qwen3-VL-235B-A22B-Instruct",  # ✅ Correct model
        max_tokens=2000
    )
```

### For Direct Image Processing:

```python
# If you already have an image file
with open("image.png", "rb") as f:
    image_data = base64.b64encode(f.read()).decode()

message = Message(
    role="user",
    content=[
        {"type": "text", "text": "Describe this image"},
        {
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{image_data}"}
        }
    ]
)

client = ChutesClient()
response = client.chat_completion(
    messages=[message],
    model="Qwen/Qwen3-VL-235B-A22B-Instruct",
    temperature=0.3,
    max_tokens=500
)
```

## Verification

### Quick Test

```bash
cd /Users/cnowlin/Developer/pocket_musec
python3 -c "from backend.llm.chutes_client import ChutesClient, Message; print('✓ Import successful')"
```

### Comprehensive Test

Run the full test suite:

```bash
python3 test_vision_comprehensive.py
```

**Test Results (2025-11-12):**
```
✅ PASS: Text Messages
✅ PASS: Vision with PDF  
✅ PASS: Message Dataclass
🎉 ALL TESTS PASSED! Vision API is fully functional.
```

The vision model successfully extracted all standard IDs from a PDF page:
- K.CN.1.1, K.CN.1.2, K.CN.1.3, K.CN.2.1, K.CN.2.2
- K.CR.1.1, K.CR.1.2, K.CR.2.1, K.CR.2.2  
- K.PR.1.1, K.PR.1.2, K.PR.1.3, K.PR.1.4
- K.RE.1.1, K.RE.1.2, K.RE.2.1, K.RE.2.2

## Key Takeaways

1. **PDFs require conversion**: Vision models need images, not PDF files directly
2. **Multimodal format**: Use list of content parts with `type: "text"` and `type: "image_url"`
3. **Base64 encoding**: Images must be base64-encoded with proper MIME type (e.g., `data:image/png;base64,{data}`)
4. **Message flexibility**: The updated `Message` class now supports both simple and multimodal content
5. **Authorization format**: Must use `Bearer {api_key}` format in Authorization header
6. **Correct model**: Use `Qwen/Qwen3-VL-235B-A22B-Instruct` for vision tasks

## Related Files

- `backend/llm/chutes_client.py` - Core client (fixed)
- `backend/ingestion/nc_standards_unified_parser.py` - PDF parser using vision
- `backend/ingestion/complex_layout_parser.py` - Another PDF parser
- `backend/image_processing/vision_analyzer.py` - Image analysis utility
- `test_vision_comprehensive.py` - Test suite

## References

- [Claude PDF Support Documentation](https://support.claude.com/en/articles/8241126-what-kinds-of-documents-can-i-upload-to-claude)
- [OpenAI Vision + PDF Discussion](https://community.openai.com/t/chat-completions-vs-responses-and-pdf-file/1143115)
- Chutes API follows OpenAI-compatible format for multimodal messages
