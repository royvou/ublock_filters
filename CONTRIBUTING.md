# Contributing

## Report a filter issue

Use the repository's filter issue form. Include the page URL, enabled filter files, what
should be hidden or kept, and Firefox/uBlock Origin versions. Mention other cleanup
extensions and filter lists. Remove personal details from screenshots before sharing
them.

## Change a rule

Edit the relevant file under `filters/`; the [README table](README.md#available-filters)
links every available list. These files are published subscriptions and require no build
step. Keep their paths stable.

- Scope every rule to a hostname declared in that file's `! Domains:` header. Separate
  multiple hostnames with commas. Use explicit lowercase hostnames; wildcard, global and
  negated scopes are outside this collection's conventions.
- Keep rules cosmetic and lists standalone; do not use scriptlets, removal/style actions
  or `!#` preprocessor directives/includes.
- Prefer specific classes, IDs and native CSS selectors. Use procedural operators only
  when needed; avoid matching arbitrary page text.
- Check the intended match and ordinary content that should remain.
- Add a short comment explaining a new rule and link the issue when available.
- Bump the changed list's `Version` (`YYYY.MM.DD.N`) and update `CHANGELOG.md`.
- Keep the short MIT license headers and any source attribution. The full license text
  belongs in `LICENSE`.

See
[uBO's static filter syntax](https://github.com/gorhill/uBlock/wiki/Static-filter-syntax)
and
[procedural cosmetic filters](https://github.com/gorhill/uBlock/wiki/Procedural-cosmetic-filters).

## Add a site

1. Add a descriptively named `.txt` file under `filters/`, with `Title`, `Description`,
   `Homepage`, `Version`, `Domains`, `Expires`, `License: MIT` and
   `SPDX-License-Identifier: MIT` headers. Describe whether it stands alone or extends
   another list.
2. Add a row to the README table and a `docs/<site>.md` page describing behavior,
   limitations and any source attribution.
3. Add `scripts/sites/<site>.py`. Declare `LISTS`, a tuple of subscription paths
   relative to the repository root, and implement
   `verify(session, root, screenshots_dir, baseline=None)` returning a JSON-compatible
   results dictionary. Use `scripts/sites/marktplaats.py` as the working example.
4. Run the repository checks and the site verifier below; record results in the pull
   request.

The shared Firefox runner discovers site modules automatically. Each suite owns its live
URLs, cookie handling, fixtures, positive/negative cases and optional-list checks. It
receives `session.driver` for page interaction, `session.parse_filters(text)` for the
actual uBO parser, and `session.apply_filters(text)` to replace the active rules and
reload the engine. These methods manage dashboard navigation; navigate to the site again
before checking page content. `session.procedural(parsed)` extracts compiled procedural
rules when candidate comparisons are useful.

## Check your changes

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and Git, then run
the same command used in CI:

```sh
uv run --locked python scripts/check.py
```

uv installs the development tools from `uv.lock` and selects Python 3.12 or newer. The
first run needs network access to download tools. The pinned `actionlint-py` package
installs a prebuilt Actionlint binary; no Go compiler is required. Later runs reuse
local caches. The command checks:

- Python lint, import order and common bug patterns with Ruff, plus Ruff formatting.
- Python types with mypy, including bodies of unannotated functions. Selenium's untyped
  external interfaces remain dynamic.
- Markdown formatting with mdformat/GFM and Markdown structure with PyMarkdown. The
  formatter controls wrapping; long tables and URLs are allowed.
- YAML syntax/style with yamllint and GitHub workflow semantics with Actionlint.
- Python/TOML syntax, SVG XML, and both the development and Firefox-script lockfiles.
- Filter metadata, declared domain scopes, duplicates and regression tests.

The runner includes tracked and untracked files that are not ignored by Git. Generated
artifacts and tool caches are excluded. CI checks files without changing or publishing
them. To apply safe Python lint fixes and Python/Markdown formatting:

```sh
uv run --locked python scripts/check.py --fix
```

For a quick filter-only check, run `uv run scripts/check-filters.py`. Neither that check
nor the fast CI suite parses uBO selectors or checks the live DOM.

For rule changes, install Firefox, download the official XPI from
[Mozilla](https://addons.mozilla.org/en-US/firefox/addon/ublock-origin/), and run:

```sh
# Run every site's suite.
uv run --locked scripts/verify-firefox.py /absolute/path/to/ublock_origin.xpi

# Run one site's suite.
uv run --locked scripts/verify-firefox.py /absolute/path/to/ublock_origin.xpi --site marktplaats
```

The runner creates a disposable Firefox profile, installs the actual uBO engine, and
imports the selected site suites. Only the suite's rules are enabled, so built-in lists
cannot mask a missing rule. An all-sites run requires every published filter file to
belong to a suite. Firefox closes even if verification fails. Site-specific coverage is
described in each site's documentation.

Network access is required; Selenium may download geckodriver. uv manages pinned Python
dependencies. Screenshots are grouped by site in `.artifacts/screenshots/`, and the JSON
report in `.artifacts/verification.json` groups results under `sites`. Both are ignored
by Git. Use `--screenshots-dir` or `--report` to change locations. Screenshots precede
fixture insertion and are for manual inspection, with no automated visual comparison.
Procedural candidate counts are not a CPU benchmark.

The report records `status: passed` or `status: failed`. Live visibility failures are
recorded alongside card evidence, and the runner exits nonzero after completing the
suite. Unexpected suite errors also replace the report with a failed result. Keep
durable verification summaries in `docs/`; link them from the site's notes.

Also check the specific page your rule addresses. Live site changes can fail a suite;
investigate before weakening a check. Note what you checked in the pull request. To
compare a site's primary list with an earlier version, use
`--site <site> --baseline /path/to/previous-list.txt` if its suite supports comparison.

To update browser dependencies, edit the Firefox runner's inline metadata, then run
`uv lock --script scripts/verify-firefox.py` and include its lockfile. To update the
development tools, use `uv lock --upgrade` and include `uv.lock`. Run all checks after
either update.

Contributions are under the [MIT license](LICENSE).
