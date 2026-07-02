# Asset Fuel Automation
## Objective

When a fueled asset is returned, a charge for fuel should be added to the EZRental basket as an order line. The order line should include asset internal code, qty of gallons and the total amount for the line.

## Limitations

* Ezrentout doesn't record fuel events for swaps, or early returns.
* Ezrentout's API doesn't expose order id when an item is returned, so a custom report will have to be used to track events.


## Data Flow

Asset Snapshot

Asset Snapshot

Compare Snapshots

If event exist

Request Report

Download Report

Validate Data

If event incomplete mark incomplete in db

If event is incomplete, get information from staff

If event gets completed (by report or by staff input, post to EZ should be made)
