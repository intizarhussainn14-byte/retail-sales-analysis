"""Resolve current relative metadata and legacy Windows paths after a clone/move."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def project_path(value, marker):
    text = str(value).replace('\\', '/')
    # Only allow the expected project subtree; never follow a former user's drive.
    if text.startswith(marker + '/'):
        relative = text
    elif '/' + marker + '/' in text:
        relative = marker + '/' + text.split('/' + marker + '/', 1)[1]
    else:
        raise ValueError(f'Metadata path is outside expected subtree {marker}: {value}')
    target = (ROOT / relative).resolve()
    if not target.is_relative_to((ROOT / marker).resolve()):
        raise ValueError('Metadata path escapes the expected project subtree')
    return target


def relative_path(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()
