import json
import os
import shutil
import socket
import subprocess
import time
from collections.abc import Iterator
from decimal import Decimal
from pathlib import Path
from urllib import request

import pytest
from fastapi.testclient import TestClient

import main as app_module
from api.deps import get_covenant_handler
from business.calculator.resolver import CalculatorResolver
from business.covenant import CovenantHandler
from core.clients.covenant_registry import (
    get_covenant_registry_client,
    reset_covenant_registry_clients,
)
from core.settings import Settings
from main import app

REPO_ROOT = Path(__file__).resolve().parents[3]
SMART_CONTRACT_ROOT = REPO_ROOT / "smart-contract"
DEFAULT_ANVIL_PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"


def load_json(path: Path) -> str:
    """Load JSON and serialize it as a compact string.

    Args:
        path: JSON file to load.

    Returns:
        str: Serialized JSON payload.
    """

    return json.dumps(json.loads(path.read_text()))


def find_free_port() -> int:
    """Find a free local TCP port.

    Returns:
        int: Available TCP port.
    """

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_for_rpc(rpc_url: str) -> None:
    """Wait for the JSON-RPC server to accept requests.

    Args:
        rpc_url: JSON-RPC endpoint.

    Raises:
        RuntimeError: If the server does not become ready in time.
    """

    payload = json.dumps(
        {"jsonrpc": "2.0", "method": "eth_chainId", "params": [], "id": 1}
    ).encode()
    for _ in range(60):
        try:
            req = request.Request(
                rpc_url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with request.urlopen(req, timeout=1):
                return
        except Exception:
            time.sleep(0.25)

    raise RuntimeError(f"Anvil did not become ready at {rpc_url}")


@pytest.fixture(scope="module")
def anvil_rpc_url() -> Iterator[str]:
    if not shutil.which("anvil") or not shutil.which("forge"):
        pytest.skip("Foundry tools are required for e2e contract tests")

    port = find_free_port()
    rpc_url = f"http://127.0.0.1:{port}"
    process = subprocess.Popen(
        ["anvil", "--host", "127.0.0.1", "--port", str(port), "--chain-id", "31337"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        wait_for_rpc(rpc_url)
        yield rpc_url
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


@pytest.fixture(scope="module")
def registry_address(anvil_rpc_url: str) -> str:
    env = os.environ.copy()
    env["PRIVATE_KEY"] = DEFAULT_ANVIL_PRIVATE_KEY
    subprocess.run(
        [
            "forge",
            "script",
            "script/Deploy.s.sol:DeployFacilityCovenantRegistry",
            "--rpc-url",
            anvil_rpc_url,
            "--broadcast",
        ],
        cwd=SMART_CONTRACT_ROOT,
        env=env,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    broadcast_path = (
        SMART_CONTRACT_ROOT / "broadcast" / "Deploy.s.sol" / "31337" / "run-latest.json"
    )
    broadcast = json.loads(broadcast_path.read_text())
    for transaction in broadcast["transactions"]:
        if transaction.get("contractAddress"):
            return str(transaction["contractAddress"])

    raise RuntimeError("Deploy broadcast did not include a contract address")


@pytest.fixture
def on_chain_api_client(
    anvil_rpc_url: str,
    registry_address: str,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[TestClient]:
    settings = Settings(
        educa_covenant_threshold=Decimal("22.0"),
        payearly_covenant_threshold=Decimal("3.0"),
        nomina_covenant_threshold=Decimal("5.0"),
        web3_rpc_url=anvil_rpc_url,
        web3_chain_id=31337,
        covenant_registry_address=registry_address,
        covenant_registry_private_key=DEFAULT_ANVIL_PRIVATE_KEY,
    )

    def build_handler() -> CovenantHandler:
        return CovenantHandler(
            resolver=CalculatorResolver(settings),
            registry_client=get_covenant_registry_client(settings),
        )

    reset_covenant_registry_clients()
    monkeypatch.setattr(app_module.settings, "web3_rpc_url", anvil_rpc_url)
    app.dependency_overrides[get_covenant_handler] = build_handler
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
    reset_covenant_registry_clients()


def test_api_publishes_and_reads_covenant_result_on_chain(
    on_chain_api_client: TestClient,
) -> None:
    response = on_chain_api_client.post(
        "/api/v1/covenants/calculate",
        content=load_json(REPO_ROOT / "data" / "facility_a_educa_isa.json"),
        headers={"X-Fence-Facility-Type": "educa"},
    )

    assert response.status_code == 200
    published = response.json()
    assert published["computed_effective_rate"] == "18.33"
    assert published["publication"]["transaction_hash"].startswith("0x")

    reset_covenant_registry_clients()

    read_response = on_chain_api_client.get(
        "/api/v1/covenants/result",
        headers={"X-Fence-Facility-Type": "educa"},
    )

    assert read_response.status_code == 200
    on_chain = read_response.json()
    assert on_chain["facility"] == "educa"
    assert on_chain["effective_rate_bps"] == 1833
    assert on_chain["computed_effective_rate"] == "18.33"
    assert on_chain["summary"] == published["summary"]
    assert on_chain["included_assets"] == published["included_assets"]
    assert on_chain["excluded_assets"] == published["excluded_assets"]
