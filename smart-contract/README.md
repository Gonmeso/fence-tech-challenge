## Smart Contract

This Foundry project stores and publishes backend-computed covenant outputs for
the supported facilities: `educa`, `payearly`, and `nomina`.

The contract does not recalculate rates or eligibility on-chain. The backend is
the source of truth for computation, and the contract stores the latest published
snapshot per facility.

## Dependency setup

`forge-std` is tracked as a git submodule under `lib/forge-std`.

Clone the repository with submodules:

```shell
git clone --recurse-submodules <repo_url>
cd fence-tech-challenge
```

If the repository is already cloned:

```shell
git submodule update --init --recursive
```

### Stored report fields

- facility name
- effective rate in basis points
- covenant status
- summary counts
- included external IDs
- excluded assets with external IDs and exclusion reasons
- update timestamp
- updating wallet

### Access control

- `openWrite = true` by default for local testing
- owner can disable open mode
- when open mode is disabled, only whitelisted writers can publish

### Commands

Build:

```shell
forge build
```

Test:

```shell
forge test
```

Format:

```shell
forge fmt
```

Run Anvil:

```shell
anvil
```

Deploy:

```shell
forge script script/Deploy.s.sol:DeployFacilityCovenantRegistry --rpc-url <rpc_url> --broadcast
```

Read a saved facility value with `cast`:

```shell
bash smart-contract/script/check_saved_value.sh <contract_address> educa <rpc_url>
bash smart-contract/script/check_saved_value.sh <contract_address> payearly <rpc_url>
bash smart-contract/script/check_saved_value.sh <contract_address> nomia <rpc_url>
```

The helper accepts `educa`, `payearly`, and `nomia` as input values. `nomia`
is normalized to the on-chain facility key `nomina` before calling the
contract.
