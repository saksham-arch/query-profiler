import unittest

from query_profiler import QueryObservation, summarize_observations


class QuerySummaryTests(unittest.TestCase):
    def test_groups_observations_and_tracks_known_metric_counts(self) -> None:
        observations = [
            QueryObservation("SELECT", 20, 8, 3, None),
            QueryObservation("UPDATE", 12, None, 0, 2),
            QueryObservation("SELECT", 10, 4, 1, None),
        ]

        select_summary, update_summary = summarize_observations(observations)

        self.assertEqual(select_summary.statement_kind, "SELECT")
        self.assertEqual(select_summary.observation_count, 2)
        self.assertEqual(select_summary.execute_total_ns, 30)
        self.assertEqual(select_summary.execute_median_ns, 15)
        self.assertEqual(select_summary.client_elapsed_total_ns, 42)
        self.assertEqual(select_summary.client_elapsed_median_ns, 21)
        self.assertEqual(select_summary.fetch_observation_count, 2)
        self.assertEqual(select_summary.fetch_total_ns, 12)
        self.assertEqual(select_summary.fetch_median_ns, 6)
        self.assertEqual(select_summary.fetch_share_of_client_elapsed, 12 / 42)
        self.assertEqual(select_summary.rows_returned_total, 4)
        self.assertEqual(select_summary.fetch_ns_per_returned_row, 3.0)
        self.assertEqual(select_summary.rows_affected_observation_count, 0)

        self.assertEqual(update_summary.statement_kind, "UPDATE")
        self.assertIsNone(update_summary.fetch_median_ns)
        self.assertIsNone(update_summary.fetch_share_of_client_elapsed)
        self.assertEqual(update_summary.client_elapsed_total_ns, 12)
        self.assertEqual(update_summary.rows_affected_observation_count, 1)
        self.assertEqual(update_summary.rows_affected_total, 2)
        self.assertEqual(update_summary.execute_ns_per_affected_row, 6.0)
        self.assertIsNone(update_summary.fetch_ns_per_returned_row)
        self.assertIsNone(select_summary.execute_ns_per_affected_row)

    def test_zero_row_fetch_does_not_invent_per_row_cost(self) -> None:
        summary = summarize_observations(
            [QueryObservation("SELECT", 10, 5, 0, None)]
        )[0]
        self.assertEqual(summary.fetch_total_ns, 5)
        self.assertEqual(summary.fetch_share_of_client_elapsed, 1 / 3)
        self.assertIsNone(summary.fetch_ns_per_returned_row)

    def test_zero_duration_query_does_not_invent_fetch_share(self) -> None:
        summary = summarize_observations(
            [QueryObservation("SELECT", 0, 0, 1, None)]
        )[0]
        self.assertIsNone(summary.fetch_share_of_client_elapsed)

    def test_zero_affected_rows_does_not_invent_per_row_cost(self) -> None:
        summary = summarize_observations(
            [QueryObservation("UPDATE", 12, None, 0, 0)]
        )[0]
        self.assertIsNone(summary.execute_ns_per_affected_row)

    def test_empty_input_produces_no_summaries(self) -> None:
        self.assertEqual(summarize_observations([]), ())


if __name__ == "__main__":
    unittest.main()
