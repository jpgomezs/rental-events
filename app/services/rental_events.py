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

def download_events_report() -> list[csv.DictReader]:
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

    return list(reader)
