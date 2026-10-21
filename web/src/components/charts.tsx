import type { ReactNode } from 'react'
import { motion } from 'framer-motion'

// Paleta de referência (modo escuro), validada pelo skill de dataviz.
export const SERIE = { cliente: '#3987e5', fornecedor: '#d95926', investidor: '#199e70' } as const
export const AZUL = '#3987e5'
export const GRADE = '#2c2c2a'
export const EIXO = '#383835'
export const TINTA_MUDA = '#898781'

export const eixoTick = { fill: TINTA_MUDA, fontSize: 12 }

export function ChartCard({ titulo, sub, children, legenda, delay = 0 }: {
  titulo: string; sub?: string; children: ReactNode; legenda?: ReactNode; delay?: number
}) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, delay, ease: 'easeOut' }}
      className="card p-5"
    >
      <div className="mb-4 flex flex-wrap items-start justify-between gap-2">
        <div>
          <h2 className="text-sm font-medium">{titulo}</h2>
          {sub && <p className="mt-0.5 text-xs text-ink-muted">{sub}</p>}
        </div>
        {legenda}
      </div>
      {children}
    </motion.section>
  )
}

export function Legenda({ itens }: { itens: { cor: string; nome: string }[] }) {
  return (
    <div className="flex gap-4 text-xs text-ink-soft">
      {itens.map((i) => (
        <span key={i.nome} className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-sm" style={{ background: i.cor }} />
          {i.nome}
        </span>
      ))}
    </div>
  )
}

interface TooltipProps {
  active?: boolean
  payload?: { payload: Record<string, unknown> }[]
  rotulo: (p: Record<string, unknown>) => string
  valor: (p: Record<string, unknown>) => string
}

export function Dica({ active, payload, rotulo, valor }: TooltipProps) {
  if (!active || !payload?.length) return null
  const p = payload[0].payload
  return (
    <div className="rounded-lg border border-white/10 bg-raised px-3 py-2 text-xs shadow-xl">
      <div className="text-ink-soft">{rotulo(p)}</div>
      <div className="tabular mt-0.5 font-medium text-ink">{valor(p)}</div>
    </div>
  )
}
