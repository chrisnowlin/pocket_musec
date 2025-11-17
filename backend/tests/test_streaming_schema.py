"""Tests for harmonized streaming schema"""

import json
from backend.models.streaming_schema import (
    StreamingEvent,
    StreamingEventType,
    create_delta_event,
    create_status_event,
    create_persisted_event,
    create_complete_event,
    create_error_event,
    create_progress_event,
    create_job_status_envelope,
    emit_stream_event,
    parse_sse_chunk
)
from backend.models.ingestion_schema import (
    IngestionResponse,
    create_success_response,
    create_error_response,
    create_partial_response,
    create_pending_response
)


class TestStreamingSchema:
    """Test streaming event schema and helpers"""

    def test_create_delta_event(self):
        """Test delta event creation"""
        event = create_delta_event("Hello world", {"test": True})

        assert event.type == StreamingEventType.DELTA
        assert event.payload["text"] == "Hello world"
        assert event.meta["test"] is True
        assert event.timestamp is not None

    def test_create_status_event(self):
        """Test status event creation"""
        event = create_status_event("Processing...")

        assert event.type == StreamingEventType.STATUS
        assert event.payload["message"] == "Processing..."
        assert event.timestamp is not None

    def test_create_persisted_event(self):
        """Test persisted event creation"""
        event = create_persisted_event(True, "Saved successfully")

        assert event.type == StreamingEventType.PERSISTED
        assert event.payload["session_updated"] is True
        assert event.payload["message"] == "Saved successfully"

    def test_create_complete_event(self):
        """Test complete event creation"""
        payload_data = {"response": "Complete response"}
        event = create_complete_event(payload_data)

        assert event.type == StreamingEventType.COMPLETE
        assert event.payload == payload_data

    def test_create_error_event(self):
        """Test error event creation"""
        event = create_error_event("Failed to process", "PROCESS_ERROR", True)

        assert event.type == StreamingEventType.ERROR
        assert event.payload["message"] == "Failed to process"
        assert event.payload["code"] == "PROCESS_ERROR"
        assert event.payload["retry_recommended"] is True

    def test_create_progress_event(self):
        """Test progress event creation"""
        event = create_progress_event(75, 100, "Generating...")

        assert event.type == StreamingEventType.PROGRESS
        assert event.payload["progress"] == 75
        assert event.payload["total"] == 100
        assert event.payload["message"] == "Generating..."

    def test_emit_stream_event(self):
        """Test SSE emission format"""
        event = create_delta_event("test")
        sse_data = emit_stream_event(event)

        assert sse_data.startswith("data: ")
        assert sse_data.endswith("\n\n")

        # Parse back to verify format
        parsed = json.loads(sse_data[6:-2])  # Remove "data: " and "\n\n"
        assert parsed["type"] == "delta"
        assert parsed["payload"]["text"] == "test"

    def test_parse_sse_chunk(self):
        """Test SSE chunk parsing"""
        valid_chunk = 'data: {"type": "delta", "payload": {"text": "test"}}\n\n'

        event = parse_sse_chunk(valid_chunk)
        assert event is not None
        assert event.type == "delta"
        assert event.payload["text"] == "test"

    def test_parse_invalid_sse_chunk(self):
        """Test handling of invalid SSE chunks"""
        invalid_chunk = '{"type": "delta", "payload": {"text": "test"}}'

        event = parse_sse_chunk(invalid_chunk)
        assert event is None

    def test_parse_empty_chunk(self):
        """Test handling of empty chunks"""
        empty_chunk = 'data: [DONE]\n\n'

        event = parse_sse_chunk(empty_chunk)
        assert event is None

    def test_job_status_envelope(self):
        """Test job status envelope creation"""
        progress = {"completion_percentage": 100}
        meta = {"job_id": "test-123"}

        envelope = create_job_status_envelope(
            status="completed",
            progress=progress,
            meta=meta
        )

        assert envelope.status == "completed"
        assert envelope.progress == progress
        assert envelope.meta == meta
        assert envelope.timestamp is not None

        # Test serialization
        serialized = envelope.to_dict()
        assert "status" in serialized
        assert "progress" in serialized
        assert "meta" in serialized
        assert "timestamp" in serialized


class TestIngestionSchema:
    """Test ingestion response schema and helpers"""

    def test_create_success_response(self):
        """Test success response creation"""
        data = {"id": "test", "filename": "test.jpg"}
        response = create_success_response("Upload successful", data)

        assert response.status == "success"
        assert response.message == "Upload successful"
        assert response.data == data
        assert response.errors is None
        assert response.timestamp is not None

    def test_create_error_response(self):
        """Test error response creation"""
        errors = [{"message": "Invalid format", "code": "FORMAT_ERROR"}]
        response = create_error_response("Upload failed", errors)

        assert response.status == "error"
        assert response.message == "Upload failed"
        assert response.errors == errors
        assert response.data is None

    def test_create_partial_response(self):
        """Test partial response creation"""
        data = {"success": 3, "failed": 2}
        errors = [{"message": "File 4 failed"}]
        response = create_partial_response("Partial success", data, errors)

        assert response.status == "partial"
        assert response.message == "Partial success"
        assert response.data == data
        assert response.errors == errors

    def test_create_pending_response(self):
        """Test pending response creation"""
        response = create_pending_response("Processing started")

        assert response.status == "pending"
        assert response.message == "Processing started"
        assert response.data is None

    def test_ingestion_response_serialization(self):
        """Test response serialization"""
        data = {"id": "test"}
        response = create_success_response("Success", data)

        serialized = response.to_dict()
        assert isinstance(serialized, dict)
        assert serialized["status"] == "success"
        assert serialized["message"] == "Success"
        assert serialized["data"] == data
        assert "timestamp" in serialized


if __name__ == "__main__":
    # Basic sanity checks
    print("Running streaming schema tests...")

    schema = TestStreamingSchema()
    schema.test_create_delta_event()
    schema.test_create_status_event()
    schema.test_create_persisted_event()
    schema.test_create_complete_event()
    schema.test_create_error_event()
    schema.test_create_progress_event()
    schema.test_emit_stream_event()
    schema.test_parse_sse_chunk()
    schema.test_parse_invalid_sse_chunk()
    schema.test_parse_empty_chunk()
    schema.test_job_status_envelope()

    ingestion = TestIngestionSchema()
    ingestion.test_create_success_response()
    ingestion.test_create_error_response()
    ingestion.test_create_partial_response()
    ingestion.test_create_pending_response()
    ingestion.test_ingestion_response_serialization()

    print("All tests passed!")