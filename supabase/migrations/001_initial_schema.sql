-- NOTE: Enable "uuid-ossp" and "vector" extensions first from:
-- Supabase Dashboard → Database → Extensions → search and enable both

-- Profiles table (anonymous user row seeded below)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY,
    full_name TEXT NOT NULL,
    avatar_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert the anonymous/session user row that PitchPilot uses for no-auth mode
INSERT INTO public.profiles (id, full_name)
VALUES ('00000000-0000-0000-0000-000000000000', 'Anonymous')
ON CONFLICT (id) DO NOTHING;

-- API Keys (encrypted)
CREATE TABLE IF NOT EXISTS public.api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    provider TEXT NOT NULL,          -- 'openai', 'tavily'
    encrypted_key BYTEA NOT NULL,
    key_hint TEXT NOT NULL,          -- Last 4 chars of key
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, provider)
);

-- Meetings / Boardroom Sessions
CREATE TABLE IF NOT EXISTS public.meetings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    pitch_text TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'created',
    thread_id TEXT UNIQUE NOT NULL,
    agent_outputs JSONB DEFAULT '{}',
    transcript JSONB DEFAULT '[]',
    metrics JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- PDF Reports
CREATE TABLE IF NOT EXISTS public.reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meeting_id UUID UNIQUE NOT NULL REFERENCES public.meetings(id) ON DELETE CASCADE,
    sections JSONB NOT NULL,
    pdf_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Embeddings for semantic search (requires vector extension enabled above)
CREATE TABLE IF NOT EXISTS public.meeting_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meeting_id UUID NOT NULL REFERENCES public.meetings(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding vector(1536),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Standard indexes
CREATE INDEX IF NOT EXISTS idx_meetings_user_id ON public.meetings(user_id);
CREATE INDEX IF NOT EXISTS idx_meetings_status ON public.meetings(status);
CREATE INDEX IF NOT EXISTS idx_meetings_created_at ON public.meetings(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON public.api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_meeting_embeddings_meeting_id ON public.meeting_embeddings(meeting_id);

-- HNSW vector similarity index for fast semantic search
CREATE INDEX IF NOT EXISTS idx_meeting_embeddings_vector ON public.meeting_embeddings
    USING hnsw (embedding vector_cosine_ops);
