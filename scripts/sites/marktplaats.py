"""Marktplaats live pages and fixtures for the shared Firefox verifier."""

import json
import time

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from sites._listing_checks import visibility_failures

LISTS = ("filters/marktplaats.txt", "filters/optional.txt")


def accept_cookie_dialog(driver):
    frames = driver.find_elements(By.CSS_SELECTOR, 'iframe[id^="sp_message_iframe"]')
    for frame in frames:
        if not frame.is_displayed():
            continue
        driver.switch_to.frame(frame)
        try:
            accept = WebDriverWait(driver, 10).until(
                lambda d: next(
                    (
                        x
                        for x in d.find_elements(
                            By.XPATH, '//*[normalize-space(text())="Accepteren"]'
                        )
                        if x.is_displayed()
                    ),
                    False,
                )
            )
            accept.click()
            print("Accepted Marktplaats cookies", flush=True)
        finally:
            driver.switch_to.default_content()
        WebDriverWait(driver, 10).until(EC.invisibility_of_element(frame))


def verify(session, root, screenshots_dir, baseline=None):
    driver = session.driver
    filters, optional_filters = ((root / path).read_text() for path in LISTS)
    default_parse = session.parse_filters(filters)
    parse = default_parse + session.parse_filters(optional_filters)
    default_procedural = session.procedural(default_parse)
    baseline_procedural = (
        session.procedural(session.parse_filters(baseline.read_text()))
        if baseline
        else None
    )
    print(
        "Parser accepted",
        len(parse),
        "rules;",
        len(default_procedural),
        "default procedural rules",
        flush=True,
    )
    session.apply_filters(filters)
    print("Applied default list", flush=True)
    time.sleep(3)
    reports = []
    for name, url, minimum_visible_ratio in [
        ("01-fiets", "https://www.marktplaats.nl/q/fiets/", 0.5),
        ("02-fiets-page-3", "https://www.marktplaats.nl/q/fiets/p/3/", 0.5),
        (
            "03-antieke-boekenkast",
            "https://www.marktplaats.nl/q/antieke+boekenkast/",
            0.0,
        ),
    ]:
        driver.get(url)
        WebDriverWait(driver, 40).until(
            lambda d: d.execute_script(
                'return document.querySelectorAll("li.hz-Listing").length>0'
            )
        )
        time.sleep(3)
        accept_cookie_dialog(driver)
        screenshot = screenshots_dir / f"{name}.png"
        if not driver.save_screenshot(str(screenshot)):
            raise RuntimeError(f"Could not save screenshot: {screenshot}")
        result = driver.execute_script(
            """return [...document.querySelectorAll('li.hz-Listing')].map(x=>({visible:!!x.getClientRects().length,badge:x.querySelector('[class*="hz-Listing-priority"]')?.textContent.trim(),url:x.querySelector('a[href*="/v/"]')?.getAttribute('href'),website:x.querySelector('.hz-Listing-seller-link,.hz-Listing-seller-external-link')?.textContent.trim(),sticker:!!x.querySelector('[data-testid="listing-opval-sticker"],.hz-Listing-Opvalsticker-wrapper,.hz-Listing-Opvalsticker-wrapper-new')}));"""
        )
        report = {
            "url": url,
            "total": len(result),
            "visible": sum(x["visible"] for x in result),
            "topVisible": sum(
                x["visible"] and x["badge"] == "Topadvertentie" for x in result
            ),
            "dayVisible": sum(
                x["visible"] and x["badge"] == "Dagtopper" for x in result
            ),
            "minimumVisibleRatio": minimum_visible_ratio,
            "cards": [
                {**card, "url": (card["url"] or "").split("?")[0]} for card in result
            ],
        }
        report["failures"] = visibility_failures(result, report["minimumVisibleRatio"])
        report["screenshot"] = str(screenshot)
        report["proceduralCandidates"] = driver.execute_script(
            "return arguments[0].reduce((sum,x)=>sum+document.querySelectorAll(x.selector).length,0);",
            default_procedural,
        )
        if baseline_procedural is not None:
            report["baselineProceduralCandidates"] = driver.execute_script(
                "return arguments[0].reduce((sum,x)=>sum+document.querySelectorAll(x.selector).length,0);",
                baseline_procedural,
            )
        reports.append(report)
        print(
            "Live",
            json.dumps({key: value for key, value in report.items() if key != "cards"}),
            flush=True,
        )
    fixture = """<section id="filter-check"><ul>
    <li id="ordinary" class="hz-Listing"><a class="hz-Listing-coverLink" href="/v/audio/apparatuur/m123-radio">A Topadvertentie radio</a><span class="hz-Listing-priority-new"> </span></li>
    <li id="top" class="hz-Listing"><span class="hz-Listing-priority"><span> Topadvertentie </span></span></li>
    <li id="day" class="hz-Listing"><span class="ListingPriority_hz-Listing-priority-new__abc">Dagtopper</span></li>
    <li id="business" class="hz-Listing"><a class="hz-Listing-coverLink" href="/v/audio/apparatuur/a123-radio">Radio</a></li>
    <li id="query" class="hz-Listing"><a class="hz-Listing-coverLink" href="/v/audio/apparatuur/m123-radio?ref=/a456-promo">Radio</a></li>
    <li id="website" class="hz-Listing"><div class="hz-Listing-seller-external-link"><span>Bezoek website</span></div></li>
    <li id="sticker" class="hz-Listing"><div data-testid="listing-opval-sticker">Promo</div></li>
    <li id="reserved" class="hz-Listing"><span class="hz-Listing-price">Gereserveerd</span></li>
    <li id="reserved-title" class="hz-Listing"><h2>Gereserveerd boek</h2><span class="hz-Listing-price">€ 20</span></li>
    <li id="upper-business" class="hz-Listing"><a class="hz-Listing-coverLink" href="/v/fietsen/heren/A789-bike">Bike</a></li>
    <li id="badge-description" class="hz-Listing"><span class="hz-Listing-priority-new">Geen Topadvertentie</span></li>
    <li id="legacy-sticker" class="hz-Listing"><div class="hz-Listing-Opvalsticker-wrapper">Promo</div></li>
    <li id="legacy-new-sticker" class="hz-Listing"><div class="hz-Listing-Opvalsticker-wrapper-new">Promo</div></li>
    <li id="ordinary-with-seller-recs" class="hz-Listing"><a class="hz-Listing-coverLink" href="/v/kleding/hoeden/m123-hoed">Ordinary hat</a><div id="seller-recs" data-testid="listing-other-seller"><a href="/v/kleding/hoeden/a456-promo">Ook van deze adverteerder</a></div></li>
    <li id="ordinary-website" class="hz-Listing"><a class="hz-Listing-coverLink" href="/v/fietsen/heren/m456-bike">Bike</a><a class="hz-Listing-seller-link">Bezoek website</a></li>
    </ul><a id="home-ad" class="hz-Link hz-Link--block"><span class="hz-Listing-imageOverlayLabel">Homepagina-advertentie</span></a>
    <div id="partner" class="hz-StructuredListing"><a href="https://www.marktplaats.nl/v/x/y/a456-partner">Partner</a></div>
    <div id="regular-related" class="SimilarAdsList-related-ads-section">Related</div>
    <div id="banner-check" class="hz-Banner">Advertisement</div></section>"""
    driver.execute_script(
        'document.body.insertAdjacentHTML("beforeend",arguments[0]);', fixture
    )
    expected = {
        "ordinary": True,
        "top": False,
        "day": False,
        "business": False,
        "query": True,
        "website": True,
        "ordinary-website": True,
        "sticker": False,
        "reserved": True,
        "reserved-title": True,
        "home-ad": False,
        "partner": False,
        "regular-related": True,
        "banner-check": False,
        "upper-business": False,
        "badge-description": True,
        "legacy-sticker": False,
        "legacy-new-sticker": False,
    }
    expected.update({"ordinary-with-seller-recs": True, "seller-recs": True})

    def state():
        return driver.execute_script(
            'return Object.fromEntries([...document.querySelectorAll("#filter-check [id]")].map(x=>[x.id,getComputedStyle(x).display!=="none"]));'
        )

    def check_fixture(label, expected):
        try:
            WebDriverWait(driver, 15).until(lambda d: state() == expected)
        except TimeoutException as error:
            raise RuntimeError(
                f"{label} fixture mismatch: expected={expected}, actual={state()}"
            ) from error

    check_fixture("Default", expected)
    default_cases = len(expected)
    print("Default fixture passed", default_cases, "cases", flush=True)
    driver.execute_script(
        'document.querySelector("#filter-check ul").insertAdjacentHTML("beforeend",arguments[0]);',
        '<li id="dynamic" class="hz-Listing"><span class="hz-Listing-priority-new">Topadvertentie</span></li>',
    )
    WebDriverWait(driver, 15).until(lambda d: state().get("dynamic") is False)
    print("Dynamic insertion passed", flush=True)
    session.apply_filters(filters + "\n" + optional_filters)
    time.sleep(2)
    driver.get("https://www.marktplaats.nl/q/vintage+hoed/")
    WebDriverWait(driver, 40).until(
        lambda d: d.execute_script(
            'return document.querySelectorAll("li.hz-Listing").length>0'
        )
    )
    time.sleep(3)
    accept_cookie_dialog(driver)
    # Recommendations are not guaranteed on every load; the fixture is mandatory.
    seller_recommendations = driver.execute_script(
        "return document.querySelectorAll('[data-testid=\"listing-other-seller\"]').length"
    )
    if seller_recommendations:
        WebDriverWait(driver, 15).until(
            lambda d: d.execute_script(
                'return [...document.querySelectorAll(\'[data-testid="listing-other-seller"]\')].every(x=>getComputedStyle(x).display==="none")'
            )
        )
    else:
        print(
            "Optional live recommendations not observed; checking fixture", flush=True
        )
    optional_screenshot = screenshots_dir / "04-vintage-hoed-optional.png"
    if not driver.save_screenshot(str(optional_screenshot)):
        raise RuntimeError(f"Could not save screenshot: {optional_screenshot}")
    driver.execute_script(
        'document.body.insertAdjacentHTML("beforeend",arguments[0]);', fixture
    )
    expected["reserved"] = False
    expected["regular-related"] = False
    expected["seller-recs"] = False
    check_fixture("Combined", expected)
    print("Optional fixture passed", len(expected), "cases", flush=True)
    optional_live_url = driver.current_url
    session.apply_filters(optional_filters)
    driver.get(optional_live_url)
    WebDriverWait(driver, 40).until(
        lambda d: d.execute_script(
            'return document.querySelectorAll("li.hz-Listing").length>0'
        )
    )
    accept_cookie_dialog(driver)
    driver.execute_script(
        'document.body.insertAdjacentHTML("beforeend",arguments[0]);', fixture
    )
    standalone_expected = dict.fromkeys(expected, True)
    standalone_expected.update(
        {"reserved": False, "regular-related": False, "seller-recs": False}
    )
    check_fixture("Standalone optional", standalone_expected)
    print(
        "Standalone optional fixture passed",
        len(standalone_expected),
        "cases",
        flush=True,
    )
    return {
        "rules": len(parse),
        "live": reports,
        "defaultCases": default_cases,
        "optionalCases": len(expected),
        "optionalStandaloneCases": len(standalone_expected),
        "defaultProceduralRules": len(default_procedural),
        "dynamicInsertion": True,
        "failures": [
            f"{report['url']}: {failure}"
            for report in reports
            for failure in report["failures"]
        ],
        "optionalLive": {
            "url": optional_live_url,
            "sellerRecommendationsObserved": bool(seller_recommendations),
            "sellerRecommendationsHidden": seller_recommendations,
            "screenshot": str(optional_screenshot),
        },
    }
