import time

from app.services.rental_events import (
    detect_asset_changes,
    download_events_report,
    rented_assets_ids,
    parse_datetime,
    ingest_report,
    process_csv,
)


def main():
    previous_snapshot = rented_assets_ids()

    while True:
        time.sleep(10)
        current_snapshot = rented_assets_ids()
        events = detect_asset_changes(previous_snapshot, current_snapshot)


        has_events = bool(events['check_ins'] or events['check_outs'])

        if not has_events:
            print("No asset check-in or check-out detected")
        else:
            reader =download_events_report()
            print("Asset check-in or check-out detected, processing report")
            time.sleep(10)
            clean_reader = process_csv(reader)
            ingest_report(clean_reader)

        previous_snapshot = current_snapshot


if __name__ == "__main__":
    main()
