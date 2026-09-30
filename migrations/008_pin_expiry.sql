-- Migration 008 — pins expire, and at most one story holds each Top Stories rank (F10, epic 002).
--
-- Before: every "Make top" / drag-reorder wrote action='pinned' + pinned_rank with no expiry and no
-- uniqueness, so pins lived forever and several stories could all claim rank 1.
-- After:
--   * pinned_until timestamptz — the app sets it on every pin (PIN_TTL_HOURS, src/lib/studio/pins.ts);
--     past it the story stays Published but no longer forces its rank.
--   * one_pin_per_rank — an EXCLUDE constraint: no two action='pinned' rows share a pinned_rank.
--     DEFERRABLE INITIALLY DEFERRED so a multi-row reorder can shuffle ranks inside one transaction
--     and is checked once, at COMMIT (a violation rolls the whole reorder back).
--   * pinned rows must carry a rank >= 1.
--
-- DEPLOY ORDER: apply this BEFORE deploying the F10 app code — the app writes pinned_until on every
-- override write. Idempotent: safe to re-run (IF NOT EXISTS / guarded DO blocks / no-op updates).

ALTER TABLE rigwire.editorial_overrides
  ADD COLUMN IF NOT EXISTS pinned_until timestamptz;

-- Normalise legacy pins so the constraints below can hold. Every change is written to the audit
-- ledger (editor 'migration-008') so the clean-up is visible in Studio → Audit like any edit.
WITH fixed AS (
  UPDATE rigwire.editorial_overrides
     SET pinned_rank = 1, updated_at = now()
   WHERE action = 'pinned' AND (pinned_rank IS NULL OR pinned_rank < 1)
  RETURNING story_id
)
INSERT INTO rigwire.editorial_audit (story_id, editor_id, action, before, after)
SELECT story_id, 'migration-008', 'pin_normalise', NULL, jsonb_build_object('pinnedRank', 1)
  FROM fixed;

-- Several stories pinned at the same rank: keep the most recently set one, un-pin the rest
-- (they stay Published — action 'live').
WITH ranked AS (
  SELECT story_id,
         row_number() OVER (PARTITION BY pinned_rank ORDER BY updated_at DESC, story_id) AS rn,
         pinned_rank
    FROM rigwire.editorial_overrides
   WHERE action = 'pinned'
),
demoted AS (
  UPDATE rigwire.editorial_overrides o
     SET action = 'live', pinned_rank = NULL, pinned_until = NULL, updated_at = now()
    FROM ranked r
   WHERE o.story_id = r.story_id AND r.rn > 1
  RETURNING o.story_id, r.pinned_rank
)
INSERT INTO rigwire.editorial_audit (story_id, editor_id, action, before, after)
SELECT story_id, 'migration-008', 'unpin',
       jsonb_build_object('action', 'pinned', 'pinnedRank', pinned_rank),
       jsonb_build_object('action', 'live', 'pinnedRank', NULL)
  FROM demoted;

-- No pin is forever: give surviving legacy pins an expiry from now (matches PIN_TTL_HOURS = 12).
UPDATE rigwire.editorial_overrides
   SET pinned_until = now() + interval '12 hours'
 WHERE action = 'pinned' AND pinned_until IS NULL;

-- Non-pinned rows never carry an expiry.
UPDATE rigwire.editorial_overrides
   SET pinned_until = NULL
 WHERE action <> 'pinned' AND pinned_until IS NOT NULL;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
     WHERE conname = 'one_pin_per_rank' AND conrelid = 'rigwire.editorial_overrides'::regclass
  ) THEN
    ALTER TABLE rigwire.editorial_overrides
      ADD CONSTRAINT one_pin_per_rank
      EXCLUDE USING btree (pinned_rank WITH =) WHERE (action = 'pinned')
      DEFERRABLE INITIALLY DEFERRED;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
     WHERE conname = 'pinned_has_rank' AND conrelid = 'rigwire.editorial_overrides'::regclass
  ) THEN
    ALTER TABLE rigwire.editorial_overrides
      ADD CONSTRAINT pinned_has_rank
      CHECK (action <> 'pinned' OR (pinned_rank IS NOT NULL AND pinned_rank >= 1));
  END IF;
END $$;
