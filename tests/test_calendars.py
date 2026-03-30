"""Tests for calendar and appointment commands."""

from datetime import date
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from ghl.cli import main
from ghl.services import calendars as calendars_svc
from ghl.tui.calendar_appointments import slot_iso_in_calendar_tz


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
        assert isinstance(call_args[1]["params"]["startDate"], int)
        assert isinstance(call_args[1]["params"]["endDate"], int)
        assert call_args[1].get("include_location_id") is False

    def test_calendars_slots_default_start_today(
        self, runner, mock_token, mock_location_id, mock_calendar_client
    ):
        """Slots without --start uses today (local date)."""
        mock_calendar_client.get.return_value = {"slots": []}

        fixed = date(2024, 1, 20)
        with patch("ghl.commands.calendars.date") as mock_date:
            mock_date.today.return_value = fixed
            result = runner.invoke(main, ["calendars", "slots", "calendar-123"])

        assert result.exit_code == 0
        mock_calendar_client.get.assert_called_once()
        call_args = mock_calendar_client.get.call_args
        assert "/calendars/calendar-123/free-slots" in call_args[0][0]
        assert call_args[1]["params"]["startDate"] == calendars_svc.ymd_to_utc_start_ms(
            "2024-01-20"
        )


class TestCalendarEventsHelpers:
    """GET /calendars/events response normalization and time windows."""

    def test_events_from_response_nested_by_date(self):
        ev = {"id": "a1", "startTime": "2024-06-01T15:00:00Z"}
        resp = {"events": {"2024-06-01": [ev]}}
        assert calendars_svc.events_from_response(resp) == [ev]

    def test_events_from_response_top_level_list(self):
        ev = {"id": "x", "calendarId": "c1"}
        assert calendars_svc.events_from_response([ev]) == [ev]

    def test_events_from_response_data_wrapper(self):
        ev = {"id": "y", "startTime": 1_700_000_000_000}
        assert calendars_svc.events_from_response({"data": {"events": [ev]}}) == [ev]

    def test_default_events_unfiltered_includes_lookback(self):
        start_ms, end_ms = calendars_svc.default_events_time_range_ms(None, None)
        assert start_ms < end_ms
        assert end_ms - start_ms >= 29 * 86400 * 1000


class TestCalendarSlotHelpers:
    """Booking helpers for GHL selectedSlot / selectedTimezone."""

    def test_slot_iso_in_calendar_tz_uses_calendar_zone(self):
        """Slot is ISO with offset in the calendar IANA zone (not implicit UTC)."""
        iso, tz = slot_iso_in_calendar_tz("2025-03-24", "09", "00", "America/New_York")
        assert tz == "America/New_York"
        assert iso == "2025-03-24T09:00:00-04:00"


class TestAppointmentCommands:
    """Test appointment management commands."""

    def test_appointments_list(self, runner, mock_token, mock_location_id, mock_calendar_client, sample_appointment):
        """Test listing appointments (GET /calendars/events per calendar)."""

        def mock_get(path, params=None, **kwargs):
            if path == "/calendars/":
                return {"calendars": [{"id": "calendar-123", "name": "Main"}]}
            if path == "/calendars/events":
                return {"events": [sample_appointment]}
            return {}

        mock_calendar_client.get.side_effect = mock_get

        result = runner.invoke(main, ["calendars", "appointments", "list"])
        assert result.exit_code == 0
        assert "Meeting" in result.output
        assert mock_calendar_client.get.call_count >= 1

    def test_appointments_get(self, runner, mock_token, mock_location_id, mock_calendar_client, sample_appointment):
        """Test getting an appointment by ID."""
        mock_calendar_client.get.return_value = {"appointment": sample_appointment}

        result = runner.invoke(main, ["calendars", "appointments", "get", "appt-123"])
        assert result.exit_code == 0
        assert "appt-123" in result.output
        mock_calendar_client.get.assert_called_once_with(
            "/calendars/events/appointments/appt-123",
            include_location_id=False,
        )

    def test_appointments_create(
        self, runner, mock_token, mock_location_id, mock_calendar_client, sample_appointment, sample_calendar
    ):
        """Test creating an appointment."""
        mock_calendar_client.post.return_value = {"appointment": sample_appointment}
        mock_calendar_client.get.return_value = {"calendar": sample_calendar}

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
        assert data["selectedTimezone"] == "America/New_York"

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
        assert call_args[1].get("include_location_id") is False

    def test_appointments_delete(self, runner, mock_token, mock_location_id, mock_calendar_client):
        """Test deleting an appointment."""
        mock_calendar_client.delete.return_value = {}

        result = runner.invoke(main, ["calendars", "appointments", "delete", "appt-123"], input="y\n")
        assert result.exit_code == 0
        assert "Appointment deleted" in result.output
        mock_calendar_client.delete.assert_called_once_with(
            "/calendars/events/appointments/appt-123",
            include_location_id=False,
        )
