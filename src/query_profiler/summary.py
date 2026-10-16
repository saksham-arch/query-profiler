from dataclasses import dataclass
from statistics import median
from typing import Iterable, Optional

from .measurement import QueryObservation


@dataclass(frozen=True)
class QuerySummary:
    statement_kind: str
    observation_count: int
    execute_total_ns: int
    execute_median_ns: float
    client_elapsed_total_ns: int
    client_elapsed_median_ns: float
    fetch_observation_count: int
    fetch_total_ns: int
    fetch_median_ns: Optional[float]
    fetch_share_of_client_elapsed: Optional[float]
    rows_returned_total: int
    fetch_ns_per_returned_row: Optional[float]
    rows_affected_observation_count: int
    rows_affected_total: int
    execute_ns_per_affected_row: Optional[float]


def summarize_observations(
    observations: Iterable[QueryObservation],
) -> tuple[QuerySummary, ...]:
    """Aggregate observations by statement kind without retaining query text."""
    grouped: dict[str, list[QueryObservation]] = {}
    for observation in observations:
        grouped.setdefault(observation.statement_kind, []).append(observation)

    summaries: list[QuerySummary] = []
    for statement_kind in sorted(grouped):
        group = grouped[statement_kind]
        execute_samples = [observation.execute_ns for observation in group]
        client_elapsed_samples = [
            observation.client_elapsed_ns for observation in group
        ]
        fetch_samples = [
            observation.fetch_ns
            for observation in group
            if observation.fetch_ns is not None
        ]
        affected_rows = [
            observation.rows_affected
            for observation in group
            if observation.rows_affected is not None
        ]
        affected_execute_total_ns = sum(
            observation.execute_ns
            for observation in group
            if observation.rows_affected is not None
        )
        rows_affected_total = sum(affected_rows)
        rows_returned_total = sum(
            observation.rows_returned for observation in group
        )
        client_elapsed_total_ns = sum(client_elapsed_samples)
        fetch_total_ns = sum(fetch_samples)
        summaries.append(
            QuerySummary(
                statement_kind=statement_kind,
                observation_count=len(group),
                execute_total_ns=sum(execute_samples),
                execute_median_ns=median(execute_samples),
                client_elapsed_total_ns=client_elapsed_total_ns,
                client_elapsed_median_ns=median(client_elapsed_samples),
                fetch_observation_count=len(fetch_samples),
                fetch_total_ns=fetch_total_ns,
                fetch_median_ns=median(fetch_samples) if fetch_samples else None,
                fetch_share_of_client_elapsed=(
                    fetch_total_ns / client_elapsed_total_ns
                    if fetch_samples and client_elapsed_total_ns > 0
                    else None
                ),
                rows_returned_total=rows_returned_total,
                fetch_ns_per_returned_row=(
                    fetch_total_ns / rows_returned_total
                    if rows_returned_total > 0
                    else None
                ),
                rows_affected_observation_count=len(affected_rows),
                rows_affected_total=rows_affected_total,
                execute_ns_per_affected_row=(
                    affected_execute_total_ns / rows_affected_total
                    if rows_affected_total > 0
                    else None
                ),
            )
        )
    return tuple(summaries)
