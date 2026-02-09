"""Tests for conversation commands (mocked to avoid sending real messages)."""

import pytest
from click.testing import CliRunner

from ghl.cli import main


class TestConversationCommands:
    """Test conversation management commands."""

    def test_conversations_list(self, runner, mock_token, mock_location_id, mock_conversation_client, sample_conversation):
        """Test listing conversations."""
        mock_conversation_client.get.return_value = {"conversations": [sample_conversation]}

        result = runner.invoke(main, ["conversations", "list"])
        assert result.exit_code == 0
        assert "conv-123" in result.output
        mock_conversation_client.get.assert_called_once()
        call_args = mock_conversation_client.get.call_args
        assert "/conversations/search" in call_args[0][0]

    def test_conversations_list_with_contact_filter(
        self, runner, mock_token, mock_location_id, mock_conversation_client, sample_conversation
    ):
        """Test listing conversations filtered by contact."""
        mock_conversation_client.get.return_value = {"conversations": [sample_conversation]}

        result = runner.invoke(main, ["conversations", "list", "--contact", "contact-123"])
        assert result.exit_code == 0
        mock_conversation_client.get.assert_called_once()
        call_args = mock_conversation_client.get.call_args
        assert call_args[1]["params"]["contactId"] == "contact-123"

    def test_conversations_get(self, runner, mock_token, mock_location_id, mock_conversation_client, sample_conversation):
        """Test getting a conversation by ID."""
        mock_conversation_client.get.return_value = {"conversation": sample_conversation}

        result = runner.invoke(main, ["conversations", "get", "conv-123"])
        assert result.exit_code == 0
        assert "conv-123" in result.output
        mock_conversation_client.get.assert_called_once_with("/conversations/conv-123")

    def test_conversations_messages(self, runner, mock_token, mock_location_id, mock_conversation_client):
        """Test listing messages in a conversation."""
        messages = [
            {
                "id": "msg-1",
                "type": "sms",
                "direction": "outbound",
                "body": "Hello!",
                "dateAdded": "2024-01-01T00:00:00Z",
            }
        ]
        mock_conversation_client.get.return_value = {"messages": messages}

        result = runner.invoke(main, ["conversations", "messages", "conv-123"])
        assert result.exit_code == 0
        assert "Hello!" in result.output
        mock_conversation_client.get.assert_called_once()
        call_args = mock_conversation_client.get.call_args
        assert call_args[0][0] == "/conversations/conv-123/messages"
        assert call_args[1]["params"]["limit"] == 20

    def test_conversations_search(self, runner, mock_token, mock_location_id, mock_conversation_client, sample_conversation):
        """Test searching conversations."""
        mock_conversation_client.get.return_value = {"conversations": [sample_conversation]}

        result = runner.invoke(main, ["conversations", "search", "test"])
        assert result.exit_code == 0
        mock_conversation_client.get.assert_called_once()
        call_args = mock_conversation_client.get.call_args
        assert call_args[1]["params"]["q"] == "test"

    def test_conversations_send_sms_mocked(
        self, runner, mock_token, mock_location_id, mock_conversation_client, sample_conversation
    ):
        """Test sending SMS (mocked to avoid sending real messages)."""
        mock_conversation_client.post.return_value = {"message": {"id": "msg-123"}}

        result = runner.invoke(
            main,
            [
                "conversations",
                "send",
                "--contact",
                "contact-123",
                "--type",
                "sms",
                "--message",
                "Test message",
            ],
        )
        assert result.exit_code == 0
        assert "Message sent" in result.output
        mock_conversation_client.post.assert_called_once()
        call_args = mock_conversation_client.post.call_args
        assert call_args[0][0] == "/conversations/messages"
        data = call_args[1]["json"]
        assert data["contactId"] == "contact-123"
        assert data["type"] == "SMS"
        assert data["message"] == "Test message"

    def test_conversations_send_email_mocked(
        self, runner, mock_token, mock_location_id, mock_conversation_client, sample_conversation
    ):
        """Test sending email (mocked to avoid sending real emails)."""
        mock_conversation_client.post.return_value = {"message": {"id": "msg-123"}}

        result = runner.invoke(
            main,
            [
                "conversations",
                "send",
                "--contact",
                "contact-123",
                "--type",
                "email",
                "--subject",
                "Test Subject",
                "--message",
                "Test body",
            ],
        )
        assert result.exit_code == 0
        assert "Message sent" in result.output
        mock_conversation_client.post.assert_called_once()
        call_args = mock_conversation_client.post.call_args
        data = call_args[1]["json"]
        assert data["contactId"] == "contact-123"
        assert data["type"] == "Email"
        assert data["subject"] == "Test Subject"
        assert data["message"] == "Test body"
