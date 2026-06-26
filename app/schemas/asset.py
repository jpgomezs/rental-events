from pydantic import BaseModel

class Asset(BaseModel):
    ez_id: int
    internal_id: str
    state: str
    rental_meter: int
    checkout_on: str
    hour_meter: float
    last_order_id: str | None = None
