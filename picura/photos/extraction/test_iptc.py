from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from .iptc import IptcData, extract_iptc


def make_img():
    return MagicMock()


def test_returns_empty_dataclass_when_no_iptc_info():
    with patch(
        'picura.photos.extraction.iptc.IptcImagePlugin.getiptcinfo', return_value=None
    ):
        result = extract_iptc(make_img())
    assert result == IptcData()


def test_returns_empty_dataclass_on_exception():
    with patch(
        'picura.photos.extraction.iptc.IptcImagePlugin.getiptcinfo',
        side_effect=Exception('boom'),
    ):
        result = extract_iptc(make_img())
    assert result == IptcData()


def test_extracts_title():
    iptc = {(2, 5): [b'Sunset over the Lake']}
    with patch(
        'picura.photos.extraction.iptc.IptcImagePlugin.getiptcinfo', return_value=iptc
    ):
        result = extract_iptc(make_img())
    assert result.title == 'Sunset over the Lake'


def test_extracts_description():
    iptc = {(2, 120): [b'A beautiful landscape.']}
    with patch(
        'picura.photos.extraction.iptc.IptcImagePlugin.getiptcinfo', return_value=iptc
    ):
        result = extract_iptc(make_img())
    assert result.description == 'A beautiful landscape.'


def test_extracts_copyright():
    iptc = {(2, 116): [b'\xc2\xa9 2024 Jane Smith']}
    with patch(
        'picura.photos.extraction.iptc.IptcImagePlugin.getiptcinfo', return_value=iptc
    ):
        result = extract_iptc(make_img())
    assert result.copyright == '© 2024 Jane Smith'


def test_extracts_creator():
    iptc = {(2, 80): [b'Jane Smith']}
    with patch(
        'picura.photos.extraction.iptc.IptcImagePlugin.getiptcinfo', return_value=iptc
    ):
        result = extract_iptc(make_img())
    assert result.creator == 'Jane Smith'


def test_extracts_keywords_as_list():
    iptc = {(2, 25): [b'nature', b'landscape', b'sunset']}
    with patch(
        'picura.photos.extraction.iptc.IptcImagePlugin.getiptcinfo', return_value=iptc
    ):
        result = extract_iptc(make_img())
    assert result.keywords == ['nature', 'landscape', 'sunset']


def test_extracts_single_keyword():
    iptc = {(2, 25): [b'portrait']}
    with patch(
        'picura.photos.extraction.iptc.IptcImagePlugin.getiptcinfo', return_value=iptc
    ):
        result = extract_iptc(make_img())
    assert result.keywords == ['portrait']


def test_keywords_empty_list_when_absent():
    iptc = {(2, 5): [b'Title Only']}
    with patch(
        'picura.photos.extraction.iptc.IptcImagePlugin.getiptcinfo', return_value=iptc
    ):
        result = extract_iptc(make_img())
    assert result.keywords == []


def test_missing_fields_are_none():
    iptc = {(2, 5): [b'Only Title']}
    with patch(
        'picura.photos.extraction.iptc.IptcImagePlugin.getiptcinfo', return_value=iptc
    ):
        result = extract_iptc(make_img())
    assert result.description is None
    assert result.copyright is None
    assert result.creator is None


def test_strips_whitespace_from_string_fields():
    iptc = {(2, 5): [b'  Padded Title  '], (2, 80): [b'  Author  ']}
    with patch(
        'picura.photos.extraction.iptc.IptcImagePlugin.getiptcinfo', return_value=iptc
    ):
        result = extract_iptc(make_img())
    assert result.title == 'Padded Title'
    assert result.creator == 'Author'


def test_blank_string_becomes_none():
    iptc = {(2, 5): [b'   ']}
    with patch(
        'picura.photos.extraction.iptc.IptcImagePlugin.getiptcinfo', return_value=iptc
    ):
        result = extract_iptc(make_img())
    assert result.title is None


def test_accepts_path_object(tmp_path):
    from PIL import Image as PilImage

    img = PilImage.new('RGB', (1, 1))
    path = tmp_path / 'test.jpg'
    img.save(path)
    result = extract_iptc(path)
    assert result == IptcData()


def test_raises_when_path_does_not_exist():
    with pytest.raises(FileNotFoundError):
        extract_iptc(Path('/nonexistent/image.jpg'))


def test_extracts_all_fields_together():
    iptc = {
        (2, 5): [b'My Photo'],
        (2, 120): [b'A caption.'],
        (2, 25): [b'travel', b'city'],
        (2, 116): [b'(c) 2024'],
        (2, 80): [b'John Doe'],
    }
    with patch(
        'picura.photos.extraction.iptc.IptcImagePlugin.getiptcinfo', return_value=iptc
    ):
        result = extract_iptc(make_img())
    assert result == IptcData(
        title='My Photo',
        description='A caption.',
        keywords=['travel', 'city'],
        copyright='(c) 2024',
        creator='John Doe',
    )
