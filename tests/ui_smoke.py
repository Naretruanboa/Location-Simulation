"""Optional real-browser smoke test. Start a mock server first; see requirements-ui.txt."""

import json
import os
from pathlib import Path

import httpx
from playwright.sync_api import expect, sync_playwright

BASE = os.getenv("GPS_TEST_URL", "http://127.0.0.1:8000")
ARTIFACTS = Path(os.getenv("GPS_TEST_ARTIFACTS", "docs/screenshots"))


def main():
    with httpx.Client(base_url=BASE, trust_env=False) as client:
        assert client.get("/api/state").json()["provider"] == "mock", "UI smoke tests require Mock Mode"
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        executable = os.getenv("CHROME_PATH", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
        browser = p.chromium.launch(executable_path=executable, headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 1000},
            device_scale_factor=1,
            geolocation={"latitude": 13.73001, "longitude": 100.57002, "accuracy": 25},
            permissions=["geolocation"],
        )
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(BASE)
        expect(page.locator("#socket-status")).to_contain_text("Live connection")
        page.locator("#connect").click()
        expect(page.locator("#device-status")).to_have_text("CONNECTED")
        page.locator("#locate-mac").click()
        expect(page.locator("#destination-display")).to_have_text("13.730010, 100.570020")
        page.locator("#search").fill("13.7563, 100.5018")
        page.locator("#search-form button").click()
        page.locator("#teleport").click()
        expect(page.locator("#latitude")).to_have_text("13.756300")
        page.locator('[data-mode="joystick"]').click()
        page.keyboard.down("w")
        expect(page.locator("#movement")).to_have_text("Moving")
        page.wait_for_timeout(300)
        page.keyboard.up("w")
        expect(page.locator("#movement")).to_have_text("Idle")
        assert float(page.locator("#latitude").inner_text()) > 13.7563
        box = page.locator("#joystick").bounding_box()
        x, y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
        page.mouse.move(x, y)
        page.mouse.down()
        page.mouse.move(x + 35, y - 35, steps=5)
        expect(page.locator("#movement")).to_have_text("Moving")
        expect(page.locator("#bearing")).to_have_text("45°")
        page.mouse.up()
        expect(page.locator("#movement")).to_have_text("Idle")
        page.locator('[data-speed="10"]').click()
        expect(page.locator("#speed-value")).to_contain_text("10.0")
        page.locator('[data-mode="two"]').click()
        page.locator("#add-waypoint").click()
        page.locator("#search").fill("13.7573, 100.5028")
        page.locator("#search-form button").click()
        page.locator("#add-waypoint").click()
        expect(page.locator("#route-summary")).to_contain_text("2 waypoints")
        page.locator("#start-route").click()
        expect(page.locator("#route-status")).to_contain_text("running")
        page.locator("#pause-route").click()
        expect(page.locator("#route-status")).to_contain_text("paused")
        page.locator("#resume-route").click()
        expect(page.locator("#route-status")).to_contain_text("running")
        page.locator("#stop-route").click()
        expect(page.locator("#route-status")).to_contain_text("stopped")
        # Search metadata must not leak into strict coordinate payloads.
        page.locator('[data-mode="route"]').click()
        page.locator("#clear-route").click()
        page.locator("#use-current").click()
        page.route("**/api/search?**", lambda route: route.fulfill(json={"results": [
            {"name": "Test destination", "type": "park", "latitude": 13.75631, "longitude": 100.5018}
        ]}))
        page.locator("#search").fill("Test destination")
        page.locator("#search-form button").click()
        page.locator("#search-results button").click()
        page.locator("#add-waypoint").click()
        page.locator("#search").fill("13.75632, 100.5018")
        page.locator("#search-form button").click()
        page.locator("#add-waypoint").click()
        expect(page.locator("#route-summary")).to_contain_text("3 waypoints")
        page.locator("#start-route").click()
        expect(page.locator("#route-status")).to_contain_text("completed", timeout=15000)
        expect(page.locator("#latitude")).to_have_text("13.756320")
        expect(page.locator("#pause-route")).to_be_disabled()
        expect(page.locator("#resume-route")).to_be_disabled()
        page.locator('#waypoints button').filter(has_text="Remove").last.click()
        expect(page.locator("#route-summary")).to_contain_text("2 waypoints")
        page.locator('[data-mode="gpx"]').click()
        page.locator("#gpx-file").set_input_files("examples/bangkok-walk.gpx")
        expect(page.locator("#route-summary")).to_contain_text("3 waypoints")
        page.once("dialog", lambda dialog: dialog.accept("UI smoke favorite"))
        page.locator("#favorite").click()
        page.locator('[data-mode="favorites"]').click()
        expect(page.locator("#saved-list")).to_contain_text("UI smoke favorite")
        page.locator("#saved-list button").filter(has_text="Delete").first.click()
        page.locator('[data-mode="history"]').click()
        expect(page.locator("#saved-list")).to_contain_text("Today")
        page.locator('[data-mode="teleport"]').click()
        page.screenshot(path=str(ARTIFACTS / "desktop.png"), full_page=True)
        page.set_viewport_size({"width": 390, "height": 844})
        page.screenshot(path=str(ARTIFACTS / "mobile.png"), full_page=True)
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), "Mobile overflow"
        page.locator("#restore").click()
        expect(page.locator("#simulation-label")).to_have_text("Simulation inactive")
        expect(page.locator("#latitude")).to_have_text("—")
        assert not errors, errors
        browser.close()
        print(
            json.dumps(
                {
                    "result": "PASS",
                    "browser": "Chrome headless",
                    "console_errors": errors,
                    "screenshots": str(ARTIFACTS),
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
