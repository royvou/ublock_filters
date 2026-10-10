"""Exercise declared-domain validation without a browser or live site."""

import contextlib
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "check_filters", Path(__file__).resolve().parents[1] / "check-filters.py"
)
if spec is None or spec.loader is None:
    raise RuntimeError("Could not load the filter validator")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class CheckFiltersTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / "filters").mkdir()
        (self.root / "LICENSE").write_text("MIT License\n")

    def add_list(self, filename, domains, rules):
        path = self.root / "filters" / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "! Title: Test filters\n! Description: Test cleanup\n"
            "! Homepage: https://github.com/royvou/ublock_filters\n"
            "! Version: 2026.10.10.1\n! Expires: 7 days\n"
            "! License: MIT\n! SPDX-License-Identifier: MIT\n"
            f"! Domains: {domains}\n{rules}\n"
        )

    def check(self):
        output = io.StringIO()
        with (
            patch.object(checker, "ROOT", self.root),
            contextlib.redirect_stdout(output),
            contextlib.redirect_stderr(output),
        ):
            return checker.main(), output.getvalue()

    def test_accepts_multiple_sites_and_nested_lists(self):
        self.add_list("marktplaats.txt", "marktplaats.nl", "marktplaats.nl##.advert")
        self.add_list(
            "example/cleanup.txt",
            "example.com, shop.example.com",
            "example.com,shop.example.com##.promotion",
        )
        status, output = self.check()
        self.assertEqual(status, 0, output)
        self.assertIn("Checked 2 lists, 2 rules", output)

    def test_rejects_undeclared_and_global_scopes(self):
        for rule in (
            "other.example##.advert",
            "##.advert",
            "example.com,other.example##.advert",
        ):
            with self.subTest(rule=rule):
                self.add_list("example.txt", "example.com", rule)
                status, output = self.check()
                self.assertEqual(status, 1)
                self.assertIn("scoped to declared Domains", output)

    def test_rejects_missing_domain_declaration(self):
        self.add_list("example.txt", "example.com", "example.com##.advert")
        path = self.root / "filters/example.txt"
        path.write_text(path.read_text().replace("! Domains: example.com\n", ""))
        status, output = self.check()
        self.assertEqual(status, 1)
        self.assertIn("expected one Domains header", output)
        self.assertNotIn("scoped to declared Domains", output)

    def test_rejects_duplicate_domain_declaration_without_cascade(self):
        self.add_list("example.txt", "example.com", "example.com##.advert")
        path = self.root / "filters/example.txt"
        path.write_text(path.read_text() + "! Domains: example.com\n")
        status, output = self.check()
        self.assertEqual(status, 1)
        self.assertIn("expected one Domains header", output)
        self.assertNotIn("scoped to declared Domains", output)

    def test_rejects_missing_homepage(self):
        self.add_list("example.txt", "example.com", "example.com##.advert")
        path = self.root / "filters/example.txt"
        path.write_text(
            path.read_text().replace(
                "! Homepage: https://github.com/royvou/ublock_filters\n", ""
            )
        )
        status, output = self.check()
        self.assertEqual(status, 1)
        self.assertIn("expected one Homepage header", output)

    def test_rejects_include_bypass(self):
        self.add_list(
            "example.txt",
            "example.com",
            "example.com##.advert\n!#include bypass.filters",
        )
        status, output = self.check()
        self.assertEqual(status, 1)
        self.assertIn("preprocessor directives", output)

    def test_rejects_non_hiding_actions(self):
        for selector in (
            "+js(test)",
            ".advert:remove()",
            ".advert:style(color:red)",
            "^script",
        ):
            with self.subTest(selector=selector):
                self.add_list("example.txt", "example.com", f"example.com##{selector}")
                status, output = self.check()
                self.assertEqual(status, 1, output)

    def test_rejects_duplicates_across_lists(self):
        for name in ("first.txt", "second.txt"):
            self.add_list(name, "example.com", "example.com##.advert")
        status, output = self.check()
        self.assertEqual(status, 1)
        self.assertIn("duplicate of", output)


if __name__ == "__main__":
    unittest.main()
