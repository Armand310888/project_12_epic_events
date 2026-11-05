from sqlalchemy.orm import configure_mappers

import epic_events.models


def test_orm_mappings():
    """Verify that all ORM mappings can be configured."""
    configure_mappers()
