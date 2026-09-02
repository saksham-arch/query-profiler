from dataclasses import dataclass
from time import perf_counter_ns
from typing import Any, Callable, Optional, Sequence


@dataclass(frozen=True)
class QueryObservation:
    statement_kind: str
    execute_ns: int
    fetch_ns: Optional[int]
    rows_returned: int
    rows_affected: Optional[int]


def _statement_kind(sql: str) -> str:
    tokens = sql.strip().split()
    if not tokens:
        raise ValueError("sql must not be empty")
    return tokens[0].upper()


def profile_query(
    connection: Any,
    sql: str,
    parameters: Sequence[Any] = (),
    *,
    clock: Callable[[], int] = perf_counter_ns,
) -> tuple[QueryObservation, list[Any]]:
    """Execute and fully fetch one DB-API query without committing it."""
    kind = _statement_kind(sql)
    cursor = connection.cursor()
    execute_started = clock()
    cursor.execute(sql, parameters)
    execute_ns = clock() - execute_started
    if execute_ns < 0:
        raise ValueError("clock must be monotonic")

    rows: list[Any] = []
    fetch_ns: Optional[int] = None
    if cursor.description is not None:
        fetch_started = clock()
        rows = list(cursor.fetchall())
        fetch_ns = clock() - fetch_started
        if fetch_ns < 0:
            raise ValueError("clock must be monotonic")

    rowcount = cursor.rowcount
    observation = QueryObservation(
        statement_kind=kind,
        execute_ns=execute_ns,
        fetch_ns=fetch_ns,
        rows_returned=len(rows),
        rows_affected=rowcount if rowcount >= 0 else None,
    )
    cursor.close()
    return observation, rows

