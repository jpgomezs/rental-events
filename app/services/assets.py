from app.clients.ezrentout.client import create_http_client, EzRentOutClient
from app.schemas.schemas import Asset


def rented_out_assets() -> list[Asset]:
    """Return all assets that are currently rented out.

    Retrieves the list of rented-out assets from the EZRentOut API,
    converts the response into a list of `Asset` models,
    and closes the API client before returning.
    """
    http_client = create_http_client()
    ezrentout = EzRentOutClient(http_client)

    try:
        data = ezrentout.get_all_rented_out_assets()

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
        http_client.close()

# Transforms data format of rented_out_assets
def rented_assets_by_id() -> dict[int, Asset]:
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
