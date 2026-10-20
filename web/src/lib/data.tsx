import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'
import { supabase } from './supabase'
import type { Lead, Segmento } from './types'

interface DataState {
  leads: Lead[]
  segmentos: Segmento[]
  carregando: boolean
  erro: string | null
  recarregar: () => Promise<void>
  atualizarLead: (id: string, campos: Partial<Lead>) => Promise<string | null>
}

const DataContext = createContext<DataState | null>(null)

export function DataProvider({ children }: { children: ReactNode }) {
  const [leads, setLeads] = useState<Lead[]>([])
  const [segmentos, setSegmentos] = useState<Segmento[]>([])
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState<string | null>(null)

  const recarregar = useCallback(async () => {
    setCarregando(true)
    const [l, s] = await Promise.all([
      supabase.from('leads').select('*').order('score', { ascending: false, nullsFirst: false }),
      supabase.from('segmentos').select('*').order('tipo').order('nome'),
    ])
    setErro(l.error?.message ?? s.error?.message ?? null)
    setLeads((l.data as Lead[]) ?? [])
    setSegmentos((s.data as Segmento[]) ?? [])
    setCarregando(false)
  }, [])

  const atualizarLead = useCallback(async (id: string, campos: Partial<Lead>) => {
    const { data, error } = await supabase.from('leads').update(campos).eq('id', id).select().single()
    if (error) return error.message
    setLeads((atual) => atual.map((l) => (l.id === id ? (data as Lead) : l)))
    return null
  }, [])

  useEffect(() => {
    recarregar()
  }, [recarregar])

  return (
    <DataContext.Provider value={{ leads, segmentos, carregando, erro, recarregar, atualizarLead }}>
      {children}
    </DataContext.Provider>
  )
}

export function useData() {
  const ctx = useContext(DataContext)
  if (!ctx) throw new Error('useData fora do DataProvider')
  return ctx
}
