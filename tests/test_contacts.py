"""Tests for contact commands."""

import pytest
from click.testing import CliRunner

from ghl.cli import main


class TestContactCommands:
    """Test contact management commands."""

    def test_contacts_list(self, runner, mock_token, mock_location_id, mock_client, sample_contacts):
        """Test listing contacts."""
        mock_client.get.return_value = {"contacts": sample_contacts}

        result = runner.invoke(main, ["contacts", "list"])
        assert result.exit_code == 0
        assert "John" in result.output
        assert "Jane" in result.output
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert "/contacts/" in call_args[0][0]

    def test_contacts_list_with_limit(self, runner, mock_token, mock_location_id, mock_client, sample_contacts):
        """Test listing contacts with limit."""
        mock_client.get.return_value = {"contacts": sample_contacts}

        result = runner.invoke(main, ["contacts", "list", "--limit", "10"])
        assert result.exit_code == 0
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[1]["params"]["limit"] == 10

    def test_contacts_list_with_query(self, runner, mock_token, mock_location_id, mock_client, sample_contacts):
        """Test listing contacts with query."""
        mock_client.get.return_value = {"contacts": sample_contacts}

        result = runner.invoke(main, ["contacts", "list", "--query", "john"])
        assert result.exit_code == 0
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[1]["params"]["query"] == "john"

    def test_contacts_list_quiet(self, runner, mock_token, mock_location_id, mock_client, sample_contacts):
        """Test listing contacts with --quiet flag."""
        mock_client.get.return_value = {"contacts": sample_contacts}

        result = runner.invoke(main, ["contacts", "list", "--quiet"])
        assert result.exit_code == 0
        # Should only output IDs, one per line
        output_lines = result.output.strip().split("\n")
        assert len(output_lines) == 2
        assert "contact-1" in result.output
        assert "contact-2" in result.output
        # Should not contain other contact info
        assert "John" not in result.output
        assert "Doe" not in result.output

    def test_contacts_list_json(self, runner, mock_token, mock_location_id, mock_client, sample_contacts):
        """Test listing contacts in JSON format."""
        mock_client.get.return_value = {"contacts": sample_contacts}

        result = runner.invoke(main, ["contacts", "list", "--json"])
        assert result.exit_code == 0
        import json
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) == 2

    def test_contacts_list_csv(self, runner, mock_token, mock_location_id, mock_client, sample_contacts):
        """Test listing contacts in CSV format."""
        mock_client.get.return_value = {"contacts": sample_contacts}

        result = runner.invoke(main, ["contacts", "list", "--csv"])
        assert result.exit_code == 0
        assert "ID," in result.output
        assert "First Name," in result.output
        assert "contact-1" in result.output

    def test_contacts_get(self, runner, mock_token, mock_location_id, mock_client, sample_contact):
        """Test getting a contact by ID."""
        mock_client.get.return_value = {"contact": sample_contact}

        result = runner.invoke(main, ["contacts", "get", "contact-123"])
        assert result.exit_code == 0
        assert "John" in result.output
        assert "Doe" in result.output
        assert "john.doe@example.com" in result.output
        mock_client.get.assert_called_once_with("/contacts/contact-123")

    def test_contacts_get_json(self, runner, mock_token, mock_location_id, mock_client, sample_contact):
        """Test getting a contact in JSON format."""
        mock_client.get.return_value = {"contact": sample_contact}

        result = runner.invoke(main, ["contacts", "get", "contact-123", "--json"])
        assert result.exit_code == 0
        import json
        data = json.loads(result.output)
        assert data["id"] == "contact-123"

    def test_contacts_create_minimal(self, runner, mock_token, mock_location_id, mock_client, sample_contact):
        """Test creating a contact with minimal required fields."""
        mock_client.post.return_value = {"contact": sample_contact}

        result = runner.invoke(main, ["contacts", "create", "--email", "test@example.com"])
        assert result.exit_code == 0
        assert "Contact created" in result.output
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/contacts/"
        assert call_args[1]["json"]["email"] == "test@example.com"

    def test_contacts_create_with_phone(self, runner, mock_token, mock_location_id, mock_client, sample_contact):
        """Test creating a contact with phone number."""
        mock_client.post.return_value = {"contact": sample_contact}

        result = runner.invoke(main, ["contacts", "create", "--phone", "+1234567890"])
        assert result.exit_code == 0
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[1]["json"]["phone"] == "+1234567890"

    def test_contacts_create_full(self, runner, mock_token, mock_location_id, mock_client, sample_contact):
        """Test creating a contact with all fields."""
        mock_client.post.return_value = {"contact": sample_contact}

        result = runner.invoke(
            main,
            [
                "contacts",
                "create",
                "--email",
                "test@example.com",
                "--first-name",
                "Test",
                "--last-name",
                "User",
                "--company",
                "Test Corp",
                "--tag",
                "VIP",
                "--tag",
                "Customer",
            ],
        )
        assert result.exit_code == 0
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        data = call_args[1]["json"]
        assert data["email"] == "test@example.com"
        assert data["firstName"] == "Test"
        assert data["lastName"] == "User"
        assert data["companyName"] == "Test Corp"
        assert data["tags"] == ["VIP", "Customer"]

    def test_contacts_create_requires_email_or_phone(self, runner, mock_token, mock_location_id):
        """Test that creating a contact requires email or phone."""
        result = runner.invoke(main, ["contacts", "create", "--first-name", "Test"])
        assert result.exit_code != 0
        assert "At least --email or --phone is required" in result.output

    def test_contacts_create_quiet(self, runner, mock_token, mock_location_id, mock_client, sample_contact):
        """Test creating a contact with --quiet flag."""
        mock_client.post.return_value = {"contact": sample_contact}

        result = runner.invoke(main, ["contacts", "create", "--email", "test@example.com", "--quiet"])
        assert result.exit_code == 0
        # Should only output the contact ID
        assert result.output.strip() == "contact-123"
        assert "Contact created" not in result.output

    def test_contacts_update(self, runner, mock_token, mock_location_id, mock_client, sample_contact):
        """Test updating a contact."""
        mock_client.put.return_value = {"contact": sample_contact}

        result = runner.invoke(
            main,
            ["contacts", "update", "contact-123", "--email", "new@example.com", "--first-name", "NewName"],
        )
        assert result.exit_code == 0
        assert "Contact updated" in result.output
        mock_client.put.assert_called_once()
        call_args = mock_client.put.call_args
        assert call_args[0][0] == "/contacts/contact-123"
        assert call_args[1]["json"]["email"] == "new@example.com"
        assert call_args[1]["json"]["firstName"] == "NewName"

    def test_contacts_update_no_fields(self, runner, mock_token, mock_location_id):
        """Test updating a contact with no fields specified."""
        result = runner.invoke(main, ["contacts", "update", "contact-123"])
        assert result.exit_code != 0
        assert "No fields to update" in result.output

    def test_contacts_delete(self, runner, mock_token, mock_location_id, mock_client):
        """Test deleting a contact."""
        mock_client.delete.return_value = {}

        result = runner.invoke(main, ["contacts", "delete", "contact-123"], input="y\n")
        assert result.exit_code == 0
        assert "Contact deleted" in result.output
        mock_client.delete.assert_called_once_with("/contacts/contact-123")

    def test_contacts_search(self, runner, mock_token, mock_location_id, mock_client, sample_contacts):
        """Test searching contacts."""
        mock_client.get.return_value = {"contacts": sample_contacts}

        result = runner.invoke(main, ["contacts", "search", "john"])
        assert result.exit_code == 0
        assert "john" in result.output.lower() or "John" in result.output
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[1]["params"]["query"] == "john"

    def test_contacts_tag(self, runner, mock_token, mock_location_id, mock_client, sample_contact):
        """Test adding tags to a contact."""
        # First call returns contact with existing tags
        mock_client.get.return_value = {"contact": sample_contact}
        # Second call is the update
        mock_client.put.return_value = {"contact": sample_contact}

        result = runner.invoke(main, ["contacts", "tag", "contact-123", "--tag", "NewTag"])
        assert result.exit_code == 0
        assert "Tags added" in result.output
        # Verify update was called with merged tags
        mock_client.put.assert_called_once()
        call_args = mock_client.put.call_args
        tags = call_args[1]["json"]["tags"]
        assert "NewTag" in tags
        assert "VIP" in tags  # Existing tag should remain

    def test_contacts_untag(self, runner, mock_token, mock_location_id, mock_client, sample_contact):
        """Test removing tags from a contact."""
        # First call returns contact with existing tags
        mock_client.get.return_value = {"contact": sample_contact}
        # Second call is the update
        mock_client.put.return_value = {"contact": sample_contact}

        result = runner.invoke(main, ["contacts", "untag", "contact-123", "--tag", "VIP"])
        assert result.exit_code == 0
        assert "Tags removed" in result.output
        # Verify update was called with tags removed
        mock_client.put.assert_called_once()
        call_args = mock_client.put.call_args
        tags = call_args[1]["json"]["tags"]
        assert "VIP" not in tags
        assert "Customer" in tags  # Other tag should remain

    def test_contacts_notes(self, runner, mock_token, mock_location_id, mock_client):
        """Test listing contact notes."""
        notes = [
            {"id": "note-1", "body": "First note", "dateAdded": "2024-01-01T00:00:00Z"},
            {"id": "note-2", "body": "Second note", "dateAdded": "2024-01-02T00:00:00Z"},
        ]
        mock_client.get.return_value = {"notes": notes}

        result = runner.invoke(main, ["contacts", "notes", "contact-123"])
        assert result.exit_code == 0
        assert "First note" in result.output
        assert "Second note" in result.output
        mock_client.get.assert_called_once_with("/contacts/contact-123/notes")

    def test_contacts_add_note(self, runner, mock_token, mock_location_id, mock_client):
        """Test adding a note to a contact."""
        mock_client.post.return_value = {"note": {"id": "note-123"}}

        result = runner.invoke(main, ["contacts", "add-note", "contact-123", "This is a test note"])
        assert result.exit_code == 0
        assert "Note added" in result.output
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/contacts/contact-123/notes"
        assert call_args[1]["json"]["body"] == "This is a test note"

    def test_contacts_tasks(self, runner, mock_token, mock_location_id, mock_client):
        """Test listing contact tasks."""
        tasks = [
            {
                "id": "task-1",
                "title": "Follow up",
                "dueDate": "2024-01-20T00:00:00Z",
                "completed": False,
                "assignedTo": "user-123",
            }
        ]
        mock_client.get.return_value = {"tasks": tasks}

        result = runner.invoke(main, ["contacts", "tasks", "contact-123"])
        assert result.exit_code == 0
        assert "Follow up" in result.output
        mock_client.get.assert_called_once_with("/contacts/contact-123/tasks")
