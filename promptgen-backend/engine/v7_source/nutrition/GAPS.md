# Nutrition Engine — Coverage Gaps

Source: 15_Supplement_Safety_and_Interaction_Engine.md (the sole real
source — the "nutrition" name is broader than what's actually covered).
34 tests passing.

## Scope is narrower than the name suggests
This engine covers supplement safety/interaction tiers (protein powder,
creatine, caffeine, electrolytes, vitamin D as Tier 1; riskier stacks as
Tier 2/3), NOT macro targets, meal planning, or calorie calculations.
Your existing `fitness_generator.py` daily-calorie/protein logic is a
separate concern this engine doesn't touch or replace.

## Known gap: unusual data encoding
Several lookup_tables.py values are encoded as long snake_case string
tokens (e.g. `"range": "3-5g_day_ongoing_loading_phase_optional_not_required"`)
rather than structured fields (amount + unit + condition as separate
keys). This mirrors the source's prose-heavy, note-style guidance rather
than being a fabrication — file 15 reads more like clinical notes than a
clean numeric table — but it means callers need to parse these strings
themselves if they want the numeric value in isolation (e.g. "3-5" and
"g/day" out of that token). Worth normalizing into structured fields if
this engine sees real use, rather than parsing snake_case at call sites.
