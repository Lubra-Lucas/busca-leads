import { Ban, CalendarCheck, Circle, MessageCircle, Send, Sparkles, Trophy, XCircle, type LucideIcon } from 'lucide-react'
import type { LeadStatus } from './types'

// fases que a usuária entende; cada fase agrupa etapas do funil
export type FaseId = 'nao_contatado' | 'aguardando' | 'andamento' | 'fechado' | 'encerrado'

export const FASES: { id: FaseId; nome: string; status: LeadStatus[] }[] = [
  { id: 'nao_contatado', nome: 'Não contatado', status: ['novo', 'qualificado'] },
  { id: 'aguardando', nome: 'Contatado / aguardando', status: ['contatado'] },
  { id: 'andamento', nome: 'Em andamento', status: ['respondeu', 'reuniao'] },
  { id: 'fechado', nome: 'Fechado', status: ['ganho'] },
  { id: 'encerrado', nome: 'Encerrado', status: ['perdido', 'descartado'] },
]

// nome curto para os chips de filtro
export const FASE_CURTA: Record<FaseId, string> = {
  nao_contatado: 'Não contatado',
  aguardando: 'Contatado',
  andamento: 'Em andamento',
  fechado: 'Fechado',
  encerrado: 'Encerrado',
}

export const faseDe = (s: LeadStatus): FaseId => FASES.find((f) => f.status.includes(s))!.id

export interface EstiloStatus {
  icone: LucideIcon
  /** classes do badge (borda, fundo, texto) */
  badge: string
  /** cor do ponto */
  ponto: string
  /** cor do ícone/texto quando selecionado na ficha */
  ativo: string
}

export const ESTILO_STATUS: Record<LeadStatus, EstiloStatus> = {
  novo: { icone: Circle, badge: 'border-zinc-500/30 bg-zinc-500/10 text-zinc-300', ponto: 'bg-zinc-400', ativo: 'border-zinc-400/60 bg-zinc-500/20 text-zinc-100' },
  qualificado: { icone: Sparkles, badge: 'border-sky-400/30 bg-sky-400/10 text-sky-300', ponto: 'bg-sky-400', ativo: 'border-sky-400/60 bg-sky-400/20 text-sky-100' },
  contatado: { icone: Send, badge: 'border-amber-400/30 bg-amber-400/10 text-amber-300', ponto: 'bg-amber-400', ativo: 'border-amber-400/60 bg-amber-400/20 text-amber-100' },
  respondeu: { icone: MessageCircle, badge: 'border-violet-400/30 bg-violet-400/10 text-violet-300', ponto: 'bg-violet-400', ativo: 'border-violet-400/60 bg-violet-400/20 text-violet-100' },
  reuniao: { icone: CalendarCheck, badge: 'border-violet-400/30 bg-violet-400/10 text-violet-300', ponto: 'bg-violet-400', ativo: 'border-violet-400/60 bg-violet-400/20 text-violet-100' },
  ganho: { icone: Trophy, badge: 'border-emerald-400/30 bg-emerald-400/10 text-emerald-300', ponto: 'bg-emerald-400', ativo: 'border-emerald-400/60 bg-emerald-400/20 text-emerald-100' },
  perdido: { icone: XCircle, badge: 'border-red-400/20 bg-red-400/10 text-red-300/80', ponto: 'bg-red-400/70', ativo: 'border-red-400/50 bg-red-400/15 text-red-200' },
  descartado: { icone: Ban, badge: 'border-red-400/20 bg-red-400/10 text-red-300/80', ponto: 'bg-red-400/70', ativo: 'border-red-400/50 bg-red-400/15 text-red-200' },
}

// cor do ponto de cada fase (chips de filtro)
export const PONTO_FASE: Record<FaseId, string> = {
  nao_contatado: 'bg-zinc-400',
  aguardando: 'bg-amber-400',
  andamento: 'bg-violet-400',
  fechado: 'bg-emerald-400',
  encerrado: 'bg-red-400/70',
}

// cor do avatar derivada do nome: sempre a mesma para o mesmo nome
const MATIZES = [350, 24, 45, 150, 175, 200, 225, 265, 290]
export function corAvatar(nome: string) {
  let h = 0
  for (const c of nome) h = (h * 31 + c.charCodeAt(0)) >>> 0
  const m = MATIZES[h % MATIZES.length]
  return { backgroundColor: `hsl(${m} 35% 24%)`, color: `hsl(${m} 60% 80%)` }
}

export function iniciais(nome: string) {
  const p = nome.replace(/[^\p{L}\s]/gu, ' ').split(/\s+/).filter(Boolean)
  if (!p.length) return '?'
  return (p.length === 1 ? p[0].slice(0, 2) : p[0][0] + p[p.length - 1][0]).toUpperCase()
}
