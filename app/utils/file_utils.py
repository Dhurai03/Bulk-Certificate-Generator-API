from pathlib import Path
from typing import Optional
from app.config import settings


def get_certificate_filename(certificate_id: int) -> str:
    """Generate a clean, deterministic filename for a certificate."""
    return f"certificate_{certificate_id}.pdf"


def get_certificate_path(certificate_id: int, base_dir: Optional[Path] = None) -> Path:
    """
    Get the absolute filesystem path for a certificate PDF.
    Ensures safe naming based on integer ID, avoiding user input traversal.
    """
    directory = (base_dir or settings.GENERATED_DIR).resolve()
    filename = get_certificate_filename(certificate_id)
    return directory / filename


def is_safe_path(target_path: Path, base_dir: Optional[Path] = None) -> bool:
    """
    Verify that the target path resides securely inside the allowed base directory.
    Prevents path traversal attacks.
    """
    base = (base_dir or settings.GENERATED_DIR).resolve()
    try:
        resolved_target = target_path.resolve()
        return base in resolved_target.parents or resolved_target.parent == base
    except (ValueError, RuntimeError):
        return False
