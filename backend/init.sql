-- Initialize database with extensions and optimizations

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pg_trgm for text search optimization
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Create indexes will be handled by Alembic migrations
-- This file is for initial database setup only

-- Set timezone
SET timezone = 'UTC';
