import type { Lead } from '../lib/types'
import { NICHOS } from '../lib/nichos'

// PROVISÓRIO: versão mínima até a definitiva chegar
export default function NichoFiltro({ leads, selecionados, onChange }: { leads: Lead[]; selecionados: string[]; onChange: (nichos: string[]) => void }) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {NICHOS.map((n) => {
        const on = selecionados.includes(n)
        const qtd = leads.filter((l) => (l.extras?.nichos as string[] | undefined)?.includes(n)).length
        return (
          <button key={n} onClick={() => onChange(on ? selecionados.filter((x) => x !== n) : [...selecionados, n])}
            className={`rounded-full border px-3 py-1 text-xs ${on ? 'border-garnet bg-garnet/15' : 'border-white/10 text-ink-muted'}`}>
            {n} {qtd}
          </button>
        )
      })}
    </div>
  )
}
