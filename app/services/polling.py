import time

from app.services.assets import Asset
from app.services.assets import (
    rented_assets_by_id,
    detect_asset_changes,
)


# TODO:
# Consider type alias AssetSnapshot = dict[int, Asset],
# or using a list type
def watch_for_event(
    previous_snapshot: dict[int, Asset],
    interval: int
) -> tuple[bool, dict[int, Asset]]:
    """Poll for rental asset check-in and check-out events.

    Waits for the specified polling interval, compares the previous and
    current rented asset snapshots, and returns:

    - `has_events`: `True` if any check-ins or check-outs were detected.
    - `current_snapshot`: The latest rented asset snapshot to use in the
      next polling cycle.
    """
    time.sleep(interval)
    current_snapshot = rented_assets_by_id()
    events = detect_asset_changes(previous_snapshot, current_snapshot)

    has_events = bool(events['check_ins'] or events['check_outs'])

    return has_events, current_snapshot
