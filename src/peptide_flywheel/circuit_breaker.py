from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import json
from pathlib import Path
import time
from typing import Any, Callable, Dict, Optional, Tuple


class BreakerState(str, Enum):
    CLOSED = "closed"        # Normal operation: remote calls allowed
    OPEN = "open"            # Tripped: remote calls blocked, route to fallback heuristic
    HALF_OPEN = "half_open"  # Probing: allowing canary calls through to test service health


@dataclass
class CircuitBreakerConfig:
    failure_threshold: float = 0.40      # 40% failure rate triggers breaker trip
    sliding_window_size: int = 10        # evaluate failure rate over last N calls
    recovery_timeout_sec: float = 30.0   # wait duration before transitioning from OPEN to HALF_OPEN
    min_calls_for_eval: int = 5          # minimum calls before evaluating trip threshold


class DeadLetterQueue:
    """Persistent Dead-Letter Queue (DLQ) journaling unrecoverable failures to disk."""

    def __init__(self, dlq_dir: Path | str = ".flywheel_dlq"):
        self.dlq_dir = Path(dlq_dir)
        self.dlq_dir.mkdir(parents=True, exist_ok=True)

    def write_entry(
        self,
        agent_name: str,
        error_type: str,
        error_message: str,
        input_payload: Dict[str, Any],
    ) -> Path:
        timestamp_str = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        target_path = self.dlq_dir / f"{timestamp_str}_{agent_name}_{error_type}.json"
        data = {
            "agent_name": agent_name,
            "error_type": error_type,
            "error_message": error_message,
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "input_payload": input_payload,
        }
        target_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return target_path


class AgentCircuitBreaker:
    """3-State SRE Circuit Breaker protecting multi-agent pipelines from cascading outages."""

    def __init__(
        self,
        agent_name: str,
        config: Optional[CircuitBreakerConfig] = None,
        dlq: Optional[DeadLetterQueue] = None,
    ):
        self.agent_name = agent_name
        self.config = config or CircuitBreakerConfig()
        self.dlq = dlq or DeadLetterQueue()
        
        self.state = BreakerState.CLOSED
        self.call_history: deque[bool] = deque(maxlen=self.config.sliding_window_size)
        self.last_state_change: float = time.time()
        self.consecutive_canary_successes: int = 0

    def _check_and_update_state(self) -> None:
        if self.state == BreakerState.OPEN:
            if time.time() - self.last_state_change >= self.config.recovery_timeout_sec:
                self.state = BreakerState.HALF_OPEN
                self.last_state_change = time.time()
                self.consecutive_canary_successes = 0

    def is_allowed(self) -> bool:
        self._check_and_update_state()
        return self.state in (BreakerState.CLOSED, BreakerState.HALF_OPEN)

    def record_success(self) -> None:
        self.call_history.append(True)
        if self.state == BreakerState.HALF_OPEN:
            self.consecutive_canary_successes += 1
            if self.consecutive_canary_successes >= 2:
                self.state = BreakerState.CLOSED
                self.last_state_change = time.time()
                self.call_history.clear()

    def record_failure(
        self,
        error_type: str,
        error_message: str,
        input_payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.call_history.append(False)
        if input_payload is not None:
            self.dlq.write_entry(self.agent_name, error_type, error_message, input_payload)

        if self.state == BreakerState.HALF_OPEN:
            self.state = BreakerState.OPEN
            self.last_state_change = time.time()
            return

        if len(self.call_history) >= self.config.min_calls_for_eval:
            failure_rate = (len(self.call_history) - sum(self.call_history)) / len(self.call_history)
            if failure_rate >= self.config.failure_threshold:
                self.state = BreakerState.OPEN
                self.last_state_change = time.time()

    def execute_with_fallback(
        self,
        primary_fn: Callable[[], Any],
        fallback_fn: Callable[[], Any],
        input_payload: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Any, bool]:
        if not self.is_allowed():
            return fallback_fn(), True

        try:
            result = primary_fn()
            self.record_success()
            return result, False
        except Exception as e:
            self.record_failure(type(e).__name__, str(e), input_payload)
            return fallback_fn(), True
