import { Fragment, useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowDown, AtSign, Briefcase, Check, ChevronLeft, ChevronRight, CircleDot, Download, Gauge, Mail, MapPin, MessageCircle, Music2, Phone, Search, ShoppingBag, Star, StickyNote, X, type LucideIcon } from 'lucide-react'
import CategoriaNav, { agruparCategorias } from '../components/CategoriaNav'
import FiltroPopover, { ListaOpcoes } from '../components/FiltroPopover'
import LeadDrawer from '../components/LeadDrawer'
import NichoFiltro from '../components/NichoFiltro'
import StatusBadge from '../components/StatusBadge'
import { useData } from '../lib/data'
import { STATUS, TIPO_NOME, temContato, vendeNoTikTokShop, type Lead, type LeadTipo } from '../lib/types'
import { FASES, FASE_CURTA, PONTO_FASE, corAvatar, faseDe, iniciais, type FaseId } from '../lib/status'
import { temNichos } from '../lib/nichos'
import { baixarCsv, instagramUrl, nf, nfCompacto, scorePilula, tiktokUrl, urlDe, whatsappUrl } from '../lib/format'

const POR_PAGINA = 50

const numero = (v: unknown) => (v == null || v === '' || !Number.isFinite(Number(v)) ? null : Number(v))
const ORDENS: Record<string, (l: Lead) => number | null> = {
  seguidores: (l) => l.seguidores,
  views: (l) => numero(l.extras?.media_views_reels),
}

const TIPOS: { id: '' | LeadTipo; nome: string }[] = [
  { id: '', nome: 'Todos' },
  { id: 'cliente', nome: 'Clientes' },
  { id: 'fornecedor', nome: 'Fornecedores' },
  { id: 'investidor', nome: 'Investidores' },
]

