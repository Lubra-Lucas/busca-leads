import type { Lead } from './types'

export const nf = new Intl.NumberFormat('pt-BR')

// 1.250.000 -> "1,3 mi" · 350.000 -> "350 mil"
export const nfCompacto = new Intl.NumberFormat('pt-BR', { notation: 'compact', maximumFractionDigits: 1 })

export function urlDe(site: string) {
  return /^https?:\/\//.test(site) ? site : `https://${site}`
}

export function instagramUrl(handle: string) {
  return `https://instagram.com/${handle.replace(/^@/, '')}`
}

export function tiktokUrl(handle: string) {
  return `https://www.tiktok.com/@${handle.replace(/^@/, '')}`
}

export function whatsappUrl(numero: string) {
  let digitos = numero.replace(/\D/g, '')
  if (digitos.length <= 11) digitos = `55${digitos}`
  return `https://wa.me/${digitos}`
}

export function scoreTom(score: number | null) {
  if (score == null) return 'text-ink-muted'
  if (score >= 80) return 'text-emerald-400'
  if (score >= 60) return 'text-amber-300'
  return 'text-ink-soft'
}

const COLUNAS: (keyof Lead)[] = [
  'nome', 'tipo', 'segmento_id', 'subsegmento', 'status', 'score', 'cidade', 'uf', 'bairro', 'endereco',
  'contato_nome', 'contato_cargo', 'email', 'telefone', 'whatsapp', 'site', 'instagram', 'tiktok', 'seguidores',
  'linkedin', 'fonte', 'fonte_url', 'observacoes',
]

export function baixarCsv(leads: Lead[]) {
  const esc = (v: unknown) => {
    const s = v == null ? '' : String(v)
    return /[";\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s
  }
  // ";" e BOM: abre direto no Excel em português
  const linhas = [COLUNAS.join(';'), ...leads.map((l) => COLUNAS.map((c) => esc(l[c])).join(';'))]
  const blob = new Blob(['﻿' + linhas.join('\n')], { type: 'text/csv;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `leads-${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(a.href)
}
