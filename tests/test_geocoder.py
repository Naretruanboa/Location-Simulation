import httpx
import pytest

from services.geocoder import Geocoder, GeocodingError


async def test_search_filters_caches_and_identifies_client():
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(
            200,
            json=[
                {"display_name": "Bangkok, Thailand", "lat": "13.75", "lon": "100.50", "type": "city"},
                {"display_name": "Invalid", "lat": "999", "lon": "0"},
            ],
        )

    geocoder = Geocoder("https://example.test")
    await geocoder.client.aclose()
    geocoder.client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        first = await geocoder.search(" Bangkok ", "th-TH")
        second = await geocoder.search("bangkok", "en")
        assert first == second
        assert first[0]["latitude"] == 13.75
        assert len(calls) == 1
        assert calls[0].headers["user-agent"].startswith("iPhoneGPSWebController/")
        assert calls[0].url.params["accept-language"] == "th-TH"
    finally:
        await geocoder.close()


async def test_search_failure_is_stable_error():
    geocoder = Geocoder("https://example.test")
    await geocoder.client.aclose()
    geocoder.client = httpx.AsyncClient(transport=httpx.MockTransport(lambda request: httpx.Response(503)))
    try:
        with pytest.raises(GeocodingError, match="temporarily unavailable"):
            await geocoder.search("Tokyo")
    finally:
        await geocoder.close()
