-- ================================================================
-- Migration: Add generation_prompt_data column for prompt storage
-- Date: 2025-11-11
-- Issue: DEF-151 (simplified version)
-- ================================================================

-- Add column to store generation prompt as JSON
ALTER TABLE definities
ADD COLUMN generation_prompt_data TEXT;

-- Comment explaining the column
-- generation_prompt_data stores JSON with format:
-- {
--   "prompt": "full prompt text",
--   "model": "gpt-4-turbo-2024-04-09",
--   "temperature": 0.7,
--   "tokens_used": 1234,
--   "tokens_prompt": 800,
--   "tokens_completion": 434,
--   "created_at": "2025-11-11T14:23:45Z"
-- }

-- Create index for querying generations with prompts
CREATE INDEX IF NOT EXISTS idx_definities_has_prompt
ON definities(generation_prompt_data)
WHERE generation_prompt_data IS NOT NULL;
