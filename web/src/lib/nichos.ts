import type { Lead } from './types'

// PROVISÓRIO: versão mínima até a definitiva chegar
export const NICHOS: string[] = ['Maquiagem', 'Cabelo', 'Skincare']

export function temNichos(lead: Lead, nichos: string[]): boolean {
  const n = (lead.extras?.nichos as string[] | undefined) ?? []
  return nichos.every((x) => n.includes(x))
}
