"""Configure database connectivity and SQLAlchemy components."""


import os

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import DeclarativeBase, sessionmaker

password = os.environ["EPIC_EVENTS_DB_PASSWORD"]

url = URL.create(
    drivername="mysql+pymysql",
    username="epic_events_app",
    password=password,
    host="172.29.16.1",
    port=3306,
    database="epic_events"
)

engine = create_engine(url=url, echo=True)

if __name__ == "__main__":
    with engine.connect() as connection:
        print("Connection successful!")


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""


session_factory = sessionmaker(bind=engine)
