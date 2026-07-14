-- Phase 6 patch: the ACTUAL feedback tables the frontend writes to are
-- workout_set_feedback / workout_exercise_feedback (written directly from
-- browser JS in Templates/result.html), not plan_feedback. Run this
-- instead of/in addition to create_reassessment_tables.sql.
--
-- Problem being fixed: both tables were upserted on a key that did NOT
-- include cycle, so every new biweekly cycle's feedback OVERWROTE the
-- previous cycle's rows. No history = no trend to progress off. This adds
-- cycle_number and widens the unique constraint so each cycle's rows are
-- kept separately.

-- 1. Add the column (nullable first, so it doesn't fail on existing rows).
alter table workout_set_feedback      add column if not exists cycle_number int;
alter table workout_exercise_feedback add column if not exists cycle_number int;

-- 2. Backfill any pre-existing rows as cycle 1 (best guess — they predate
--    cycle tracking entirely, so there's no way to know their real cycle).
update workout_set_feedback      set cycle_number = 1 where cycle_number is null;
update workout_exercise_feedback set cycle_number = 1 where cycle_number is null;

alter table workout_set_feedback      alter column cycle_number set not null;
alter table workout_exercise_feedback alter column cycle_number set not null;
alter table workout_set_feedback      alter column cycle_number set default 1;
alter table workout_exercise_feedback alter column cycle_number set default 1;

-- 3. Drop the old (too-narrow) unique constraint and add the correct one.
--    NOTE: constraint names below are Postgres/Supabase's default naming —
--    if yours differ, run:
--      select conname from pg_constraint where conrelid = 'workout_set_feedback'::regclass;
--    and swap the name in below.
alter table workout_set_feedback
  drop constraint if exists workout_set_feedback_member_id_day_index_exercise_set_number_key;
alter table workout_set_feedback
  add constraint workout_set_feedback_member_cycle_day_ex_set_key
  unique (member_id, cycle_number, day_index, exercise, set_number);

alter table workout_exercise_feedback
  drop constraint if exists workout_exercise_feedback_member_id_day_index_exercise_key;
alter table workout_exercise_feedback
  add constraint workout_exercise_feedback_member_cycle_day_ex_key
  unique (member_id, cycle_number, day_index, exercise);

create index if not exists workout_set_feedback_member_cycle_idx
  on workout_set_feedback(member_id, cycle_number);
create index if not exists workout_exercise_feedback_member_cycle_idx
  on workout_exercise_feedback(member_id, cycle_number);
