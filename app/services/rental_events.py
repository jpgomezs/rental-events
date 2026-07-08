import csv
from http import client
import time
import httpx
from datetime import datetime
from _collections_abc import Iterator
from io import StringIO

from app.clients import ezrentout
from app.database import Session
from app.models.rental_event import Event
from sqlalchemy.dialects.postgresql import insert

from app.clients.ezrentout.client import (
    EzRentOutClient,
    create_http_client,
)

from app.schemas.schemas import EventReportRow


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
    with create_http_client() as http_client:
        client = EzRentOutClient(http_client)

        report_job_id = request_events_report_job_id(client)
        wait_for_report(seconds=20)
        return download_csv(client, report_job_id)

EVENTS_REPORT_ID = "707267"

def request_events_report_job_id(client: EzRentOutClient) -> str:
    """Request generation of the events report and return its background job ID.

    Initiates the export of the configured events report through the
    EZRentOut API and extracts the identifier of the background job
    responsible for generating the report.

    Returns:
        The background job ID used to track report generation.

    Raises:
        httpx.HTTPStatusError: If the report request fails.
        KeyError: If the expected background job ID is missing from
            the API response.
    """
    report_data = client.export_custom_report(EVENTS_REPORT_ID)
    report_job_id =  report_data['background_job']['id']
    return report_job_id

# TODO: Consider polling to know when the report is ready
def wait_for_report(seconds: int) -> None:
    """Pause execution to allow the report to be generated.

    Waits for the specified number of seconds before returning.
    This is a temporary implementation until report readiness is
    determined by polling the background job status.

    Args:
        seconds: Number of seconds to wait.
    """
    time.sleep(seconds)


def download_csv(client: EzRentOutClient, background_job_id: str) -> csv.DictReader:
    """Download the generated events report as a CSV reader.

    Retrieves the background job details from the EZRentOut API,
    obtains the download URL of the generated report, downloads the
    CSV file, and returns it as a `csv.DictReader`.

    Args:
        client: EZRentOut API client.
        background_job_id: Identifier of the background job that
            generated the report.

    Returns:
        csv.DictReader: Reader for the downloaded CSV report.

    Raises:
        ValueError: If the background job has no attachments or no
            download URL.
        httpx.HTTPStatusError: If downloading the CSV fails.
    """
    background_jobs_details = client.get_background_job_details(background_job_id)
    attachments = background_jobs_details['background_job']['attachments']

    if not attachments:
        raise ValueError(f"No attachments found for job {background_job_id}")

    download_url = attachments[0].get('download_url')

    if not download_url:
        raise ValueError(f"No download URL found for job {background_job_id}")

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


def import_events_report() -> None:
    """Download, process, and ingest the latest rental events report.

    Retrieves the latest events report from EZRentOut, transforms the
    CSV into validated event records, and stores them in the database.
    """
    reader = download_events_report()
    clean_reader = process_csv(reader)
    ingest_report(clean_reader)
