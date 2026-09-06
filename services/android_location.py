import asyncio
import re
import shlex

from services.adb import executable


class AndroidLocationProvider:
    """Android developer test-provider adapter through the persistent local ADB daemon."""

    PROVIDERS = ("gps", "network")

    def __init__(self):
        self.serial: str | None = None
        self.provider_added = False
        self.original_appop = "default"
        self.last_location: tuple[float, float] | None = None
        self.keepalive_task: asyncio.Task | None = None
        self.command_lock = asyncio.Lock()
        self.shell: asyncio.subprocess.Process | None = None

    async def _run(self, *args: str, timeout: float = 5) -> str:
        if not self.serial:
            raise ConnectionError("Android device disconnected")
        if args and args[0] == "shell":
            return await self._run_shell(*args[1:], timeout=timeout)
        async with self.command_lock:
            process = await asyncio.create_subprocess_exec(
                executable(),
                "-s",
                self.serial,
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            try:
                output, _ = await asyncio.wait_for(process.communicate(), timeout)
            except TimeoutError:
                process.kill()
                await process.wait()
                raise ConnectionError("ADB command timed out") from None
        text = output.decode(errors="replace").strip()
        if process.returncode:
            raise ConnectionError(text or "ADB command failed")
        return text

    async def _run_shell(self, *args: str, timeout: float = 5) -> str:
        async with self.command_lock:
            if not self.shell or self.shell.returncode is not None:
                self.shell = await asyncio.create_subprocess_exec(
                    executable(),
                    "-s",
                    self.serial,
                    "shell",
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                )
            assert self.shell.stdin and self.shell.stdout
            marker = "__GPS_WEB_DONE__"
            self.shell.stdin.write((shlex.join(args) + f"; echo {marker}$?\n").encode())
            await self.shell.stdin.drain()
            lines = []
            try:
                while True:
                    line = await asyncio.wait_for(self.shell.stdout.readline(), timeout)
                    if not line:
                        raise ConnectionError("BlueStacks ADB shell closed unexpectedly")
                    decoded = line.decode(errors="replace").rstrip()
                    if decoded.startswith(marker):
                        if decoded != marker + "0":
                            raise ConnectionError("\n".join(lines) or "ADB shell command failed")
                        return "\n".join(lines).strip()
                    lines.append(decoded)
            except TimeoutError:
                await self._close_shell()
                raise ConnectionError("ADB shell command timed out") from None

    async def _close_shell(self) -> None:
        if not self.shell:
            return
        if self.shell.returncode is None:
            self.shell.terminate()
            try:
                await asyncio.wait_for(self.shell.wait(), 2)
            except TimeoutError:
                self.shell.kill()
                await self.shell.wait()
        self.shell = None

    async def connect(self, device: dict) -> None:
        await self.disconnect()
        self.serial = device["udid"]
        if await self._run("get-state") != "device":
            raise ConnectionError("Unlock Android and accept the USB debugging RSA prompt")
        status = await self._run("shell", "cmd", "appops", "get", "2000", "android:mock_location")
        match = re.search(r"(?:android:mock_location:|Default mode:)\s+(allow|deny|ignore|default)", status)
        self.original_appop = match.group(1) if match else "default"
        await self._run("shell", "cmd", "appops", "set", "2000", "android:mock_location", "allow")

    async def _add_providers(self) -> None:
        if self.provider_added:
            return
        added = []
        try:
            for provider in self.PROVIDERS:
                properties = (
                    ("--requiresSatellite", "--supportsSpeed", "--supportsBearing")
                    if provider == "gps"
                    else ("--requiresNetwork",)
                )
                await self._run(
                    "shell",
                    "cmd",
                    "location",
                    "providers",
                    "add-test-provider",
                    provider,
                    *properties,
                )
                added.append(provider)
                await self._run(
                    "shell", "cmd", "location", "providers", "set-test-provider-enabled", provider, "true"
                )
            self.provider_added = True
        except Exception:
            for provider in reversed(added):
                try:
                    await self._run("shell", "cmd", "location", "providers", "remove-test-provider", provider)
                except Exception:
                    pass
            raise

    async def set_location(self, lat: float, lon: float) -> None:
        await self._add_providers()
        self.last_location = (lat, lon)
        await self._send_location(lat, lon)
        if not self.keepalive_task or self.keepalive_task.done():
            self.keepalive_task = asyncio.create_task(self._keepalive())

    async def _send_location(self, lat: float, lon: float) -> None:
        for provider in self.PROVIDERS:
            await self._run(
                "shell",
                "cmd",
                "location",
                "providers",
                "set-test-provider-location",
                provider,
                "--location",
                f"{lat:.8f},{lon:.8f}",
                "--accuracy",
                "3",
            )

    async def _keepalive(self) -> None:
        try:
            while self.provider_added and self.last_location:
                await asyncio.sleep(0.75)
                if self.provider_added and self.last_location:
                    await self._send_location(*self.last_location)
        except (asyncio.CancelledError, ConnectionError):
            pass

    async def clear_location(self) -> None:
        if self.keepalive_task:
            self.keepalive_task.cancel()
            try:
                await self.keepalive_task
            except asyncio.CancelledError:
                pass
            self.keepalive_task = None
        error = None
        if self.provider_added:
            for provider in reversed(self.PROVIDERS):
                try:
                    await self._run("shell", "cmd", "location", "providers", "remove-test-provider", provider)
                except ConnectionError as exc:
                    error = error or exc
            self.provider_added = False
        self.last_location = None
        if error:
            raise error

    async def disconnect(self) -> None:
        if not self.serial:
            return
        try:
            await self.clear_location()
            await self._run(
                "shell",
                "cmd",
                "appops",
                "set",
                "2000",
                "android:mock_location",
                self.original_appop,
            )
        finally:
            await self._close_shell()
            self.serial = None
            self.provider_added = False
