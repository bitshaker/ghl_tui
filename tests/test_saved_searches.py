"""Tests for saved_searches module."""

import pytest

from ghl import saved_searches


class TestSavedSearches:
    """Test list, save, delete, get_saved_search."""

    def test_list_empty_when_no_file(self, mock_config_dir):
        """list_saved_searches returns [] when file does not exist."""
        assert saved_searches.list_saved_searches() == []

    def test_save_and_list(self, mock_config_dir):
        """save_search persists and list_saved_searches returns it."""
        out = saved_searches.save_search(name="My search", query="john", tags=["VIP"])
        assert out["name"] == "My search"
        assert out["query"] == "john"
        assert out["tags"] == ["VIP"]
        assert "id" in out
        listed = saved_searches.list_saved_searches()
        assert len(listed) == 1
        assert listed[0]["name"] == "My search"
        assert listed[0]["id"] == out["id"]

    def test_save_update_by_id(self, mock_config_dir):
        """save_search with id updates existing and does not duplicate."""
        one = saved_searches.save_search(name="First", query="a", id="id-1")
        assert one["id"] == "id-1"
        two = saved_searches.save_search(name="Updated", query="b", id="id-1")
        assert two["name"] == "Updated"
        assert two["id"] == "id-1"
        listed = saved_searches.list_saved_searches()
        assert len(listed) == 1
        assert listed[0]["name"] == "Updated"

    def test_delete_saved_search(self, mock_config_dir):
        """delete_saved_search removes by id and returns True."""
        saved_searches.save_search(name="To remove", id="remove-me")
        assert len(saved_searches.list_saved_searches()) == 1
        ok = saved_searches.delete_saved_search("remove-me")
        assert ok is True
        assert saved_searches.list_saved_searches() == []
        assert saved_searches.delete_saved_search("remove-me") is False

    def test_get_saved_search(self, mock_config_dir):
        """get_saved_search returns the search by id or None."""
        assert saved_searches.get_saved_search("missing") is None
        saved_searches.save_search(name="Found", id="find-me")
        found = saved_searches.get_saved_search("find-me")
        assert found is not None
        assert found["name"] == "Found"
        assert found["id"] == "find-me"
