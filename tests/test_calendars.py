"""Tests for calendar and appointment commands."""

import pytest
from click.testing import CliRunner

from ghl.cli import main


class TestCalendarCommands:
    """Test calendar management commands."""

    def test_calendars_list(self, runner, mock_token, mock_location_id, mock_calendar_client, sample_calendar):
        """Test listing calendars."""
        mock_calendar_client.get.return_value = {"calendars": [sample_calendar]}

        result = runner.invoke(main, ["calendars", "list"])
        assert result.exit_code == 0
        assert "Main Calendar" in result.output
        mock_calendar_client.get.assert_called_once_with("/calendars/")

    def test_calendars_get(self, runner, mock_token, mock_location_id, mock_calendar_client, sample_calendar):
        """Test getting a calendar by ID."""
        mock_calendar_client.get.return_value = {"calendar": sample_calendar}

        result = runner.invoke(main, ["calendars", "get", "calendar-123"])
        assert result.exit_code == 0
        assert "calendar-123" in result.output
        mock_calendar_client.get.assert_called_once_with("/calendars/calendar-123")

    def test_calendars_slots(self, runner, mock_token, mock_location_id, mock_calendar_client):
        """Test getting available calendar slots."""
        slots = [
            {"startTime": "2024-01-20T10:00:00Z", "endTime": "2024-01-20T10:30:00Z"},
            {"startTime": "2024-01-20T11:00:00Z", "endTime": "2024-01-20T11:30:00Z"},
        ]
        mock_calendar_client.get.return_value = {"slots": slots}

        result = runner.invoke(main, ["calendars", "slots", "calendar-123", "--start", "2024-01-20"])
        assert result.exit_code == 0
        mock_calendar_client.get.assert_called_once()
        call_args = mock_calendar_client.get.call_args
        assert "/calendars/calendar-123/free-slots" in call_args[0][0]
        assert call_args[1]["params"]["startDate"] == "2024-01-20"


class TestAppointmentCommands:
    """Test appointment management commands."""

    def test_appointments_list(self, runner, mock_token, mock_location_id, mock_calendar_client, sample_appointment):
        """Test listing appointments."""
        mock_calendar_client.get.return_value = {"appointments": [sample_appointment]}

        result = runner.invoke(main, ["calendars", "appointments", "list"])
        assert result.exit_code == 0
        assert "Meeting" in result.output
        mock_calendar_client.get.assert_called_once()

    def test_appointments_get(self, runner, mock_token, mock_location_id, mock_calendar_client, sample_appointment):
        """Test getting an appointment by ID."""
        mock_calendar_client.get.return_value = {"appointment": sample_appointment}

        result = runner.invoke(main, ["calendars", "appointments", "get", "appt-123"])
        assert result.exit_code == 0
        assert "appt-123" in result.output
        mock_calendar_client.get.assert_called_once_with("/calendars/events/appointments/appt-123")

    def test_appointments_create(self, runner, mock_token, mock_location_id, mock_calendar_client, sample_appointment):
        """Test creating an appointment."""
        mock_calendar_client.post.return_value = {"appointment": sample_appointment}

        result = runner.invoke(
            main,
            [
                "calendars",
                "appointments",
                "create",
                "--calendar",
                "calendar-123",
                "--contact",
                "contact-123",
                "--slot",
                "2024-01-20T10:00:00Z",
            ],
        )
        assert result.exit_code == 0
        assert "Appointment created" in result.output
        mock_calendar_client.post.assert_called_once()
        call_args = mock_calendar_client.post.call_args
        assert call_args[0][0] == "/calendars/events/appointments"
        data = call_args[1]["json"]
        assert data["calendarId"] == "calendar-123"
        assert data["contactId"] == "contact-123"

    def test_appointments_update(self, runner, mock_token, mock_location_id, mock_calendar_client, sample_appointment):
        """Test updating an appointment."""
        mock_calendar_client.put.return_value = {"appointment": sample_appointment}

        result = runner.invoke(
            main, ["calendars", "appointments", "update", "appt-123", "--title", "New Title"]
        )
        assert result.exit_code == 0
        assert "Appointment updated" in result.output
        mock_calendar_client.put.assert_called_once()
        call_args = mock_calendar_client.put.call_args
        assert call_args[0][0] == "/calendars/events/appointments/appt-123"
        assert call_args[1]["json"]["title"] == "New Title"

    def test_appointments_delete(self, runner, mock_token, mock_location_id, mock_calendar_client):
        """Test deleting an appointment."""
        mock_calendar_client.delete.return_value = {}

        result = runner.invoke(main, ["calendars", "appointments", "delete", "appt-123"], input="y\n")
        assert result.exit_code == 0
        assert "Appointment deleted" in result.output
        mock_calendar_client.delete.assert_called_once_with("/calendars/events/appointments/appt-123")
