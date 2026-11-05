from sqlalchemy.orm import configure_mappers

from epic_events.models.contract import Contract
from epic_events.models.customer import Customer
from epic_events.models.employee import Employee
from epic_events.models.event import Event
from epic_events.models.role import Role


def test_orm_mappings():
    """Verify that all ORM mappings can be configured."""
    configure_mappers()
