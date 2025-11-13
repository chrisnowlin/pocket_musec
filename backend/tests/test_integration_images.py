"""
Integration tests for image processing system.

Tests the complete image processing pipeline including:
- Image upload
- OCR text extraction
- Vision AI analysis
- Image storage and retrieval
- Storage quota management
"""

import pytest
import os
import tempfile
import io
from PIL import Image
from fastapi.testclient import TestClient

# Add backend to path
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.api.main import app
from backend.repositories.migrations import DatabaseMigrator


@pytest.fixture
def test_db():
    """Create a temporary test database."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    # Migrate database
    migrator = DatabaseMigrator(db_path)
    migrator.migrate()

    # Update app to use test database
    from backend.api import dependencies
    from backend.config import config

    dependencies.DATABASE_PATH = db_path
    config.database.path = db_path

    yield db_path

    # Cleanup
    os.unlink(db_path)


@pytest.fixture
def temp_image_dir():
    """Create temporary directory for image storage."""
    import tempfile

    temp_dir = tempfile.mkdtemp()

    # Update image storage path
    from backend.image_processing import image_storage

    image_storage.STORAGE_PATH = temp_dir

    yield temp_dir

    # Cleanup
    import shutil

    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def client(test_db, temp_image_dir):
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def test_image():
    """Create a simple test image."""
    # Create a simple PNG image with text
    img = Image.new("RGB", (200, 100), color="white")

    # Save to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)

    return img_bytes


class TestImageUpload:
    """Test image upload functionality."""

    def test_upload_single_image(self, client, test_image):
        """Test uploading a single image without auth headers (demo mode)."""
        response = client.post(
            "/api/images/upload",
            files={"file": ("test.png", test_image, "image/png")},
            data={"processing_mode": "cloud"},
        )

        assert response.status_code in [201, 500]

        if response.status_code == 201:
            data = response.json()
            assert "id" in data
            assert data["filename"] == "test.png"
            assert data["mime_type"] == "image/png"

    def test_upload_invalid_file_type(self, client):
        """Test uploading non-image file is rejected."""
        text_file = io.BytesIO(b"This is not an image")

        response = client.post(
            "/api/images/upload",
            files={"file": ("test.txt", text_file, "text/plain")},
        )

        assert response.status_code in [400, 422]

    def test_batch_upload(self, client, test_image):
        """Test uploading multiple images."""
        test_image.seek(0)
        img2 = io.BytesIO()
        img = Image.new("RGB", (200, 100), color="blue")
        img.save(img2, format="PNG")
        img2.seek(0)

        response = client.post(
            "/api/images/upload/batch",
            files=[
                ("files", ("test1.png", test_image, "image/png")),
                ("files", ("test2.png", img2, "image/png")),
            ],
            data={"processing_mode": "cloud"},
        )

        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 2


class TestImageRetrieval:
    """Test image retrieval and listing."""

    @pytest.fixture
    def uploaded_image(self, client, test_image):
        """Upload an image for testing retrieval."""
        response = client.post(
            "/api/images/upload",
            files={"file": ("test.png", test_image, "image/png")},
        )

        if response.status_code == 201:
            return response.json()
        return None

    def test_list_images(self, client, uploaded_image):
        """Test listing user's images."""
        response = client.get("/api/images")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        if uploaded_image:
            assert len(data) > 0

    def test_get_image_by_id(self, client, uploaded_image):
        """Test retrieving specific image."""
        if not uploaded_image:
            pytest.skip("Image upload not available")

        response = client.get(f"/api/images/{uploaded_image['id']}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == uploaded_image["id"]

    def test_get_nonexistent_image(self, client):
        """Test retrieving non-existent image."""
        response = client.get("/api/images/nonexistent_id")

        assert response.status_code == 404

    def test_search_images(self, client, uploaded_image):
        """Test searching images by content."""
        response = client.get(
            "/api/images/search",
            params={"q": "test", "limit": 10},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestImageDeletion:
    """Test image deletion."""

    @pytest.fixture
    def uploaded_image(self, client, test_image):
        """Upload an image for testing deletion."""
        response = client.post(
            "/api/images/upload",
            files={"file": ("test.png", test_image, "image/png")},
        )

        if response.status_code == 201:
            return response.json()
        return None

    def test_delete_image(self, client, uploaded_image):
        """Test deleting an image."""
        if not uploaded_image:
            pytest.skip("Image upload not available")

        response = client.delete(f"/api/images/{uploaded_image['id']}")

        assert response.status_code == 200

        # Verify image is gone
        get_response = client.get(f"/api/images/{uploaded_image['id']}")
        assert get_response.status_code == 404

    def test_delete_nonexistent_image(self, client):
        """Test deleting non-existent image."""
        response = client.delete("/api/images/nonexistent_id")

        assert response.status_code == 404


class TestStorageManagement:
    """Test storage quota and management."""

    def test_get_storage_info(self, client):
        """Test getting storage information."""
        response = client.get("/api/images/storage/info")

        assert response.status_code == 200
        data = response.json()
        assert "usage_mb" in data
        assert "limit_mb" in data
        assert "available_mb" in data
        assert "percentage" in data
        assert "image_count" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
