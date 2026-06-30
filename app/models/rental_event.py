from sqlalchemy import (Integer,
                        String,
                        DateTime,
                        Float,
                        Column,
                        UniqueConstraint,
)

from app.db_base import Base


class Event(Base):
    __tablename__ = 'events'

    __table_args__ = (
        UniqueConstraint('ain', 'action_taken_on', 'action'),
    )

    id = Column(Integer, primary_key=True)
    ain = Column(String)
    action_taken_on = Column(DateTime)
    action = Column(String)
    fuel_percentage = Column(Float)
    quantity = Column(Integer)
    oin = Column(String)
    actual_usage = Column(Integer)
    meter_start = Column(Float)
    meter_end = Column(Float)
    item_id = Column(Integer)
    order_id = Column(Integer)
    rentout_date = Column(DateTime)
    return_date = Column(DateTime)
    fuel_capacity = Column(Float)
    fuel_type = Column(String)
    item_name = Column(String)
    rental_meter_ez = Column(Integer)
    expected_return_date = Column(DateTime)
    item_type = Column(String)
