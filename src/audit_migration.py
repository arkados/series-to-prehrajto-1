#!/usr/bin/env python3
"""Fail closed if migration receipts or unresolved reservations disappear."""
from __future__ import annotations

import gzip
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def episode(row):
    return tuple(int(row[field]) for field in ("series_id", "season", "episode"))


def audit(root=ROOT):
    with gzip.open(root / "config/migration-baseline.json.gz", "rt") as stream:
        baseline = json.load(stream)
    receipts, completed, pending = set(), set(), set()
    for path in sorted((root / "state").glob("uploaded*.json")):
        state = json.loads(path.read_text())
        for row in state.get("uploads", []):
            key = episode(row)
            owner = row.get("upload_account") or "primary"
            receipts.add((owner, str(row["prehrajto_video_id"]), key))
            completed.add((owner, key))
        for row in state.get("pending_uploads", []):
            pending.add((row["upload_account"], row["intent_id"], episode(row)))
    missing = [row for row in baseline["receipts"]
               if (row[0], row[1], tuple(row[2])) not in receipts]
    lost = [row for row in baseline["reservations"]
            if (row[0], row[1], tuple(row[2])) not in pending
            and (row[0], tuple(row[2])) not in completed]
    if missing or lost:
        raise RuntimeError(f"Migration audit failed: {len(missing)} missing receipts, "
                           f"{len(lost)} unaccounted reservations")
    print(f"Migration audit passed: {len(baseline['receipts'])} receipts and "
          f"{len(baseline['reservations'])} reservations protected")


if __name__ == "__main__":
    audit()
