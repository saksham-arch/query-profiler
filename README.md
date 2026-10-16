# query-profiler

A DB-API query measurement primitive that separates execute time from result
fetch time. Observations retain only the statement kind and numeric metrics;
SQL text and parameter values are deliberately excluded.

```python
from query_profiler import profile_query

observation, rows = profile_query(connection, "SELECT * FROM events WHERE id = ?", (42,))
```

Multiple observations can be summarized by statement kind without storing SQL
text or parameter values:

```python
from query_profiler import summarize_observations

for summary in summarize_observations(observations):
    print(summary.statement_kind, summary.execute_median_ns)
```

The summary keeps separate counts for fetch and affected-row metrics because
those values are not available for every kind of statement. Totals describe
only the observations supplied by the caller; they are not database-wide
telemetry.

Each observation also exposes `client_elapsed_ns`, the sum of its measured
execute and fetch phases. Summaries report the total and median of that value.
This is client-observed time, not server execution time, and it excludes work
outside the two measured phases.

Fetch observations and statement summaries also report nanoseconds per returned
row. The value is `None` for empty results rather than dividing by zero. It
includes driver, transfer, conversion, and fixed fetch overhead, so it is a
client-side diagnostic ratio—not a database server's row-processing cost.

Write observations and summaries report execute nanoseconds per affected row
when the driver supplies a positive affected-row count. Summary values divide
the execute time of observations with known counts by their total affected
rows. The value is `None` when no rows were affected, and it includes client,
driver, network, and fixed statement overhead rather than measuring server-only
row-update cost.

Summaries report `fetch_share_of_client_elapsed` when fetch observations and a
positive combined client duration are available. This divides total measured
fetch time by total execute-plus-fetch time for that statement kind. It helps
locate client-side phase balance, but it does not separate server execution,
network transfer, driver conversion, or scheduling overhead.

Run the tests with `python3 -m unittest discover -s tests`.

Client-side timings include driver and local scheduling overhead. They do not
replace database-native execution plans or server-side telemetry, and the
helper never commits a transaction on the caller's behalf.
Database cursors are closed on both successful and failed executions so a
measurement cannot quietly exhaust driver resources.
