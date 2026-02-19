"""GHL CLI command groups."""

from .calendars import calendars
from .config_cmd import config
from .contacts import contacts
from .conversations import conversations
from .custom_fields import custom_fields
from .locations import locations
from .opportunities import opportunities
from .pipelines import pipelines
from .tags import tags
from .tasks import tasks
from .users import users
from .workflows import workflows

__all__ = [
    "calendars",
    "config",
    "contacts",
    "conversations",
    "custom_fields",
    "locations",
    "opportunities",
    "pipelines",
    "tags",
    "tasks",
    "users",
    "workflows",
]
