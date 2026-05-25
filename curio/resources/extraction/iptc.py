from dataclasses import dataclass, field

from PIL import Image, IptcImagePlugin


@dataclass
class IptcData:
    title: str | None = None
    description: str | None = None
    keywords: list[str] = field(default_factory=list)
    copyright: str | None = None
    creator: str | None = None


def _decode_str(value) -> str | None:
    if isinstance(value, list):
        value = value[0] if value else None
    if isinstance(value, bytes):
        return value.decode('utf-8', errors='replace').strip() or None
    return str(value).strip() or None if value else None


def _decode_list(value) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        value = [value]
    result = []
    for item in value:
        if isinstance(item, bytes):
            decoded = item.decode('utf-8', errors='replace').strip()
        else:
            decoded = str(item).strip()
        if decoded:
            result.append(decoded)
    return result


def extract_iptc(img: Image.Image) -> IptcData:
    try:
        iptc = IptcImagePlugin.getiptcinfo(img)
    except Exception:
        return IptcData()
    if not iptc:
        return IptcData()
    return IptcData(
        title=_decode_str(iptc.get((2, 5))),
        description=_decode_str(iptc.get((2, 120))),
        keywords=_decode_list(iptc.get((2, 25))),
        copyright=_decode_str(iptc.get((2, 116))),
        creator=_decode_str(iptc.get((2, 80))),
    )
