import os
import platform
from contextlib import AsyncExitStack

import httpx


async def open_rsd(stack: AsyncExitStack, udid: str):
    """Compatibility boundary verified against installed pymobiledevice3 11.3.1."""
    from pymobiledevice3.remote.remote_service_discovery import RemoteServiceDiscoveryService

    transport = os.getenv("IOS_TRANSPORT", "native" if platform.system() == "Darwin" else "tunneld")
    if transport == "native":
        from pymobiledevice3.remote.native_tunnel import NativeRemotedTunnel

        return await stack.enter_async_context(NativeRemotedTunnel(serial=udid))
    if transport != "tunneld":
        raise ValueError("IOS_TRANSPORT must be native or tunneld")
    async with httpx.AsyncClient(timeout=3, trust_env=False) as client:
        response = await client.get("http://127.0.0.1:49151/")
        response.raise_for_status()
        endpoints = response.json().get(udid, [])
    if not endpoints:
        raise ConnectionError("No developer tunnel. Start pymobiledevice3 remote tunneld over USB.")
    endpoint = endpoints[0]
    rsd = RemoteServiceDiscoveryService((endpoint["tunnel-address"], endpoint["tunnel-port"]))
    stack.push_async_callback(rsd.close)
    await rsd.connect()
    return rsd
