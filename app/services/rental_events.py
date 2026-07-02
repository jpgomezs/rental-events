import csv
from datetime import datetime
from _collections_abc import Iterator

from app.database import Session
from app.models.rental_event import Event
from sqlalchemy.dialects.postgresql import insert

import time
import httpx
import csv
from io import StringIO
from app.clients.ezrentout import EzRentOutEndpoint, create_ezrentout_client
from app.schemas.schemas import Asset, EventReportRow


def rented_out_assets() -> list[Asset]:
    """Return all assets that are currently rented out.

    Retrieves the list of rented-out assets from the EZRentOut API,
    converts the response into a list of `Asset` models,
    and closes the API client before returning.
    """
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

# TODO:
# Consider renaming function to: rented_assets_by_id() -> dict[int, Asset]:
# because it returns a mapping from IDs to assets, not just the IDs themselves.
def rented_assets_ids() -> dict[int, Asset]:
    """Return a mapping of EZRentOut asset IDs to `Asset` models."""
    rented_assets = rented_out_assets()

    return {
        asset.ez_id: asset
        for asset in  rented_assets
    }


def detect_asset_changes(
    previous: dict[int, Asset],
    current: dict[int, Asset],
) -> dict[str, list[Asset]]:
    """Detect changes between two snapshots of rented assets.

    Returns a dictionary containing two lists:
    - ``check_ins``: Assets that are no longer rented.
    - ``check_outs``: Assets that have been newly rented.
    """
    previous_ids = set(previous)
    current_ids = set(current)

    check_in_ids = previous_ids - current_ids
    check_out_ids = current_ids - previous_ids

    return {
        "check_ins": [previous[asset_id] for asset_id in check_in_ids],
        "check_outs": [current[asset_id] for asset_id in check_out_ids],
    }

# Consider splitting it into smaller helpers, see notes.txt
def download_events_report() -> csv.DictReader:
    """Download the latest events report as a CSV reader.

    Requests the configured custom report from the EZRentOut API,
    waits for the report to be generated, downloads the CSV file,
    and returns a `csv.DictReader`.

    Raises:
        ValueError: If the generated report has no attachment or
            download URL.
        httpx.HTTPStatusError: If any HTTP request fails.
    """
    ezrent_client = create_ezrentout_client()
    ezrent_endpoint = EzRentOutEndpoint(ezrent_client)

    report_data = ezrent_endpoint.export_custom_report()

    report_id =  report_data['background_job']['id']

    time.sleep(20)
    background_jobs_details = ezrent_endpoint.get_background_job_details(report_id)

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
    """Parse a date and time string in ``"%d-%m-%Y %H:%M"`` format."""
    return datetime.strptime(value, "%d-%m-%Y %H:%M")


# TODO:
# Move date_keys outside the loop
def process_csv(
    reader: csv.DictReader,
) -> Iterator[dict[str, str | datetime | None]]:
    """Yield normalized rows from a CSV reader.

    Strips whitespace from column names, converts empty and "N/A"
    values to `None`, parses date fields into `datetime` objects,
    and yields each processed row.
    """
    for row in reader:
        date_keys = [
            'Rentouts / Returns - Action Taken On',
            'Order Line Item - Rent Out/Selling Date',
            'Order Line Item - Return Date',
            'Rentouts / Returns - Expected Return Date',
        ]
        processed_row = {}

        for key, value in row.items():
            clean_key = key.strip()
            clean_value = None if value in ("", "N/A") else value
            if clean_key in date_keys and clean_value is not None:
                clean_value = datetime.strptime(value, '%d-%m-%Y %H:%M')

            processed_row[clean_key] = clean_value
        # Yield the complete row before moving to the next one
        yield processed_row

def ingest_report(
    reader: Iterator[dict[str, str | datetime | int | float | None]],
) -> None:
    """Insert processed report rows into the database.

    Validates each row against the `EventReportRow` model,
    inserts it into the database, ignores duplicate events,
    and commits the transaction.
    """
    with Session() as session:
        for row in reader:
            report_event = EventReportRow.model_validate(row)

            statement = (
                insert(Event).values(**report_event.model_dump())
                .on_conflict_do_nothing(
                index_elements=["ain", "action_taken_on", "action"]
                )
            )

            # NOTE: execute() clearly separates two phases: building the
            # statement, and executing the statement.
            session.execute(statement)

        session.commit()


            # NOTE: SQLAlchemy statements are immutable. Methods that add
            # clauses return a new statement, so reassign the variable.
            # NOTE: Statements can be built incrementally by chaining methods
            # as in the example shown below.

            #statement = insert(Event).values(**report_event.model_dump())

            #statement = statement.on_conflict_do_nothing(
            #    index_elements=["ain", "action_taken_on", "action"]
            #)
