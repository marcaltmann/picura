import json
import urllib.parse
import urllib.request

from django.conf import settings


def _format_address(address: dict) -> str:
    place = (
        address.get('village')
        or address.get('town')
        or address.get('city')
        or address.get('municipality')
        or address.get('county')
        or ''
    )
    country = address.get('country', '')
    if place and country:
        return f'{place}, {country}'
    return place or country


class NominatimProvider:
    _BASE_URL = 'https://nominatim.openstreetmap.org/reverse'

    def __init__(self, user_agent: str):
        self.user_agent = user_agent

    def reverse_geocode(self, lat: float, lon: float, lang: str = 'en') -> str | None:
        params = urllib.parse.urlencode(
            {
                'lat': lat,
                'lon': lon,
                'format': 'json',
                'accept-language': lang,
            }
        )
        req = urllib.request.Request(
            f'{self._BASE_URL}?{params}',
            headers={'User-Agent': self.user_agent},
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read())
        except OSError:
            return None
        address = data.get('address')
        if not address:
            return None
        return _format_address(address) or None


def reverse_geocode(lat: float, lon: float, lang: str = 'en') -> str | None:
    provider = getattr(settings, 'GEOCODING_PROVIDER', 'nominatim')
    if provider == 'nominatim':
        user_agent = getattr(settings, 'GEOCODING_USER_AGENT', 'picura/1.0')
        return NominatimProvider(user_agent).reverse_geocode(lat, lon, lang)
    raise ValueError(f'Unknown geocoding provider: {provider!r}')
