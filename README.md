# ReplicaQuorum

One successful run is a result. A result becomes reproducible only when separate reviewers can follow the same frozen method against the same frozen artifact and report what happened.

ReplicaQuorum turns that distinction into reusable contract state. A study creator pins an artifact page, a method page, an authorized reviewer set, a quorum threshold, and a closing time. GenLayer validators fetch the artifact and method at registration and preserve their SHA-256 receipts. Later reports are rejected if either frozen source has changed.

## Review protocol

Each authorized reviewer gets one report. The report must come from a hostname that no earlier report used and must contain exact quotes identifying:

1. the tested artifact,
2. the followed method,
3. the execution environment,
4. the observed result.

Comparative validator consensus checks the whole report against the frozen study and validates one bounded outcome: `SUPPORTS`, `FAILS`, or `INCONCLUSIVE`. The contract never stores a leader-only score or freeform rationale.

Once enough reports arrive, anyone can close the study. A single `FAILS` report makes the result `CONTESTED`; enough supporting reports produce `REPRODUCED`; every other closed combination is `INCONCLUSIVE`. If quorum never forms, permissionless finalization becomes available after the recorded deadline.

## Authority model

The study creator chooses the reviewer wallets, so ReplicaQuorum does not claim that they are neutral institutions. Distinct wallet addresses and report hosts reduce accidental duplication but do not defeat coordinated Sybils. Applications integrating this primitive must publish their reviewer-selection policy. The included pages and live wallets are operator-created test fixtures, not independent laboratories.

## Contract surface

- `open_study`: freezes sources, reviewers, threshold, and deadline.
- `submit_report`: binds one authorized reviewer to one fetched report.
- `finalize_study`: permissionlessly derives the terminal verdict.
- `cancel_empty_study`: lets the creator remove an unused study before reports exist.
- `get_study` and `get_report`: expose the complete attributable record.

## Local verification

```bash
python -m pytest tests -q -p no:cacheprovider
genvm-lint lint contracts/replica_quorum.py --json
npm run deploy
npm run smoke
npm run verify
```

Deployment targets GenLayer Studio Next, chain `61997`. Exact live evidence is added to `deployment.json` after the network lifecycle succeeds.

## Studio Next record

- Contract: [`0xEc23EdA122F457D2B5D689b36F074D5862E4EeD4`](https://explorer-studio-dev.genlayer.com/address/0xEc23EdA122F457D2B5D689b36F074D5862E4EeD4)
- Deployment transaction: [`0x9e69efad...3b8977a4`](https://explorer-studio-dev.genlayer.com/tx/0x9e69efad02dd560a51e4b18cc32f638ce25c2dcceb22f97a1af70b333b8977a4)
- Demonstration study: `replica-demo-musn7zyo`
- Deployed source SHA-256: `6da241d1a9567516f3bc9dbf85c55eb42e8774a6fe3ff23f4393931bdcb1446e`

The live run used two fresh reviewer wallets and two report hostnames. Both report transactions reached `FINALIZED` with `MAJORITY_AGREE`; the permissionless close produced `REPRODUCED` with two supports and no failures. The repository labels both reports as operator-controlled fixtures, so the demonstration proves contract behavior, not institutional independence.

## Files

- `contracts/replica_quorum.py`: source freezing, reviewer authorization, consensus, and aggregation
- `tests/`: lifecycle, source mutation, forged quote, authorization, host separation, and permissionless-finalization checks
- `docs/`: explicit demonstration fixtures plus the mechanism comparison
- `scripts/`: deployment, multi-wallet smoke test, and source verification
