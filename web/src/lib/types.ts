export type LeadTipo = 'cliente' | 'fornecedor'

export type LeadStatus =
  | 'novo'
  | 'qualificado'
  | 'contatado'
  | 'respondeu'
  | 'reuniao'
  | 'ganho'
  | 'perdido'
  | 'descartado'

export interface Segmento {
  id: string
  tipo: LeadTipo
  nome: string
  descricao: string | null
}

export interface Lead {
  id: string
  tipo: LeadTipo
  segmento_id: string
  nome: string
  contato_nome: string | null
  contato_cargo: string | null
  cidade: string | null
  uf: string | null
  site: string | null
  instagram: string | null
  instagram_seguidores: number | null
  linkedin: string | null
  email: string | null
  telefone: string | null
  whatsapp: string | null
  fonte: string
  fonte_url: string | null
  score: number | null
  status: LeadStatus
  observacoes: string | null
  created_at: string
  updated_at: string
}

export interface Interacao {
  id: string
  lead_id: string
  canal: string
  resumo: string
  created_at: string
}

export const STATUS: { id: LeadStatus; nome: string }[] = [
  { id: 'novo', nome: 'Novo' },
  { id: 'qualificado', nome: 'Qualificado' },
  { id: 'contatado', nome: 'Contatado' },
  { id: 'respondeu', nome: 'Respondeu' },
  { id: 'reuniao', nome: 'Reunião' },
  { id: 'ganho', nome: 'Ganho' },
  { id: 'perdido', nome: 'Perdido' },
  { id: 'descartado', nome: 'Descartado' },
]

export const CANAIS = ['email', 'whatsapp', 'instagram', 'linkedin', 'telefone', 'presencial', 'outro'] as const

export const temContato = (l: Lead) => Boolean(l.email || l.telefone || l.whatsapp)
