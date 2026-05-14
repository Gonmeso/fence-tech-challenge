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
- The codebase is being optimized first for explainability and challenge fit, then
  for production hardening.

## Handling Facility Variability

- Shared concepts such as `external_id`, monetary amounts, reporting dates, and
  covenant outputs should be normalized into common internal structures.
- Facility-specific source fields, eligibility rules, and effective-rate formulas
  should remain isolated in facility modules.
- Exclusion reasons should be first-class outputs so covenant reports explain why
  an asset was omitted.

## How The Covenant Model Influenced The Architecture

- Covenant computation must be independently verifiable, so the architecture
  should preserve calculation inputs, eligibility decisions, and the final result.
- Publication should happen from a deterministic report artifact rather than from
  ad hoc runtime state.
- Reporting must include both the computed rate and the compliance decision,
  because downstream financial processes depend on both.

## Trade-Offs

- Prioritizing the FastAPI backend first reduces delivery risk but may delay full
  on-chain publication depth.
- Explicit facility modules increase code volume, but they keep differing business
  logic legible and testable.
- SQLite keeps local setup simple, but it is not the target production datastore.

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

Run the backend locally:

```bash
cd backend
uv run uvicorn main:app --reload --loop uvloop
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

Near-term usage to document as implementation grows:

- how to load sample facility data,
- how to generate covenant reports,
- how to publish covenant outputs,
- how to run tests.

## Transcript

The full AI conversation transcript is tracked in [transcription.md](./transcription.md).
