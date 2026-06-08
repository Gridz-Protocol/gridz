# Gridz on-chain deployments

gridz.bio production runs on **Base mainnet** (chain id `8453`). Subject names stay `*.gridz.eth`; the app reads `GridzResolver` directly on Base via RPC.

## Base mainnet (production — gridz.bio)

| Contract / config | Address / value |
|-------------------|-----------------|
| Chain ID | `8453` |
| GridzResolver (UUPS proxy) | `0x73c5e3944B780D4927c403d351A4F94875DC57B3` |
| EAS | `0x4200000000000000000000000000000000000021` |
| EAS SchemaRegistry | `0x4200000000000000000000000000000000000020` |
| `gridz.cell.v1` schema UID | `0x394d8e67b1470cbdb7fa6c7d15d15d295ca81d822b55267939751a8a686abb87` |
| Registrar (server publish) | `0xEBE4ceb499Ad95DC1e5662E3a223Ec8cc0a555d9` |
| Public RPC | `https://base.publicnode.com` |
| EAS explorer | https://base.easscan.org |

Schema string (same on all EAS networks; UID differs per chain):

```
bytes32 gridId, string key, string valueHashHex, uint64 expiresAt, bytes32 widgetTypeHash
```

## Ethereum mainnet (legacy)

Earlier gridz.bio publishes used L1 before the Base migration. Legacy resolver:

| Contract | Address |
|----------|---------|
| GridzResolver (UUPS proxy) | `0x190a9c0D29bCca03efeA85dcDF8F4b283e32dc52` |
| EAS | `0xA1207F3BBa224E2c9c3c6D5aF63D0eb1582Ce587` |

## Sepolia (testnet)

| Contract | Address |
|----------|---------|
| EAS | `0xC2679fBD37d54388Ce493F1DB75320D236e1815e` |
| EAS SchemaRegistry | `0x0a7E2Ff54e576B096E04665717A6C3B2a33b9e4a` |

Deploy a fresh resolver with `forge script script/Deploy.s.sol` and register the cell schema with `node scripts/register-cell-schema.mjs`.

## Upgrade

```bash
PROXY_ADDRESS=<proxy> forge script script/Upgrade.s.sol --rpc-url <rpc> --broadcast --private-key <key>
```

Caller must hold `UPGRADER_ROLE` on the proxy.
