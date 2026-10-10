"""Ensure live verification cannot pass when the whole grid disappears."""

import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "listing_checks", Path(__file__).resolve().parents[1] / "sites/_listing_checks.py"
)
if spec is None or spec.loader is None:
    raise RuntimeError("Could not load the listing checks")
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)
visibility_failures = checks.visibility_failures


class ListingChecksTests(unittest.TestCase):
    def test_all_hidden_promotions_fail_generic_search_floor(self):
        cards = [{"visible": False, "badge": "Dagtopper"}] * 39
        self.assertIn(
            "Visibility below 50%: 0/39 cards", visibility_failures(cards, 0.5)
        )

    def test_hidden_ordinary_card_fails_even_above_floor(self):
        cards = [{"visible": True}] * 30 + [{"visible": False}]
        self.assertEqual(
            visibility_failures(cards, 0.5), ["Unmarked ordinary cards were hidden"]
        )

    def test_half_visible_with_promotions_hidden_passes(self):
        cards = [{"visible": True}, {"visible": False, "badge": "Topadvertentie"}]
        self.assertEqual(visibility_failures(cards, 0.5), [])

    def test_visible_promotion_fails(self):
        self.assertEqual(
            visibility_failures([{"visible": True, "badge": "Dagtopper"}], 0.5),
            ["Promotional cards remain visible"],
        )

    def test_empty_page_fails(self):
        self.assertEqual(visibility_failures([], 0.5), ["No listing cards found"])

    def test_website_link_alone_is_not_a_verified_promotion(self):
        cards = [
            {
                "visible": False,
                "website": "Bezoek website",
                "url": "/v/fietsen/heren/m456-bike",
            }
        ]
        self.assertEqual(
            visibility_failures(cards), ["Unmarked ordinary cards were hidden"]
        )

    def test_category_and_query_are_not_admarkt_ids(self):
        for url in (
            "/v/audio/radio/m123-radio?ref=/a456-promo",
            "/v/antiek/kast/m123-kast",
        ):
            self.assertEqual(
                visibility_failures([{"visible": True, "url": url}], 0.5), []
            )

    def test_uppercase_admarkt_is_still_promotional(self):
        self.assertEqual(
            visibility_failures(
                [{"visible": True, "url": "/v/fietsen/heren/A789-bike"}], 0.5
            ),
            ["Promotional cards remain visible"],
        )
