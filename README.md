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

Run the tests with `python3 -m unittest discover -s tests`.

Client-side timings include driver and local scheduling overhead. They do not
replace database-native execution plans or server-side telemetry, and the
helper never commits a transaction on the caller's behalf.
Database cursors are closed on both successful and failed executions so a
measurement cannot quietly exhaust driver resources.
