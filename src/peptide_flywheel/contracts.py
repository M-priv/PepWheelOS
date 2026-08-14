from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import functools
import inspect
from typing import Any, Callable, Dict, List, Optional, Tuple


class ContractSeverity(str, Enum):
    FATAL = "fatal"
    WARNING = "warning"
    INFORMATIONAL = "informational"


class ContractViolation(Exception):
    """Raised when an Assume-Guarantee contract or physical invariant is violated."""

    def __init__(
        self,
        message: str,
        contract_name: str,
        violation_type: str,  # "assumption" or "guarantee"
        severity: ContractSeverity = ContractSeverity.FATAL,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(f"[{severity.value.upper()}] Contract '{contract_name}' {violation_type} failed: {message}")
        self.contract_name = contract_name
        self.violation_type = violation_type
        self.severity = severity
        self.details = details or {}


@dataclass(frozen=True)
class Contract:
    """Assume-Guarantee Contract Definition."""
    name: str
    description: str = ""
    assumptions: List[Callable[[Dict[str, Any]], Tuple[bool, str]]] = field(default_factory=list)
    guarantees: List[Callable[[Any, Dict[str, Any]], Tuple[bool, str]]] = field(default_factory=list)
    severity: ContractSeverity = ContractSeverity.FATAL


def enforce_contract(contract: Contract):
    """Decorator to enforce Assume-Guarantee contracts on functions or agent runners.
    
    Checks:
    1. Assumptions (Preconditions): Evaluated on function arguments before execution.
    2. Guarantees (Postconditions): Evaluated on function return value and input context.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Extract call context by binding parameters
            sig = inspect.signature(func)
            bound_args = sig.bind_partial(*args, **kwargs)
            bound_args.apply_defaults()
            context = dict(bound_args.arguments)

            # 1. Precondition Assumption Checks
            for assumption_fn in contract.assumptions:
                passed, reason = assumption_fn(context)
                if not passed:
                    if contract.severity == ContractSeverity.FATAL:
                        raise ContractViolation(
                            message=reason,
                            contract_name=contract.name,
                            violation_type="assumption (precondition)",
                            severity=contract.severity,
                            details={"context_keys": list(context.keys())},
                        )

            # 2. Execute Transformation
            result = func(*args, **kwargs)

            # 3. Postcondition Guarantee Checks
            for guarantee_fn in contract.guarantees:
                passed, reason = guarantee_fn(result, context)
                if not passed:
                    if contract.severity == ContractSeverity.FATAL:
                        raise ContractViolation(
                            message=reason,
                            contract_name=contract.name,
                            violation_type="guarantee (postcondition)",
                            severity=contract.severity,
                            details={"result_type": type(result).__name__},
                        )

            return result
        return wrapper
    return decorator


# --- Standard Contract Assumption / Guarantee Helpers ---

STANDARD_AMINO_ACIDS = set("ACDEFGHIKLMNPQRSTVWY")


def assume_valid_sequence(key: str = "sequence", min_len: int = 2, max_len: int = 100) -> Callable[[Dict[str, Any]], Tuple[bool, str]]:
    """Assumption: Input must contain a valid IUPAC amino acid sequence within length bounds."""
    def check(ctx: Dict[str, Any]) -> Tuple[bool, str]:
        val = ctx.get(key)
        if not val or not isinstance(val, str):
            return False, f"Missing or invalid string sequence at parameter '{key}'."
        clean_seq = val.strip().upper()
        if len(clean_seq) < min_len or len(clean_seq) > max_len:
            return False, f"Sequence length {len(clean_seq)} outside allowed range [{min_len}, {max_len}]."
        invalid_residues = set(clean_seq) - STANDARD_AMINO_ACIDS
        if invalid_residues:
            return False, f"Sequence contains non-standard amino acid characters: {sorted(invalid_residues)}."
        return True, ""
    return check


def assume_context_has_keys(*required_keys: str) -> Callable[[Dict[str, Any]], Tuple[bool, str]]:
    """Assumption: Input context dictionary must contain specified required keys."""
    def check(ctx: Dict[str, Any]) -> Tuple[bool, str]:
        missing = [k for k in required_keys if k not in ctx or ctx[k] is None]
        if missing:
            return False, f"Context missing required parameters: {missing}."
        return True, ""
    return check


def guarantee_non_null_output() -> Callable[[Any, Dict[str, Any]], Tuple[bool, str]]:
    """Guarantee: Output must not be None."""
    def check(result: Any, _ctx: Dict[str, Any]) -> Tuple[bool, str]:
        if result is None:
            return False, "Function returned None when non-null result was guaranteed."
        return True, ""
    return check


def guarantee_bounded_score(field_name: str = "overall_score", min_val: float = 0.0, max_val: float = 100.0) -> Callable[[Any, Dict[str, Any]], Tuple[bool, str]]:
    """Guarantee: Result object or dictionary has numerical field within [min_val, max_val]."""
    def check(result: Any, _ctx: Dict[str, Any]) -> Tuple[bool, str]:
        val = getattr(result, field_name, None) if hasattr(result, field_name) else (result.get(field_name) if isinstance(result, dict) else None)
        if val is None or not isinstance(val, (int, float)):
            return False, f"Result missing numerical score field '{field_name}'."
        if val < min_val or val > max_val:
            return False, f"Score '{field_name}' value {val} outside guaranteed bounds [{min_val}, {max_val}]."
        return True, ""
    return check
