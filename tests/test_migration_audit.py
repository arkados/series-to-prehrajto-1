import gzip
import json

import pytest

from src.audit_migration import audit


def snapshot(tmp_path, uploads=(), pending=()):
    (tmp_path / "config").mkdir()
    (tmp_path / "state").mkdir()
    with gzip.open(tmp_path / "config/migration-baseline.json.gz", "wt") as out:
        json.dump({"receipts": [["primary", "123", [1, 2, 3]]],
                   "reservations": [["serialy", "intent", [4, 5, 6]]]}, out)
    (tmp_path / "state/uploaded.json").write_text(json.dumps(
        {"uploads": list(uploads), "pending_uploads": list(pending)}))
    return tmp_path


RECEIPT = dict(series_id=1, season=2, episode=3, prehrajto_video_id=123)
PENDING = dict(series_id=4, season=5, episode=6, upload_account="serialy", intent_id="intent")


def test_receipt_and_pending_are_preserved(tmp_path):
    audit(snapshot(tmp_path, [RECEIPT], [PENDING]))


def test_pending_may_only_close_on_its_own_account(tmp_path):
    completed = {**PENDING, "prehrajto_video_id": 456}
    audit(snapshot(tmp_path, [RECEIPT, completed]))
    completed["upload_account"] = "primary"
    (tmp_path / "state/uploaded.json").write_text(json.dumps({"uploads": [RECEIPT, completed]}))
    with pytest.raises(RuntimeError, match="1 unaccounted"):
        audit(tmp_path)


def test_receipt_identity_cannot_be_replaced(tmp_path):
    with pytest.raises(RuntimeError, match="1 missing receipts"):
        audit(snapshot(tmp_path, [{**RECEIPT, "prehrajto_video_id": 999}], [PENDING]))
