# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Check repository conventions, not uBO selector syntax or live behavior."""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    errors = []
    seen: dict[str, str] = {}
    total = 0
    if not (ROOT / "LICENSE").is_file():
        errors.append("Repository LICENSE file is missing")
    paths = sorted((ROOT / "filters").rglob("*.txt"))
    if not paths:
        errors.append("No filter lists found")
    for path in paths:
        label = path.relative_to(ROOT)
        raw = path.read_bytes()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            errors.append(f"{label}: expected UTF-8")
            continue
        if not raw.endswith(b"\n") or b"\r" in raw:
            errors.append(f"{label}: use LF line endings and a final newline")
        for field in (
            "Title",
            "Description",
            "Homepage",
            "Version",
            "Expires",
            "License",
            "SPDX-License-Identifier",
        ):
            values = re.findall(rf"^! {field}: (.+)$", text, re.M)
            if len(values) != 1:
                errors.append(f"{label}: expected one {field} header")
                continue
            value = values[0]
            if field in ("License", "SPDX-License-Identifier") and value != "MIT":
                errors.append(f"{label}: {field} must be MIT")
            if field == "Version" and not re.fullmatch(
                r"\d{4}\.\d{2}\.\d{2}\.\d+", value
            ):
                errors.append(f"{label}: Version must be YYYY.MM.DD.N")
            if field == "Expires" and not re.fullmatch(r"[1-9]\d* days", value):
                errors.append(f"{label}: Expires must be a positive number of days")
        domain_headers = re.findall(r"^! Domains: (.+)$", text, re.M)
        domains = set()
        if len(domain_headers) != 1:
            errors.append(f"{label}: expected one Domains header")
        else:
            domains = {domain.strip() for domain in domain_headers[0].split(",")}
            hostname = r"(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,}"
            if not domains or any(
                not re.fullmatch(hostname, domain) for domain in domains
            ):
                errors.append(
                    f"{label}: Domains must list explicit lowercase hostnames"
                )
        count = 0
        for number, line in enumerate(text.splitlines(), 1):
            location = f"{label}:{number}"
            if line.rstrip() != line:
                errors.append(f"{location}: trailing whitespace")
            if line.startswith("!#"):
                errors.append(
                    f"{location}: preprocessor directives are outside standalone-list scope"
                )
            if not line or line.startswith("!"):
                continue
            scope, separator, selector = line.partition("##")
            rule_domains = set(scope.split(","))
            if (
                not separator
                or not selector.strip()
                or selector.startswith("^")
                or (len(domain_headers) == 1 and not rule_domains.issubset(domains))
            ):
                errors.append(
                    f"{location}: expected a cosmetic rule scoped to declared Domains"
                )
            if "+js(" in line or ":remove(" in line or ":style(" in line:
                errors.append(f"{location}: only cosmetic hiding is in scope")
            if line in seen:
                errors.append(f"{location}: duplicate of {seen[line]}")
            seen[line] = location
            count += 1
        if not count:
            errors.append(f"{label}: no rules found")
        total += count
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"Checked {len(paths)} lists, {total} rules; repository conventions passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
