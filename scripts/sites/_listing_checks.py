"""Visibility checks shared by live Marktplaats diagnostics and unit tests."""

import re


def promotional(card):
    return bool(
        card.get("badge") in ("Topadvertentie", "Dagtopper")
        or card.get("sticker")
        or re.search(r"^[^?#]*/a\d+(?:[-/]|[?#]|$)", card.get("url") or "", re.I)
    )


def visibility_failures(cards, minimum_visible_ratio=0.0):
    if not cards:
        return ["No listing cards found"]
    failures = []
    visible = sum(card["visible"] for card in cards)
    if visible / len(cards) < minimum_visible_ratio:
        failures.append(
            f"Visibility below {minimum_visible_ratio:.0%}: {visible}/{len(cards)} cards"
        )
    if any(card["visible"] and promotional(card) for card in cards):
        failures.append("Promotional cards remain visible")
    if any(not card["visible"] and not promotional(card) for card in cards):
        failures.append("Unmarked ordinary cards were hidden")
    return failures
