import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { Briefcase, ChevronLeft, ChevronRight, Download, Mail, MessageCircle, Phone, Search, X } from 'lucide-react'
import LeadDrawer from '../components/LeadDrawer'
import { useData } from '../lib/data'
import { STATUS, temContato, type LeadTipo } from '../lib/types'
import { baixarCsv, nf, nfCompacto, scoreTom } from '../lib/format'

const POR_PAGINA = 50

const TIPOS: { id: '' | LeadTipo; nome: string }[] = [
  { id: '', nome: 'Todos' },
  { id: 'cliente', nome: 'Clientes' },
  { id: 'fornecedor', nome: 'Fornecedores' },
]

export default function Leads() {
  const { leads, segmentos } = useData()
  const [params, setParams] = useSearchParams()

  // filtros ficam na URL: dá para voltar, compartilhar e chegar aqui pelos gráficos
  const f = {
    q: params.get('q') ?? '',
    tipo: (params.get('tipo') ?? '') as '' | LeadTipo,
    segmento: params.get('segmento') ?? '',
    status: params.get('status') ?? '',
    uf: params.get('uf') ?? '',
    cidade: params.get('cidade') ?? '',
    scoreMin: Number(params.get('scoreMin') ?? 0),
    contato: params.get('contato') === '1',
  }
  const leadAberto = params.get('lead')

  function set(campo: string, valor: string) {
    const p = new URLSearchParams(params)
    if (valor) p.set(campo, valor)
    else p.delete(campo)
    if (campo === 'tipo') p.delete('segmento')
    setParams(p, { replace: campo === 'q' })
  }

  const ufs = useMemo(() => [...new Set(leads.map((l) => l.uf).filter(Boolean))].sort() as string[], [leads])
  const cidades = useMemo(
    () => [...new Set(leads.filter((l) => !f.uf || l.uf === f.uf).map((l) => l.cidade).filter(Boolean))].sort() as string[],
    [leads, f.uf],
  )
  const segsVisiveis = segmentos.filter((s) => !f.tipo || s.tipo === f.tipo)
  const nomeSeg = (id: string) => segmentos.find((s) => s.id === id)?.nome ?? id
  // filtrando influenciadoras, a coluna de segmento seria repetida: mostra seguidores no lugar
  const verSeguidores = f.segmento === 'influenciadora'

  const filtrados = useMemo(() => {
    const q = f.q.trim().toLowerCase()
    return leads.filter(
      (l) =>
        (!f.tipo || l.tipo === f.tipo) &&
        (!f.segmento || l.segmento_id === f.segmento) &&
        (!f.status || l.status === f.status) &&
        (!f.uf || l.uf === f.uf) &&
        (!f.cidade || l.cidade === f.cidade) &&
        (l.score ?? 0) >= f.scoreMin &&
        (!f.contato || temContato(l)) &&
        (!q || [l.nome, l.contato_nome, l.observacoes, l.cidade, l.bairro, l.instagram, l.tiktok, l.email, l.subsegmento]
          .some((v) => v?.toLowerCase().includes(q))),
    )
  }, [leads, f.q, f.tipo, f.segmento, f.status, f.uf, f.cidade, f.scoreMin, f.contato])

  const [pagina, setPagina] = useState(0)
  useEffect(() => setPagina(0), [filtrados])
  const paginas = Math.max(1, Math.ceil(filtrados.length / POR_PAGINA))
  const visiveis = filtrados.slice(pagina * POR_PAGINA, (pagina + 1) * POR_PAGINA)

  const temFiltro = [...params.keys()].some((k) => k !== 'lead')
  const lead = leads.find((l) => l.id === leadAberto) ?? null

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Leads</h1>
          <p className="mt-1 text-sm text-ink-muted">
            <span className="tabular text-ink">{nf.format(filtrados.length)}</span> de {nf.format(leads.length)} leads
          </p>
        </div>
        <button onClick={() => baixarCsv(filtrados)} className="btn-ghost" disabled={!filtrados.length}>
          <Download size={15} /> Exportar CSV
        </button>
      </div>

      <div className="card space-y-3 p-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative min-w-[220px] flex-1">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-muted" />
            <input className="input pl-9" placeholder="Buscar por nome, cidade, observação…" value={f.q}
              onChange={(e) => set('q', e.target.value)} />
          </div>
          <div className="flex rounded-lg border border-white/10 bg-raised p-0.5">
            {TIPOS.map((t) => (
              <button key={t.id} onClick={() => set('tipo', t.id)}
                className={`relative rounded-md px-3 py-1.5 text-sm transition ${f.tipo === t.id ? 'text-ink' : 'text-ink-muted hover:text-ink'}`}>
                {f.tipo === t.id && (
                  <motion.span layoutId="tipo-ativo" className="absolute inset-0 rounded-md bg-white/10"
                    transition={{ type: 'spring', stiffness: 400, damping: 32 }} />
                )}
                <span className="relative">{t.nome}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-6">
          <select className="input" value={f.segmento} onChange={(e) => set('segmento', e.target.value)}>
            <option value="">Todos os segmentos</option>
            {segsVisiveis.map((s) => <option key={s.id} value={s.id}>{s.nome}</option>)}
          </select>
          <select className="input" value={f.status} onChange={(e) => set('status', e.target.value)}>
            <option value="">Todos os status</option>
            {STATUS.map((s) => <option key={s.id} value={s.id}>{s.nome}</option>)}
          </select>
          <select className="input" value={f.uf} onChange={(e) => { set('uf', e.target.value) }}>
            <option value="">Todos os estados</option>
            {ufs.map((u) => <option key={u} value={u}>{u}</option>)}
          </select>
          <select className="input" value={f.cidade} onChange={(e) => set('cidade', e.target.value)}>
            <option value="">Todas as cidades</option>
            {cidades.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
          <label className="flex items-center gap-3 rounded-lg border border-white/10 bg-raised px-3 py-2 text-sm">
            <span className="whitespace-nowrap text-ink-muted">Score ≥</span>
            <input type="range" min={0} max={100} step={5} value={f.scoreMin}
              onChange={(e) => set('scoreMin', e.target.value === '0' ? '' : e.target.value)} className="w-full accent-garnet" />
            <span className="tabular w-6 text-right">{f.scoreMin}</span>
          </label>
          <label className="flex cursor-pointer items-center gap-2 rounded-lg border border-white/10 bg-raised px-3 py-2 text-sm">
            <input type="checkbox" checked={f.contato} onChange={(e) => set('contato', e.target.checked ? '1' : '')}
              className="accent-garnet" />
            Só com contato
          </label>
        </div>

        {temFiltro && (
          <button onClick={() => setParams({})} className="flex items-center gap-1 text-xs text-ink-muted hover:text-ink">
            <X size={13} /> Limpar filtros
          </button>
        )}
      </div>

      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/10 text-left text-xs text-ink-muted">
                <th className="px-4 py-3 font-medium">Nome</th>
                <th className={`px-4 py-3 font-medium ${verSeguidores ? 'text-right' : ''}`}>{verSeguidores ? 'Seguidores' : 'Segmento'}</th>
                {verSeguidores && <th className="px-4 py-3 text-right font-medium" title="Média dos últimos 12 Reels">Média de views</th>}
                {!verSeguidores && <th className="hidden px-4 py-3 font-medium md:table-cell">Local</th>}
                <th className="px-4 py-3 font-medium">Contato</th>
                <th className="hidden px-4 py-3 font-medium sm:table-cell">Status</th>
                <th className="px-4 py-3 text-right font-medium">Score</th>
              </tr>
            </thead>
            <tbody>
              <AnimatePresence initial={false} mode="popLayout">
                {visiveis.map((l) => (
                  <motion.tr key={l.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                    onClick={() => set('lead', l.id)}
                    className="cursor-pointer border-b border-white/5 transition hover:bg-white/[0.03]">
                    <td className="px-4 py-3">
                      <div className="font-medium">{l.nome}</div>
                      <div className="text-xs text-ink-muted">{l.subsegmento ?? (l.tipo === 'cliente' ? 'Cliente' : 'Fornecedor')}</div>
                    </td>
                    {verSeguidores ? (
                      <td className="tabular px-4 py-3 text-right" title={l.seguidores ? nf.format(l.seguidores) : undefined}>
                        {l.seguidores ? (
                          <>
                            <span className="font-medium">{nfCompacto.format(l.seguidores)}</span>
                            {(l.extras?.plataforma as string | undefined) && (
                              <span className="ml-1.5 text-xs text-ink-muted">{String(l.extras.plataforma)}</span>
                            )}
                          </>
                        ) : <span className="text-ink-muted">—</span>}
                      </td>
                    ) : (
                      <td className="px-4 py-3 text-ink-soft">{nomeSeg(l.segmento_id)}</td>
                    )}
                    {verSeguidores && <td className="tabular px-4 py-3 text-right"><MediaViews valor={l.extras?.media_views_reels} /></td>}
{!verSeguidores && (
                    <td className="hidden px-4 py-3 text-ink-soft md:table-cell">
                      {[l.cidade, l.uf].filter(Boolean).join(' / ') || <span className="text-ink-muted">—</span>}
                    </td>
                    )}
                    <td className="px-4 py-3">
                      <div className="flex gap-2 text-ink-muted">
                        <Mail size={15} className={l.email ? 'text-ink' : 'opacity-30'} />
                        <MessageCircle size={15} className={l.whatsapp ? 'text-ink' : 'opacity-30'} />
                        <Phone size={15} className={l.telefone ? 'text-ink' : 'opacity-30'} />
                        <Briefcase size={15} className={l.linkedin ? 'text-ink' : 'opacity-30'} />
                      </div>
                    </td>
                    <td className="hidden px-4 py-3 sm:table-cell">
                      <span className="rounded-full border border-white/10 px-2 py-0.5 text-xs text-ink-soft">
                        {STATUS.find((s) => s.id === l.status)?.nome}
                      </span>
                    </td>
                    <td className={`tabular px-4 py-3 text-right font-semibold ${scoreTom(l.score)}`}>{l.score ?? '—'}</td>
                  </motion.tr>
                ))}
              </AnimatePresence>
            </tbody>
          </table>
          {!filtrados.length && <p className="p-8 text-center text-sm text-ink-muted">Nenhum lead com esses filtros.</p>}
        </div>
        {paginas > 1 && (
          <div className="flex items-center justify-between border-t border-white/10 px-4 py-3 text-sm text-ink-muted">
            <span className="tabular">
              {pagina * POR_PAGINA + 1}–{Math.min((pagina + 1) * POR_PAGINA, filtrados.length)} de {nf.format(filtrados.length)}
            </span>
            <div className="flex items-center gap-2">
              <button className="btn-ghost px-2" disabled={pagina === 0} onClick={() => setPagina(pagina - 1)}><ChevronLeft size={15} /></button>
              <span className="tabular">{pagina + 1} / {paginas}</span>
              <button className="btn-ghost px-2" disabled={pagina >= paginas - 1} onClick={() => setPagina(pagina + 1)}><ChevronRight size={15} /></button>
            </div>
          </div>
        )}
      </div>

      <LeadDrawer lead={lead} onClose={() => set('lead', '')} />
    </div>
  )
}

function MediaViews({ valor }: { valor: unknown }) {
  const n = typeof valor === 'number' ? valor : Number(valor)
  if (!valor || !Number.isFinite(n)) return <span className="text-ink-muted">—</span>
  return <span title={`${nf.format(n)} views em média nos últimos 12 Reels`}>{nfCompacto.format(n)}</span>
}
