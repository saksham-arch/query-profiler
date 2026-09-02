import sqlite3
import unittest

from query_profiler import profile_query


class FakeClock:
    def __init__(self, values: list[int]) -> None:
        self.values = iter(values)

    def __call__(self) -> int:
        return next(self.values)


class QueryMeasurementTests(unittest.TestCase):
    def setUp(self) -> None:
        self.connection = sqlite3.connect(":memory:")
        self.connection.execute("CREATE TABLE events (id INTEGER, name TEXT)")
        self.connection.executemany("INSERT INTO events VALUES (?, ?)", [(1, "a"), (2, "b")])

    def tearDown(self) -> None:
        self.connection.close()

    def test_separates_execute_and_fetch_timings(self) -> None:
        observation, rows = profile_query(
            self.connection,
            "SELECT id FROM events ORDER BY id",
            clock=FakeClock([0, 10, 20, 35]),
        )
        self.assertEqual(rows, [(1,), (2,)])
        self.assertEqual(observation.statement_kind, "SELECT")
        self.assertEqual(observation.execute_ns, 10)
        self.assertEqual(observation.fetch_ns, 15)
        self.assertEqual(observation.rows_returned, 2)
        self.assertIsNone(observation.rows_affected)

    def test_reports_affected_rows_without_committing(self) -> None:
        observation, rows = profile_query(
            self.connection,
            "UPDATE events SET name = ? WHERE id = ?",
            ("changed", 1),
            clock=FakeClock([0, 8]),
        )
        self.assertEqual(rows, [])
        self.assertEqual(observation.rows_affected, 1)
        self.assertIsNone(observation.fetch_ns)
        self.assertTrue(self.connection.in_transaction)

    def test_rejects_empty_sql(self) -> None:
        with self.assertRaises(ValueError):
            profile_query(self.connection, "   ")


if __name__ == "__main__":
    unittest.main()
