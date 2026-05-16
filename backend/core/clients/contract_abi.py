import json
from pathlib import Path
from typing import Any


def default_registry_abi_path() -> Path:
    """Return the default backend-local registry ABI path.

    Returns:
        Path: Filesystem path to the checked-in registry ABI.
    """

    return Path(__file__).resolve().parents[2] / "contracts" / "FacilityCovenantRegistry.abi.json"


def load_registry_abi(path: Path | None = None) -> list[dict[str, Any]]:
    """Load the FacilityCovenantRegistry ABI.

    Args:
        path: Optional ABI path for tests or standalone scripts.

    Raises:
        ValueError: If the ABI file does not contain a JSON array.

    Returns:
        list[dict[str, Any]]: Contract ABI entries.
    """

    abi_path = path or default_registry_abi_path()
    abi = json.loads(abi_path.read_text())
    if not isinstance(abi, list):
        raise ValueError("FacilityCovenantRegistry ABI must be a JSON array")
    return abi
