import { useMemo } from 'react'
import type { Lead } from '../lib/types'
import { NICHOS, nichosDoLead } from '../lib/nichos'

export default function NichoFiltro({ leads, selecionados, onChange }: {
  leads: Lead[]
  selecionados: string[]
  onChange: (nichos: string[]) => void
}) {
  const contagem = useMemo(() => {
    const c = new Map<string, number>()
    for (const l of leads) for (const n of nichosDoLead(l)) c.set(n, (c.get(n) ?? 0) + 1)
    return c
  }, [leads])

  const visiveis = NICHOS.filter((n) => (contagem.get(n) ?? 0) > 0 || selecionados.includes(n))
  if (!visiveis.length) return null

  return (
    <div className="flex flex-wrap items-center gap-1.5" title="Mostra quem tem TODOS os nichos marcados">
      <span className="mr-1 text-xs text-ink-muted">Nicho</span>
      {visiveis.map((n) => {
        const on = selecionados.includes(n)
        return (
          <button
            key={n}
            onClick={() => onChange(on ? selecionados.filter((x) => x !== n) : [...selecionados, n])}
            className={`rounded-full border px-2.5 py-1 text-xs transition ${on ? 'border-garnet bg-garnet/15 text-ink' : 'border-white/10 text-ink-muted hover:text-ink'}`}
          >
            {n} <span className="tabular opacity-70">{contagem.get(n) ?? 0}</span>
          </button>
        )
      })}
    </div>
  )
}