export default function Leads() {
  const { leads, segmentos, favoritos, alternarFavorito, salvarNota } = useData()
  const [notaAberta, setNotaAberta] = useState<string | null>(null)
  const [erroFav, setErroFav] = useState<string | null>(null)
  const [params, setParams] = useSearchParams()

  // filtros ficam na URL: dá para voltar, compartilhar e chegar aqui pelos gráficos
  const f = {
    q: params.get('q') ?? '',
    tipo: (params.get('tipo') ?? '') as '' | LeadTipo,
    cat: params.get('cat') ?? '',
    segmento: params.get('segmento') ?? '',
    status: params.get('status') ?? '',
    fase: params.get('fase') ?? '',
    nichos: (params.get('nichos') ?? '').split(',').filter(Boolean),
    uf: params.get('uf') ?? '',
    cidade: params.get('cidade') ?? '',
    scoreMin: Number(params.get('scoreMin') ?? 0),
    contato: params.get('contato') === '1',
    ordem: params.get('ordem') ?? '',
    tiktokShop: params.get('tiktokshop') === '1',
    salvos: params.get('salvos') === '1',
  }
  const leadAberto = params.get('lead')

  function set(campo: string, valor: string) {
    const p = new URLSearchParams(params)
    if (valor) p.set(campo, valor)
    else p.delete(campo)
    if (campo === 'tipo') { p.delete('cat'); p.delete('segmento') }
    if (campo === 'cat') p.delete('segmento')
    if (campo === 'tipo' || campo === 'cat' || campo === 'segmento') { p.delete('ordem'); p.delete('nichos') }
    if (campo === 'uf') p.delete('cidade')
    setParams(p, { replace: campo === 'q' })
  }

  const segInfo = useMemo(() => Object.fromEntries(segmentos.map((s) => [s.id, s])), [segmentos])
  const categorias = useMemo(() => agruparCategorias(segmentos.filter((s) => !f.tipo || s.tipo === f.tipo)), [segmentos, f.tipo])
  const nomeSeg = (id: string) => segInfo[id]?.nome ?? id
  const catDe = (id: string) => segInfo[id]?.categoria ?? segInfo[id]?.nome ?? ''
  const catAtual = categorias.find((c) => c.nome === f.cat)
  // filtrando influenciadoras, a coluna de segmento seria repetida: mostra seguidores no lugar
  const verSeguidores = f.segmento === 'influenciadora'
  // nicho é o passo seguinte a escolher "Influenciadoras"
  const verNichos = verSeguidores
  const nichosAtivos = verNichos ? f.nichos : []

  // um filtro só, com a opção de ignorar alguns campos (para as contagens de cada controle)
  const chave = [...params].filter(([k]) => k !== 'lead').map((x) => x.join('=')).join('&')
  const passa = useMemo(() => {
    const q = f.q.trim().toLowerCase()
    return (l: Lead, sem: string[] = []) => {
      const usa = (c: string) => !sem.includes(c)
      return (!f.tipo || l.tipo === f.tipo) &&
        (!usa('status') || !f.status || l.status === f.status) &&
        (!usa('fase') || !f.fase || faseDe(l.status) === f.fase) &&
        (!usa('uf') || !f.uf || l.uf === f.uf) &&
        (!usa('cidade') || !f.cidade || l.cidade === f.cidade) &&
        (l.score ?? 0) >= f.scoreMin &&
        (!f.contato || temContato(l)) &&
        (!f.tiktokShop || vendeNoTikTokShop(l)) &&
        (!f.salvos || favoritos.has(l.id)) &&
        (!usa('cat') || !f.cat || catDe(l.segmento_id) === f.cat) &&
        (!usa('segmento') || !f.segmento || l.segmento_id === f.segmento) &&
        (!usa('nichos') || !nichosAtivos.length || temNichos(l, nichosAtivos)) &&
        (!q || [l.nome, l.contato_nome, l.observacoes, l.cidade, l.bairro, l.instagram, l.tiktok, l.email, l.subsegmento]
          .some((v) => v?.toLowerCase().includes(q)))
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chave, favoritos, segInfo])

  const contar = (lista: Lead[], campo: (l: Lead) => string | null) => {
    const c: Record<string, number> = {}
    for (const l of lista) { const k = campo(l); if (k) c[k] = (c[k] ?? 0) + 1 }
    return c
  }

  // cartões de categoria: tudo menos categoria, segmento e nicho
  const contagem = useMemo(() => contar(leads.filter((l) => passa(l, ['cat', 'segmento', 'nichos'])), (l) => l.segmento_id), [leads, passa])
  const contagemFase = useMemo(() => contar(leads.filter((l) => passa(l, ['fase'])), (l) => faseDe(l.status)), [leads, passa])
  const totalFases = Object.values(contagemFase).reduce((a, b) => a + b, 0)
  const paraNichos = useMemo(() => leads.filter((l) => passa(l, ['nichos'])), [leads, passa])
  const opcoesStatus = useMemo(() => {
    const c = contar(leads.filter((l) => passa(l, ['status'])), (l) => l.status)
    return STATUS.map((s) => ({ id: s.id, nome: s.nome, qtd: c[s.id] ?? 0, ponto: PONTO_FASE[faseDe(s.id)] }))
  }, [leads, passa])
  const opcoesUf = useMemo(() => {
    const c = contar(leads.filter((l) => passa(l, ['uf', 'cidade'])), (l) => l.uf)
    return Object.entries(c).sort((a, b) => b[1] - a[1]).map(([id, qtd]) => ({ id, nome: id, qtd }))
  }, [leads, passa])
  const opcoesCidade = useMemo(() => {
    const c = contar(leads.filter((l) => passa(l, ['cidade'])), (l) => l.cidade)
    return Object.entries(c).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0])).map(([id, qtd]) => ({ id, nome: id, qtd }))
  }, [leads, passa])

  const filtrados = useMemo(() => {
    const lista = leads.filter((l) => passa(l))
    const chaveOrdem = ORDENS[f.ordem]
    // nos salvos: os mexidos por último primeiro
    if (f.salvos && !chaveOrdem) return [...lista].sort((a, b) => (favoritos.get(b.id)?.updated_at ?? '').localeCompare(favoritos.get(a.id)?.updated_at ?? ''))
    // maior primeiro; quem não tem o número vai para o fim
    if (chaveOrdem) return [...lista].sort((a, b) => (chaveOrdem(b) ?? -1) - (chaveOrdem(a) ?? -1))
    // em blocos: categoria/segmento na ordem definida no banco e, dentro de cada bloco, maior score primeiro
    return [...lista].sort((a, b) =>
      (segInfo[a.segmento_id]?.ordem ?? 999) - (segInfo[b.segmento_id]?.ordem ?? 999) || (b.score ?? 0) - (a.score ?? 0))
  }, [leads, passa, favoritos, f.salvos, f.ordem, segInfo])
  const emBlocos = !ORDENS[f.ordem] && !f.salvos && !f.segmento
  const totalSalvos = useMemo(() => leads.filter((l) => favoritos.has(l.id)).length, [leads, favoritos])
  const totalTipo = (t: string) => leads.filter((l) => !t || l.tipo === t).length

  const [pagina, setPagina] = useState(0)
  useEffect(() => setPagina(0), [filtrados])
  const paginas = Math.max(1, Math.ceil(filtrados.length / POR_PAGINA))
  const visiveis = filtrados.slice(pagina * POR_PAGINA, (pagina + 1) * POR_PAGINA)

  // salvar abre a anotação rápida; tirar dos salvos fecha
  async function marcar(id: string) {
    const jaSalvo = favoritos.has(id)
    setNotaAberta(jaSalvo ? null : id)
    setErroFav(await alternarFavorito(id))
  }

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
          <button onClick={() => set('tiktokshop', f.tiktokShop ? '' : '1')}
            title="Marcas e criadores com loja no TikTok Shop"
            className={`flex items-center gap-1.5 rounded-lg border px-3 py-2 text-sm transition ${
              f.tiktokShop ? 'border-garnet bg-garnet/15 text-ink' : 'border-white/10 bg-raised text-ink-muted hover:text-ink'}`}>
            <ShoppingBag size={14} /> TikTok Shop
          </button>
          <button onClick={() => set('salvos', f.salvos ? '' : '1')} aria-pressed={f.salvos}
            title="Leads que você marcou como interessantes"
            className={`flex items-center gap-1.5 rounded-lg border px-3 py-2 text-sm transition ${
              f.salvos ? 'border-amber-400/60 bg-amber-400/15 text-ink' : 'border-white/10 bg-raised text-ink-muted hover:text-ink'}`}>
            <Star size={14} className={f.salvos || totalSalvos ? 'fill-amber-400 text-amber-400' : ''} /> Salvos
            <span className="tabular text-xs opacity-60">{nf.format(totalSalvos)}</span>
          </button>
          <div className="flex max-w-full overflow-x-auto rounded-lg border border-white/10 bg-raised p-0.5">
            {TIPOS.map((t) => (
              <button key={t.id} onClick={() => set('tipo', t.id)}
                className={`relative whitespace-nowrap rounded-md px-3 py-1.5 text-sm transition ${f.tipo === t.id ? 'text-ink' : 'text-ink-muted hover:text-ink'}`}>
                {f.tipo === t.id && (
                  <motion.span layoutId="tipo-ativo" className="absolute inset-0 rounded-md bg-white/10"
                    transition={{ type: 'spring', stiffness: 400, damping: 32 }} />
                )}
                <span className="relative">{t.nome} <span className="tabular text-xs opacity-60">{nf.format(totalTipo(t.id))}</span></span>
              </button>
            ))}
          </div>
        </div>

        <CategoriaNav categorias={categorias} contagem={contagem} cat={f.cat} mostrarTipo={!f.tipo}
          onCategoria={(c) => set('cat', c)} />

        <div className="flex flex-wrap items-center gap-2">
          <FiltroPopover rotulo="Status" icone={CircleDot} valor={STATUS.find((x) => x.id === f.status)?.nome} onLimpar={() => set('status', '')}>
            {(fechar) => <ListaOpcoes todos="Todos os status" opcoes={opcoesStatus} valor={f.status}
              onEscolher={(v) => { set('status', v); fechar() }} />}
          </FiltroPopover>
          <FiltroPopover rotulo="Estado" icone={MapPin} valor={f.uf} onLimpar={() => set('uf', '')}>
            {(fechar) => <ListaOpcoes todos="Todos os estados" opcoes={opcoesUf} valor={f.uf} buscaPlaceholder="Buscar estado…"
              onEscolher={(v) => { set('uf', v); fechar() }} />}
          </FiltroPopover>
          <FiltroPopover rotulo="Cidade" icone={MapPin} valor={f.cidade} onLimpar={() => set('cidade', '')}>
            {(fechar) => <ListaOpcoes todos={f.uf ? `Todas as cidades de ${f.uf}` : 'Todas as cidades'} opcoes={opcoesCidade} valor={f.cidade}
              buscaPlaceholder="Buscar cidade…" onEscolher={(v) => { set('cidade', v); fechar() }} />}
          </FiltroPopover>
          <FiltroPopover rotulo="Score" icone={Gauge} valor={f.scoreMin ? `≥ ${f.scoreMin}` : null} onLimpar={() => set('scoreMin', '')}>
            {() => (
              <div className="space-y-3 p-1">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-ink-muted">Score mínimo</span>
                  <span className="tabular font-semibold">{f.scoreMin}</span>
                </div>
                <input type="range" min={0} max={100} step={5} value={f.scoreMin} aria-label="Score mínimo"
                  onChange={(e) => set('scoreMin', e.target.value === '0' ? '' : e.target.value)} className="w-full accent-garnet" />
                <div className="flex gap-1.5">
                  {[0, 50, 70, 80].map((v) => (
                    <button key={v} onClick={() => set('scoreMin', v ? String(v) : '')}
                      className={`flex-1 rounded-lg border px-2 py-1 text-xs transition ${
                        f.scoreMin === v ? 'border-garnet bg-garnet/15 text-ink' : 'border-white/10 text-ink-muted hover:text-ink'}`}>
                      {v ? `≥ ${v}` : 'Todos'}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </FiltroPopover>
          <button onClick={() => set('contato', f.contato ? '' : '1')} aria-pressed={f.contato}
            className={`flex items-center gap-1.5 whitespace-nowrap rounded-full border px-3 py-1.5 text-sm transition ${
              f.contato ? 'border-garnet/60 bg-garnet/10 text-ink' : 'border-white/10 bg-raised text-ink-muted hover:border-white/20 hover:text-ink'}`}>
            <Phone size={14} className={f.contato ? 'text-garnet' : ''} /> Com contato
          </button>
          {temFiltro && (
            <button onClick={() => setParams({})} className="ml-auto flex items-center gap-1 whitespace-nowrap text-xs text-ink-muted hover:text-ink">
              <X size={13} /> Limpar filtros
            </button>
          )}
        </div>
      </div>

      {erroFav && <p className="text-sm text-red-400" role="alert">Não foi possível salvar: {erroFav}</p>}

      <div className="card overflow-hidden">
        <div className="space-y-3 border-b border-white/10 px-3 py-3 sm:px-4">
          {catAtual && catAtual.segmentos.length > 1 && (
            <Etapas rotulo={catAtual.nome} itens={[
              { id: '', nome: 'Todos', qtd: catAtual.segmentos.reduce((n, x) => n + (contagem[x.id] ?? 0), 0) },
              ...catAtual.segmentos.map((x) => ({ id: x.id, nome: x.nome, qtd: contagem[x.id] ?? 0 })),
            ]} valor={f.segmento} destaque={!f.segmento} onEscolher={(id) => set('segmento', id)} />
          )}
          {verNichos && (
            <NichoFiltro leads={paraNichos} selecionados={f.nichos} onChange={(n) => set('nichos', n.join(','))} />
          )}
          <div className="flex gap-1.5 overflow-x-auto" role="group" aria-label="Filtrar por fase">
            {[{ id: '' as '' | FaseId, nome: 'Todas as fases', ponto: '' }, ...FASES.map((x) => ({ id: x.id, nome: FASE_CURTA[x.id], ponto: PONTO_FASE[x.id] }))].map((x) => {
              const ativo = f.fase === x.id
              const qtd = x.id ? contagemFase[x.id] ?? 0 : totalFases
              return (
                <button key={x.id} onClick={() => set('fase', x.id)} aria-pressed={ativo}
                  title={x.id ? FASES.find((y) => y.id === x.id)!.status.map((st) => STATUS.find((t) => t.id === st)!.nome).join(' · ') : undefined}
                  className={`flex shrink-0 items-center gap-1.5 whitespace-nowrap rounded-full border px-3 py-1 text-xs transition ${
                    ativo ? 'border-white/30 bg-white/10 text-ink' : 'border-white/10 text-ink-muted hover:bg-white/5 hover:text-ink'}`}>
                  {x.ponto && <span className={`h-1.5 w-1.5 rounded-full ${x.ponto}`} />}
                  {x.nome} <span className="tabular opacity-60">{nf.format(qtd)}</span>
                </button>
              )
            })}
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/10 bg-white/[0.02] text-left text-[11px] uppercase tracking-wider text-ink-muted">
                <th className="px-3 py-3 font-medium sm:px-4">Nome</th>
                {verSeguidores ? (
                  <>
                    <ThOrdenavel nome="Seguidores" ativo={f.ordem === 'seguidores'} onClick={() => set('ordem', f.ordem === 'seguidores' ? '' : 'seguidores')} />
                    <ThOrdenavel nome="Média de views" dica="Média dos últimos 12 Reels" ativo={f.ordem === 'views'}
                      onClick={() => set('ordem', f.ordem === 'views' ? '' : 'views')} />
                  </>
                ) : (
                  <th className="hidden px-4 py-3 font-medium sm:table-cell">Segmento</th>
                )}
                {!verSeguidores && <th className="hidden px-4 py-3 font-medium md:table-cell">Local</th>}
                <th className="px-3 py-3 font-medium sm:px-4">Contato</th>
                <th className="hidden px-4 py-3 font-medium sm:table-cell">Status</th>
                <th className="px-3 py-3 text-right font-medium sm:px-4">Score</th>
              </tr>
            </thead>
            <tbody>
                {visiveis.map((l, i) => {
                  const perfil = perfilSocial(l)
                  const fav = favoritos.get(l.id)
                  return (
                  <Fragment key={l.id}>
                  {emBlocos && (i === 0 || visiveis[i - 1].segmento_id !== l.segmento_id) && (
                    <tr className="border-y border-white/10 bg-gradient-to-r from-garnet/[0.07] to-transparent">
                      <td colSpan={6} className="px-4 py-2.5">
                        <div className="flex items-center gap-2">
                          <span className="h-3.5 w-0.5 rounded-full bg-garnet" />
                          <span className="text-xs font-semibold uppercase tracking-wider text-ink-soft">{catDe(l.segmento_id)}</span>
                          {catDe(l.segmento_id) !== nomeSeg(l.segmento_id) && (
                            <span className="text-xs uppercase tracking-wider text-ink-muted">· {nomeSeg(l.segmento_id)}</span>
                          )}
                          <span className="tabular rounded-full bg-white/10 px-1.5 py-px text-[10px] text-ink-soft">{nf.format(contagem[l.segmento_id] ?? 0)}</span>
                        </div>
                      </td>
                    </tr>
                  )}
                  <motion.tr initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                    onClick={() => set('lead', l.id)}
                    className="cursor-pointer border-b border-white/5 transition odd:bg-white/[0.015] hover:bg-white/[0.05]">
                    <td className={`${verSeguidores ? 'max-w-[6.5rem]' : 'max-w-[9.5rem]'} px-3 py-3 sm:max-w-[15rem] sm:px-4 lg:max-w-[22rem] xl:max-w-[26rem]`}>
                      <div className="flex items-center gap-2 sm:gap-3">
                        <button onClick={(e) => { e.stopPropagation(); marcar(l.id) }}
                          title={fav ? 'Remover dos salvos' : 'Salvar como interessante'} aria-pressed={!!fav}
                          aria-label={fav ? 'Remover dos salvos' : 'Salvar como interessante'}
                          className="-m-1 shrink-0 rounded-md p-1 transition hover:bg-white/10">
                          <Star size={16} className={fav ? 'fill-amber-400 text-amber-400' : 'text-ink-muted hover:text-amber-300'} />
                        </button>
                        <span style={corAvatar(l.nome)} aria-hidden
                          className="hidden h-8 sm:flex w-8 shrink-0 items-center justify-center rounded-full text-[11px] font-semibold">
                          {iniciais(l.nome)}
                        </span>
                        <div className="min-w-0">
                          <div className="flex items-center gap-2 font-medium text-ink">
                            <span className="truncate">{l.nome}</span>
                            {fav?.nota && (
                              <button title={fav.nota} aria-label={`Minha anotação: ${fav.nota}`}
                                onClick={(e) => { e.stopPropagation(); setNotaAberta(l.id) }}
                                className="shrink-0 text-amber-300/80 hover:text-amber-300">
                                <StickyNote size={13} />
                              </button>
                            )}
                            {vendeNoTikTokShop(l) && (
                              <span title="Vende no TikTok Shop" className="shrink-0 rounded-full bg-garnet/15 px-1.5 py-0.5 text-[10px] font-medium text-garnet">TikTok Shop</span>
                            )}
                          </div>
                          {verSeguidores && perfil ? (
                            <div className="mt-0.5 flex items-center gap-1.5 overflow-hidden text-xs text-ink-muted">
                              <span className="inline-flex shrink-0 items-center gap-1 rounded bg-white/5 px-1 py-px text-[10px] text-ink-soft">
                                {perfil.plataforma === 'TikTok' ? <Music2 size={10} /> : <AtSign size={10} />}{perfil.plataforma}
                              </span>
                              <span className="truncate">{perfil.arroba}</span>
                              {l.subsegmento && <span className="hidden truncate sm:inline">· {l.subsegmento}</span>}
                            </div>
                          ) : (
                            <div className="truncate text-xs text-ink-muted">{l.subsegmento ?? TIPO_NOME[l.tipo]}</div>
                          )}
                          {fav?.nota && <div className="truncate text-[11px] text-amber-200/70" title={fav.nota}>{fav.nota}</div>}
                        </div>
                      </div>
                    </td>
                    {verSeguidores ? (
                      <td className="tabular px-2 py-3 text-right sm:px-4" title={l.seguidores ? nf.format(l.seguidores) : undefined}>
                        {l.seguidores ? <span className="font-medium">{nfCompacto.format(l.seguidores)}</span> : <span className="text-ink-muted">—</span>}
                      </td>
                    ) : (
                      <td className="hidden whitespace-nowrap px-4 py-3 text-ink-soft sm:table-cell">{nomeSeg(l.segmento_id)}</td>
                    )}
                    {verSeguidores && <td className="tabular hidden px-4 py-3 text-right sm:table-cell"><MediaViews valor={l.extras?.media_views_reels} /></td>}
                    {!verSeguidores && (
                      <td className="hidden whitespace-nowrap px-4 py-3 text-ink-soft md:table-cell">
                        {[l.cidade, l.uf].filter(Boolean).join(' / ') || <span className="text-ink-muted">—</span>}
                      </td>
                    )}
                    <td className="px-3 py-3 sm:px-4"><Canais lead={l} /></td>
                    <td className="hidden px-4 py-3 sm:table-cell"><StatusBadge status={l.status} /></td>
                    <td className="px-3 py-3 text-right sm:px-4">
                      <span className={`tabular inline-flex min-w-[2.25rem] justify-center rounded-full border px-2 py-0.5 text-xs font-semibold ${scorePilula(l.score)}`}>
                        {l.score ?? '—'}
                      </span>
                    </td>
                  </motion.tr>
                  {notaAberta === l.id && (
                    <tr className="border-b border-white/5 bg-amber-400/[0.06]" onClick={(e) => e.stopPropagation()}>
                      <td colSpan={6} className="px-3 py-2 sm:px-4">
                        <NotaRapida inicial={fav?.nota ?? ''} onFechar={() => setNotaAberta(null)}
                          onSalvar={async (n) => { setNotaAberta(null); setErroFav(await salvarNota(l.id, n)) }} />
                      </td>
                    </tr>
                  )}
                  </Fragment>
                  )
                })}
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

// passo 2: os segmentos da categoria escolhida, em pílulas coladas na tabela
function Etapas({ rotulo, itens, valor, destaque, onEscolher }: {
  rotulo: string
  itens: { id: string; nome: string; qtd: number }[]
  valor: string
  destaque: boolean
  onEscolher: (id: string) => void
}) {
  return (
    <div className="flex items-center gap-2 overflow-x-auto">
      <span className="flex shrink-0 items-center gap-1.5 text-xs font-medium uppercase tracking-wider text-ink-soft">
        <span className="h-3.5 w-0.5 rounded-full bg-garnet" />{rotulo}
        <ChevronRight size={13} className="text-ink-muted" />
      </span>
      <div className={`flex shrink-0 gap-0.5 rounded-full border p-0.5 transition ${destaque ? 'border-garnet/40 bg-garnet/[0.06]' : 'border-white/10 bg-raised'}`}>
        {itens.map((x) => {
          const ativo = valor === x.id
          return (
            <button key={x.id} onClick={() => onEscolher(x.id)} aria-pressed={ativo}
              className={`relative whitespace-nowrap rounded-full px-3 py-1 text-sm transition ${ativo ? 'text-ink' : 'text-ink-muted hover:text-ink'}`}>
              {ativo && <motion.span layoutId="etapa-ativa" className="absolute inset-0 rounded-full bg-white/10"
                transition={{ type: 'spring', stiffness: 400, damping: 32 }} />}
              <span className="relative">{x.nome} <span className="tabular text-xs opacity-60">{nf.format(x.qtd)}</span></span>
            </button>
          )
        })}
      </div>
    </div>
  )
}

function NotaRapida({ inicial, onSalvar, onFechar }: { inicial: string; onSalvar: (nota: string) => void; onFechar: () => void }) {
  const [texto, setTexto] = useState(inicial)
  return (
    <div className="flex items-center gap-2">
      <StickyNote size={14} className="shrink-0 text-amber-300" />
      <input autoFocus className="input !py-1.5 text-sm" value={texto} maxLength={500} placeholder="Anotação rápida (opcional)"
        onChange={(e) => setTexto(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter') onSalvar(texto)
          if (e.key === 'Escape') { e.stopPropagation(); onFechar() }
        }} />
      <button onClick={() => onSalvar(texto)} title="Salvar anotação (Enter)" aria-label="Salvar anotação" className="btn-ghost px-2 py-1.5"><Check size={15} /></button>
      <button onClick={onFechar} title="Fechar (Esc)" aria-label="Fechar" className="btn-ghost px-2 py-1.5"><X size={15} /></button>
    </div>
  )
}

function MediaViews({ valor }: { valor: unknown }) {
  const n = typeof valor === 'number' ? valor : Number(valor)
  if (!valor || !Number.isFinite(n)) return <span className="text-ink-muted">—</span>
  return <span title={`${nf.format(n)} views em média nos últimos 12 Reels`}>{nfCompacto.format(n)}</span>
}

function ThOrdenavel({ nome, dica, ativo, onClick }: { nome: string; dica?: string; ativo: boolean; onClick: () => void }) {
  return (
    <th className={`px-2 py-3 text-right font-medium sm:px-4 ${dica ? 'hidden sm:table-cell' : ''}`}>
      <button onClick={onClick} title={ativo ? 'Voltar à ordem por score' : `${dica ? dica + ' · ' : ''}Ordenar do maior para o menor`}
        className={`inline-flex items-center gap-1 transition hover:text-ink ${ativo ? 'text-ink' : ''}`}>
        {nome}
        <ArrowDown size={13} className={ativo ? 'text-garnet' : 'opacity-40'} />
      </button>
    </th>
  )
}

// @ e plataforma da influenciadora: a indicada na planilha, senão Instagram, senão TikTok
function perfilSocial(l: Lead) {
  const pref = String(l.extras?.plataforma ?? '').toLowerCase()
  const ig = l.instagram ? { plataforma: 'Instagram', arroba: l.instagram.startsWith('@') ? l.instagram : `@${l.instagram}` } : null
  const tt = l.tiktok ? { plataforma: 'TikTok', arroba: l.tiktok.startsWith('@') ? l.tiktok : `@${l.tiktok}` } : null
  return (pref.includes('tiktok') ? tt ?? ig : ig ?? tt)
}

// só os canais que existem, cada um com tooltip e link
function Canais({ lead: l }: { lead: Lead }) {
  const canais: { nome: string; icone: LucideIcon; href: string; cor: string }[] = []
  if (l.email) canais.push({ nome: `E-mail: ${l.email}`, icone: Mail, href: `mailto:${l.email}`, cor: 'text-sky-300' })
  if (l.whatsapp) canais.push({ nome: `WhatsApp: ${l.whatsapp}`, icone: MessageCircle, href: whatsappUrl(l.whatsapp), cor: 'text-emerald-300' })
  if (l.telefone) canais.push({ nome: `Telefone: ${l.telefone}`, icone: Phone, href: `tel:${l.telefone}`, cor: 'text-ink-soft' })
  if (l.linkedin) canais.push({ nome: 'LinkedIn', icone: Briefcase, href: urlDe(l.linkedin), cor: 'text-blue-300' })
  if (l.instagram) canais.push({ nome: `Instagram: ${l.instagram}`, icone: AtSign, href: instagramUrl(l.instagram), cor: 'text-pink-300' })
  if (l.tiktok) canais.push({ nome: `TikTok: ${l.tiktok}`, icone: Music2, href: tiktokUrl(l.tiktok), cor: 'text-cyan-300' })
  if (!canais.length) return <span className="text-xs text-ink-muted/70">sem contato</span>
  return (
    <div className="flex gap-1">
      {canais.map((c, i) => (
        <a key={c.nome} href={c.href} target="_blank" rel="noreferrer" title={c.nome} aria-label={c.nome}
          onClick={(e) => e.stopPropagation()}
          className={`${i >= 2 ? 'hidden sm:flex' : 'flex'} h-6 w-6 items-center sm:h-7 sm:w-7 justify-center rounded-md bg-white/5 transition hover:bg-white/10 ${c.cor}`}>
          <c.icone size={14} />
        </a>
      ))}
    </div>
  )
}
