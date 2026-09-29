"""
Deployer state: pending and processed orders.

Stored as JSON. No database. Atomic writes to avoid corruption if the
process dies mid-write.
"""

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


_lock = threading.Lock()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    tmp.replace(path)


class OrderState:
    def __init__(self, state_dir: Path):
        self.state_dir = Path(state_dir)
        self.pending_path = self.state_dir / "pending.json"
        self.processed_path = self.state_dir / "processed.json"

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------

    def add_order(self, order: dict) -> None:
        with _lock:
            pending = _read_json(self.pending_path)
            order["created_at"] = _now_iso()
            pending[order["order_id"]] = order
            _write_json(self.pending_path, pending)

    def update_order(self, order_id: str, **fields) -> None:
        with _lock:
            pending = _read_json(self.pending_path)
            if order_id not in pending:
                return
            pending[order_id].update(fields)
            pending[order_id]["updated_at"] = _now_iso()
            _write_json(self.pending_path, pending)

    def mark_processed(self, order_id: str, **fields) -> None:
        with _lock:
            pending = _read_json(self.pending_path)
            processed = _read_json(self.processed_path)

            order = pending.pop(order_id, None)
            if order is None:
                order = processed.get(order_id, {"order_id": order_id})

            order.update(fields)
            order["processed_at"] = _now_iso()
            processed[order_id] = order

            _write_json(self.pending_path, pending)
            _write_json(self.processed_path, processed)

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------

    def get_order(self, order_id: str) -> Optional[dict]:
        with _lock:
            pending = _read_json(self.pending_path)
            if order_id in pending:
                return pending[order_id]
            processed = _read_json(self.processed_path)
            return processed.get(order_id)

    def list_pending(self) -> list[dict]:
        with _lock:
            return list(_read_json(self.pending_path).values())

    def list_processed(self) -> list[dict]:
        with _lock:
            return list(_read_json(self.processed_path).values())

