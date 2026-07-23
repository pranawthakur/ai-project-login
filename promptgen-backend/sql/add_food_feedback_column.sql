-- Run this once in Supabase → SQL Editor.
--
-- Adds an optional free-text "food problems" field to the existing
-- `checkins` table (the biweekly Progress Check-in), alongside the
-- existing pain_notes column. Lets a member flag an ingredient/food
-- that's causing issues (or a new intolerance) without waiting for a
-- full new intake form — checkin_engine.store_checkin() already writes
-- this column once it exists; nothing else needs to change in the
-- table shape.
--
-- Read back on the member's NEXT plan regeneration via
-- _apply_latest_checkin_to_profile() in main.py, which copies it into
-- profile["food_feedback_notes"]; diet_engine.parse_allergies() and
-- diet_engine.parse_food_feedback_exclusions() then use it to keep
-- future diet.meals options from repeating whatever the member flagged.

ALTER TABLE checkins
  ADD COLUMN IF NOT EXISTS food_feedback text;
