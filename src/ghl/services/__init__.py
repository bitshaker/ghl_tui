"""Service layer shared by CLI and TUI."""

from .contacts import (
    add_note,
    add_tag,
    contacts_search,
    create_contact,
    delete_contact,
    get_contact,
    list_contacts,
    list_notes,
    list_tasks,
    remove_tag,
    search_contacts,
    update_contact,
)
from .opportunities import (
    create_opportunity,
    delete_opportunity,
    get_opportunity,
    list_opportunities,
    mark_lost,
    mark_won,
    move_opportunity,
    update_opportunity,
)
from .pipelines import get_pipeline, list_pipelines, list_stages
from .tasks import search_tasks
from .users import list_users

__all__ = [
    "add_note",
    "add_tag",
    "contacts_search",
    "create_contact",
    "delete_contact",
    "get_contact",
    "list_users",
    "get_pipeline",
    "get_opportunity",
    "list_contacts",
    "list_notes",
    "list_opportunities",
    "list_pipelines",
    "list_stages",
    "list_tasks",
    "mark_lost",
    "mark_won",
    "move_opportunity",
    "remove_tag",
    "search_contacts",
    "search_tasks",
    "update_contact",
    "update_opportunity",
    "create_opportunity",
    "delete_opportunity",
]
