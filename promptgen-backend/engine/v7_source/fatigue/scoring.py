"""No distinct numeric scoring model in file 10 beyond the tables already
in lookup_tables.py (recovery quality tiers, fatigue indicator warnings).
Kept as a thin re-export point for callers that expect scoring.py to exist."""
from .rules import evaluate_fatigue_indicators, recovery_quality_tier
