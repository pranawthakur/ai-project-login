-- Run this against the SAME Supabase project as the member app / dev
-- dashboard. Idempotent — safe to run multiple times.
--
-- Creates one internal "Dev QA" gym and 3 fixed member rows that exist
-- ONLY so developers can hit POST /generate/full (see app/main.py) and get
-- a full, real generated plan back — same pipeline a real member gets,
-- Trainer Review included — without needing an actual gym signup or member
-- login. Gated on that endpoint by X-Dev-Test-Key, not by these rows being
-- secret; treat them as internal tooling, not real customer data.
--
-- 3 slots so a couple of people can test in parallel without their
-- cycle_number/plan-history stepping on each other. Add more by copying
-- the pattern below with DEVQA4, DEVQA5, etc. — app/main.py's
-- /generate/full endpoint accepts any slot number as long as a matching
-- login_code exists here.

insert into gyms (name, slug)
select 'Dev QA (internal testing — not a real gym)', 'dev-qa'
where not exists (select 1 from gyms where slug = 'dev-qa');

insert into members (gym_id, name, login_code, status)
select g.id, 'Dev QA Slot 1', 'DEVQA1', 'active'
from gyms g
where g.slug = 'dev-qa'
  and not exists (
    select 1 from members m where m.gym_id = g.id and m.login_code = 'DEVQA1'
  );

insert into members (gym_id, name, login_code, status)
select g.id, 'Dev QA Slot 2', 'DEVQA2', 'active'
from gyms g
where g.slug = 'dev-qa'
  and not exists (
    select 1 from members m where m.gym_id = g.id and m.login_code = 'DEVQA2'
  );

insert into members (gym_id, name, login_code, status)
select g.id, 'Dev QA Slot 3', 'DEVQA3', 'active'
from gyms g
where g.slug = 'dev-qa'
  and not exists (
    select 1 from members m where m.gym_id = g.id and m.login_code = 'DEVQA3'
  );

-- If this errors on a NOT NULL column I don't know about (the members
-- table schema lives in a different repo I don't have), add that column
-- with a placeholder value to each of the 3 inserts above and re-run —
-- the "where not exists" guards make re-running always safe.
