# PocketMusec Integration Tests

Comprehensive integration tests for Milestone 3 features.

## Test Coverage

### Authentication Tests (`test_integration_auth.py`)
- User registration (admin only)
- Login/logout flows
- Token refresh mechanism
- Password changes
- Role-based access control
- Rate limiting on auth endpoints

### Image Processing Tests (`test_integration_images.py`)
- Single and batch image upload
- Image retrieval and listing
- Search functionality
- Image deletion
- Storage quota management
- User isolation (users can only access their own images)

### Settings Tests (`test_integration_settings.py`)
- Processing mode listing
- Mode switching (cloud ↔ local)
- Local model status checking
- User preference persistence
- Preference isolation between users

## Running Tests

### Install Test Dependencies

```bash
pip install -e ".[dev]"
```

Or with the new dependency groups:

```bash
pip install --dev
```

### Run All Tests

```bash
pytest
```

### Run Specific Test Files

```bash
# Authentication tests only
pytest backend/tests/test_integration_auth.py

# Image processing tests only
pytest backend/tests/test_integration_images.py

# Settings tests only
pytest backend/tests/test_integration_settings.py
```

### Run Tests by Marker

```bash
# Run only auth tests
pytest -m auth

# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

### Run with Coverage

```bash
pytest --cov=backend --cov-report=html
```

Open `htmlcov/index.html` to view coverage report.

### Run Verbose

```bash
pytest -vv
```

### Run Specific Test Class

```bash
pytest backend/tests/test_integration_auth.py::TestAuthenticationFlow
```

### Run Specific Test Method

```bash
pytest backend/tests/test_integration_auth.py::TestAuthenticationFlow::test_login_success
```

## Test Environment

Tests use temporary databases and storage directories that are automatically cleaned up after each test run. No need for manual cleanup.

### External Dependencies

Some tests may skip or fail if external services are unavailable:

- **Tesseract OCR**: Required for image OCR tests
  - Install: `sudo apt-get install tesseract-ocr` (Ubuntu/Debian)
  - Tests will fail gracefully if not available

- **Ollama**: Required for local mode tests
  - Install: `curl -fsSL https://ollama.com/install.sh | sh`
  - Start: `ollama serve`
  - Download model: `ollama pull qwen2.5:8b`
  - Tests will skip or report unavailable if not running

- **Chutes API**: Required for cloud mode vision tests
  - Set `CHUTES_API_KEY` in `.env`
  - Tests will fail gracefully if not configured

## Test Structure

Each test file contains multiple test classes:

```python
class TestAuthenticationFlow:
    """Test complete authentication workflows."""

    def test_login_success(self, client, admin_user):
        """Test successful login."""
        # Test implementation
```

### Fixtures

Common fixtures available in all tests:

- `test_db`: Temporary SQLite database with migrations applied
- `client`: FastAPI TestClient for making HTTP requests
- `admin_user`: Pre-created admin user
- `admin_token`: Valid JWT token for admin user
- `teacher_user`: Pre-created teacher user (in some tests)
- `teacher_token`: Valid JWT token for teacher user (in some tests)

## Expected Results

### All External Services Available

If Tesseract, Ollama, and Chutes API are all configured:
- All tests should pass
- Some tests may be slow due to actual OCR/AI processing

### Minimal Configuration (No External Services)

Without external services:
- Authentication tests: **All pass**
- Settings tests: **All pass** (with some mode switching limitations)
- Image tests: **Some pass, some fail gracefully**
  - Upload will fail (no OCR/vision)
  - Retrieval, deletion, storage management will pass if no uploads

### Recommended for CI/CD

For continuous integration, we recommend:
- Always run authentication tests (no external deps)
- Always run settings tests (no external deps)
- Mock or skip image processing tests that require external APIs

## Debugging Failed Tests

### View Full Error Output

```bash
pytest --tb=long
```

### Run with Print Statements

```bash
pytest -s
```

### Run Specific Failing Test

```bash
pytest backend/tests/test_integration_auth.py::TestAuthenticationFlow::test_login_wrong_password -vv
```

### Check Test Database

Tests use temporary databases, but you can inspect them by adding a breakpoint:

```python
def test_something(self, test_db):
    import pdb; pdb.set_trace()  # Database path in test_db
    # Run your test
```

## Adding New Tests

### Test File Template

```python
"""
Integration tests for [feature name].

Tests the complete [feature] flow including:
- [Capability 1]
- [Capability 2]
"""

import pytest
from fastapi.testclient import TestClient

class TestFeatureName:
    """Test [feature] functionality."""

    def test_something(self, client, admin_token):
        """Test description."""
        response = client.post(
            "/api/endpoint",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"data": "value"}
        )

        assert response.status_code == 200
        assert response.json()["result"] == "expected"
```

### Best Practices

1. **Use descriptive test names**: `test_teacher_cannot_delete_admin_images`
2. **Test both success and failure**: Test invalid inputs, auth failures, etc.
3. **Use fixtures**: Don't duplicate setup code
4. **Assert specific values**: Not just status codes
5. **Clean up resources**: Let fixtures handle cleanup
6. **Document external dependencies**: Mark tests that need Tesseract, etc.

## Continuous Integration

For CI/CD pipelines, add this to your workflow:

```yaml
- name: Run tests
  run: |
    pip install -e ".[dev]"
    pytest --cov=backend --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Performance

Typical test execution times (with all external services):

- Authentication tests: ~5-10 seconds
- Settings tests: ~3-5 seconds
- Image tests: ~10-30 seconds (depends on OCR/vision processing)

**Total: ~20-45 seconds**

Without external services:

- Authentication tests: ~5 seconds
- Settings tests: ~3 seconds
- Image tests: ~5 seconds (most skip or fail fast)

**Total: ~13 seconds**
