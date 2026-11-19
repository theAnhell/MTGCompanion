from django.test import SimpleTestCase

from stats.collation import locale_sort_key


class LocaleSortKeyTests(SimpleTestCase):
    def test_accented_name_sorts_with_unaccented_equivalent(self):
        names = ["Zelda", "Éowyn", "Alice"]
        sorted_names = sorted(names, key=locale_sort_key)
        self.assertEqual(sorted_names, ["Alice", "Éowyn", "Zelda"])

    def test_case_insensitive(self):
        names = ["bob", "Alice"]
        sorted_names = sorted(names, key=locale_sort_key)
        self.assertEqual(sorted_names, ["Alice", "bob"])

    def test_tiebreak_on_original_value(self):
        # Same casefolded/stripped key but different original casing: stable,
        # deterministic ordering via the second tuple element.
        key_a = locale_sort_key("alice")
        key_b = locale_sort_key("Alice")
        self.assertNotEqual(key_a, key_b)
        self.assertEqual(key_a[0], key_b[0])
