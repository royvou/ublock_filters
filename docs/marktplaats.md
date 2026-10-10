# Marktplaats filters

<img src="../assets/marktplaats.svg" width="64" height="64" alt="">

These lists customize **marktplaats.nl**. Import their subscription URLs from the
[available filters table](../README.md#available-filters).

## Promotional cleanup

[`filters/marktplaats.txt`](../filters/marktplaats.txt) hides topadvertenties,
dagtoppers, Admarkt listings, promotional stickers, advertising slots and sponsored
recommendations. Ordinary reserved listings and related sections remain visible.

## Optional cleanup

[`filters/optional.txt`](../filters/optional.txt) adds exclusions for reserved listings,
ordinary related recommendations and “Ook van deze adverteerder” strips. Install it on
its own or alongside promotional cleanup if you want these exclusions. It does not
require the promotional list. The same-seller strip is hidden without hiding its main
listing.

## Limitations

The lists hide content; they do not change pagination or the site's result count.
Generic bicycle searches currently become empty with promotional cleanup enabled. This
is a release blocker: the live verifier requires at least half the cards to remain
visible on the two generic bicycle searches, even when all cards have promotion markers.
Mobile/grid views, favorites, signed-in states and every placement variant are not
exhaustively covered. Site changes may require rule updates.

The lists replace Cleanplaats's advertising cleanup, not its themes, alerts or other
features. They are inspired by [Cleanplaats](https://github.com/Aron220/Cleanplaats) and
are independent of Cleanplaats and Marktplaats. The reviewed source commit is recorded
in the promotional list header.

## Verification

Run the site's suite with the shared Firefox runner:

```sh
uv run --locked scripts/verify-firefox.py /absolute/path/to/ublock_origin.xpi --site marktplaats
```

[`scripts/sites/marktplaats.py`](../scripts/sites/marktplaats.py) checks desktop
searches, promoted and ordinary listing fixtures, optional exclusions and dynamic
insertion. It accepts Marktplaats cookies in the disposable profile. Live checks also
reject hidden cards without a verified promotion marker and enforce the generic-search
visibility floor. A failed floor produces a failed JSON report and a nonzero exit
status, while fixture checks still run. Only repository rules are enabled. Live
recommendations may be absent; the report records whether they appeared, and the
same-seller fixture is always checked. Screenshots capture live pages before fixture
insertion. See [CONTRIBUTING.md](../CONTRIBUTING.md#check-your-changes) for setup and
shared validation behavior.
