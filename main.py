import time

from app.services.rental_events import detect_asset_changes, download_events_report, download_events_report, rented_assets_ids

def main():
    previous_snapshot = rented_assets_ids()

    while True:
        time.sleep(10)
        current_snapshot = rented_assets_ids()
        events = detect_asset_changes(previous_snapshot, current_snapshot)
        print(events)
        previous_snapshot = current_snapshot

if __name__ == "__main__":
    #main()
    rows = download_events_report()

    for row in rows:
        print(row)
