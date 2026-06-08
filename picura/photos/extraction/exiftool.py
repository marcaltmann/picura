import json
import subprocess

# Read from stdin ('-'), emit JSON ('-j') with raw numeric values ('-n').
# Drop the filesystem ('File') and tool ('ExifTool') tag groups so the result
# is image metadata only.
_COMMAND = ['exiftool', '-j', '-n', '--File:all', '--ExifTool:all', '-']
_TIMEOUT = 30


def run_exiftool(data: bytes) -> dict:
    # Exceptions are caught one type per clause on purpose: ruff format
    # currently rewrites multi-type ``except (A, B):`` tuples into invalid
    # syntax, so the parenthesised form cannot be used here.
    try:
        proc = subprocess.run(
            _COMMAND, input=data, capture_output=True, timeout=_TIMEOUT
        )
    except OSError:
        return {}
    except subprocess.SubprocessError:
        return {}
    if proc.returncode != 0:
        return {}
    try:
        parsed = json.loads(proc.stdout)
    except ValueError:
        return {}
    if not parsed:
        return {}
    result = parsed[0]
    result.pop('SourceFile', None)
    return result
