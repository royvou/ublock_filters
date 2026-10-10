# /// script
# requires-python = ">=3.12"
# dependencies = ["selenium==4.51.0"]
# ///
"""Verify personal filter lists in a disposable Firefox/uBO profile.

Runs every site suite by default. Use --site NAME to select one suite.
Requires uv, Firefox, an official uBlock Origin XPI and network access.
"""

import argparse
import importlib
import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.ui import WebDriverWait

ROOT = Path(__file__).resolve().parents[1]


class FilterSession:
    """Load and parse isolated filters; site suites own their page checks."""

    def __init__(self, driver):
        self.driver = driver
        driver.set_context("chrome")
        uuids = driver.execute_script(
            "return Services.prefs.getStringPref('extensions.webextensions.uuids');"
        )
        self.dashboard_url = f"moz-extension://{json.loads(uuids)['uBlock0@raymondhill.net']}/1p-filters.html"
        self.open_dashboard()
        self.selected_lists = self.async_js(
            'vAPI.messaging.send("dashboard",{what:"applyFilterListSelection",toSelect:["user-filters"]})'
            '.then(()=>vAPI.messaging.send("dashboard",{what:"getLists"}))'
            ".then(r=>done(Object.keys(r.available).filter(key=>r.available[key].off===false)))"
            ".catch(e=>done({error:String(e)}));"
        )
        if self.selected_lists != ["user-filters"]:
            raise RuntimeError(
                f"Could not isolate repository filters: {self.selected_lists}"
            )

    def async_js(self, code, *args):
        return self.driver.execute_async_script(
            "const done=arguments[arguments.length-1];" + code, *args
        )

    def open_dashboard(self):
        self.driver.set_context("content")
        if self.driver.current_url != self.dashboard_url:
            self.driver.set_context("chrome")
            self.driver.execute_script(
                "gBrowser.selectedBrowser.loadURI(Services.io.newURI(arguments[0]),"
                "{triggeringPrincipal:Services.scriptSecurityManager.getSystemPrincipal()});",
                self.dashboard_url,
            )
            self.driver.set_context("content")
        WebDriverWait(self.driver, 30).until(
            lambda d: d.execute_script(
                'return typeof vAPI !== "undefined" && !!vAPI.messaging'
            )
        )

    def parse_filters(self, content):
        self.open_dashboard()
        parsed = self.async_js(
            'import("./js/static-filtering-parser.js").then(({AstFilterParser})=>{'
            "const p=new AstFilterParser({nativeCssHas:true});"
            'done(arguments[0].split("\\n").filter(x=>x&&!x.startsWith("!"))'
            ".map(line=>{p.parse(line);return {line,error:p.hasError(),compiled:p.result.compiled};}));"
            "}).catch(e=>done({error:String(e)}));",
            content,
        )
        if not isinstance(parsed, list) or any(x["error"] for x in parsed):
            raise RuntimeError(f"uBO parser rejected filters: {parsed}")
        return parsed

    @staticmethod
    def procedural(parsed):
        compiled = [
            json.loads(x["compiled"]) for x in parsed if x["compiled"].startswith("{")
        ]
        return [item for item in compiled if "tasks" in item]

    def apply_filters(self, content):
        self.open_dashboard()
        result = self.async_js(
            'vAPI.messaging.send("dashboard",{what:"writeUserFilters",content:arguments[0],enabled:true,trusted:false})'
            '.then(r=>vAPI.messaging.send("dashboard",{what:"reloadAllFilters"}).then(()=>done(r)))'
            ".catch(e=>done({error:String(e)}));",
            content,
        )
        if (
            not isinstance(result, dict)
            or result.get("content", "").strip() != content.strip()
        ):
            raise RuntimeError(f"Could not apply filters: {result}")


def main():
    available = sorted(
        path.stem
        for path in (ROOT / "scripts/sites").glob("*.py")
        if not path.stem.startswith("_")
    )
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("addon", type=Path, help="Official uBlock Origin Firefox XPI")
    cli.add_argument(
        "--site", choices=available, help="Run one site (default: all sites)"
    )
    cli.add_argument(
        "--baseline",
        type=Path,
        help="Previous primary list for candidate comparison; requires one site",
    )
    cli.add_argument(
        "--screenshots-dir", type=Path, default=ROOT / ".artifacts/screenshots"
    )
    cli.add_argument(
        "--report", type=Path, default=ROOT / ".artifacts/verification.json"
    )
    args = cli.parse_args()
    names = [args.site] if args.site else available
    if not names:
        cli.error("No site verification suites found")
    if args.baseline and len(names) != 1:
        cli.error("--baseline requires selecting one site with --site")
    suites = {name: importlib.import_module(f"sites.{name}") for name in names}
    covered = {path for suite in suites.values() for path in suite.LISTS}
    if not args.site:
        published = {
            str(path.relative_to(ROOT)) for path in (ROOT / "filters").rglob("*.txt")
        }
        if published != covered:
            cli.error(
                f"Site suites must cover all published lists; missing={published - covered}, unknown={covered - published}"
            )
    with zipfile.ZipFile(args.addon.resolve()) as archive:
        addon_version = json.loads(archive.read("manifest.json"))["version"]
    options = Options()
    options.add_argument("-headless")
    driver = webdriver.Firefox(
        options=options, service=Service(service_args=["--allow-system-access"])
    )
    results: dict[str, Any] = {}
    report = {
        "status": "failed",
        "firefox": driver.capabilities["browserVersion"],
        "ublock": addon_version,
        "sites": results,
    }
    report_path = args.report.resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        driver.set_script_timeout(30)
        driver.set_window_size(1440, 1100)
        print("Firefox", driver.capabilities["browserVersion"], flush=True)
        print(
            "Addon",
            driver.install_addon(str(args.addon.resolve()), temporary=True),
            flush=True,
        )
        session = FilterSession(driver)
        report["selectedFilterLists"] = session.selected_lists
        for name, suite in suites.items():
            screenshots = args.screenshots_dir.resolve() / name
            screenshots.mkdir(parents=True, exist_ok=True)
            print("Verifying", name, flush=True)
            results[name] = suite.verify(session, ROOT, screenshots, args.baseline)
        report["status"] = (
            "failed"
            if any(result.get("failures") for result in results.values())
            else "passed"
        )
        if report["status"] == "failed":
            raise RuntimeError(
                "Live verification failed; see failures in the saved report"
            )
    except Exception as error:
        report["error"] = str(error)
        raise
    finally:
        report["checkedAt"] = datetime.now(UTC).isoformat()
        try:
            report_path.write_text(json.dumps(report, indent=2) + "\n")
            print("Report saved:", report_path, report["status"], flush=True)
        finally:
            driver.quit()


if __name__ == "__main__":
    main()
