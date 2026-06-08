import json
import subprocess
from unittest.mock import patch

from .exiftool import run_exiftool


def _completed(stdout, returncode=0):
    return subprocess.CompletedProcess(
        args=['exiftool'], returncode=returncode, stdout=stdout, stderr=b''
    )


def test_returns_first_object_without_source_file():
    payload = json.dumps([{'SourceFile': '-', 'Make': 'NIKON', 'FNumber': 2.8}])
    with patch('subprocess.run', return_value=_completed(payload.encode())) as run:
        result = run_exiftool(b'image-bytes')
    assert result == {'Make': 'NIKON', 'FNumber': 2.8}
    args, kwargs = run.call_args
    assert args[0][0] == 'exiftool'
    assert kwargs['input'] == b'image-bytes'


def test_returns_empty_dict_when_binary_missing():
    with patch('subprocess.run', side_effect=FileNotFoundError):
        assert run_exiftool(b'data') == {}


def test_returns_empty_dict_on_nonzero_exit():
    with patch('subprocess.run', return_value=_completed(b'', returncode=1)):
        assert run_exiftool(b'data') == {}


def test_returns_empty_dict_on_invalid_json():
    with patch('subprocess.run', return_value=_completed(b'not json')):
        assert run_exiftool(b'data') == {}


def test_returns_empty_dict_on_empty_list():
    with patch('subprocess.run', return_value=_completed(b'[]')):
        assert run_exiftool(b'data') == {}


def test_returns_empty_dict_on_timeout():
    with patch(
        'subprocess.run',
        side_effect=subprocess.TimeoutExpired(cmd='exiftool', timeout=30),
    ):
        assert run_exiftool(b'data') == {}
