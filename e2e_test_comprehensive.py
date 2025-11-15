#!/usr/bin/env python3
"""
Comprehensive End-to-End Testing for PocketMusec
Tests all major system components and workflows
"""

import asyncio
import json
import time
import requests
import base64
from pathlib import Path
from typing import Dict, Any, List
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class E2ETestSuite:
    """Comprehensive E2E test suite for PocketMusec"""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        frontend_url: str = "http://localhost:5173",
    ):
        self.base_url = base_url
        self.frontend_url = frontend_url
        self.session = requests.Session()
        self.test_results = []
        self.start_time = datetime.now()

    def log_test(
        self, test_name: str, passed: bool, details: str = "", response_time: float = 0
    ):
        """Log test result"""
        result = {
            "test": test_name,
            "passed": passed,
            "details": details,
            "response_time": response_time,
            "timestamp": datetime.now().isoformat(),
        }
        self.test_results.append(result)

        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status} {test_name} - {details} ({response_time:.2f}s)")

    def test_health_check(self):
        """Test API health check endpoint"""
        try:
            start = time.time()
            response = self.session.get(f"{self.base_url}/health")
            response_time = time.time() - start

            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "API Health Check",
                    True,
                    f"Status: {data.get('status')}",
                    response_time,
                )
                return True
            else:
                self.log_test(
                    "API Health Check",
                    False,
                    f"Status: {response.status_code}",
                    response_time,
                )
                return False
        except Exception as e:
            self.log_test("API Health Check", False, f"Exception: {str(e)}")
            return False

    def test_frontend_access(self):
        """Test frontend accessibility"""
        try:
            start = time.time()
            response = self.session.get(self.frontend_url)
            response_time = time.time() - start

            if response.status_code == 200:
                self.log_test(
                    "Frontend Access", True, "Frontend server responding", response_time
                )
                return True
            else:
                self.log_test(
                    "Frontend Access",
                    False,
                    f"Status: {response.status_code}",
                    response_time,
                )
                return False
        except Exception as e:
            self.log_test("Frontend Access", False, f"Exception: {str(e)}")
            return False

    def test_standards_endpoints(self):
        """Test standards-related endpoints"""
        tests_passed = 0
        total_tests = 0

        # Test grade levels
        try:
            start = time.time()
            response = self.session.get(f"{self.base_url}/api/standards/grades")
            response_time = time.time() - start
            total_tests += 1

            if response.status_code == 200:
                grades = response.json()
                if isinstance(grades, list) and len(grades) > 0:
                    self.log_test(
                        "Get Grade Levels",
                        True,
                        f"Found {len(grades)} grades",
                        response_time,
                    )
                    tests_passed += 1
                else:
                    self.log_test(
                        "Get Grade Levels",
                        False,
                        "Invalid response format",
                        response_time,
                    )
            else:
                self.log_test(
                    "Get Grade Levels",
                    False,
                    f"Status: {response.status_code}",
                    response_time,
                )
        except Exception as e:
            self.log_test("Get Grade Levels", False, f"Exception: {str(e)}")
            total_tests += 1

        # Test strands
        try:
            start = time.time()
            response = self.session.get(f"{self.base_url}/api/standards/strands")
            response_time = time.time() - start
            total_tests += 1

            if response.status_code == 200:
                strands = response.json()
                if isinstance(strands, list) and len(strands) > 0:
                    self.log_test(
                        "Get Strands",
                        True,
                        f"Found {len(strands)} strands",
                        response_time,
                    )
                    tests_passed += 1
                else:
                    self.log_test(
                        "Get Strands", False, "Invalid response format", response_time
                    )
            else:
                self.log_test(
                    "Get Strands",
                    False,
                    f"Status: {response.status_code}",
                    response_time,
                )
        except Exception as e:
            self.log_test("Get Strands", False, f"Exception: {str(e)}")
            total_tests += 1

        return tests_passed, total_tests

    def test_sessions_workflow(self):
        """Test session creation and management workflow"""
        tests_passed = 0
        total_tests = 0

        # Create session
        try:
            start = time.time()
            session_data = {
                "grade_level": "Grade 3",
                "strand_code": "CN",
                "standard_id": None,
                "additional_context": "E2E test session",
            }
            response = self.session.post(
                f"{self.base_url}/api/sessions", json=session_data
            )
            response_time = time.time() - start
            total_tests += 1

            if response.status_code == 200:
                session = response.json()
                if "id" in session and session.get("grade_level") == "Grade 3":
                    session_id = session["id"]
                    self.log_test(
                        "Create Session",
                        True,
                        f"Session ID: {session_id}",
                        response_time,
                    )
                    tests_passed += 1

                    # Test session retrieval
                    try:
                        start = time.time()
                        response = self.session.get(
                            f"{self.base_url}/api/sessions/{session_id}"
                        )
                        response_time = time.time() - start
                        total_tests += 1

                        if response.status_code == 200:
                            retrieved_session = response.json()
                            if retrieved_session.get("id") == session_id:
                                self.log_test(
                                    "Get Session",
                                    True,
                                    f"Retrieved session {session_id}",
                                    response_time,
                                )
                                tests_passed += 1
                            else:
                                self.log_test(
                                    "Get Session",
                                    False,
                                    "Session ID mismatch",
                                    response_time,
                                )
                        else:
                            self.log_test(
                                "Get Session",
                                False,
                                f"Status: {response.status_code}",
                                response_time,
                            )
                    except Exception as e:
                        self.log_test("Get Session", False, f"Exception: {str(e)}")
                        total_tests += 1
                else:
                    self.log_test(
                        "Create Session",
                        False,
                        "Invalid session response",
                        response_time,
                    )
            else:
                self.log_test(
                    "Create Session",
                    False,
                    f"Status: {response.status_code}",
                    response_time,
                )
        except Exception as e:
            self.log_test("Create Session", False, f"Exception: {str(e)}")
            total_tests += 1

        return tests_passed, total_tests

    def test_lesson_generation(self):
        """Test lesson generation endpoint"""
        try:
            start = time.time()
            lesson_request = {
                "grade_level": "Grade 3",
                "strand_code": "CN",
                "standard_id": "3.CN.1",
                "objectives": ["Students will practice rhythmic patterns"],
                "duration": "30 minutes",
                "class_size": "25",
                "additional_context": "E2E test lesson generation",
            }
            response = self.session.post(
                f"{self.base_url}/api/lessons/generate", json=lesson_request
            )
            response_time = time.time() - start

            if response.status_code == 200:
                lesson = response.json()
                if "title" in lesson and "content" in lesson:
                    self.log_test(
                        "Lesson Generation",
                        True,
                        f"Generated: {lesson.get('title', 'Unknown')}",
                        response_time,
                    )
                    return True
                else:
                    self.log_test(
                        "Lesson Generation",
                        False,
                        "Invalid lesson response format",
                        response_time,
                    )
            else:
                self.log_test(
                    "Lesson Generation",
                    False,
                    f"Status: {response.status_code}",
                    response_time,
                )
        except Exception as e:
            self.log_test("Lesson Generation", False, f"Exception: {str(e)}")

        return False

    def test_embeddings_search(self):
        """Test embeddings search functionality"""
        try:
            start = time.time()
            search_request = {
                "query": "rhythmic patterns music",
                "limit": 10,
                "filters": {},
            }
            response = self.session.post(
                f"{self.base_url}/api/embeddings/search", json=search_request
            )
            response_time = time.time() - start

            if response.status_code == 200:
                results = response.json()
                if "results" in results and isinstance(results["results"], list):
                    self.log_test(
                        "Embeddings Search",
                        True,
                        f"Found {len(results['results'])} results",
                        response_time,
                    )
                    return True
                else:
                    self.log_test(
                        "Embeddings Search",
                        False,
                        "Invalid search response format",
                        response_time,
                    )
            else:
                self.log_test(
                    "Embeddings Search",
                    False,
                    f"Status: {response.status_code}",
                    response_time,
                )
        except Exception as e:
            self.log_test("Embeddings Search", False, f"Exception: {str(e)}")

        return False

    def test_image_upload(self):
        """Test image upload and processing"""
        # Create a simple test image (1x1 pixel PNG)
        test_image_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        )

        try:
            start = time.time()
            files = {"file": ("test.png", test_image_data, "image/png")}
            data = {"processing_mode": "cloud"}
            response = self.session.post(
                f"{self.base_url}/api/images/upload", files=files, data=data
            )
            response_time = time.time() - start

            # Accept both 200 and 201 as success (201 is Created, which is correct for resource creation)
            if response.status_code in [200, 201]:
                result = response.json()
                if "id" in result or "message" in result:
                    self.log_test(
                        "Image Upload",
                        True,
                        f"Upload successful: {result.get('message', 'Processed')}",
                        response_time,
                    )
                    return True
                else:
                    self.log_test(
                        "Image Upload", False, "Invalid upload response", response_time
                    )
            else:
                self.log_test(
                    "Image Upload",
                    False,
                    f"Status: {response.status_code}",
                    response_time,
                )
        except Exception as e:
            self.log_test("Image Upload", False, f"Exception: {str(e)}")

        return False

    def test_settings_management(self):
        """Test settings endpoints"""
        try:
            start = time.time()
            # Get current settings (using correct endpoint)
            response = self.session.get(
                f"{self.base_url}/api/settings/processing-modes"
            )
            response_time = time.time() - start

            if response.status_code == 200:
                settings = response.json()
                if isinstance(settings, dict) and "modes" in settings:
                    self.log_test(
                        "Get Settings",
                        True,
                        f"Retrieved {len(settings['modes'])} processing modes, current: {settings['current']}",
                        response_time,
                    )
                    return True
                else:
                    self.log_test(
                        "Get Settings",
                        False,
                        "Invalid settings response",
                        response_time,
                    )
            else:
                self.log_test(
                    "Get Settings",
                    False,
                    f"Status: {response.status_code}",
                    response_time,
                )
        except Exception as e:
            self.log_test("Get Settings", False, f"Exception: {str(e)}")

        return False

    def test_citation_system(self):
        """Test citation tracking system"""
        try:
            start = time.time()
            # Test citation formatting
            citation_request = {
                "sources": [
                    {
                        "title": "Test Music Standard",
                        "author": "National Core Arts Standards",
                        "year": "2024",
                        "url": "https://example.com/standard",
                    }
                ],
                "format": "ieee",
            }
            response = self.session.post(
                f"{self.base_url}/api/citations/format", json=citation_request
            )
            response_time = time.time() - start

            if response.status_code == 200:
                formatted = response.json()
                if "citations" in formatted:
                    self.log_test(
                        "Citation Formatting",
                        True,
                        f"Formatted {len(formatted['citations'])} citations",
                        response_time,
                    )
                    return True
                else:
                    self.log_test(
                        "Citation Formatting",
                        False,
                        "Invalid citation response",
                        response_time,
                    )
            else:
                self.log_test(
                    "Citation Formatting",
                    False,
                    f"Status: {response.status_code}",
                    response_time,
                )
        except Exception as e:
            self.log_test("Citation Formatting", False, f"Exception: {str(e)}")

        return False

    def test_error_handling(self):
        """Test API error handling with invalid requests"""
        tests_passed = 0
        total_tests = 0

        # Test invalid endpoint
        try:
            start = time.time()
            response = self.session.get(f"{self.base_url}/api/invalid/endpoint")
            response_time = time.time() - start
            total_tests += 1

            if response.status_code == 404:
                self.log_test(
                    "404 Error Handling",
                    True,
                    "Correctly returns 404 for invalid endpoint",
                    response_time,
                )
                tests_passed += 1
            else:
                self.log_test(
                    "404 Error Handling",
                    False,
                    f"Expected 404, got {response.status_code}",
                    response_time,
                )
        except Exception as e:
            self.log_test("404 Error Handling", False, f"Exception: {str(e)}")
            total_tests += 1

        # Test invalid JSON
        try:
            start = time.time()
            response = self.session.post(
                f"{self.base_url}/api/sessions", data="invalid json"
            )
            response_time = time.time() - start
            total_tests += 1

            if response.status_code == 422:
                self.log_test(
                    "Invalid JSON Handling",
                    True,
                    "Correctly returns 422 for invalid JSON",
                    response_time,
                )
                tests_passed += 1
            else:
                self.log_test(
                    "Invalid JSON Handling",
                    False,
                    f"Expected 422, got {response.status_code}",
                    response_time,
                )
        except Exception as e:
            self.log_test("Invalid JSON Handling", False, f"Exception: {str(e)}")
            total_tests += 1

        return tests_passed, total_tests

    def run_all_tests(self):
        """Run all E2E tests"""
        logger.info("🧪 Starting Comprehensive E2E Test Suite")
        logger.info(f"Backend URL: {self.base_url}")
        logger.info(f"Frontend URL: {self.frontend_url}")
        logger.info("=" * 60)

        # Core functionality tests
        self.test_health_check()
        self.test_frontend_access()

        # API endpoint tests
        standards_passed, standards_total = self.test_standards_endpoints()
        sessions_passed, sessions_total = self.test_sessions_workflow()

        # Feature tests
        self.test_lesson_generation()
        self.test_embeddings_search()
        self.test_image_upload()
        self.test_settings_management()
        self.test_citation_system()

        # Error handling tests
        error_passed, error_total = self.test_error_handling()

        # Calculate results
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["passed"])

        # Generate summary
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        logger.info("=" * 60)
        logger.info("📊 E2E Test Results Summary")
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {total_tests - passed_tests}")
        logger.info(f"Success Rate: {(passed_tests / total_tests) * 100:.1f}%")
        logger.info(f"Duration: {duration:.2f}s")
        logger.info("=" * 60)

        # Detailed results
        logger.info("📋 Detailed Results:")
        for result in self.test_results:
            status = "✅" if result["passed"] else "❌"
            logger.info(f"{status} {result['test']} - {result['details']}")

        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": (passed_tests / total_tests) * 100,
            "duration": duration,
            "results": self.test_results,
        }


def main():
    """Main function to run E2E tests"""
    test_suite = E2ETestSuite()
    results = test_suite.run_all_tests()

    # Save results to file
    results_file = Path("e2e_test_results.json")
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"📄 Results saved to {results_file}")

    # Exit with appropriate code
    exit_code = 0 if results["success_rate"] >= 80 else 1
    exit(exit_code)


if __name__ == "__main__":
    main()
