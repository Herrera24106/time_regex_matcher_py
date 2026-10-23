"""Tests for time_regex_matcher_py.core. Covers the edge cases the implementation claims to handle."""

import unittest

from time_regex_matcher_py import TimeMatcher, TimeMatch


class TestTimeMatcher(unittest.TestCase):
    def setUp(self):
        self.matcher = TimeMatcher()

    def test_basic_pm_time(self):
        results = self.matcher.find_all("Meet at 3:15 PM")
        self.assertEqual(len(results), 1)
        r = results[0]
        self.assertEqual(r.hour, 15)
        self.assertEqual(r.minute, 15)
        self.assertEqual(r.second, 0)
        self.assertEqual(r.to_iso(), "15:15:00")
        self.assertEqual(r.raw, "3:15 PM")

    def test_basic_am_time(self):
        results = self.matcher.find_all("Wake at 9 AM")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].hour, 9)
        self.assertEqual(results[0].to_iso(), "09:00:00")

    def test_hour_only_no_minutes(self):
        results = self.matcher.find_all("Lunch at 12 PM")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].hour, 12)
        self.assertEqual(results[0].minute, 0)
        self.assertEqual(results[0].second, 0)
        self.assertEqual(results[0].to_iso(), "12:00:00")

    def test_midnight_edge_case(self):
        """12 AM normalizes to 00:00:00 — the key non-obvious case."""
        results = self.matcher.find_all("Midnight is 12 AM")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].hour, 0)
        self.assertEqual(results[0].to_iso(), "00:00:00")

    def test_noon_edge_case(self):
        """12 PM stays 12:00:00."""
        results = self.matcher.find_all("Noon is 12 PM")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].hour, 12)
        self.assertEqual(results[0].to_iso(), "12:00:00")

    def test_seconds_extraction(self):
        results = self.matcher.find_all("Timer ends at 1:30:45 PM")
        self.assertEqual(len(results), 1)
        r = results[0]
        self.assertEqual(r.hour, 13)
        self.assertEqual(r.minute, 30)
        self.assertEqual(r.second, 45)
        self.assertEqual(r.to_iso(), "13:30:45")

    def test_dotted_meridiem(self):
        results = self.matcher.find_all("Train at 6:00 a.m.")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].hour, 6)
        self.assertEqual(results[0].minute, 0)

    def test_lowercase_meridiem(self):
        results = self.matcher.find_all("Bus at 7:30 pm")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].hour, 19)
        self.assertEqual(results[0].minute, 30)

    def test_multiple_times(self):
        results = self.matcher.find_all("From 9 AM to 5 PM")
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].hour, 9)
        self.assertEqual(results[1].hour, 17)

    def test_24_hour_times_not_supported(self):
        """24-hour notation like 14:30 is intentionally out of scope."""
        results = self.matcher.find_all("Meet at 14:30")
        self.assertEqual(results, [])

    def test_invalid_meridiem_not_matched(self):
        """Bare numbers without AM/PM are not times."""
        results = self.matcher.find_all("Order 12 items")
        self.assertEqual(results, [])

    def test_find_first_present(self):
        r = self.matcher.find_first("From 9 AM to 5 PM")
        self.assertIsNotNone(r)
        self.assertEqual(r.hour, 9)
        self.assertIsInstance(r, TimeMatch)

    def test_find_first_absent(self):
        r = self.matcher.find_first("No times here")
        self.assertIsNone(r)

    def test_match_positions(self):
        text = "Meet at 3 PM sharp"
        results = self.matcher.find_all(text)
        self.assertEqual(len(results), 1)
        r = results[0]
        self.assertEqual(text[r.start:r.end], r.raw)

    def test_pm_hour_conversion(self):
        """All PM hours except 12 get +12."""
        results = self.matcher.find_all("8 PM")
        self.assertEqual(results[0].hour, 20)

    def test_pm_hour_12_no_conversion(self):
        """12 PM must not get +12 — a common bug if the rule is too simple."""
        results = self.matcher.find_all("12 PM")
        self.assertEqual(results[0].hour, 12)

    def test_am_hour_12_to_zero(self):
        """12 AM -> 0, the mirror of 12 PM."""
        results = self.matcher.find_all("12 AM")
        self.assertEqual(results[0].hour, 0)

    def test_am_hour_no_conversion(self):
        results = self.matcher.find_all("7 AM")
        self.assertEqual(results[0].hour, 7)

    def test_empty_string(self):
        self.assertEqual(self.matcher.find_all(""), [])
        self.assertIsNone(self.matcher.find_first(""))

    def test_pm_hour_eleven(self):
        results = self.matcher.find_all("11 PM")
        self.assertEqual(results[0].hour, 23)


if __name__ == "__main__":
    unittest.main()
