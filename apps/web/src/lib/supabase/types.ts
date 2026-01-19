export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Platform = 'web' | 'ios' | 'android' | 'all'
export type ProjectStatus = 'idle' | 'planning' | 'designing' | 'generating' | 'testing' | 'complete' | 'error'
export type AgentStatus = 'pending' | 'running' | 'complete' | 'error'
export type ABTestStatus = 'draft' | 'running' | 'completed'

export interface Database {
  public: {
    Tables: {
      projects: {
        Row: {
          id: string
          user_id: string
          name: string
          description: string | null
          platform: Platform
          status: ProjectStatus
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          user_id: string
          name: string
          description?: string | null
          platform?: Platform
          status?: ProjectStatus
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          user_id?: string
          name?: string
          description?: string | null
          platform?: Platform
          status?: ProjectStatus
          created_at?: string
          updated_at?: string
        }
      }
      project_files: {
        Row: {
          id: string
          project_id: string
          path: string
          content: string | null
          language: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          project_id: string
          path: string
          content?: string | null
          language?: string | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          project_id?: string
          path?: string
          content?: string | null
          language?: string | null
          created_at?: string
          updated_at?: string
        }
      }
      agent_executions: {
        Row: {
          id: string
          project_id: string
          agent_name: string
          agent_type: string | null
          status: AgentStatus
          input: Json | null
          output: Json | null
          error: string | null
          started_at: string | null
          completed_at: string | null
          created_at: string
        }
        Insert: {
          id?: string
          project_id: string
          agent_name: string
          agent_type?: string | null
          status?: AgentStatus
          input?: Json | null
          output?: Json | null
          error?: string | null
          started_at?: string | null
          completed_at?: string | null
          created_at?: string
        }
        Update: {
          id?: string
          project_id?: string
          agent_name?: string
          agent_type?: string | null
          status?: AgentStatus
          input?: Json | null
          output?: Json | null
          error?: string | null
          started_at?: string | null
          completed_at?: string | null
          created_at?: string
        }
      }
      code_embeddings: {
        Row: {
          id: string
          project_id: string
          file_path: string
          chunk_index: number
          content: string
          embedding: number[] | null
          metadata: Json | null
          created_at: string
        }
        Insert: {
          id?: string
          project_id: string
          file_path: string
          chunk_index?: number
          content: string
          embedding?: number[] | null
          metadata?: Json | null
          created_at?: string
        }
        Update: {
          id?: string
          project_id?: string
          file_path?: string
          chunk_index?: number
          content?: string
          embedding?: number[] | null
          metadata?: Json | null
          created_at?: string
        }
      }
      market_research: {
        Row: {
          id: string
          project_id: string
          tam: number | null
          sam: number | null
          som: number | null
          competitors: Json | null
          trends: Json | null
          recommendations: Json | null
          created_at: string
        }
        Insert: {
          id?: string
          project_id: string
          tam?: number | null
          sam?: number | null
          som?: number | null
          competitors?: Json | null
          trends?: Json | null
          recommendations?: Json | null
          created_at?: string
        }
        Update: {
          id?: string
          project_id?: string
          tam?: number | null
          sam?: number | null
          som?: number | null
          competitors?: Json | null
          trends?: Json | null
          recommendations?: Json | null
          created_at?: string
        }
      }
      audit_results: {
        Row: {
          id: string
          project_id: string
          audit_type: string
          findings: Json | null
          score: number | null
          recommendations: Json | null
          created_at: string
        }
        Insert: {
          id?: string
          project_id: string
          audit_type: string
          findings?: Json | null
          score?: number | null
          recommendations?: Json | null
          created_at?: string
        }
        Update: {
          id?: string
          project_id?: string
          audit_type?: string
          findings?: Json | null
          score?: number | null
          recommendations?: Json | null
          created_at?: string
        }
      }
      ab_tests: {
        Row: {
          id: string
          project_id: string
          name: string
          description: string | null
          variant_a: Json | null
          variant_b: Json | null
          status: ABTestStatus
          git_branch_a: string | null
          git_branch_b: string | null
          created_at: string
          started_at: string | null
          completed_at: string | null
        }
        Insert: {
          id?: string
          project_id: string
          name: string
          description?: string | null
          variant_a?: Json | null
          variant_b?: Json | null
          status?: ABTestStatus
          git_branch_a?: string | null
          git_branch_b?: string | null
          created_at?: string
          started_at?: string | null
          completed_at?: string | null
        }
        Update: {
          id?: string
          project_id?: string
          name?: string
          description?: string | null
          variant_a?: Json | null
          variant_b?: Json | null
          status?: ABTestStatus
          git_branch_a?: string | null
          git_branch_b?: string | null
          created_at?: string
          started_at?: string | null
          completed_at?: string | null
        }
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      [_ in never]: never
    }
    Enums: {
      [_ in never]: never
    }
  }
}

// Helper types for easier access
export type Project = Database['public']['Tables']['projects']['Row']
export type ProjectInsert = Database['public']['Tables']['projects']['Insert']
export type ProjectUpdate = Database['public']['Tables']['projects']['Update']

export type ProjectFile = Database['public']['Tables']['project_files']['Row']
export type ProjectFileInsert = Database['public']['Tables']['project_files']['Insert']

export type AgentExecution = Database['public']['Tables']['agent_executions']['Row']
export type AgentExecutionInsert = Database['public']['Tables']['agent_executions']['Insert']
export type AgentExecutionUpdate = Database['public']['Tables']['agent_executions']['Update']

export type CodeEmbedding = Database['public']['Tables']['code_embeddings']['Row']
export type MarketResearch = Database['public']['Tables']['market_research']['Row']
export type AuditResult = Database['public']['Tables']['audit_results']['Row']
export type ABTest = Database['public']['Tables']['ab_tests']['Row']
