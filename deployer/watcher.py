"""
Deployer watcher.

Loop every N seconds:
    1. Read state.pending
    2. For each order, read the USDC balance of the predicted address
    3. If balance >= fee_wei, deploy the splitter

Verification is a single eth_call per order (balanceOf).
No log scanning, no block dependency, no 413 errors.

Retries deployment up to `max_attempts` times.
"""

import logging
import threading
from typing import Callable

from web3 import Web3

from deployer.executor import execute_order
from deployer.state import OrderState
from deployer.verifier import check_balance


log = logging.getLogger(__name__)


class Watcher:
    def __init__(
        self,
        w3: Web3,
        state: OrderState,
        factory_address: str,
        usdc_address: str,
        interval_seconds: int = 60,
        max_attempts: int = 3,
        lookback_blocks: int = 100,  # ignored, kept for compatibility
        on_deployed: Callable[[str, str], None] | None = None,
        private_key: str | None = None,
    ):
        self.w3 = w3
        self.state = state
        self.factory_address = factory_address
        self.usdc_address = usdc_address
        self.interval_seconds = interval_seconds
        self.max_attempts = max_attempts
        self.on_deployed = on_deployed
        self.private_key = private_key

        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        log.info("watcher started (interval=%ss)", self.interval_seconds)

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5)
            log.info("watcher stopped")

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                self.tick()
            except Exception as e:
                log.exception("error in tick: %s", e)
            self._stop.wait(self.interval_seconds)

    def tick(self) -> None:
        pending = self.state.list_pending()
        if not pending:
            return

        log.debug("tick: %d pending orders", len(pending))

        for order in pending:
            if self._stop.is_set():
                return

            order_id = order["order_id"]
            if order["status"] in ("deploying", "failed"):
                continue

            self._process_order(order_id)

    def _process_order(self, order_id: str) -> None:
        order = self.state.get_order(order_id)
        if order is None:
            return

        predicted = order["predicted_splitter_address"]
        expected_wei = order["fee_wei"]

        # Read current balance of the splitter in USDC
        try:
            paid, balance = check_balance(
                self.w3,
                self.usdc_address,
                predicted,
                expected_wei,
            )
        except Exception as e:
            log.warning("error reading balance of %s: %s", predicted, e)
            return

        if not paid:
            log.debug(
                "order %s: balance=%d, expected=%d, no payment yet",
                order_id, balance, expected_wei,
            )
            return

        # --- Payment detected ---
        attempts = order.get("deploy_attempts", 0) + 1
        self.state.update_order(
            order_id,
            status="deploying",
            deploy_attempts=attempts,
            received_wei=balance,
        )

        log.info(
            "order %s: payment detected (balance=%d), attempting deploy (%d/%d)",
            order_id, balance, attempts, self.max_attempts,
        )

        tx_deploy, splitter, err = execute_order(
            self.w3,
            self.factory_address,
            self.usdc_address,
            order,
            private_key=self.private_key,
        )

        if err is None and splitter is not None:
            self.state.mark_processed(
                order_id,
                status="deployed",
                splitter_address=splitter,
                deploy_tx_hash=tx_deploy,
            )
            log.info("order %s deployed at %s", order_id, splitter)

            if self.on_deployed is not None:
                try:
                    self.on_deployed(order_id, splitter)
                except Exception:
                    log.exception("on_deployed callback failed")
            return

        # --- Deploy failed ---
        if attempts >= self.max_attempts:
            self.state.mark_processed(
                order_id,
                status="failed",
                error=err or "unknown",
                deploy_tx_hash=tx_deploy,
            )
            log.error(
                "order %s marked as failed after %d attempts: %s",
                order_id, attempts, err,
            )
        else:
            self.state.update_order(
                order_id,
                status="pending",
                error=err or "unknown",
            )
            log.warning(
                "order %s: attempt %d/%d failed (%s), retrying",
                order_id, attempts, self.max_attempts, err,
            )

