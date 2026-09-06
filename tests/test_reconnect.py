import asyncio

from models.schemas import Coordinates
from services.controller import Controller


async def test_usb_reconnect_restores_and_does_not_resume_motion(tmp_path):
    c = Controller("mock", str(tmp_path / "reconnect.db"), 20, 5)
    c.monitor_interval = 0.03
    await c.start()
    try:
        await c.connect("mock-iphone")
        device = c.state.selected_device.copy()
        await c.state.set_position(Coordinates(latitude=13, longitude=100))
        c.state.moving = True
        present = False

        async def scan():
            c.devices.devices = [device] if present else []
            return c.devices.devices

        c.devices.scan = scan
        await asyncio.sleep(0.1)
        assert c.state.status == "DISCONNECTED"
        assert c.state.restore_pending
        assert not c.state.moving
        present = True
        await asyncio.sleep(0.1)
        assert c.state.status == "CONNECTED"
        assert not c.state.restore_pending
        assert not c.state.simulation_active
        assert not c.state.moving
        assert c.state.provider.location is None
    finally:
        await c.close()
