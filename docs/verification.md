# Verification report

Verified on 6 September 2026 in Mock Mode and against an attached iPhone where explicitly stated.

## Automated checks

- `pytest -q`: 56 passed. Two upstream deprecation warnings are emitted by FastAPI/Starlette's test client.
- `ruff check .`: passed.
- Python `compileall`: passed.
- `node --check static/js/*.js`: passed.
- FastAPI startup on `127.0.0.1:8000`: passed.
- Static HTML, CSS, JavaScript and vendored Leaflet requests: passed.
- REST and WebSocket integration tests: passed.
- Reconnect simulation, shutdown clear, WebSocket owner cleanup and dead-man timeout: passed.

## Browser smoke test

Headless Google Chrome was run at 1440×1000 and 390×844 against the live Mock Mode server. It verified device selection, Teleport, WASD movement, pointer joystick at 45°, speed changes, Two Spot route controls, GPX preview, Favorites persistence, History, and Restore Real Location. No page JavaScript errors were recorded. The mobile layout had no horizontal document overflow.

Screenshots: [desktop](screenshots/desktop.png) and [mobile](screenshots/mobile.png).

## Real iPhone adapter check

An attached USB iPhone was discovered successfully. The read-only metadata check reported iOS 26.6, USB transport, Developer Mode enabled and a trusted Lockdown session.

Using pymobiledevice3 11.3.1, the application opened and closed the complete native macOS transport stack successfully:

`NativeRemotedTunnel → RSD → DvtProvider → LocationSimulation`

This verification did not call `LocationSimulation.set()` or change the real device's position. Real-device Teleport, continuous movement, route execution, physical USB removal and `clear()` were therefore not exercised. Their control flow is covered by the Mock provider tests, while final behavior still depends on the connected iOS build and developer services.

The in-app browser bridge was unavailable in this session, so visual verification used a separate local headless Chrome instance.

## BlueStacks Air adapter check

BlueStacks Air on macOS was discovered through its bundled `hd-adb` at `127.0.0.1:5555` and represented once as `ADB EMULATOR`, despite BlueStacks also publishing an `emulator-5554` alias. The controller opened a persistent ADB shell, connected successfully, set a Bangkok test coordinate, kept it active for two seconds, and restored the normal providers successfully. The test ended with simulation inactive while the web server remained connected to the emulator.
