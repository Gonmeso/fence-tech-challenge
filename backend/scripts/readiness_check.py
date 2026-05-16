import json
from urllib import request


def get_json(url: str) -> dict[str, object]:
    """Get JSON and return the decoded response.

    Args:
        url: URL to call.

    Returns:
        dict[str, object]: Decoded JSON response.
    """

    with request.urlopen(url, timeout=2) as response:
        return json.loads(response.read().decode())


def main() -> None:
    """Check the API process.

    Returns:
        None: Exits with a non-zero status if any check fails.
    """

    health = get_json("http://127.0.0.1:8000/api/v1/health")
    if health.get("status") != "ok":
        raise SystemExit("API healthcheck did not return ok")


if __name__ == "__main__":
    main()
