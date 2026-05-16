import json
from urllib import request


def check_rpc_connection(rpc_url: str, *, timeout: float = 2) -> int:
    """Check RPC reachability with `eth_chainId`.

    Args:
        rpc_url: JSON-RPC endpoint to check.
        timeout: Request timeout in seconds.

    Raises:
        RuntimeError: If the RPC response does not include a chain id.
        URLError: If the RPC endpoint cannot be reached.

    Returns:
        int: Chain id returned by the RPC endpoint.
    """

    payload = json.dumps(
        {"jsonrpc": "2.0", "method": "eth_chainId", "params": [], "id": 1}
    ).encode()
    req = request.Request(
        rpc_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=timeout) as response:
        body = json.loads(response.read().decode())

    result = body.get("result")
    if not isinstance(result, str):
        raise RuntimeError("RPC eth_chainId did not return a result")

    return int(result, 16)
