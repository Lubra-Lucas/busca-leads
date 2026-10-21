import type { Lead } from './types'

// Nichos das influenciadoras, gravados em leads.extras.nichos (o primeiro é o nicho_principal).
export const NICHOS = [
  'Maquiagem', 'Skincare', 'Cabelo', 'Fitness', 'Moda', 'Lifestyle',
  'UGC', 'Celebridade', 'Unhas', 'Maternidade', 'Humor/Entretenimento',
] as const

export type Nicho = (typeof NICHOS)[number]

export function nichosDoLead(lead: Lead): string[] {
  const n = lead.extras?.nichos
  return Array.isArray(n) ? n.filter((x): x is string => typeof x === 'string') : []
}

// Precisa ter TODOS os nichos marcados; lista vazia não filtra.
export function temNichos(lead: Lead, nichos: string[]): boolean {
  if (!nichos.length) return true
  const n = nichosDoLead(lead)
  return nichos.every((x) => n.includes(x))
}
