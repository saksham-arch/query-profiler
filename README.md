# query-profiler

A DB-API query measurement primitive that separates execute time from result
fetch time. Observations retain only the statement kind and numeric metrics;
SQL text and parameter values are deliberately excluded.

```python
from query_profiler import profile_query

observation, rows = profile_query(connection, "SELECT * FROM events WHERE id = ?", (42,))
```

Run the tests with `python3 -m unittest discover -s tests`.

Client-side timings include driver and local scheduling overhead. They do not
replace database-native execution plans or server-side telemetry, and the
helper never commits a transaction on the caller's behalf.

