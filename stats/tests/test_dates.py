from datetime import datetime

from django.test import SimpleTestCase

from stats.dates import days_since, js_round, round1, ymd


class YmdTests(SimpleTestCase):
    def test_formats_date(self):
        self.assertEqual(ymd(datetime(2026, 3, 5)), "2026-03-05")

    def test_none_returns_none(self):
        self.assertIsNone(ymd(None))


class DaysSinceTests(SimpleTestCase):
    def test_counts_whole_days(self):
        then = datetime(2026, 1, 1)
        now = datetime(2026, 1, 10)
        self.assertEqual(days_since(then, now=now), 9)

    def test_same_day_is_zero(self):
        now = datetime(2026, 1, 1, 8, 0)
        then = datetime(2026, 1, 1, 6, 0)
        self.assertEqual(days_since(then, now=now), 0)


class JsRoundTests(SimpleTestCase):
    def test_rounds_half_up(self):
        self.assertEqual(js_round(2.5), 3)

    def test_rounds_down_below_half(self):
        self.assertEqual(js_round(2.4), 2)

    def test_rounds_up_above_half(self):
        self.assertEqual(js_round(2.6), 3)


class Round1Tests(SimpleTestCase):
    def test_rounds_to_one_decimal(self):
        self.assertEqual(round1(33.333), 33.3)

    def test_rounds_half_up_at_one_decimal(self):
        self.assertEqual(round1(33.35), 33.4)

    def test_whole_number_stays_whole(self):
        self.assertEqual(round1(100.0), 100.0)
