import unittest
from datetime import date

from days_until import days_until


class DaysUntilTests(unittest.TestCase):
    def test_month_end(self) -> None:
        self.assertEqual(days_until(date(2026, 2, 1), date(2026, 1, 31)), 1)

    def test_leap_day(self) -> None:
        self.assertEqual(days_until(date(2028, 3, 1), date(2028, 2, 28)), 2)

    def test_past_date(self) -> None:
        self.assertEqual(days_until(date(2026, 1, 1), date(2026, 1, 3)), -2)


if __name__ == "__main__":
    unittest.main()
