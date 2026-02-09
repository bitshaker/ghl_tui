"""Tests for service layer (contacts, opportunities, pipelines)."""

from unittest.mock import MagicMock

import pytest

from ghl.services import contacts as contact_svc
from ghl.services import opportunities as opp_svc
from ghl.services import pipelines as pipeline_svc


@pytest.fixture
def mock_client():
    return MagicMock()


class TestContactsService:
    def test_list_contacts(self, mock_client):
        mock_client.get.return_value = {"contacts": [{"id": "c1", "firstName": "A"}]}
        out = contact_svc.list_contacts(mock_client, limit=10)
        assert len(out) == 1
        assert out[0]["id"] == "c1"
        mock_client.get.assert_called_once()
        args, kwargs = mock_client.get.call_args
        assert args[0] == "/contacts/"
        assert kwargs["params"]["limit"] == 10

    def test_list_contacts_with_query(self, mock_client):
        mock_client.get.return_value = {"contacts": []}
        contact_svc.list_contacts(mock_client, limit=20, query="john")
        mock_client.get.assert_called_once()
        assert mock_client.get.call_args[1]["params"]["query"] == "john"

    def test_get_contact(self, mock_client):
        mock_client.get.return_value = {"contact": {"id": "c1", "email": "a@b.com"}}
        out = contact_svc.get_contact(mock_client, "c1")
        assert out["id"] == "c1"
        mock_client.get.assert_called_once_with("/contacts/c1")

    def test_create_contact(self, mock_client):
        mock_client.post.return_value = {"contact": {"id": "c2"}}
        out = contact_svc.create_contact(
            mock_client, location_id="loc1", email="x@y.com", first_name="X"
        )
        assert out["id"] == "c2"
        mock_client.post.assert_called_once()
        body = mock_client.post.call_args[1]["json"]
        assert body["locationId"] == "loc1"
        assert body["email"] == "x@y.com"
        assert body["firstName"] == "X"

    def test_add_tag(self, mock_client):
        mock_client.get.return_value = {"contact": {"id": "c1", "tags": ["A"]}}
        mock_client.put.return_value = {}
        contact_svc.add_tag(mock_client, "c1", ["B"])
        mock_client.put.assert_called_once()
        tags = mock_client.put.call_args[1]["json"]["tags"]
        assert set(tags) == {"A", "B"}


class TestOpportunitiesService:
    def test_list_opportunities(self, mock_client):
        mock_client.get.return_value = {"opportunities": [{"id": "o1", "name": "Deal"}]}
        out = opp_svc.list_opportunities(mock_client, limit=5)
        assert len(out) == 1
        mock_client.get.assert_called_once()
        assert "/opportunities/search" in mock_client.get.call_args[0][0]
        assert mock_client.get.call_args[1]["params"]["limit"] == 5

    def test_list_opportunities_with_filters(self, mock_client):
        mock_client.get.return_value = {"opportunities": []}
        opp_svc.list_opportunities(
            mock_client, pipeline_id="p1", stage_id="s1", status="open"
        )
        params = mock_client.get.call_args[1]["params"]
        assert params["pipelineId"] == "p1"
        assert params["pipelineStageId"] == "s1"
        assert params["status"] == "open"

    def test_move_opportunity(self, mock_client):
        mock_client.put.return_value = {"opportunity": {"id": "o1", "pipelineStageId": "s2"}}
        out = opp_svc.move_opportunity(mock_client, "o1", "s2")
        assert out["pipelineStageId"] == "s2"
        mock_client.put.assert_called_once()
        assert mock_client.put.call_args[1]["json"]["pipelineStageId"] == "s2"


class TestPipelinesService:
    def test_list_pipelines(self, mock_client):
        mock_client.get.return_value = {"pipelines": [{"id": "p1", "name": "Sales"}]}
        out = pipeline_svc.list_pipelines(mock_client)
        assert len(out) == 1
        mock_client.get.assert_called_once_with("/opportunities/pipelines")

    def test_get_pipeline(self, mock_client):
        mock_client.get.return_value = {
            "pipeline": {"id": "p1", "name": "Sales", "stages": [{"id": "s1"}]},
        }
        out = pipeline_svc.get_pipeline(mock_client, "p1")
        assert out["id"] == "p1"
        assert len(out["stages"]) == 1
        mock_client.get.assert_called_once_with("/opportunities/pipelines/p1")

    def test_list_stages(self, mock_client):
        mock_client.get.return_value = {
            "pipeline": {"stages": [{"id": "s1", "name": "Lead"}]},
        }
        out = pipeline_svc.list_stages(mock_client, "p1")
        assert len(out) == 1
        assert out[0]["name"] == "Lead"
