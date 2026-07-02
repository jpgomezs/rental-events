# Main Workflow Description

Event Polling
(Could also be handled by downloading the report every x amount of time)
        │
        ▼
Ingest Report if changes detected
(if changes detected; includes download, validation, completeness evaluation, and storage)
        │
        ▼
Complete Incomplete Events
(staff enters missing data through a separate input table)
        │
        ▼
Post fuel charge Line to EZRentout
(for completed events that have not yet been posted)


## Event Polling

1. Get the initial snapshot of currently rented-out assets/orders from EZRentOut.

2. Start polling loop.

3. Wait a fixed amount of time.

4. Get a new snapshot of currently rented-out assets/orders.

5. Compare the previous snapshot with the new snapshot.

6. If changes detected:
    Ingest report.

7. Update previous snapshot.

8. Continue polling.


## Ingest Report Worflow

1. Download report.

2. Read report.

3. For each report row:
       Validate row.
       Evaluate completeness.
       Build Event.
       Store Event.

4. Commit transaction.


### Event Completeness Evaluation

1. Determine the fields required for this event.
       - Fuel percentage (if the asset requires fuel tracking).
       - Hour meter (if the asset requires meter tracking).
       - Additional requirements as defined by future business rules.

2. Verify that all required fields are present.

3. If one or more required fields are missing:
       Return "Incomplete".

4. Otherwise:
       Return "Complete".


## Complete Incomplete Events

1. Retrieve incomplete event.

2. Staff enters missing information.

3. Re-evaluate completeness.

4. Update event.

5. If complete, mark event as complete.


## Post Fuel Charge Line on EZRentOut

1. Find completed events that have not been posted.

2. Build the fuel charge.

3. Post the charge to EZRentOut.

4. Mark the event as posted.

5. Log any errors.
