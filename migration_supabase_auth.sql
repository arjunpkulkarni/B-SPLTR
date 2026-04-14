-- Migration: drop legacy auth columns from users table.
-- Supabase Auth is now the single source of truth for credentials.
-- The users table retains profile data only (id = Supabase user UUID).

ALTER TABLE users DROP COLUMN IF EXISTS password_hash;
ALTER TABLE users DROP COLUMN IF EXISTS auth_provider;
ALTER TABLE users DROP COLUMN IF EXISTS apple_id;
