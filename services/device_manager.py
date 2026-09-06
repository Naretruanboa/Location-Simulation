import asyncio
import logging

from services.adb import endpoints, executable

logger = logging.getLogger(__name__)


class DeviceManager:
    def __init__(self, mode: str):
        self.mode = mode
        self.devices: list[dict] = []
        self.error: str | None = None

    async def scan(self) -> list[dict]:
        if self.mode == "mock":
            self.devices = [
                {
                    "udid": "mock-iphone",
                    "name": "Development iPhone",
                    "ios_version": "Mock",
                    "connection": "MOCK",
                    "developer_mode": True,
                    "status": "DISCONNECTED",
                }
            ]
            return self.devices
        if self.mode == "android":
            return await self._scan_android()
        from pymobiledevice3.lockdown import create_using_usbmux
        from pymobiledevice3.usbmux import list_devices

        found = []
        try:
            devices = await asyncio.wait_for(list_devices(), 4)
            for device in devices:
                if device.connection_type != "USB":
                    continue
                info = {
                    "udid": device.serial,
                    "name": "iPhone",
                    "ios_version": "Unknown",
                    "connection": "USB",
                    "developer_mode": None,
                    "status": "DISCONNECTED",
                }
                client = None
                try:
                    client = await asyncio.wait_for(
                        create_using_usbmux(serial=device.serial, connection_type="USB", autopair=False), 4
                    )
                    info["name"] = client.all_values.get("DeviceName", "iPhone")
                    info["ios_version"] = client.all_values.get("ProductVersion", "Unknown")
                    try:
                        info["developer_mode"] = await asyncio.wait_for(client.get_developer_mode_status(), 2)
                    except Exception:
                        pass
                except Exception:
                    info["status"] = "ERROR"
                    info["error"] = "Unlock iPhone and Trust This Computer"
                finally:
                    if client:
                        await client.close()
                found.append(info)
            self.error = None
        except Exception as exc:
            self.error = "USB discovery unavailable: " + type(exc).__name__
        self.devices = found
        return found

    async def _scan_android(self) -> list[dict]:
        try:
            for endpoint in endpoints():
                connect = await asyncio.create_subprocess_exec(
                    executable(),
                    "connect",
                    endpoint,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                await asyncio.wait_for(connect.wait(), 5)
            process = await asyncio.create_subprocess_exec(
                executable(),
                "devices",
                "-l",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), 5)
            if process.returncode:
                raise ConnectionError(stderr.decode(errors="replace"))
            found = []
            endpoint_set = set(endpoints())
            for line in stdout.decode(errors="replace").splitlines()[1:]:
                fields = line.split()
                if len(fields) < 2:
                    continue
                serial, adb_status = fields[:2]
                details = dict(part.split(":", 1) for part in fields[2:] if ":" in part)
                name = details.get("model", "Android").replace("_", " ")
                connection = (
                    "ADB EMULATOR" if serial.startswith("emulator-") or serial in endpoint_set else "ADB USB"
                )
                found.append(
                    {
                        "udid": serial,
                        "name": name,
                        "ios_version": "Android",
                        "connection": connection,
                        "developer_mode": adb_status == "device",
                        "status": "DISCONNECTED" if adb_status == "device" else "ERROR",
                        **({"error": "Accept the USB debugging prompt"} if adb_status != "device" else {}),
                    }
                )
            # BlueStacks exposes the same instance under an emulator alias and a TCP endpoint.
            # Prefer the configured TCP endpoint, which is stable across project restarts.
            if endpoint_set:
                preferred = [item for item in found if item["udid"] in endpoint_set]
                if preferred:
                    found = preferred
            self.devices, self.error = found, None
        except Exception as exc:
            self.devices = []
            self.error = "ADB discovery unavailable: " + type(exc).__name__
        return self.devices
