from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db_base import Base

SQL_ALCHEMY_DB_URL = "postgresql+psycopg:///rental_events"

engine = create_engine(SQL_ALCHEMY_DB_URL, echo=True)

Session = sessionmaker(bind=engine)
