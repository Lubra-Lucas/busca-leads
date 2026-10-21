import { motion } from 'framer-motion'
import { FlaskConical, Handshake, Landmark, Megaphone, Package, Palette, Shirt, Sparkles, Store, Tag, type LucideIcon } from 'lucide-react'
import { nf } from '../lib/format'
import { TIPO_NOME, type Segmento } from '../lib/types'

const ICONES: Record<string, LucideIcon> = {
  'Influência': Sparkles,
  'Marcas de beleza': Palette,
  'Moda': Shirt,
  'Varejo e salões': Store,
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

export default function CategoriaNav({ categorias, contagem, cat, segmento, mostrarTipo, onCategoria, onSegmento }: {
  categorias: Categoria[]
  contagem: Record<string, number>
  cat: string
  segmento: string
  mostrarTipo: boolean
  onCategoria: (nome: string) => void
  onSegmento: (cat: string, id: string) => void
}) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      {categorias.map((c, i) => {
        const Icone = ICONES[c.nome] ?? Tag
        const total = c.segmentos.reduce((n, s) => n + (contagem[s.id] ?? 0), 0)
        const ativa = cat === c.nome
        return (
          <motion.div key={c.nome}
            initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3, delay: i * 0.03 }}
            onClick={() => onCategoria(ativa ? '' : c.nome)}
            className={`cursor-pointer rounded-xl border p-3.5 transition ${
              ativa ? 'border-garnet/70 bg-garnet/10' : 'border-white/10 bg-raised hover:border-white/20'}`}>
            <div className="flex items-start justify-between gap-2">
              <div className="flex items-center gap-2.5">
                <span className={`grid h-8 w-8 place-items-center rounded-lg ${ativa ? 'bg-garnet/20 text-garnet' : 'bg-white/5 text-ink-soft'}`}>
                  <Icone size={16} />
                </span>
                <div>
                  <div className="text-sm font-medium leading-tight">{c.nome}</div>
                  {mostrarTipo && <div className="text-[11px] text-ink-muted">{TIPO_NOME[c.tipo]}</div>}
                </div>
              </div>
              <span className="tabular text-lg font-semibold">{nf.format(total)}</span>
            </div>
            {c.segmentos.length > 1 && (
              <div className="mt-3 flex flex-wrap gap-1.5">
                {c.segmentos.map((s) => (
                  <button key={s.id}
                    onClick={(e) => { e.stopPropagation(); onSegmento(c.nome, segmento === s.id ? '' : s.id) }}
                    className={`rounded-full border px-2 py-0.5 text-[11px] transition ${
                      segmento === s.id ? 'border-garnet bg-garnet/15 text-ink' : 'border-white/10 text-ink-muted hover:text-ink'}`}>
                    {s.nome} <span className="tabular opacity-70">{nf.format(contagem[s.id] ?? 0)}</span>
                  </button>
                ))}
              </div>
            )}
          </motion.div>
        )
      })}
    </div>
  )
}
