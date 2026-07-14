# Biomechanics Engine — Coverage Gaps

Sources: 16_biomechanics_engine/README.md, 10_movement_engine/movement_patterns.md,
10_movement_engine/movement_schema.md, 22_Movement_Intelligence_Engine/README.md.

manifest.json records "tables_extracted": 0 for this engine — these
sources define a *taxonomy* (10 movement pattern names) and a *field
schema* (what to store per exercise: prime movers, plane of motion, force
vector, etc.), but contain zero populated exercise records. Real
per-exercise data lives in exercise_database (sourced from
16_Exercise_Intelligence_Database.md instead).

## Known gaps — fields with no KB-defined value set

The KB names these schema fields but never defines what values they can
take. Rather than inventing "real" values and presenting them as
KB-sourced, this engine models them with an explicit engineering-default
enum, documented as such in every relevant docstring:

  - Plane (sagittal/frontal/transverse/multi_planar) — standard anatomical
    planes used as a reasonable default taxonomy, not from the KB
  - ForceVector — name-only field in the source; taxonomy invented here
  - FunctionalCategory (push/pull/hip_dominant/etc.) — same
  - ComplexityTier (1-3) — KB names "Complexity" as a field but gives no
    scale; a 3-tier scale was chosen over a false-precision numeric score

`lookup_tables.PATTERN_DEFAULTS` applies these engineering defaults at
the pattern level (e.g. all SQUAT-pattern exercises default to
sagittal-plane, vertical-force, closed-chain) — any specific exercise
that doesn't fit its pattern's default (e.g. a landmine press vs. a
standard vertical push) should override on its own MovementRecord rather
than trust the pattern default blindly.

## What IS KB-sourced
Only the 10-pattern taxonomy itself (MovementPattern enum) and the
schema's field *names* (what to track) — not the values.
