from datetime import datetime

from pydantic import BaseModel, Field
from sqlalchemy import Null


class Asset(BaseModel):
    ez_id: int
    internal_id: str
    state: str
    rental_meter: int
    checkout_on: str
    hour_meter: float
    last_order_id: str | None = None

class Event(BaseModel):
    ain: str = Field(validation_alias="Rentouts / Returns - AIN")

    action_taken_on: datetime = Field(
        validation_alias="Rentouts / Returns - Action Taken On",
    )

    action: str = Field(validation_alias="Rentouts / Returns - Action")

    fuel_percentage: int | None = Field(
        validation_alias="Rentouts / Returns - Porcentaje de combustible",
    )

    quantity: int = Field(validation_alias="Rentouts / Returns - Quantity")

    oin: str = Field(validation_alias="Order - Identification Number")

    actual_usage: float | None = Field(
        None,
        validation_alias="Order Line Item - Actual Usage",
    )

    meter_start: float | None = Field(
        validation_alias="Order Line Item - Meter Start",
    )

    meter_end: float | None = Field(
        validation_alias="Order Line Item - Meter End",
    )

    item_id: int = Field(validation_alias="Rentouts / Returns - Item#")

    order_id: int = Field(validation_alias="Order - Order#")

    rentout_date: datetime | None = Field(
        None,
        validation_alias="Order Line Item - Rent Out/Selling Date",
    )

    return_date: datetime | None = Field(
        None,
        validation_alias="Order Line Item - Return Date",
    )

    fuel_capacity: float | None = Field(
        None,
        validation_alias="Item - Capacidad Combustible Gal",
    )

    fuel_type: str | None = Field(
        None,
        validation_alias="Item - Tipo Combustible",
    )

    item_name: str = Field(validation_alias="Rentouts / Returns - Item Name")

    rental_meter_ez: int = Field(
        validation_alias="Item - Rental Meter (Current Value)"
    )

    expected_return_date: datetime = Field(
        validation_alias="Rentouts / Returns - Expected Return Date"
    )

    item_type: str = Field(validation_alias="Item - Item Type")
