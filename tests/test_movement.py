import asyncio

import pytest

from models.schemas import Coordinates
from models.state import AppState
from services.controller import Controller
from services.ios_location import MockLocationProvider


class FailingProvider(MockLocationProvider):
    async def set_location(self, lat, lon):
        raise ConnectionError("USB removed")


async def test_provider_failure_stops_movement():
    s = AppState(FailingProvider(), status="CONNECTED", moving=True)
    with pytest.raises(ConnectionError):
        await s.set_position(Coordinates(latitude=0, longitude=0))
    assert s.status == "ERROR"
    assert not s.moving
    assert s.restore_pending


async def test_clear_failure_keeps_pending():
    class FailClear(MockLocationProvider):
        async def clear_location(self):
            raise ConnectionError("gone")

    s = AppState(FailClear(), status="CONNECTED", simulation_active=True, moving=True)
    with pytest.raises(ConnectionError):
        await s.clear()
    assert s.restore_pending and s.simulation_active and not s.moving


async def test_worker_uses_provider_and_shuts_down(tmp_path):
    c = Controller("mock", str(tmp_path / "app.db"), 20, 5)
    await c.start()
    try:
        await c.connect("mock-iphone")
        await c.state.set_position(Coordinates(latitude=0, longitude=0))
        c.state.moving = True
        await asyncio.sleep(0.2)
        assert c.state.position.latitude > 0
        assert c.state.provider.location[0] == c.state.position.latitude
        assert len(c.tasks) == 2
    finally:
        await c.close()
