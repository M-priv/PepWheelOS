from __future__ import annotations

import tempfile
import time
from pathlib import Path

from peptide_flywheel.circuit_breaker import (
    AgentCircuitBreaker,
    BreakerState,
    CircuitBreakerConfig,
    DeadLetterQueue,
)


def test_circuit_breaker_normal_execution():
    with tempfile.TemporaryDirectory() as tmpdir:
        dlq = DeadLetterQueue(dlq_dir=tmpdir)
        breaker = AgentCircuitBreaker(agent_name="test_agent", dlq=dlq)

        result, used_fallback = breaker.execute_with_fallback(
            primary_fn=lambda: "success_result",
            fallback_fn=lambda: "fallback_result",
        )

        assert result == "success_result"
        assert used_fallback is False
        assert breaker.state == BreakerState.CLOSED


def test_circuit_breaker_trips_to_open_on_failures():
    with tempfile.TemporaryDirectory() as tmpdir:
        dlq = DeadLetterQueue(dlq_dir=tmpdir)
        config = CircuitBreakerConfig(
            failure_threshold=0.40,
            sliding_window_size=5,
            min_calls_for_eval=5,
            recovery_timeout_sec=0.2,  # fast recovery for test
        )
        breaker = AgentCircuitBreaker(agent_name="test_agent", config=config, dlq=dlq)

        def failing_call():
            raise RuntimeError("API Timeout / Outage")

        def fallback_call():
            return "safe_heuristic_score"

        # Execute 5 failing calls to trip breaker
        for _ in range(5):
            res, was_fb = breaker.execute_with_fallback(
                primary_fn=failing_call,
                fallback_fn=fallback_call,
                input_payload={"candidate_id": "CAND-001"},
            )
            assert res == "safe_heuristic_score"
            assert was_fb is True

        assert breaker.state == BreakerState.OPEN

        # Verify DLQ wrote entries to disk
        dlq_files = list(Path(tmpdir).glob("*.json"))
        assert len(dlq_files) == 5

        # Subsequent call immediately falls back without executing primary
        primary_executed = False
        def tracked_primary():
            nonlocal primary_executed
            primary_executed = True
            return "ok"

        res, was_fb = breaker.execute_with_fallback(
            primary_fn=tracked_primary,
            fallback_fn=fallback_call,
        )
        assert primary_executed is False
        assert res == "safe_heuristic_score"
        assert was_fb is True

        # Wait for recovery timeout -> transitions to HALF_OPEN -> resets to CLOSED on canary successes
        time.sleep(0.25)
        assert breaker.is_allowed() is True
        assert breaker.state == BreakerState.HALF_OPEN

        # 2 canary successes reset to CLOSED
        breaker.record_success()
        breaker.record_success()
        assert breaker.state == BreakerState.CLOSED
