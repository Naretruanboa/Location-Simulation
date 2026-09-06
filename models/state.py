import asyncio
import logging
import time
from dataclasses import dataclass, field

from models.schemas import Coordinates
from services.ios_location import LocationProvider
from services.route_engine import RouteEngine

logger = logging.getLogger(__name__)


@dataclass
class AppState:
    provider: LocationProvider
    speed_kmh: float = 5
    selected_device: dict | None = None
    status: str = "DISCONNECTED"
    position: Coordinates | None = None
    bearing: float = 0
    moving: bool = False
    simulation_active: bool = False
    restore_pending: bool = False
    route: RouteEngine | None = None
    owner: str | None = None
    last_input: float = field(default_factory=time.monotonic)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def snapshot(self) -> dict:
        return {
            "type": "location_state",
            "latitude": self.position.latitude if self.position else None,
            "longitude": self.position.longitude if self.position else None,
            "speed_kmh": self.speed_kmh,
            "bearing": self.bearing,
            "moving": self.moving or bool(self.route and self.route.status == "running"),
            "simulation_active": self.simulation_active,
            "restore_pending": self.restore_pending,
        }

    def device_snapshot(self) -> dict:
        return {
            "type": "device_state",
            "device": self.selected_device,
            "status": self.status,
            "connected": self.status == "CONNECTED",
        }

    def stop(self) -> None:
        self.moving = False
        self.owner = None
        if self.route and self.route.status in ("running", "paused"):
            self.route.status = "stopped"

    def require_connected(self) -> None:
        if self.status != "CONNECTED":
            raise ConnectionError("Device disconnected. Connect a device first.")

    async def set_position(self, point: Coordinates) -> None:
        self.require_connected()
        if self.restore_pending:
            raise ConnectionError("Restore the pending simulated location before continuing.")
        try:
            self.restore_pending = True
            await asyncio.wait_for(self.provider.set_location(point.latitude, point.longitude), 5)
        except Exception:
            self.restore_pending = True
            await self.failed()
            raise ConnectionError("Location simulation failed. Check USB and Developer Mode.") from None
        self.restore_pending = False
        self.position = point
        self.simulation_active = True

    async def clear(self) -> None:
        self.stop()
        if self.simulation_active or self.restore_pending:
            try:
                await asyncio.wait_for(self.provider.clear_location(), 5)
            except Exception:
                self.restore_pending = True
                await self.failed()
                raise ConnectionError("Restore failed; reconnect this device to retry.") from None
        self.simulation_active = False
        self.restore_pending = False
        self.position = None
        logger.info("Simulation cleared")

    async def failed(self) -> None:
        self.stop()
        self.status = "ERROR"
        self.restore_pending = self.restore_pending or self.simulation_active
        try:
            await asyncio.wait_for(self.provider.disconnect(), 3)
        except Exception:
            pass
        logger.warning("Device session lost; reconnect pending")
