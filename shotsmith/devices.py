"""Device profile registry.

Each profile defines the App Store Connect submission slot dimensions and a
default caption font size that produces legible output at that resolution.

Sizes pulled from Apple's App Store Connect screenshot specifications:
https://developer.apple.com/help/app-store-connect/reference/screenshot-specifications/
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class DeviceProfile:
    name: str
    asc_category: str
    # For composed devices: ASC submission slot dimensions.
    # For passthrough devices: the raw screen dimensions (= submitted size).
    width: int
    height: int
    # frames-cli's output dimensions (used by verify to check framed/ PNGs).
    # None for passthrough devices, which never go through frames-cli.
    framed_width: int | None = None
    framed_height: int | None = None
    default_caption_size: int | None = None
    # True for devices that bypass frame + compose. shotsmith's `passthrough`
    # step just copies raw/ → output/ unmodified. Today: Apple Watch — its
    # hardware corner-radius would clip composed bezel art at viewing time, so
    # ASC accepts raw screen PNGs (e.g. 422×514 for Watch Ultra 3 49mm).
    passthrough: bool = False


# framed_* values come from frames-cli's actual output dimensions.
# iPhone 6.9" framed = 1470x3000 (verified empirically against frames-cli output).
# iPad 13" framed = 2228x3084 (estimated from frames-cli's iPad scaling pattern;
#   verify warns rather than errors if real values differ on first frame run).
DEVICES: dict[str, DeviceProfile] = {
    "iphone": DeviceProfile(
        name="iPhone 6.9\" (iPhone 17 Pro Max)",
        asc_category="iPhone 6.9\" Display",
        width=1320,
        height=2868,
        framed_width=1470,
        framed_height=3000,
        default_caption_size=115,
    ),
    "ipad": DeviceProfile(
        name="iPad 13\" (iPad Pro 13-inch M5)",
        asc_category="iPad 13\" Display",
        width=2064,
        height=2752,
        framed_width=2228,
        framed_height=3084,
        default_caption_size=130,
    ),
    "watch": DeviceProfile(
        name="Apple Watch Ultra 3 (49mm)",
        asc_category="Apple Watch Ultra (49mm)",
        # Raw screen dims for Watch Ultra 3 49mm — also the ASC submitted
        # size. No framing, no caption, no gradient: the hardware corner
        # radius would clip composed bezel art at viewing time.
        width=422,
        height=514,
        passthrough=True,
    ),
}


def get(device_key: str) -> DeviceProfile:
    if device_key not in DEVICES:
        raise ValueError(
            f"Unknown device '{device_key}'. Known: {sorted(DEVICES.keys())}"
        )
    return DEVICES[device_key]
