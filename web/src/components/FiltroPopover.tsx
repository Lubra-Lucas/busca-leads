import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { Check, ChevronDown, Search, X, type LucideIcon } from 'lucide-react'
import { nf } from '../lib/format'

// botão em pílula que abre um painel pequeno (no lugar dos selects nativos)
export default function FiltroPopover({ rotulo, valor, icone: Icone, onLimpar, children }: {
  rotulo: string
  valor?: string | null
  icone?: LucideIcon
  onLimpar?: () => void
  children: (fechar: () => void) => ReactNode
}) {
  const [aberto, setAberto] = useState(false)
  const [aDireita, setADireita] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!aberto) return
    const fora = (e: MouseEvent) => { if (!ref.current?.contains(e.target as Node)) setAberto(false) }
    const esc = (e: KeyboardEvent) => { if (e.key === 'Escape') setAberto(false) }
    document.addEventListener('mousedown', fora)
    document.addEventListener('keydown', esc)
    return () => { document.removeEventListener('mousedown', fora); document.removeEventListener('keydown', esc) }
  }, [aberto])

  function alternar() {
    // perto da borda direita, o painel abre para a esquerda
    const r = ref.current?.getBoundingClientRect()
    if (r) setADireita(r.left + 288 > window.innerWidth - 16)
    setAberto(!aberto)
  }

  const ativo = Boolean(valor)
  return (
    <div ref={ref} className="relative">
      <div className={`flex items-center rounded-full border text-sm transition ${
        ativo ? 'border-garnet/60 bg-garnet/10 text-ink' : 'border-white/10 bg-raised text-ink-muted hover:border-white/20 hover:text-ink'}`}>
        <button onClick={alternar} aria-expanded={aberto}
          className={`flex items-center gap-1.5 whitespace-nowrap py-1.5 pl-3 ${ativo && onLimpar ? 'pr-1' : 'pr-2.5'}`}>
          {Icone && <Icone size={14} className={ativo ? 'text-garnet' : ''} />}
          <span className={ativo ? 'text-ink-muted' : ''}>{rotulo}{ativo && ':'}</span>
          {ativo && <span className="max-w-[9rem] truncate font-medium">{valor}</span>}
          {!(ativo && onLimpar) && <ChevronDown size={14} className={`transition ${aberto ? 'rotate-180' : ''}`} />}
        </button>
        {ativo && onLimpar && (
          <button onClick={onLimpar} aria-label={`Limpar ${rotulo}`} title={`Limpar ${rotulo.toLowerCase()}`}
            className="mr-1 rounded-full p-1 text-ink-muted hover:bg-white/10 hover:text-ink">
            <X size={12} />
          </button>
        )}
      </div>
      <AnimatePresence>
        {aberto && (
          <motion.div initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -4 }} transition={{ duration: 0.12 }}
            className={`absolute top-full z-30 mt-2 w-72 max-w-[calc(100vw-2rem)] rounded-xl border border-white/10 bg-surface p-2 shadow-2xl shadow-black/50 ${
              aDireita ? 'right-0' : 'left-0'}`}>
            {children(() => setAberto(false))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export interface Opcao { id: string; nome: string; qtd: number; ponto?: string }

// lista de opções com contagem; com muitas opções, ganha busca
export function ListaOpcoes({ opcoes, valor, onEscolher, todos, buscaPlaceholder }: {
  opcoes: Opcao[]
  valor: string
  onEscolher: (id: string) => void
  todos: string
  buscaPlaceholder?: string
}) {
  const [busca, setBusca] = useState('')
  const filtradas = useMemo(() => {
    const b = busca.trim().toLowerCase()
    return b ? opcoes.filter((o) => o.nome.toLowerCase().includes(b)) : opcoes
  }, [opcoes, busca])
  const comBusca = opcoes.length > 8

  return (
    <div>
      {comBusca && (
        <div className="relative mb-2">
          <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-ink-muted" />
          <input autoFocus value={busca} onChange={(e) => setBusca(e.target.value)} placeholder={buscaPlaceholder ?? 'Buscar…'}
            className="input !py-1.5 pl-8 text-sm" />
        </div>
      )}
      <div className="max-h-72 overflow-y-auto">
        {!busca && <Item nome={todos} ativo={!valor} onClick={() => onEscolher('')} />}
        {filtradas.map((o) => (
          <Item key={o.id} nome={o.nome} qtd={o.qtd} ponto={o.ponto} ativo={valor === o.id} onClick={() => onEscolher(o.id)} />
        ))}
        {!filtradas.length && <p className="px-2 py-3 text-center text-xs text-ink-muted">Nada encontrado.</p>}
      </div>
    </div>
  )
}

function Item({ nome, qtd, ponto, ativo, onClick }: { nome: string; qtd?: number; ponto?: string; ativo: boolean; onClick: () => void }) {
  return (
    <button onClick={onClick}
      className={`flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left text-sm transition ${
        ativo ? 'bg-garnet/15 text-ink' : 'text-ink-soft hover:bg-white/5 hover:text-ink'}`}>
      {ponto && <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${ponto}`} />}
      <span className="flex-1 truncate">{nome}</span>
      {qtd != null && <span className="tabular text-xs text-ink-muted">{nf.format(qtd)}</span>}
      <Check size={14} className={`shrink-0 text-garnet ${ativo ? '' : 'invisible'}`} />
    </button>
  )
}
