import json
from unittest.mock import MagicMock, patch

import pytest

from picura.core.geocoding import NominatimProvider, _format_address, reverse_geocode


# --- _format_address ---


def test_format_address_city_and_country():
    assert (
        _format_address({'city': 'Berlin', 'country': 'Germany'}) == 'Berlin, Germany'
    )


def test_format_address_prefers_village_over_town_and_city():
    addr = {
        'village': 'Mellenthin',
        'town': 'Usedom',
        'city': 'Big City',
        'country': 'Germany',
    }
    assert _format_address(addr) == 'Mellenthin, Germany'


def test_format_address_town_fallback():
    assert (
        _format_address({'town': 'Usedom', 'country': 'Germany'}) == 'Usedom, Germany'
    )


def test_format_address_municipality_fallback():
    assert (
        _format_address({'municipality': 'Usedom-Süd', 'country': 'Germany'})
        == 'Usedom-Süd, Germany'
    )


def test_format_address_county_fallback():
    assert (
        _format_address({'county': 'Vorpommern', 'country': 'Germany'})
        == 'Vorpommern, Germany'
    )


def test_format_address_place_only():
    assert _format_address({'city': 'Berlin'}) == 'Berlin'


def test_format_address_country_only():
    assert _format_address({'country': 'Germany'}) == 'Germany'


def test_format_address_empty():
    assert _format_address({}) == ''


# --- NominatimProvider ---


def _mock_urlopen(address: dict):
    body = json.dumps({'address': address}).encode()
    mock_resp = MagicMock()
    mock_resp.read.return_value = body
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


def test_nominatim_returns_formatted_location():
    provider = NominatimProvider('test/1.0')
    with patch(
        'urllib.request.urlopen',
        return_value=_mock_urlopen({'city': 'Berlin', 'country': 'Germany'}),
    ):
        assert provider.reverse_geocode(52.52, 13.405, 'en') == 'Berlin, Germany'


def test_nominatim_passes_language_in_request():
    provider = NominatimProvider('test/1.0')
    captured = {}

    def fake_urlopen(req, timeout):
        captured['url'] = req.full_url
        return _mock_urlopen({'city': 'Berlin', 'country': 'Deutschland'})

    with patch('urllib.request.urlopen', side_effect=fake_urlopen):
        provider.reverse_geocode(52.52, 13.405, 'de')

    assert 'accept-language=de' in captured['url']


def test_nominatim_returns_none_on_network_error():
    provider = NominatimProvider('test/1.0')
    with patch('urllib.request.urlopen', side_effect=OSError('network error')):
        assert provider.reverse_geocode(52.52, 13.405, 'en') is None


def test_nominatim_returns_none_when_address_missing():
    provider = NominatimProvider('test/1.0')
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({'error': 'Unable to geocode'}).encode()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    with patch('urllib.request.urlopen', return_value=mock_resp):
        assert provider.reverse_geocode(0.0, 0.0, 'en') is None


def test_nominatim_sends_user_agent():
    provider = NominatimProvider('mypicura/2.0')
    captured = {}

    def fake_urlopen(req, timeout):
        captured['user_agent'] = req.get_header('User-agent')
        return _mock_urlopen({'city': 'Berlin', 'country': 'Germany'})

    with patch('urllib.request.urlopen', side_effect=fake_urlopen):
        provider.reverse_geocode(52.52, 13.405, 'en')

    assert captured['user_agent'] == 'mypicura/2.0'


# --- reverse_geocode function ---


def test_reverse_geocode_uses_nominatim_provider(settings):
    settings.GEOCODING_PROVIDER = 'nominatim'
    settings.GEOCODING_USER_AGENT = 'test/1.0'
    with patch(
        'urllib.request.urlopen',
        return_value=_mock_urlopen({'city': 'Berlin', 'country': 'Germany'}),
    ):
        assert reverse_geocode(52.52, 13.405, 'en') == 'Berlin, Germany'


def test_reverse_geocode_raises_on_unknown_provider(settings):
    settings.GEOCODING_PROVIDER = 'unknown'
    with pytest.raises(ValueError, match='unknown'):
        reverse_geocode(52.52, 13.405, 'en')
