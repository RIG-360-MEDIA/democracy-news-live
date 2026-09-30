-- Migration 009 — persist the front-page section layout; keep the recency half-life knob neutral
-- (F11 + F12, epic 002).
--
--   * ranking_weights.section_layout jsonb — the editor-saved section ORDER, visibility and band size
--     ([{topic, visible, count}], see src/lib/worldwide/sections.ts). '[]' = the default layout.
--     The app reads the row via to_jsonb(), so the reader front page works before AND after this runs;
--     only SAVING a layout from Studio needs the column.
--   * recency_halflife_h — this knob was never read before F11 (the SQL hard-coded a 24h e-fold ≈ 16.6h
--     half-life) while the column default was 12. Wiring the knob would silently make the live feed
--     decay ~40% faster, so a row no editor has ever tuned (updated_by = 'system', still 12) is set to
--     the value that reproduces today's ordering. An editor-set value is left alone.
--
-- Idempotent: safe to re-run.

ALTER TABLE rigwire.ranking_weights
  ADD COLUMN IF NOT EXISTS section_layout jsonb NOT NULL DEFAULT '[]'::jsonb;

UPDATE rigwire.ranking_weights
   SET recency_halflife_h = 16.64
 WHERE id = 1 AND updated_by = 'system' AND recency_halflife_h = 12;
