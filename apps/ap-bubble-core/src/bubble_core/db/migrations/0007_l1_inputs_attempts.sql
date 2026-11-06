-- How often the curator failed on an input; failed inputs are retried up to a limit.
ALTER TABLE l1_inputs ADD COLUMN attempts INTEGER NOT NULL DEFAULT 0;
