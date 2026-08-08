-- Run this once in Supabase → SQL Editor.
-- Stores per-set weight-used + difficulty-star ratings submitted from the
-- result.html "Submit Weekly Feedback" button. One row per set.

create table if not exists plan_feedback (
  id                bigint generated always as identity primary key,
  member_id         uuid not null references members(id) on delete cascade,
  day_index         int not null,
  day_name          text not null,
  exercise          text not null,
  set_number        int not null,
  weight_kg         numeric,
  difficulty_rating int check (difficulty_rating between 1 and 5),
  created_at        timestamptz not null default now()
);

create index if not exists plan_feedback_member_id_idx on plan_feedback(member_id);
create index if not exists plan_feedback_created_at_idx on plan_feedback(created_at);

-- NOTE: adjust `references members(id)` above if your members table has a
-- different name/primary key column — check whichever table membership.py
-- writes member rows to.
