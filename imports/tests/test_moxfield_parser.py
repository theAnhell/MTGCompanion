from django.test import SimpleTestCase

from imports.moxfield_parser import (
    extract_moxfield_deck_id,
    is_commander_card,
    normalize_card_name,
    parse_moxfield_export,
)


class ParseMoxfieldExportTests(SimpleTestCase):
    def test_plain_line(self):
        rows = parse_moxfield_export("1 Sol Ring (LEA) 226")
        self.assertEqual(
            rows,
            [{"quantity": 1, "cardName": "Sol Ring", "setCode": "LEA", "collectorNumber": "226", "isFoil": False}],
        )

    def test_quantity_greater_than_one(self):
        rows = parse_moxfield_export("3 Plains (BRO) 284")
        self.assertEqual(rows[0]["quantity"], 3)

    def test_foil_marker(self):
        rows = parse_moxfield_export("1 Queen Marchesa (SLD) 2688 *F*")
        self.assertTrue(rows[0]["isFoil"])

    def test_etched_marker_counts_as_foil(self):
        rows = parse_moxfield_export("1 Nahiri's Resolve (MAT) 137 *E*")
        self.assertTrue(rows[0]["isFoil"])

    def test_set_code_uppercased(self):
        rows = parse_moxfield_export("1 Chaos Warp (plst) C17-131")
        self.assertEqual(rows[0]["setCode"], "PLST")
        self.assertEqual(rows[0]["collectorNumber"], "C17-131")

    def test_double_faced_card_name_normalized_on_parse(self):
        rows = parse_moxfield_export("1 Branchloft Pathway / Boulderloft Pathway (ZNR) 252")
        self.assertEqual(rows[0]["cardName"], "Branchloft Pathway // Boulderloft Pathway")

    def test_multiple_lines(self):
        text = "1 Sol Ring (LEA) 226\n1 Command Tower (CMR) 331"
        rows = parse_moxfield_export(text)
        self.assertEqual(len(rows), 2)

    def test_blank_lines_ignored(self):
        text = "1 Sol Ring (LEA) 226\n\n\n1 Command Tower (CMR) 331"
        rows = parse_moxfield_export(text)
        self.assertEqual(len(rows), 2)

    def test_unrecognized_line_skipped_not_fatal(self):
        text = "1 Sol Ring (LEA) 226\nnot a real decklist line\n1 Command Tower (CMR) 331"
        rows = parse_moxfield_export(text)
        self.assertEqual(len(rows), 2)

    def test_sideboard_heading_stops_parsing(self):
        text = "1 Sol Ring (LEA) 226\nSideboard\n1 Command Tower (CMR) 331"
        rows = parse_moxfield_export(text)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["cardName"], "Sol Ring")

    def test_maybeboard_and_considering_also_stop_parsing(self):
        for heading in ["Maybeboard", "Considering", "MAYBEBOARD:"]:
            with self.subTest(heading=heading):
                text = f"1 Sol Ring (LEA) 226\n{heading}\n1 Command Tower (CMR) 331"
                rows = parse_moxfield_export(text)
                self.assertEqual(len(rows), 1)

    def test_empty_text_returns_empty_list(self):
        self.assertEqual(parse_moxfield_export(""), [])


class NormalizeCardNameTests(SimpleTestCase):
    def test_single_slash_normalized_to_double(self):
        self.assertEqual(
            normalize_card_name("Aang, Swift Savior / Aang and La, Ocean's Fury"),
            "Aang, Swift Savior // Aang and La, Ocean's Fury",
        )

    def test_already_double_slash_unchanged(self):
        self.assertEqual(normalize_card_name("Fire // Ice"), "Fire // Ice")

    def test_name_without_slash_unchanged(self):
        self.assertEqual(normalize_card_name("Sol Ring"), "Sol Ring")

    def test_strips_surrounding_whitespace(self):
        self.assertEqual(normalize_card_name("  Sol Ring  "), "Sol Ring")


class ExtractMoxfieldDeckIdTests(SimpleTestCase):
    def test_extracts_id_from_url(self):
        self.assertEqual(
            extract_moxfield_deck_id("https://www.moxfield.com/decks/abc123XYZ"), "abc123XYZ"
        )

    def test_extracts_id_with_trailing_query(self):
        self.assertEqual(
            extract_moxfield_deck_id("https://www.moxfield.com/decks/abc123?foo=bar"), "abc123"
        )

    def test_non_matching_url_returns_none(self):
        self.assertIsNone(extract_moxfield_deck_id("https://example.com/nope"))


class IsCommanderCardTests(SimpleTestCase):
    def test_exact_match(self):
        self.assertTrue(is_commander_card("Queen Marchesa", "Queen Marchesa"))

    def test_case_insensitive(self):
        self.assertTrue(is_commander_card("queen marchesa", "Queen Marchesa"))

    def test_front_face_of_split_card_matches(self):
        self.assertTrue(
            is_commander_card("Aang, Swift Savior / Aang and La, Ocean's Fury", "Aang, Swift Savior")
        )

    def test_back_face_does_not_match(self):
        self.assertFalse(
            is_commander_card("Aang, Swift Savior / Aang and La, Ocean's Fury", "Aang and La, Ocean's Fury")
        )

    def test_unrelated_card_does_not_match(self):
        self.assertFalse(is_commander_card("Sol Ring", "Queen Marchesa"))
