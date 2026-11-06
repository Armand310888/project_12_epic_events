"""Preview the MySQL database schema generated from SQLAlchemy ORM models."""

from sqlalchemy.dialects import mysql
from sqlalchemy.schema import CreateTable

import epic_events.models
from epic_events.database import Base


print("USE epic_events;")

for table in Base.metadata.sorted_tables:
    table_creator = CreateTable(table).compile(dialect=mysql.dialect())

    print(f"{str(table_creator).rstrip()};")
