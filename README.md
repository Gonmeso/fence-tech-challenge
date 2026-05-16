# Fence Tech Challenge

This repository contains a solution for the Fence Senior Product Engineer tech
challenge. The system is being designed around two connected projects:

1. a FastAPI backend, which is the primary delivery surface;
2. a smart contract publication layer for covenant outputs.

## Reasoning and Assumptions

- Facility data is delivered as JSON payloads via an API boundary, not as file
  uploads or direct database access.
- Facility data represents the current state of assets and obligations, not a
  historical time series; a calculation request is treated as a snapshot rather
  than a delta.
- Data size is manageable within a single request and does not require
  pagination or streaming.
- Outputs should be available to all parties, so a public smart contract is the
  preferred publication layer.
- No authentication or access controls are required for the API or the smart
  contract in this challenge scope.
- The smart contract stores published covenant outputs only; it does not
  recalculate effective rates or eligibility rules on-chain.
- Financial values use Decimal arithmetic to avoid floating-point error.


## Design Choices

- FastAPI is the main application boundary with a single shared endpoint; the `X-Fence-Facility-Type` header routes requests to facility-specific calculators, keeping the API surface uniform while isolating variable logic per facility.
- Pydantic models enforce typed data contracts at every layer.
- The scaffold is split into `core`, `schemas`, `api/v1`, and `business` so infrastructure, contracts, transport, and domain logic stay separated.
- Each facility has its own calculator class behind a common interface; new facilities are added by implementing a calculator and updating the resolver without touching endpoints.
- Publication is a separate concern from calculation; the smart contract stores one normalized covenant snapshot per facility and leaves computation in Python.
- The codebase is optimized first for explainability and challenge fit, then for production hardening.

## How The Covenant Model Influenced The Architecture

- The requirement to publish verifiable outputs on-chain drove a hard split between calculation (Python, per-facility) and publication (normalized on-chain snapshot), rather than mixing them in a single handler.
- Independent verifiability of the covenant result led to a dedicated GET endpoint that reads back the on-chain snapshot, so all parties can confirm the published data matches the calculated output.
- Single endpoint vs multiple endpoints was a key design choice influenced by the need to support multiple facility types without proliferating routes; the header-based routing allows for a clean separation of logic while keeping the API surface minimal.


## Trade-Offs

- Layered architecture vs simplicity: the layered approach adds some complexity and indirection, but it improves maintainability, testability, and separation of concerns for a production-grade system.
- Single vs multiple endpoints: a single endpoint with a facility type header avoids code duplication, but requires clients to set the header correctly and adds routing logic that must be clearly documented.
- Database vs smart contract for persistence: the smart contract is used as the source of truth for published results, avoiding an additional persistence layer given the challenge scope.
- Header-based routing vs body-based routing: a header keeps the request body focused on the data payload, but is less self-describing than including the facility type in the body.
- Header-based vs auth-token routing: because authentication is out of scope, an explicit header is the simplest way to specify the facility type.
- Foundry vs Hardhat: Foundry was chosen because Hardhat is more JavaScript/TypeScript-heavy, which adds friction in a Python-first project.


## How To Evolve This Toward Production

- The smart contract should be its own repository with a clear versioning and deployment strategy; for this challenge it is included as a submodule, but it should not live alongside the backend code long-term.
- Add a CI/CD pipeline for automated testing, linting, and deployment.
- Better monitoring and observability with structured logging, metrics, and tracing (Sentry, ELK).
- Implement authentication and authorization for the API and smart contract interactions.
- Smart contract security audits and formal verification for critical components.
- Better exception handling at the smart contract level.
- Improved containerization and orchestration for local development and production deployment (multipart, python version).
- Depends on the real nature of the production environment, but improve handling of much bigger data payloads, potentially with streaming or batch processing.
- Vendor specific optimizations (AWS, ECS, Lambda, etc.) depending on the target deployment environment, and cloud usage patterns.
- Maybe saving the historical data of the calculations and the publications, depending on the need of the business, but that would require a more complex data model and potentially a different approach to persistence and smart contract design.


