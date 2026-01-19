'use client'

import { useEffect, useState } from 'react'
import { User, Session } from '@supabase/supabase-js'
import { supabase } from '@/lib/supabase/client'

interface AuthState {
  user: User | null
  session: Session | null
  loading: boolean
  isLocalMode: boolean
}

// Mock user for local development
const LOCAL_MOCK_USER: User = {
  id: 'local-dev-user',
  email: 'developer@localhost',
  aud: 'authenticated',
  role: 'authenticated',
  created_at: new Date().toISOString(),
  app_metadata: {},
  user_metadata: { name: 'Local Developer' },
} as User

export function useAuth() {
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    session: null,
    loading: true,
    isLocalMode: false,
  })

  useEffect(() => {
    // Check if we're in local development mode (no Supabase URL configured)
    const isLocalMode = !process.env.NEXT_PUBLIC_SUPABASE_URL ||
      process.env.NEXT_PUBLIC_SUPABASE_URL === 'http://localhost:54321'

    if (isLocalMode) {
      // Use mock user for local development
      setAuthState({
        user: LOCAL_MOCK_USER,
        session: null,
        loading: false,
        isLocalMode: true,
      })
      return
    }

    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setAuthState({
        user: session?.user ?? null,
        session,
        loading: false,
        isLocalMode: false,
      })
    })

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setAuthState({
        user: session?.user ?? null,
        session,
        loading: false,
        isLocalMode: false,
      })
    })

    return () => subscription.unsubscribe()
  }, [])

  const signIn = async (email: string, password: string) => {
    if (authState.isLocalMode) {
      console.log('Local mode: Sign in simulated')
      return { data: { user: LOCAL_MOCK_USER, session: null }, error: null }
    }
    return supabase.auth.signInWithPassword({ email, password })
  }

  const signUp = async (email: string, password: string) => {
    if (authState.isLocalMode) {
      console.log('Local mode: Sign up simulated')
      return { data: { user: LOCAL_MOCK_USER, session: null }, error: null }
    }
    return supabase.auth.signUp({ email, password })
  }

  const signOut = async () => {
    if (authState.isLocalMode) {
      console.log('Local mode: Sign out simulated')
      return { error: null }
    }
    return supabase.auth.signOut()
  }

  const signInWithGitHub = async () => {
    if (authState.isLocalMode) {
      console.log('Local mode: GitHub sign in not available')
      return { data: { url: null, provider: 'github' }, error: null }
    }
    return supabase.auth.signInWithOAuth({
      provider: 'github',
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
      },
    })
  }

  const signInWithGoogle = async () => {
    if (authState.isLocalMode) {
      console.log('Local mode: Google sign in not available')
      return { data: { url: null, provider: 'google' }, error: null }
    }
    return supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
      },
    })
  }

  return {
    ...authState,
    signIn,
    signUp,
    signOut,
    signInWithGitHub,
    signInWithGoogle,
  }
}
