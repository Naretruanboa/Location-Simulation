from contextlib import AsyncExitStack
from typing import Protocol

from services.ios_transport import open_rsd


class LocationProvider(Protocol):
    async def connect(self, device: dict) -> None: ...
    async def set_location(self, lat: float, lon: float) -> None: ...
    async def clear_location(self) -> None: ...
    async def disconnect(self) -> None: ...


class MockLocationProvider:
    def __init__(self):
        self.connected = False
        self.location = None

    async def connect(self, device: dict) -> None:
        self.connected = True

    async def set_location(self, lat: float, lon: float) -> None:
        if not self.connected:
            raise ConnectionError("Device disconnected")
        self.location = (lat, lon)

    async def clear_location(self) -> None:
        self.location = None

    async def disconnect(self) -> None:
        self.connected = False


class PymobiledeviceLocationProvider:
    """Persistent async RSD → DVT → LocationSimulation session (pymobiledevice3 11.3.1)."""

    def __init__(self):
        self.stack = AsyncExitStack()
        self.location = None

    async def connect(self, device: dict) -> None:
        from pymobiledevice3.services.dvt.instruments.dvt_provider import DvtProvider
        from pymobiledevice3.services.dvt.instruments.location_simulation import LocationSimulation

        if device.get("developer_mode") is False:
            raise ConnectionError("Developer Mode disabled. Enable it in Settings → Privacy & Security.")
        await self.disconnect()
        try:
            rsd = await open_rsd(self.stack, device["udid"])
            if rsd.udid != device["udid"]:
                raise ConnectionError("Tunnel device identity mismatch")
            dvt = await self.stack.enter_async_context(DvtProvider(rsd))
            self.location = await self.stack.enter_async_context(LocationSimulation(dvt))
        except BaseException:
            await self.disconnect()
            raise

    async def set_location(self, lat: float, lon: float) -> None:
        if self.location is None:
            raise ConnectionError("Developer service unavailable")
        await self.location.set(lat, lon)

    async def clear_location(self) -> None:
        if self.location is None:
            raise ConnectionError("Developer service unavailable; restore pending reconnect")
        await self.location.clear()

    async def disconnect(self) -> None:
        self.location = None
        await self.stack.aclose()
        self.stack = AsyncExitStack()
