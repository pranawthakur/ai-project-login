-- Phase 6: Biweekly Reassessment & Adaptive Progression
-- Run once in Supabase -> SQL Editor.

-- 1. Extend plan_feedback with the fields progression math actually needs.
--    (existing table only had weight_kg + a 1-5 difficulty star; that's not
--    enough to compute completion %, missed sets, or rep-based 1RM trend.)
alter table plan_feedback add column if not exists reps_completed   int;
alter table plan_feedback add column if not exists target_reps      int;
alter table plan_feedback add column if not exists target_weight_kg numeric;
alter table plan_feedback add column if not exists completed        boolean not null default true;
alter table plan_feedback add column if not exists cycle_number     int not null default 1;

-- 2. Biweekly check-in form responses (subjective, capped at ~3 min).
create table if not exists checkins (
  id                bigint generated always as identity primary key,
  member_id         uuid not null references members(id) on delete cascade,
  cycle_number      int not null,
  recovery          text not null check (recovery in ('excellent','good','average','poor')),
  difficulty        text not null check (difficulty in ('too_easy','easy','just_right','hard','too_hard')),
  soreness          text not null check (soreness in ('none','mild','moderate','severe')),
  pain_areas        text[] not null default '{}',   -- e.g. {'shoulder','knee'}
  pain_notes        text,
  body_weight_kg    numeric,
  waist_cm          numeric,
  chest_cm          numeric,
  arms_cm           numeric,
  thighs_cm         numeric,
  hips_cm           numeric,
  body_fat_pct      numeric,
  created_at        timestamptz not null default now()
);

create index if not exists checkins_member_id_idx on checkins(member_id);
create index if not exists checkins_member_cycle_idx on checkins(member_id, cycle_number);

-- 3. Reassessment history — one row per biweekly cycle, stores the
--    deterministic classification + what the progression engine decided.
create table if not exists reassessments (
  id                    bigint generated always as identity primary key,
  member_id             uuid not null references members(id) on delete cascade,
  cycle_number          int not null,
  checkin_id            bigint references checkins(id) on delete set null,
  progress_state        text not null check (progress_state in
                           ('improving','maintaining','plateaued','regressing')),
  compliance_pct         numeric,
  is_deload             boolean not null default false,
  plateau_counter       int not null default 0,
  adaptations           jsonb not null default '{}',   -- full decision payload, see progression_engine.py
  created_at            timestamptz not null default now()
);

create index if not exists reassessments_member_id_idx on reassessments(member_id);
create unique index if not exists reassessments_member_cycle_uidx on reassessments(member_id, cycle_number);

-- NOTE: adjust `references members(id)` above if your members table has a
-- different name/primary key column, same caveat as create_feedback_table.sql.
