# Changelog

- Prefer bucketable selectors: collapse the priority badge and reserved-price filters to
  single substring prefilters, use top-level comma lists instead of static `:is()`
  groups, and require `/v/` before matching structured Admarkt links. No intended
  behavior changes.

- Consolidate cosmetic selectors, drop redundant class alternatives and group related
  placements without intended behavior changes.

- Locked Python and Markdown lint/format tools, type checks, YAML/workflow validation,
  and a shared local/CI check command.

- Avoid duplicate filter parsing and keep verification failures active under optimized
  Python.

- Personal filter collection with a list table and separate site documentation.

- Shared validation with declared domain scopes and per-site Firefox test suites.

- Initial default list for promoted listings, Admarkt cards, stickers and advertising
  placements on Marktplaats.

- Optional list for reserved listings, ordinary related recommendations and "Ook van
  deze adverteerder" strips beneath search listings.

- Firefox/uBlock Origin verification with screenshots and a JSON report.

- MIT license, with short license headers in subscriptions.

- Reject generic searches with fewer than half their listing cards visible, preserve
  failed verification reports, and record promotion markers for diagnosis.

- Audit the empty bicycle grids with isolated filters; removing the website-link rule
  did not restore cards. Keep all promotions hidden and treat empty generic searches as
  a release blocker.

- Align tooling on Python 3.12 and clarify that optional cleanup works standalone.

- Preserve cards with only a seller website link, and scope search-card Admarkt
  detection to the primary link so nested recommendations cannot hide their parent.

- Verify optional cleanup on its own as well as combined with promotional cleanup.
