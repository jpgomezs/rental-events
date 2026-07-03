from app.services.rental_events import import_events_report
from app.services.assets import rented_assets_by_id
from app.services.polling import watch_for_event


def main() -> None:
    """Run the rental event polling loop.

    Monitors rented assets at a fixed interval and imports the latest
    events report whenever a check-in or check-out is detected.
    """
    interval = 10
    previous_snapshot = rented_assets_by_id()

    while True:
        has_events, previous_snapshot =watch_for_event(
            previous_snapshot,
            interval=interval,
        )

        if has_events:
            print("Asset check-in or check-out detected, processing report")
            import_events_report()

        else:
            print(
                f"No asset check-in or check-out detected: ",
                f"Next run in {interval} seconds"
            )


if __name__ == "__main__":
    main()
