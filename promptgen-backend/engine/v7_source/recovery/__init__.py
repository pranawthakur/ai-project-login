"""KB V7's file 10 ('Recovery and Deload') is the single real source
covering both fatigue-indicator tracking and deload/recovery protocols --
the source material does not actually separate these into two specs
(the dedicated 'recovery_capacity_engine' and 'fatigue_engine' folders
in the original zip were empty 2-line stubs; see engines/manifest.json).

Rather than duplicate the same logic under two names, this module
re-exports the fatigue engine's real implementation. Import from either
`engines.fatigue` or `engines.recovery` -- they are the same code."""
from engines.fatigue import (
    RecoveryInputs, FatigueIndicatorReport, DeloadDecision, ClientRecoveryState,
    sleep_impact, protein_target_g_per_kg, hydration_target_ml,
    training_age_band, scheduled_deload_due, check_reactive_deload_triggers, decide_deload,
    deload_method_protocol, standard_deload_week, evaluate_fatigue_indicators,
    recovery_quality_tier, recovery_quality_adjustment, age_recovery_note,
    stress_training_adjustment, handle_missed_deload_overreach, deload_frequency_anxiety_check,
)
