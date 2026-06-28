import csv
from pathlib import Path
from datetime import datetime

from app.database import Session
from app.models.rental_event import Event
from sqlalchemy.dialects.postgresql import insert

import time
import httpx
import csv
from io import StringIO
from app.clients.ezrentout import EzRentOutEndpoint, create_ezrentout_client
from app.schemas.asset import Asset

def rented_out_assets() -> list[Asset]:
    ezrent_client = create_ezrentout_client()
    ezrent_endpoint = EzRentOutEndpoint(ezrent_client)

    try:
        data = ezrent_endpoint.get_all_rented_out_assets()

        return [
            Asset(
                ez_id=asset["sequence_num"],
                internal_id=asset["identifier"],
                state=asset["state"],
                rental_meter=asset["rental_meter"],
                checkout_on=asset["checkout_on"],
                hour_meter=float(asset["current_meter_reading"])
            )
            for asset in data
        ]

    finally:
        ezrent_client.close()

def rented_assets_ids() -> set:
    rented_assets = rented_out_assets()

    # {} is the syntax literal marker for defining a set
    return {
        asset.ez_id: asset
        for asset in  rented_assets
    }

def detect_asset_changes(
    previous: dict[int, Asset],
    current: dict[int, Asset],
) -> dict[str, list[Asset]]:
    previous_ids = set(previous)
    current_ids = set(current)

    check_in_ids = previous_ids - current_ids
    check_out_ids = current_ids - previous_ids

    return {
        "check_ins": [previous[asset_id] for asset_id in check_in_ids],
        "check_outs": [current[asset_id] for asset_id in check_out_ids],
    }

def download_events_report() -> csv.DictReader:
    ezrent_client = create_ezrentout_client()
    ezrent_endpoint = EzRentOutEndpoint(ezrent_client)

    report_data = ezrent_endpoint.export_custom_report()

    report_id =  report_data['background_job']['id']

    time.sleep(20)
    background_jobs_details = ezrent_endpoint.get_backgroud_job_details(report_id)

    attachments = background_jobs_details['background_job']['attachments']

    if not attachments:
        raise ValueError(f"No attachments found for report {report_id}")

    download_url = attachments[0].get('download_url')

    if not download_url:
        raise ValueError(f"No download URL found for report {report_id}")

    response = httpx.get(download_url)
    response.raise_for_status()

    reader = csv.DictReader(StringIO(response.text))

    return reader

def parse_datetime(value: str) -> datetime:
    return datetime.strptime(value, "%d-%m-%Y %H:%M")


def maybe_int(value):
    return int(value) if value not in ("", None) else None


def maybe_float(value):
    return float(value) if value not in ("", None) else None


def maybe_datetime(value):
    return parse_datetime(value) if value not in ("", None) else None


def ingest_report(reader):
    with Session() as session:
        for row in reader:
            values = {
                "ain": row["Rentouts / Returns - AIN"],
                "action_taken_on": parse_datetime(row["Rentouts / Returns - Action Taken On"]),
                "action": row["Rentouts / Returns - Action"],

                "item_id": maybe_int(row["Rentouts / Returns - Item#"]),
                "order_id": maybe_int(row["Order - Order#"]),
                "quantity": maybe_int(row["Rentouts / Returns - Quantity"]),

                "fuel_percentage": maybe_float(row["Rentouts / Returns - Porcentaje de combustible "]),
                "meter_reading": maybe_float(row["Item - Rental Meter (Current Value)"]),

                "item_name": row["Rentouts / Returns - Item Name"],
                "item_type": row["Item - Item Type"],
                "oin": row["Order - Identification Number"],

                "actual_usage": maybe_int(row["Order Line Item - Actual Usage"]),
                "meter_start": maybe_float(row["Order Line Item - Meter Start"]),
                "meter_end": maybe_float(row["Order Line Item - Meter End"]),

                "rentout_date": maybe_datetime(row["Order Line Item - Rent Out/Selling Date"]),
                "return_date": maybe_datetime(row["Order Line Item - Return Date"]),

                "fuel_capacity": maybe_float(row["Item - Capacidad Combustible Gal"]),
                "fuel_type": row["Item - Tipo Combustible"] or None,

                "expected_return_date": maybe_datetime(row["Rentouts / Returns - Expected Return Date"]),
            }

            statement = insert(Event).values(**values)
            statement = statement.on_conflict_do_nothing(
                index_elements=["ain", "action_taken_on", "action"]
            )

            session.execute(statement)

        session.commit()
