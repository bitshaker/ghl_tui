"""Calendar and appointment management commands."""

from typing import Optional

import click

from ..auth import get_location_id, get_token
from ..client import GHLClient
from ..config import config_manager
from ..output import output_data, print_success

CALENDAR_COLUMNS = [
    ("id", "ID"),
    ("name", "Name"),
    ("description", "Description"),
    ("isActive", "Active"),
]

APPOINTMENT_COLUMNS = [
    ("id", "ID"),
    ("title", "Title"),
    ("calendarId", "Calendar ID"),
    ("contactId", "Contact ID"),
    ("startTime", "Start"),
    ("endTime", "End"),
    ("status", "Status"),
]

APPOINTMENT_FIELDS = [
    ("id", "ID"),
    ("title", "Title"),
    ("calendarId", "Calendar ID"),
    ("contactId", "Contact ID"),
    ("startTime", "Start Time"),
    ("endTime", "End Time"),
    ("status", "Status"),
    ("address", "Address"),
    ("notes", "Notes"),
    ("dateAdded", "Created"),
]


@click.group()
def calendars():
    """Manage calendars and appointments."""
    pass


@calendars.command("list")
@click.pass_context
def list_calendars(ctx):
    """List all calendars."""
    token = get_token()
    location_id = get_location_id()
    output_format = ctx.obj.get("output_format") or config_manager.config.output_format

    with GHLClient(token, location_id) as client:
        response = client.get("/calendars/")
        calendars_list = response.get("calendars", [])

        output_data(
            calendars_list,
            columns=CALENDAR_COLUMNS,
            format=output_format,
            title="Calendars",
        )


@calendars.command("get")
@click.argument("calendar_id")
@click.pass_context
def get_calendar(ctx, calendar_id: str):
    """Get calendar details."""
    token = get_token()
    location_id = get_location_id()
    output_format = ctx.obj.get("output_format") or config_manager.config.output_format

    with GHLClient(token, location_id) as client:
        response = client.get(f"/calendars/{calendar_id}")
        calendar = response.get("calendar", response)

        fields = [
            ("id", "ID"),
            ("name", "Name"),
            ("description", "Description"),
            ("isActive", "Active"),
            ("slotDuration", "Slot Duration"),
            ("slotBuffer", "Slot Buffer"),
            ("timezone", "Timezone"),
        ]

        output_data(calendar, format=output_format, single_fields=fields)


@calendars.command("slots")
@click.argument("calendar_id")
@click.option("--start", "-s", required=True, help="Start date (YYYY-MM-DD)")
@click.option("--end", "-e", help="End date (YYYY-MM-DD), defaults to start date")
@click.option("--timezone", "-tz", help="Timezone (e.g., America/New_York)")
@click.pass_context
def get_slots(ctx, calendar_id: str, start: str, end: Optional[str], timezone: Optional[str]):
    """Get available slots for a calendar."""
    token = get_token()
    location_id = get_location_id()
    output_format = ctx.obj.get("output_format") or config_manager.config.output_format

    with GHLClient(token, location_id) as client:
        params = {"startDate": start, "endDate": end or start}
        if timezone:
            params["timezone"] = timezone

        response = client.get(f"/calendars/{calendar_id}/free-slots", params=params)

        # Response contains slots grouped by date
        slots = response.get("slots", response)

        if output_format == "json":
            output_data(slots, format="json")
        else:
            # Flatten slots for table display
            flat_slots = []
            if isinstance(slots, dict):
                for date, times in slots.items():
                    for slot in times if isinstance(times, list) else [times]:
                        flat_slots.append({"date": date, "slot": slot})
            elif isinstance(slots, list):
                for slot in slots:
                    flat_slots.append({"slot": slot})

            output_data(
                flat_slots,
                columns=[("date", "Date"), ("slot", "Available Slot")],
                format=output_format,
                title=f"Available Slots ({start})",
            )


# Appointments subgroup
@calendars.group()
def appointments():
    """Manage appointments."""
    pass


