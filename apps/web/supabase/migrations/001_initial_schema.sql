-- Code Weaver Pro Database Schema
-- Initial migration for project management and AI agent execution tracking

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Projects table
CREATE TABLE IF NOT EXISTS projects (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  description TEXT,
  platform TEXT NOT NULL DEFAULT 'web' CHECK (platform IN ('web', 'ios', 'android', 'all')),
  status TEXT NOT NULL DEFAULT 'idle' CHECK (status IN ('idle', 'planning', 'designing', 'generating', 'testing', 'complete', 'error')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Project files table (stores generated code)
CREATE TABLE IF NOT EXISTS project_files (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  path TEXT NOT NULL,
  content TEXT,
  language TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(project_id, path)
);

-- Agent executions table (tracks each agent's work)
CREATE TABLE IF NOT EXISTS agent_executions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  agent_name TEXT NOT NULL,
  agent_type TEXT,
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'complete', 'error')),
  input JSONB,
  output JSONB,
  error TEXT,
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Code embeddings table (for semantic search with LlamaIndex)
CREATE TABLE IF NOT EXISTS code_embeddings (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  file_path TEXT NOT NULL,
  chunk_index INTEGER NOT NULL DEFAULT 0,
  content TEXT NOT NULL,
  embedding vector(1536),
  metadata JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(project_id, file_path, chunk_index)
);

-- Market research results table
CREATE TABLE IF NOT EXISTS market_research (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  tam NUMERIC,
  sam NUMERIC,
  som NUMERIC,
  competitors JSONB,
  trends JSONB,
  recommendations JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Audit results table
CREATE TABLE IF NOT EXISTS audit_results (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  audit_type TEXT NOT NULL,
  findings JSONB,
  score NUMERIC,
  recommendations JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- A/B test configurations
CREATE TABLE IF NOT EXISTS ab_tests (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  description TEXT,
  variant_a JSONB,
  variant_b JSONB,
  status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'running', 'completed')),
  git_branch_a TEXT,
  git_branch_b TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_project_files_project_id ON project_files(project_id);
CREATE INDEX IF NOT EXISTS idx_agent_executions_project_id ON agent_executions(project_id);
CREATE INDEX IF NOT EXISTS idx_agent_executions_status ON agent_executions(status);
CREATE INDEX IF NOT EXISTS idx_code_embeddings_project_id ON code_embeddings(project_id);

-- Create vector similarity search index
CREATE INDEX IF NOT EXISTS idx_code_embeddings_vector ON code_embeddings
  USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Enable Row Level Security
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_executions ENABLE ROW LEVEL SECURITY;
ALTER TABLE code_embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE market_research ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE ab_tests ENABLE ROW LEVEL SECURITY;

-- RLS Policies for projects
CREATE POLICY "Users can view own projects"
  ON projects FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can create own projects"
  ON projects FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own projects"
  ON projects FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own projects"
  ON projects FOR DELETE
  USING (auth.uid() = user_id);

-- RLS Policies for project_files (inherit from project ownership)
CREATE POLICY "Users can view own project files"
  ON project_files FOR SELECT
  USING (EXISTS (
    SELECT 1 FROM projects WHERE projects.id = project_files.project_id AND projects.user_id = auth.uid()
  ));

CREATE POLICY "Users can create files in own projects"
  ON project_files FOR INSERT
  WITH CHECK (EXISTS (
    SELECT 1 FROM projects WHERE projects.id = project_files.project_id AND projects.user_id = auth.uid()
  ));

CREATE POLICY "Users can update files in own projects"
  ON project_files FOR UPDATE
  USING (EXISTS (
    SELECT 1 FROM projects WHERE projects.id = project_files.project_id AND projects.user_id = auth.uid()
  ));

CREATE POLICY "Users can delete files in own projects"
  ON project_files FOR DELETE
  USING (EXISTS (
    SELECT 1 FROM projects WHERE projects.id = project_files.project_id AND projects.user_id = auth.uid()
  ));

-- RLS Policies for agent_executions
CREATE POLICY "Users can view own agent executions"
  ON agent_executions FOR SELECT
  USING (EXISTS (
    SELECT 1 FROM projects WHERE projects.id = agent_executions.project_id AND projects.user_id = auth.uid()
  ));

CREATE POLICY "Users can create agent executions in own projects"
  ON agent_executions FOR INSERT
  WITH CHECK (EXISTS (
    SELECT 1 FROM projects WHERE projects.id = agent_executions.project_id AND projects.user_id = auth.uid()
  ));

-- RLS Policies for code_embeddings
CREATE POLICY "Users can view own code embeddings"
  ON code_embeddings FOR SELECT
  USING (EXISTS (
    SELECT 1 FROM projects WHERE projects.id = code_embeddings.project_id AND projects.user_id = auth.uid()
  ));

CREATE POLICY "Users can create embeddings in own projects"
  ON code_embeddings FOR INSERT
  WITH CHECK (EXISTS (
    SELECT 1 FROM projects WHERE projects.id = code_embeddings.project_id AND projects.user_id = auth.uid()
  ));

-- RLS Policies for market_research
CREATE POLICY "Users can view own market research"
  ON market_research FOR SELECT
  USING (EXISTS (
    SELECT 1 FROM projects WHERE projects.id = market_research.project_id AND projects.user_id = auth.uid()
  ));

CREATE POLICY "Users can create market research in own projects"
  ON market_research FOR INSERT
  WITH CHECK (EXISTS (
    SELECT 1 FROM projects WHERE projects.id = market_research.project_id AND projects.user_id = auth.uid()
  ));

-- RLS Policies for audit_results
CREATE POLICY "Users can view own audit results"
  ON audit_results FOR SELECT
  USING (EXISTS (
    SELECT 1 FROM projects WHERE projects.id = audit_results.project_id AND projects.user_id = auth.uid()
  ));

CREATE POLICY "Users can create audit results in own projects"
  ON audit_results FOR INSERT
  WITH CHECK (EXISTS (
    SELECT 1 FROM projects WHERE projects.id = audit_results.project_id AND projects.user_id = auth.uid()
  ));

-- RLS Policies for ab_tests
CREATE POLICY "Users can view own ab tests"
  ON ab_tests FOR SELECT
  USING (EXISTS (
    SELECT 1 FROM projects WHERE projects.id = ab_tests.project_id AND projects.user_id = auth.uid()
  ));

CREATE POLICY "Users can manage ab tests in own projects"
  ON ab_tests FOR ALL
  USING (EXISTS (
    SELECT 1 FROM projects WHERE projects.id = ab_tests.project_id AND projects.user_id = auth.uid()
  ));

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_projects_updated_at
  BEFORE UPDATE ON projects
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_project_files_updated_at
  BEFORE UPDATE ON project_files
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
