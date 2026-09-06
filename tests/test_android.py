from services.android_location import AndroidLocationProvider


class FakeAndroidProvider(AndroidLocationProvider):
    def __init__(self):
        super().__init__()
        self.calls = []

    async def _run(self, *args: str, timeout: float = 5) -> str:
        self.calls.append(args)
        if args == ("get-state",):
            return "device"
        if args[:5] == ("shell", "cmd", "appops", "get", "2000"):
            return "No operations.\nDefault mode: deny"
        return ""


async def test_android_provider_lifecycle():
    provider = FakeAndroidProvider()
    await provider.connect({"udid": "test-serial"})
    assert provider.original_appop == "deny"
    assert provider.calls[-1][-1] == "allow"

    await provider.set_location(13.7563, 100.5018)
    assert provider.provider_added
    assert sum("13.75630000,100.50180000" in call for call in provider.calls) == 2

    await provider.clear_location()
    assert not provider.provider_added
    assert sum("remove-test-provider" in call for call in provider.calls) == 2

    await provider.disconnect()
    assert provider.serial is None
    assert provider.calls[-1][-1] == "deny"


async def test_android_set_reuses_provider():
    provider = FakeAndroidProvider()
    await provider.connect({"udid": "test-serial"})
    await provider.set_location(0, 0)
    await provider.set_location(1, 1)
    adds = [call for call in provider.calls if "add-test-provider" in call]
    assert len(adds) == 2
    await provider.clear_location()
