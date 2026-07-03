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
from app.clients.ezrentout.client import (
    EzRentOutClient,
    create_http_client,
)
from app.schemas.schemas import EventReportRow


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
    http_client = create_http_client()
    ezrentout = EzRentOutClient(http_client)

    report_data = ezrentout.export_custom_report()

    report_id =  report_data['background_job']['id']

    time.sleep(20)
    background_jobs_details = ezrentout.get_background_job_details(report_id)

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


def process_csv(
    reader: csv.DictReader,
) -> Iterator[dict[str, str | datetime | None]]:
    """Yield normalized rows from a CSV reader.

    Strips whitespace from column names, converts empty and "N/A"
    values to `None`, parses date fields into `datetime` objects,
    and yields each processed row.
    """
    date_keys = [
        'Rentouts / Returns - Action Taken On',
        'Order Line Item - Rent Out/Selling Date',
        'Order Line Item - Return Date',
        'Rentouts / Returns - Expected Return Date',
    ]

    for row in reader:
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
