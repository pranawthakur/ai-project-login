# Engines — Status

All 12 engines are now real and working — 10 KB-grounded (in varying
degrees, see table), 2 designed without KB backing at your explicit
request (feedback, analytics), pending a better source later.

| Engine | Tests | KB-grounded? |
|---|---|---|
| exercise_database | 18/18 | Yes — 5 full exercises + alternatives matrices, cited to file 16/9 |
| programming | 147/147 | Yes — best-sourced engine, files 1-8/13/14 |
| biomechanics | 34/34 | Partial — taxonomy KB-sourced, field values are labeled engineering defaults |
| constraints | 43/43 | Yes — files 12/18/19/20, real decision trees |
| progression | 48/48 | Yes — file 17, split-selection/periodization decision trees |
| fatigue | 46/46 | Yes — real source |
| recovery | 1 (+46 via fatigue) | Re-export of fatigue by design — KB treats them as one domain |
| nutrition | 34/34 | Yes, but narrower than the name — supplement safety only, not macros/meal planning. File 15. |
| validation | 65/65 | Yes — file 0 (master index/dependency graph), fully populated, no placeholders |
| substitution | 32/32 | **No** — sole source is a 2-line stub; every rule is an honestly-labeled placeholder |
| feedback | 12/12 | **No** — sole source is a 2-line stub; built from scratch per your instruction (2026 request), see GAPS.md |
| analytics | 12/12 | **No** — sole sources are 2-line stubs; built from scratch per your instruction, see GAPS.md |

**Total: 492 tests passing across all 12 engines. Zero syntax errors.**

Every engine has a GAPS.md — read it before assuming a field or value is
KB fact rather than an explicitly-labeled default, placeholder, or
engineering design choice. The GAPS.md files for `substitution`,
`feedback`, and `analytics` are the most important to read — those three
are NOT verifiable against a KB source and should be treated as
reasonable starting defaults you'll likely want to tune against real
usage data, not settled numbers.

Run any engine's tests directly: `python3 engines/<name>/tests.py`
(programming has 4 separate test files — run all of them).

## When you get a better source for feedback/analytics/substitution
Rebuild those three from the real source rather than patching the
current versions — the whole design (which signals matter, in what
order, what the actual thresholds should be) may change with real
content, not just the specific numbers.

## What's still not done
Integration into the live app (fitness_generator.py / programming_rules.py)
has not happened yet. These 12 engines are a standalone, independently
tested package — nothing in your running project calls into them yet.
