"""Pytest configuration and fixtures for GHL CLI tests."""

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from ghl.cli import main


@pytest.fixture
def runner():
    """CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_config_dir(tmp_path, monkeypatch):
    """Create a temporary config directory."""
    config_dir = tmp_path / ".ghl"
    config_dir.mkdir()
    
    # Mock the config directory
    monkeypatch.setattr("ghl.config.ConfigManager.CONFIG_DIR", config_dir)
    monkeypatch.setattr("ghl.config.ConfigManager.CONFIG_FILE", config_dir / "config.json")
    monkeypatch.setattr("ghl.config.ConfigManager.CREDENTIALS_FILE", config_dir / "credentials.json")
    
    return config_dir


@pytest.fixture
def mock_token(monkeypatch):
    """Mock API token."""
    token = "test-api-token-12345"
    monkeypatch.setenv("GHL_API_TOKEN", token)
    return token


@pytest.fixture
def mock_location_id(monkeypatch):
    """Mock location ID."""
    location_id = "test-location-id-12345"
    monkeypatch.setenv("GHL_LOCATION_ID", location_id)
    return location_id


@pytest.fixture
def mock_client():
    """Mock GHLClient for contacts."""
    with patch("ghl.commands.contacts.GHLClient") as mock:
        client_instance = MagicMock()
        mock.return_value.__enter__.return_value = client_instance
        mock.return_value.__exit__.return_value = None
        yield client_instance


@pytest.fixture
def mock_calendar_client():
    """Mock GHLClient for calendars."""
    with patch("ghl.commands.calendars.GHLClient") as mock:
        client_instance = MagicMock()
        mock.return_value.__enter__.return_value = client_instance
        mock.return_value.__exit__.return_value = None
        yield client_instance


@pytest.fixture
def mock_opportunity_client():
    """Mock GHLClient for opportunities."""
    with patch("ghl.commands.opportunities.GHLClient") as mock:
        client_instance = MagicMock()
        mock.return_value.__enter__.return_value = client_instance
        mock.return_value.__exit__.return_value = None
        yield client_instance


@pytest.fixture
def mock_conversation_client():
    """Mock GHLClient for conversations."""
    with patch("ghl.commands.conversations.GHLClient") as mock:
        client_instance = MagicMock()
        mock.return_value.__enter__.return_value = client_instance
        mock.return_value.__exit__.return_value = None
        yield client_instance


@pytest.fixture
def mock_workflow_client():
    """Mock GHLClient for workflows."""
    with patch("ghl.commands.workflows.GHLClient") as mock:
        client_instance = MagicMock()
        mock.return_value.__enter__.return_value = client_instance
        mock.return_value.__exit__.return_value = None
        yield client_instance


@pytest.fixture
def mock_pipeline_client():
    """Mock GHLClient for pipelines."""
    with patch("ghl.commands.pipelines.GHLClient") as mock:
        client_instance = MagicMock()
        mock.return_value.__enter__.return_value = client_instance
        mock.return_value.__exit__.return_value = None
        yield client_instance


@pytest.fixture
def mock_location_client():
    """Mock GHLClient for locations."""
    with patch("ghl.commands.locations.GHLClient") as mock:
        client_instance = MagicMock()
        mock.return_value.__enter__.return_value = client_instance
        mock.return_value.__exit__.return_value = None
        yield client_instance


@pytest.fixture
def mock_user_client():
    """Mock GHLClient for users."""
    with patch("ghl.commands.users.GHLClient") as mock:
        client_instance = MagicMock()
        mock.return_value.__enter__.return_value = client_instance
        mock.return_value.__exit__.return_value = None
        yield client_instance


@pytest.fixture
def mock_tag_client():
    """Mock GHLClient for tags."""
    with patch("ghl.commands.tags.GHLClient") as mock:
        client_instance = MagicMock()
        mock.return_value.__enter__.return_value = client_instance
        mock.return_value.__exit__.return_value = None
        yield client_instance


@pytest.fixture
def sample_contact():
    """Sample contact data."""
    return {
        "id": "contact-123",
        "firstName": "John",
        "lastName": "Doe",
        "email": "john.doe@example.com",
        "phone": "+1234567890",
        "tags": ["VIP", "Customer"],
        "companyName": "Example Corp",
        "dateAdded": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def sample_contacts():
    """Sample contacts list data."""
    return [
        {
            "id": "contact-1",
            "firstName": "John",
            "lastName": "Doe",
            "email": "john@example.com",
            "phone": "+1234567890",
            "tags": ["VIP"],
        },
        {
            "id": "contact-2",
            "firstName": "Jane",
            "lastName": "Smith",
            "email": "jane@example.com",
            "phone": "+0987654321",
            "tags": [],
        },
    ]


@pytest.fixture
def sample_opportunity():
    """Sample opportunity data."""
    return {
        "id": "opp-123",
        "name": "Deal Name",
        "contactId": "contact-123",
        "pipelineId": "pipeline-123",
        "pipelineStageId": "stage-123",
        "status": "open",
        "monetaryValue": 1000.0,
    }


@pytest.fixture
def sample_conversation():
    """Sample conversation data."""
    return {
        "id": "conv-123",
        "contactId": "contact-123",
        "type": "sms",
        "status": "active",
    }


@pytest.fixture
def sample_calendar():
    """Sample calendar data."""
    return {
        "id": "calendar-123",
        "name": "Main Calendar",
        "timezone": "America/New_York",
    }


@pytest.fixture
def sample_appointment():
    """Sample appointment data."""
    return {
        "id": "appt-123",
        "calendarId": "calendar-123",
        "contactId": "contact-123",
        "title": "Meeting",
        "startTime": "2024-01-20T10:00:00Z",
    }


@pytest.fixture
def sample_workflow():
    """Sample workflow data."""
    return {
        "id": "workflow-123",
        "name": "Welcome Workflow",
        "status": "active",
    }


@pytest.fixture
def sample_pipeline():
    """Sample pipeline data."""
    return {
        "id": "pipeline-123",
        "name": "Sales Pipeline",
        "stages": [
            {"id": "stage-1", "name": "Lead"},
            {"id": "stage-2", "name": "Qualified"},
        ],
    }


@pytest.fixture
def sample_location():
    """Sample location data."""
    return {
        "id": "location-123",
        "name": "Test Location",
        "address": "123 Main St",
    }


@pytest.fixture
def sample_user():
    """Sample user data."""
    return {
        "id": "user-123",
        "firstName": "Admin",
        "lastName": "User",
        "email": "admin@example.com",
    }


@pytest.fixture
def sample_tag():
    """Sample tag data."""
    return {
        "id": "tag-123",
        "name": "VIP",
    }
