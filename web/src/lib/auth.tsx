import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import type { Session } from '@supabase/supabase-js'
import { supabase } from './supabase'

interface AuthState {
  session: Session | null
  carregando: boolean
  // só quem entrou e está liberado (função usuario_permitido no banco) edita; sem login o site é só leitura
  podeEditar: boolean
}

const AuthContext = createContext<AuthState>({ session: null, carregando: true, podeEditar: false })

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null)
  const [carregando, setCarregando] = useState(true)
  const [podeEditar, setPodeEditar] = useState(false)

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session)
      setCarregando(false)
    })
    const { data } = supabase.auth.onAuthStateChange((_e, s) => setSession(s))
    return () => data.subscription.unsubscribe()
  }, [])

  useEffect(() => {
    if (!session) return setPodeEditar(false)
    supabase.rpc('usuario_permitido').then(({ data }) => setPodeEditar(data === true))
  }, [session])

  return <AuthContext.Provider value={{ session, carregando, podeEditar }}>{children}</AuthContext.Provider>
}

export const useAuth = () => useContext(AuthContext)
