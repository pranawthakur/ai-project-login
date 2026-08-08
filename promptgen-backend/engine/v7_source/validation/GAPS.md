# Validation Engine — Coverage Gaps

Source: 0_Master_Index_Versioning_and_Localization.md (file dependency
graph/index) plus a second source document. 65 tests passing — the
best-populated of the newly-fixed engines; its own module docstring
states this KB source is "fully populated," unlike biomechanics/
substitution, so there are no engineering-default placeholders here.

## What this actually validates
This is largely a cross-reference/dependency engine — e.g. FILE_INDEX
records that "file 2 (Programming Rules) depends_on [11, 10]" — useful
for checking that a generated plan's inputs were actually available in
the right order, and for validating internal consistency of the KB
itself (which files reference which). It is not a numeric-range
validator for training data the way exercise_database's `validators.py`
is — don't expect it to catch a bad rep count, for instance.

## Known gaps
None identified yet from a first read — flag anything found during
integration so this file stays accurate rather than staying silent about
gaps once we're actually using it.
