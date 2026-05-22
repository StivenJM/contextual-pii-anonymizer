"""Detection layer."""

from .model import detect_with_model
from .rules import detect_with_rules
from .validators import is_valid_ec_cedula, is_valid_ec_ruc

__all__ = ["detect_with_model", "detect_with_rules", "is_valid_ec_cedula", "is_valid_ec_ruc"]
