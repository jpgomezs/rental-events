from app.database import engine
from app.db_base import Base
from app.models.rental_event import Event
from app.services.rental_events import import_events_report
from app.services.assets import rented_assets_by_id
from app.services.polling import watch_for_event


def main() -> None:
    """Initialize the database and run the rental event polling loop.

    Ensures the application's database schema exists, then monitors
    rented assets at a fixed interval and imports the latest events
    report whenever a check-in or check-out is detected.
    """
    Base.metadata.create_all(bind=engine)

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
