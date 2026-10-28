import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from 'react'
import { supabase } from './supabase'
import { useAuth } from './auth'
import type { Favorito, Lead, Segmento } from './types'

interface DataState {
  leads: Lead[]
  segmentos: Segmento[]
  carregando: boolean
  erro: string | null
  recarregar: () => Promise<void>
  atualizarLead: (id: string, campos: Partial<Lead>) => Promise<string | null>
  favoritos: Map<string, Favorito>
  alternarFavorito: (leadId: string) => Promise<string | null>
  salvarNota: (leadId: string, nota: string) => Promise<string | null>
}

const DataContext = createContext<DataState | null>(null)

// o Supabase devolve no máximo 1000 linhas por consulta: busca em páginas
async function buscarTodos() {
  const dados: Lead[] = []
  const PAGINA = 1000
  for (let de = 0; ; de += PAGINA) {
    const { data, error } = await supabase.from('leads').select('*')
      .order('score', { ascending: false, nullsFirst: false }).order('id').range(de, de + PAGINA - 1)
    if (error) return { dados, erro: error.message }
    dados.push(...(data as Lead[]))
    if (data.length < PAGINA) return { dados, erro: null }
  }
}

export function DataProvider({ children }: { children: ReactNode }) {
  const [leads, setLeads] = useState<Lead[]>([])
  const [segmentos, setSegmentos] = useState<Segmento[]>([])
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState<string | null>(null)
  const { session } = useAuth()
  const userId = session?.user.id
  const [favoritos, setFavoritos] = useState<Map<string, Favorito>>(new Map())
  const favRef = useRef(favoritos)
  favRef.current = favoritos

  const recarregar = useCallback(async () => {
    setCarregando(true)
    const [l, s, f] = await Promise.all([
      buscarTodos(),
      supabase.from('segmentos').select('*').order('ordem').order('nome'),
      supabase.from('favoritos').select('lead_id, nota, created_at, updated_at'),
    ])
    // favoritos são um extra: se falharem, a lista de leads continua funcionando
    setFavoritos(new Map(((f.data as (Favorito & { lead_id: string })[] | null) ?? []).map(({ lead_id, ...fav }) => [lead_id, fav])))
    setErro(l.erro ?? s.error?.message ?? null)
    setLeads(l.dados)
    setSegmentos((s.data as Segmento[]) ?? [])
    setCarregando(false)
  }, [])

  const atualizarLead = useCallback(async (id: string, campos: Partial<Lead>) => {
    const { data, error } = await supabase.from('leads').update(campos).eq('id', id).select().single()
    if (error) return error.message
    setLeads((atual) => atual.map((l) => (l.id === id ? (data as Lead) : l)))
    return null
  }, [])

  // aplica a mudança na tela já e desfaz se o banco recusar
  const otimista = useCallback(async (leadId: string, novo: Favorito | null, gravar: () => PromiseLike<{ error: { message: string } | null }>) => {
    const antes = favRef.current.get(leadId)
    const aplicar = (v: Favorito | undefined) => setFavoritos((m) => {
      const n = new Map(m)
      if (v) n.set(leadId, v)
      else n.delete(leadId)
      return n
    })
    aplicar(novo ?? undefined)
    const { error } = await gravar()
    if (error) { aplicar(antes); return error.message }
    return null
  }, [])

  const alternarFavorito = useCallback(async (leadId: string) => {
    const atual = favRef.current.get(leadId)
    if (atual) return otimista(leadId, null, () => supabase.from('favoritos').delete().eq('lead_id', leadId))
    if (!userId) return 'Sessão expirada'
    const agora = new Date().toISOString()
    return otimista(leadId, { nota: null, created_at: agora, updated_at: agora },
      () => supabase.from('favoritos').upsert({ user_id: userId, lead_id: leadId }, { onConflict: 'user_id,lead_id' }))
  }, [otimista, userId])

  // salvar a nota de um lead que ainda não é favorito já o marca como favorito
  const salvarNota = useCallback(async (leadId: string, nota: string) => {
    if (!userId) return 'Sessão expirada'
    const atual = favRef.current.get(leadId)
    const agora = new Date().toISOString()
    const texto = nota.trim() || null
    return otimista(leadId, { nota: texto, created_at: atual?.created_at ?? agora, updated_at: agora },
      () => supabase.from('favoritos').upsert({ user_id: userId, lead_id: leadId, nota: texto, updated_at: agora }, { onConflict: 'user_id,lead_id' }))
  }, [otimista, userId])

  // recarrega ao entrar ou sair: a leitura pública não traz investidores nem salvos
  useEffect(() => {
    recarregar()
  }, [recarregar, userId])

  return (
    <DataContext.Provider value={{ leads, segmentos, carregando, erro, recarregar, atualizarLead, favoritos, alternarFavorito, salvarNota }}>
      {children}
    </DataContext.Provider>
  )
}

export function useData() {
  const ctx = useContext(DataContext)
  if (!ctx) throw new Error('useData fora do DataProvider')
  return ctx
}
