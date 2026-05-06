from __future__ import annotations

import logging
import os
import sys
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_ROOT = Path(__file__).resolve().parent
USER_DATA_DIR = Path(
    os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
) / "DI88VP"
FALLBACK_USER_DATA_DIR = PROJECT_ROOT / ".appdata" / "DI88VP"
_RESOLVED_USER_DATA_DIR: Path | None = None


def get_resource_path(relative_path):
    """
    Get the absolute path to a resource, works for dev and for Nuitka/PyInstaller.
    """
    if getattr(sys, "frozen", False):
        base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, relative_path)

    return os.path.join(str(PROJECT_ROOT), relative_path)


def _resolve_path(path_value: str | os.PathLike[str]) -> Path:
    return Path(path_value).resolve()


def _is_within_path(path_value: Path, root_value: Path) -> bool:
    try:
        path_value.resolve().relative_to(root_value.resolve())
        return True
    except ValueError:
        return False


def get_user_data_dir() -> Path:
    global _RESOLVED_USER_DATA_DIR
    if _RESOLVED_USER_DATA_DIR is not None:
        return _RESOLVED_USER_DATA_DIR
    if not getattr(sys, "frozen", False):
        FALLBACK_USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
        _RESOLVED_USER_DATA_DIR = FALLBACK_USER_DATA_DIR
        return _RESOLVED_USER_DATA_DIR
    try:
        USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
        _RESOLVED_USER_DATA_DIR = USER_DATA_DIR
        return _RESOLVED_USER_DATA_DIR
    except Exception:
        logger.warning(
            "Primary user data dir unavailable, fallback to %s",
            FALLBACK_USER_DATA_DIR,
            exc_info=True,
        )
        FALLBACK_USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
        _RESOLVED_USER_DATA_DIR = FALLBACK_USER_DATA_DIR
        return _RESOLVED_USER_DATA_DIR


def get_user_data_path(relative_path: str) -> Path:
    path = get_user_data_dir() / relative_path
    return ensure_safe_output_path(path, purpose="user data")


def is_runtime_extract_path(path_value: str | os.PathLike[str]) -> bool:
    resolved = _resolve_path(path_value)
    temp_root = Path(tempfile.gettempdir()).resolve()
    if not _is_within_path(resolved, temp_root):
        return False
    return any(part.upper().startswith("DI88VP_") for part in resolved.parts)


def ensure_safe_output_path(path_value: str | os.PathLike[str], purpose: str = "output") -> Path:
    resolved = _resolve_path(path_value)
    if is_runtime_extract_path(resolved):
        logger.warning("Blocked %s inside runtime extract folder: %s", purpose, resolved)
        raise ValueError(f"Blocked {purpose} inside runtime extract folder: {resolved}")
    return resolved
