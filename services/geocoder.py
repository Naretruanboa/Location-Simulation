import asyncio
import time
from collections import OrderedDict

import httpx

USER_AGENT = "iPhoneGPSWebController/1.0 (local developer utility)"


class GeocodingError(Exception):
    pass


class Geocoder:
    """Submit-only Nominatim adapter with app-wide rate limiting and caching."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(
            timeout=8,
            follow_redirects=False,
            trust_env=False,
            headers={"User-Agent": USER_AGENT},
        )
        self.lock = asyncio.Lock()
        self.last_request = 0.0
        self.cache: OrderedDict[str, list[dict]] = OrderedDict()

    async def search(self, query: str, language: str = "en") -> list[dict]:
        normalized = " ".join(query.split()).casefold()
        if normalized in self.cache:
            self.cache.move_to_end(normalized)
            return self.cache[normalized]
        async with self.lock:
            if normalized in self.cache:
                return self.cache[normalized]
            await asyncio.sleep(max(0, 1.05 - (time.monotonic() - self.last_request)))
            try:
                response = await self.client.get(
                    f"{self.base_url}/search",
                    headers={"User-Agent": USER_AGENT},
                    params={
                        "q": query,
                        "format": "jsonv2",
                        "limit": 6,
                        "addressdetails": 0,
                        "accept-language": language[:32],
                    },
                )
                self.last_request = time.monotonic()
                response.raise_for_status()
                payload = response.json()
                results = []
                for item in payload[:6]:
                    lat, lon = float(item["lat"]), float(item["lon"])
                    if -90 <= lat <= 90 and -180 <= lon <= 180:
                        results.append(
                            {
                                "name": str(item.get("display_name", "Unknown place"))[:500],
                                "latitude": lat,
                                "longitude": lon,
                                "type": str(item.get("type", "place"))[:80],
                            }
                        )
            except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
                raise GeocodingError("Place search is temporarily unavailable.") from exc
            self.cache[normalized] = results
            while len(self.cache) > 100:
                self.cache.popitem(last=False)
            return results

    async def close(self) -> None:
        await self.client.aclose()
