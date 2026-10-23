import { motion } from 'framer-motion'
import { Factory, FlaskConical, Handshake, Landmark, Megaphone, Package, Palette, Shirt, Sparkles, Store, Tag, Truck, type LucideIcon } from 'lucide-react'
import { nf } from '../lib/format'
import { TIPO_NOME, type Segmento } from '../lib/types'

const ICONES: Record<string, LucideIcon> = {
  'Influência': Sparkles,
  'Marcas de beleza': Palette,
  'Concorrentes': Factory,
  'Moda': Shirt,
  'Varejo e salões': Store,
  'Distribuição': Truck,
  'Embalagens': Package,
  'Insumos e fragrâncias': FlaskConical,
  'Estratégicos': Handshake,
  'Mídia por participação': Megaphone,
  'Fundos e anjos': Landmark,
}

export interface Categoria {
  nome: string
  tipo: Segmento['tipo']
  segmentos: Segmento[]
}

// agrupa os segmentos (já ordenados por "ordem") nas categorias, mantendo a ordem
export function agruparCategorias(segmentos: Segmento[]): Categoria[] {
  const mapa = new Map<string, Categoria>()
  for (const s of segmentos) {
    const nome = s.categoria ?? s.nome
    if (!mapa.has(nome)) mapa.set(nome, { nome, tipo: s.tipo, segmentos: [] })
    mapa.get(nome)!.segmentos.push(s)
  }
  return [...mapa.values()]
}

// passo 1: só a categoria. Os segmentos dela aparecem como etapas logo acima da tabela.
export default function CategoriaNav({ categorias, contagem, cat, mostrarTipo, onCategoria }: {
  categorias: Categoria[]
  contagem: Record<string, number>
  cat: string
  mostrarTipo: boolean
  onCategoria: (nome: string) => void
}) {
  return (
    <div className="-mx-1 flex gap-2 overflow-x-auto px-1 pb-1 sm:mx-0 sm:grid sm:grid-cols-[repeat(auto-fill,minmax(15.5rem,1fr))] sm:overflow-visible sm:px-0 sm:pb-0">
      {categorias.map((c, i) => {
        const Icone = ICONES[c.nome] ?? Tag
        const total = c.segmentos.reduce((n, s) => n + (contagem[s.id] ?? 0), 0)
        const ativa = cat === c.nome
        const sub = [mostrarTipo && TIPO_NOME[c.tipo], c.segmentos.length > 1 && `${c.segmentos.length} segmentos`].filter(Boolean).join(' · ')
        return (
          <motion.button key={c.nome} type="button" aria-pressed={ativa}
            initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25, delay: i * 0.025 }}
            onClick={() => onCategoria(ativa ? '' : c.nome)}
            className={`group flex w-64 shrink-0 items-center gap-2.5 rounded-xl border px-3 py-2.5 sm:w-auto sm:min-w-0 text-left transition ${
              ativa ? 'border-garnet/70 bg-garnet/10' : 'border-white/10 bg-raised hover:border-white/20'}`}>
            <span className={`grid h-8 w-8 shrink-0 place-items-center rounded-lg transition ${
              ativa ? 'bg-garnet/20 text-garnet' : 'bg-white/5 text-ink-soft group-hover:text-ink'}`}>
              <Icone size={16} />
            </span>
            <span className="min-w-0 flex-1">
              <span className="block truncate text-sm font-medium leading-tight" title={c.nome}>{c.nome}</span>
              {sub && <span className="block truncate text-[11px] text-ink-muted">{sub}</span>}
            </span>
            <span className={`tabular shrink-0 text-sm font-semibold ${total ? '' : 'text-ink-muted'}`}>{nf.format(total)}</span>
          </motion.button>
        )
      })}
    </div>
  )
}
