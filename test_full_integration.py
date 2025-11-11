#!/usr/bin/env python3
"""
Full integration test for frontend-backend document ingestion
"""

import requests
import json
import time
import os


def test_full_ingestion_pipeline():
    """Test the complete ingestion pipeline through the API"""

    API_BASE = "http://localhost:8000"

    print("🧪 Testing Full Document Ingestion Pipeline")
    print("=" * 50)

    # Test 1: Health check
    print("\n1. Testing API Health...")
    try:
        response = requests.get(f"{API_BASE}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✅ API is healthy")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

    # Test 2: Get document types
    print("\n2. Testing Document Types Endpoint...")
    try:
        response = requests.get(f"{API_BASE}/ingestion/document-types")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert len(data["documentTypes"]) == 5
        print(f"✅ Found {len(data['documentTypes'])} document types")
    except Exception as e:
        print(f"❌ Document types test failed: {e}")
        return False

    # Test 3: Get advanced options
    print("\n3. Testing Advanced Options Endpoint...")
    try:
        response = requests.get(f"{API_BASE}/ingestion/advanced-options/standards")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert len(data["options"]) > 0
        print(f"✅ Found {len(data['options'])} advanced options for standards")
    except Exception as e:
        print(f"❌ Advanced options test failed: {e}")
        return False

    # Test 4: Document classification
    print("\n4. Testing Document Classification...")
    test_file = "./NC Music Standards and Resources/Second Grade GM Unpacking.pdf"

    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return False

    try:
        with open(test_file, "rb") as f:
            files = {"file": f}
            response = requests.post(f"{API_BASE}/ingestion/classify", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        classification = data["classification"]
        assert classification["documentType"]["value"] == "unpacking"
        assert classification["confidence"] > 0
        print(
            f"✅ Document classified as {classification['documentType']['label']} with {classification['confidence']:.0%} confidence"
        )
    except Exception as e:
        print(f"❌ Classification test failed: {e}")
        return False

    # Test 5: Full ingestion
    print("\n5. Testing Full Document Ingestion...")
    try:
        with open(test_file, "rb") as f:
            files = {"file": f}
            data = {"advanced_option": "Extract all content sections"}
            response = requests.post(
                f"{API_BASE}/ingestion/ingest", files=files, data=data
            )

        assert response.status_code == 200
        result = response.json()
        assert result["success"] == True
        assert "results" in result
        assert "message" in result

        results = result["results"]
        print(f"✅ Ingestion completed successfully")
        print(f"   - Sections: {results.get('sections_count', 0)}")
        print(f"   - Teaching Strategies: {results.get('strategies_count', 0)}")
        print(f"   - Assessment Guidance: {results.get('guidance_count', 0)}")

    except Exception as e:
        print(f"❌ Ingestion test failed: {e}")
        return False

    # Test 6: Get updated statistics
    print("\n6. Testing Statistics Update...")
    try:
        response = requests.get(f"{API_BASE}/ingestion/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        stats = data["stats"]

        assert stats["sections_count"] > 0
        assert stats["strategies_count"] > 0
        assert stats["guidance_count"] > 0

        print(f"✅ Database statistics updated:")
        print(f"   - Total Sections: {stats['sections_count']}")
        print(f"   - Total Strategies: {stats['strategies_count']}")
        print(f"   - Total Guidance: {stats['guidance_count']}")

    except Exception as e:
        print(f"❌ Statistics test failed: {e}")
        return False

    print("\n" + "=" * 50)
    print("🎉 All integration tests passed!")
    print("\nThe frontend-backend integration is working correctly.")
    print("Users can now upload, classify, and ingest documents through the web UI.")

    return True


if __name__ == "__main__":
    success = test_full_ingestion_pipeline()
    exit(0 if success else 1)
