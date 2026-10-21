import { ESTILO_STATUS } from '../lib/status'
import { STATUS, type LeadStatus } from '../lib/types'

// status é estado: sempre ponto/ícone + texto, nunca só cor
export default function StatusBadge({ status, comIcone = false }: { status: LeadStatus; comIcone?: boolean }) {
  const e = ESTILO_STATUS[status]
  if (!e) return null
  const Icone = e.icone
  return (
    <span className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-full border px-2 py-0.5 text-xs font-medium ${e.badge}`}>
      {comIcone ? <Icone size={12} /> : <span className={`h-1.5 w-1.5 rounded-full ${e.ponto}`} />}
      {STATUS.find((s) => s.id === status)?.nome}
    </span>
  )
}