@appointments.command("list")
@click.option("--calendar", "-c", "calendar_id", help="Filter by calendar ID")
@click.option("--contact", "contact_id", help="Filter by contact ID")
@click.option("--start", "-s", help="Start date filter (YYYY-MM-DD)")
@click.option("--end", "-e", help="End date filter (YYYY-MM-DD)")
@click.option("--limit", "-l", default=20, help="Number of results")
@click.pass_context
def list_appointments(
    ctx,
    calendar_id: Optional[str],
    contact_id: Optional[str],
    start: Optional[str],
    end: Optional[str],
    limit: int,
):
    """List appointments."""
    token = get_token()
    location_id = get_location_id()
    output_format = ctx.obj.get("output_format") or config_manager.config.output_format

    with GHLClient(token, location_id) as client:
        params = {"limit": limit}
        if calendar_id:
            params["calendarId"] = calendar_id
        if contact_id:
            params["contactId"] = contact_id
        if start:
            params["startDate"] = start
        if end:
            params["endDate"] = end

        response = client.get("/calendars/events/appointments", params=params)
        appointments_list = response.get("appointments", response.get("events", []))

        output_data(
            appointments_list,
            columns=APPOINTMENT_COLUMNS,
            format=output_format,
            title="Appointments",
        )


@appointments.command("get")
@click.argument("appointment_id")
@click.pass_context
def get_appointment(ctx, appointment_id: str):
    """Get appointment details."""
    token = get_token()
    location_id = get_location_id()
    output_format = ctx.obj.get("output_format") or config_manager.config.output_format

    with GHLClient(token, location_id) as client:
        response = client.get(f"/calendars/events/appointments/{appointment_id}")
        appointment = response.get("appointment", response.get("event", response))

        output_data(appointment, format=output_format, single_fields=APPOINTMENT_FIELDS)


@appointments.command("create")
@click.option("--calendar", "-c", "calendar_id", required=True, help="Calendar ID")
@click.option("--contact", "contact_id", required=True, help="Contact ID")
@click.option("--slot", "-s", required=True, help="Appointment slot (ISO datetime)")
@click.option("--title", "-t", help="Appointment title")
@click.option("--notes", "-n", help="Appointment notes")
@click.option("--address", "-a", help="Appointment address")
@click.pass_context
def create_appointment(
    ctx,
    calendar_id: str,
    contact_id: str,
    slot: str,
    title: Optional[str],
    notes: Optional[str],
    address: Optional[str],
):
    """Create a new appointment."""
    token = get_token()
    location_id = get_location_id()
    output_format = ctx.obj.get("output_format") or config_manager.config.output_format

    with GHLClient(token, location_id) as client:
        data = {
            "calendarId": calendar_id,
            "contactId": contact_id,
            "selectedSlot": slot,
            "locationId": location_id,
        }

        if title:
            data["title"] = title
        if notes:
            data["notes"] = notes
        if address:
            data["address"] = address

        response = client.post("/calendars/events/appointments", json=data)
        appointment = response.get("appointment", response.get("event", response))

        if output_format == "quiet":
            click.echo(appointment.get("id"))
        else:
            print_success(f"Appointment created: {appointment.get('id')}")
            output_data(appointment, format=output_format, single_fields=APPOINTMENT_FIELDS)


@appointments.command("update")
@click.argument("appointment_id")
@click.option("--slot", "-s", help="New slot (ISO datetime)")
@click.option("--title", "-t", help="New title")
@click.option("--notes", "-n", help="New notes")
@click.option("--status", help="New status (confirmed, cancelled, etc.)")
@click.pass_context
def update_appointment(
    ctx,
    appointment_id: str,
    slot: Optional[str],
    title: Optional[str],
    notes: Optional[str],
    status: Optional[str],
):
    """Update an appointment."""
    token = get_token()
    location_id = get_location_id()
    output_format = ctx.obj.get("output_format") or config_manager.config.output_format

    with GHLClient(token, location_id) as client:
        data = {}

        if slot:
            data["selectedSlot"] = slot
        if title:
            data["title"] = title
        if notes:
            data["notes"] = notes
        if status:
            data["status"] = status

        if not data:
            raise click.ClickException("No fields to update. Specify at least one option.")

        response = client.put(f"/calendars/events/appointments/{appointment_id}", json=data)
        appointment = response.get("appointment", response.get("event", response))

        print_success(f"Appointment updated: {appointment_id}")
        output_data(appointment, format=output_format, single_fields=APPOINTMENT_FIELDS)


@appointments.command("delete")
@click.argument("appointment_id")
@click.confirmation_option(prompt="Are you sure you want to delete this appointment?")
def delete_appointment(appointment_id: str):
    """Delete an appointment."""
    token = get_token()
    location_id = get_location_id()

    with GHLClient(token, location_id) as client:
        client.delete(f"/calendars/events/appointments/{appointment_id}")
        print_success(f"Appointment deleted: {appointment_id}")
