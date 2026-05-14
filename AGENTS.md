@RTK.md

# Agent Instructions

## Scope

This repository is for the Fence Senior Product Engineer tech challenge described in
`Tech Challenge Instructions - Senior Product Engineer.txt`.

The work should optimize for:

1. Clear reasoning and explainable decisions over breadth.
2. A facility-aware architecture that supports variable asset schemas, eligibility
   rules, and covenant calculations.
3. FastAPI backend delivery first.
4. Smart contract support second, with a pragmatic fallback to persistence in the
   backend if contract work would block core challenge delivery.

## Project Priorities

Treat the codebase as two related projects:

1. `backend`: primary focus. Build the ingestion, normalization, calculation,
   reporting, and publication workflow here first.
2. `smart-contract`: secondary focus. Use it to publish covenant outputs once the
   backend flow is coherent.

When trade-offs are necessary, prefer completing a strong FastAPI solution before
expanding contract scope.

## Required Stack

### Python / Backend

- FastAPI
- Pydantic
- `uv`
- Async SQLite for local development
- `web3py` with async usage for smart contract interaction in development and
  production-oriented code paths

### Smart Contract

- Foundry
- `forge`
- `cast`
- `anvil`

## Challenge-Specific Architecture Guidance

The solution should reflect the challenge constraints:

- Each facility can have its own source schema.
- Some fields are common, but facility-specific fields must remain supported.
- Eligibility rules vary by facility.
- Effective interest rate logic varies by facility.
- Covenant outputs must be independently verifiable by both counterparties.

Prefer an architecture with explicit separation between:

1. raw ingestion models,
2. facility-specific normalization/adapters,
3. covenant calculation rules,
4. covenant reporting,
5. publication/persistence layers.

Avoid hard-coding a single shared asset model that cannot represent facility
differences cleanly.

## Transcript Requirement

The challenge explicitly requires the full AI conversation transcript. This is not
optional.

For every interaction:

1. Append the human prompt to `transcription.md`.
2. Append the agent response to `transcription.md`.
3. Keep the file human-readable and machine-readable.
4. Do this continuously, not only at the end.
5. Include the current interaction, starting from the first user request related to
   this repository task.
6. Classify each interaction by prompt type.
7. Record whether the interaction completed normally or was cancelled/aborted.

Use this format in `transcription.md`:

```md
# AI Transcript

## Entry 001
- Timestamp: 2026-05-14 18:41:47 CEST
- Type: development
- Status: completed
- Human
  <exact or near-exact user message>
- Agent
  <slightly verbose but faithful agent response summarizing intent, work, and outcome>
```

Prompt `Type` must be one of:

- `development`: generating code, scaffolding, implementation, or setup work.
- `refactor`: changing existing functionality, structure, or behavior.
- `clean-up`: documentation cleanup, naming cleanup, formatting, deletion of stale
  pieces, or simplification work.
- `misc`: anything that does not fit clearly into the categories above.

`Status` should normally be `completed`. If a user message, tool run, or agent turn
was interrupted, cancelled, or aborted, record it explicitly as `cancelled` or
`aborted` and preserve the partial context rather than omitting it from the log.

Guidelines:

- Preserve meaning exactly when possible.
- The agent section should be more descriptive than a one-line acknowledgment. It
  should summarize what the agent understood, what it inspected or changed, and
  any relevant outcome or limitation.
- If the agent response is long, summarize faithfully rather than dumping noisy
  tool output.
- Keep entries chronological.
- Do not remove earlier entries.
- Include cancelled interactions as explicit entries; do not silently skip them.

## README Maintenance

Keep `README.md` aligned with the challenge deliverables.

Update it whenever the implementation changes the following:

- assumptions,
- design choices,
- how facility variability is handled,
- how the covenant model shaped the architecture,
- trade-offs,
- how the solution should evolve toward production,
- setup and usage.

The user may later refine the reasoning text, but the structure and technical facts
should remain current.

## Working Style

- Prefer concrete implementation over speculative abstraction.
- Keep facility logic explicit and testable.
- Make assumptions visible in code and README.
- When a requirement is ambiguous, choose the smallest reasonable assumption and
  document it.
- Favor asynchronous backend boundaries where I/O is involved.
- Keep local development simple; Async SQLite is the default local persistence
  choice unless the user directs otherwise.
