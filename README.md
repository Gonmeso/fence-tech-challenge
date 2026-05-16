# Fence Tech Challenge

This repository contains a solution for the Fence Senior Product Engineer tech
challenge. The system is being designed around two connected projects:

1. a FastAPI backend, which is the primary delivery surface;
2. a smart contract publication layer for covenant outputs.

## Status

This README is intentionally structured to match the challenge deliverables.
Reasoning and narrative details can be refined later, but the sections below
should stay current as implementation evolves.

## Assumptions

- Facility data arrives in facility-specific formats and requires normalization
  before calculation.
- A facility-specific covenant definition is stable enough to encode as a versioned
  calculation rule.
- Covenant calculations must be reproducible from stored input snapshots or an
  equivalent audit trail.
- The backend is the source of orchestration, even when covenant outputs are later
  published to a smart contract.
- The smart contract stores published covenant outputs only; it does not
  recalculate effective rates or eligibility rules on-chain.
- Async SQLite is sufficient for local development only.

## Design Choices

- FastAPI is the main application boundary.
- Pydantic models are used for validation and typed data contracts.
- The backend scaffold is split into `core`, `schemas`, `api/v1`, and `business`
  so infrastructure, contracts, transport, and domain logic stay separated from
  the beginning.
- Facility variability is handled through explicit adapters and calculation
  strategies instead of one oversized shared model.
- Publication is treated as a separate concern from calculation so the backend can
  support either smart contract publication or a database-backed fallback.
- The smart contract stores one latest covenant snapshot per supported facility
  and leaves computation in Python.
- The codebase is being optimized first for explainability and challenge fit, then
  for production hardening.

## Handling Facility Variability

- Shared concepts such as `external_id`, monetary amounts, reporting dates, and
  covenant outputs should be normalized into common internal structures.
- Facility-specific source fields, eligibility rules, and effective-rate formulas
  should remain isolated in facility modules.
- Exclusion reasons should be first-class outputs so covenant reports explain why
  an asset was omitted.
- The current smart-contract publication layer intentionally stores excluded
  asset IDs without exclusion reasons to keep the first on-chain shape smaller.

## How The Covenant Model Influenced The Architecture

- Covenant computation must be independently verifiable, so the architecture
  should preserve calculation inputs, eligibility decisions, and the final result.
- Publication should happen from a deterministic report artifact rather than from
  ad hoc runtime state.
- Reporting must include both the computed rate and the compliance decision,
  because downstream financial processes depend on both.
- On-chain publication is modeled as a storage concern so counterparties can read
  the latest facility report without trusting transient backend state.

## Trade-Offs

- Prioritizing the FastAPI backend first reduces delivery risk but may delay full
  on-chain publication depth.
- Explicit facility modules increase code volume, but they keep differing business
  logic legible and testable.
- SQLite keeps local setup simple, but it is not the target production datastore.
- Omitting exclusion reasons on-chain reduces storage complexity now, but detailed
  exclusion rationale remains an off-chain concern until a later revision.

## How To Evolve This Toward Production

- Replace SQLite with a production-grade relational database.
- Add versioned covenant definitions and report schemas.
- Persist raw imports, normalized assets, and calculation artifacts separately for
  stronger auditability.
- Add authentication, authorization, and provenance controls around publication.
- Harden smart contract deployment, event indexing, and reconciliation workflows.
- Expand automated testing with fixture-driven facility coverage and end-to-end
  publication scenarios.

## Setup

Current local stack:

- Python managed with `uv`
- FastAPI backend
- Async SQLite for local persistence
- `web3py` for async contract interaction
- Foundry toolchain for contract work (`forge`, `cast`, `anvil`)

Clone with submodules:

```bash
git clone --recurse-submodules <repo_url>
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