## Setup

Current local stack:

- Python managed with `uv`
- FastAPI backend
- `web3py` for async contract interaction
- Foundry toolchain for contract work (`forge`, `cast`, `anvil`)

Clone with submodules:

```bash
git clone --recurse-submodules git@github.com:Gonmeso/fence-tech-challenge.git
cd fence-tech-challenge
```

If the repository is already cloned, initialize the Foundry dependency:

```bash
git submodule update --init --recursive
```

Quickstart the development environment:

```bash
./scripts/quickstart_dev.sh
```

The quickstart script checks whether `uv`, `forge`, `cast`, and `anvil` are
available. If `uv` or Foundry is missing, it asks before running the official
installer. It then updates submodules, creates the backend virtual environment,
installs dependencies, installs pre-commit hooks, and builds the smart contract.

Smart-contract bootstrap:

```bash
cd smart-contract
forge build
```

Backend bootstrap:

```bash
cd backend
uv sync
```

Install git hooks:

```bash
uv run --project backend pre-commit install
```

## Usage

Run the full repository with Docker:

```bash
cp .env.example .env
docker compose up --build
```

If your Docker installation uses the legacy Compose binary:

```bash
docker-compose up --build
```

The Docker stack starts two services:

- `smart-contract`: starts Anvil, deploys `FacilityCovenantRegistry`, and only
  becomes healthy after contract code exists at the deterministic registry
  address.
- `backend`: starts the FastAPI API and only becomes healthy after it can serve
  `/api/v1/health` and make an `eth_chainId` RPC request to the local chain.

The `.env` values are local-only Anvil defaults. Do not reuse them outside local
development.

Run only the backend locally:

```bash
./scripts/run_local_api.sh
```

Run the full local stack with Anvil, contract deployment, and the API:

```bash
./scripts/run_local_stack.sh
```

The stack script exports these backend settings after deployment:

- `FENCE_WEB3_RPC_URL`
- `FENCE_WEB3_CHAIN_ID`
- `FENCE_COVENANT_REGISTRY_ADDRESS`
- `FENCE_COVENANT_REGISTRY_PRIVATE_KEY`

Run smart-contract tests locally:

```bash
cd smart-contract
forge test
```

Run a local chain and deploy the registry:

```bash
cd smart-contract
anvil
```

```bash
cd smart-contract
PRIVATE_KEY=<anvil_private_key> forge script script/Deploy.s.sol:DeployFacilityCovenantRegistry --rpc-url http://127.0.0.1:8545 --broadcast
```

Run the provided data through the API with curl:

```bash
./scripts/curl_covenant_samples.sh
```

Equivalent individual curl commands:

```bash
curl -sS http://127.0.0.1:8000/api/v1/health

curl -sS \
  -X POST http://127.0.0.1:8000/api/v1/covenants/calculate \
  -H "Content-Type: application/json" \
  -H "X-Fence-Facility-Type: educa" \
  --data-binary @data/facility_a_educa_isa.json

curl -sS \
  -X POST http://127.0.0.1:8000/api/v1/covenants/calculate \
  -H "Content-Type: application/json" \
  -H "X-Fence-Facility-Type: payearly" \
  --data-binary @data/facility_b_payearly_ewa.json

curl -sS \
  -X POST http://127.0.0.1:8000/api/v1/covenants/calculate \
  -H "Content-Type: application/json" \
  -H "X-Fence-Facility-Type: nomina" \
  --data-binary @data/facility_c_nomina.json

curl -sS \
  http://127.0.0.1:8000/api/v1/covenants/result \
  -H "X-Fence-Facility-Type: educa"
```

Run quality checks manually:

```bash
cd backend
uv run ruff format .
uv run ruff check .
uv run ty check .
```

Available endpoints in the current scaffold:

- `GET /`
- `GET /api/v1/health`
- `POST /api/v1/covenants/calculate`
- `GET /api/v1/covenants/result`

## Transcript

The full AI conversation transcript is tracked in [transcription.md](./transcription.md).
