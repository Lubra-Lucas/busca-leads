import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { AtSign, Briefcase, ExternalLink, Globe, MapPin, Mail, MessageCircle, Music2, Phone, Plus, X } from 'lucide-react'
import { supabase } from '../lib/supabase'
import { useData } from '../lib/data'
import { CANAIS, STATUS, TIPO_NOME, tiktokPerfil, vendeNoTikTokShop, type Interacao, type Lead, type LeadStatus } from '../lib/types'
import { instagramUrl, nf, nfCompacto, scoreTom, tiktokUrl, urlDe, whatsappUrl } from '../lib/format'

export default function LeadDrawer({ lead, onClose }: { lead: Lead | null; onClose: () => void }) {
  useEffect(() => {
    const esc = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', esc)
    return () => window.removeEventListener('keydown', esc)
  }, [onClose])

  return createPortal(
    <AnimatePresence>
      {lead && (
        <>
          <motion.div key="fundo" className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={onClose} />
          <motion.aside key="painel"
            initial={{ x: '100%' }} animate={{ x: 0 }} exit={{ x: '100%' }}
            transition={{ type: 'spring', stiffness: 320, damping: 34 }}
            className="fixed inset-y-0 right-0 z-50 w-full max-w-lg overflow-y-auto border-l border-white/10 bg-surface">
            <Ficha key={lead.id} lead={lead} onClose={onClose} />
          </motion.aside>
        </>
      )}
    </AnimatePresence>,
    document.body,
  )
}

function Ficha({ lead, onClose }: { lead: Lead; onClose: () => void }) {
  const { segmentos, atualizarLead } = useData()
  const [obs, setObs] = useState(lead.observacoes ?? '')
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)
  const [interacoes, setInteracoes] = useState<Interacao[]>([])
  const [nova, setNova] = useState({ canal: 'whatsapp', resumo: '' })

  useEffect(() => {
    supabase.from('interacoes').select('*').eq('lead_id', lead.id).order('created_at', { ascending: false })
      .then(({ data }) => setInteracoes((data as Interacao[]) ?? []))
  }, [lead.id])

  async function salvar(campos: Partial<Lead>) {
    setSalvando(true)
    setErro(await atualizarLead(lead.id, campos))
    setSalvando(false)
  }

  async function registrar() {
    if (!nova.resumo.trim()) return
    const { data, error } = await supabase.from('interacoes')
      .insert({ lead_id: lead.id, canal: nova.canal, resumo: nova.resumo.trim() }).select().single()
    if (error) return setErro(error.message)
    setInteracoes([data as Interacao, ...interacoes])
    setNova({ ...nova, resumo: '' })
    if (lead.status === 'novo' || lead.status === 'qualificado') salvar({ status: 'contatado' })
  }

  const segmento = segmentos.find((s) => s.id === lead.segmento_id)
  const zap = lead.whatsapp ?? lead.telefone

  return (
    <div className="p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-wider text-ink-muted">
            {TIPO_NOME[lead.tipo]} · {segmento?.nome}
          </p>
          {lead.subsegmento && <p className="mt-0.5 text-xs text-ink-soft">{lead.subsegmento}</p>}
          <h2 className="mt-1 text-xl font-semibold">{lead.nome}</h2>
          <p className="mt-1 text-sm text-ink-muted">
            {[lead.bairro, lead.cidade, lead.uf].filter(Boolean).join(' · ') || 'Local não informado'}
            {lead.seguidores ? ` · ${nf.format(lead.seguidores)} seguidores` : ''}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right">
            <div className={`tabular text-2xl font-semibold ${scoreTom(lead.score)}`}>{lead.score ?? '—'}</div>
            <div className="text-[10px] uppercase tracking-wider text-ink-muted">score</div>
          </div>
          <button onClick={onClose} className="btn-ghost px-2"><X size={16} /></button>
        </div>
      </div>

      {zap && (
        <a href={whatsappUrl(zap)} target="_blank" rel="noreferrer" className="btn-primary mt-5 w-full">
          <MessageCircle size={16} /> Abrir WhatsApp
        </a>
      )}

      <section className="mt-6 space-y-2">
        <h3 className="text-xs font-medium uppercase tracking-wider text-ink-muted">Contato</h3>
        {lead.contato_nome && <Linha rotulo="Pessoa">{lead.contato_nome}{lead.contato_cargo ? ` · ${lead.contato_cargo}` : ''}</Linha>}
        <Linha rotulo="E-mail" icone={Mail}>{lead.email && <a className="hover:text-garnet" href={`mailto:${lead.email}`}>{lead.email}</a>}</Linha>
        <Linha rotulo="WhatsApp" icone={MessageCircle}>{lead.whatsapp}</Linha>
        <Linha rotulo="Telefone" icone={Phone}>{lead.telefone && <a className="hover:text-garnet" href={`tel:${lead.telefone}`}>{lead.telefone}</a>}</Linha>
        <Linha rotulo="Site" icone={Globe}>{lead.site && <Externo href={urlDe(lead.site)}>{lead.site}</Externo>}</Linha>
        <Linha rotulo="Instagram" icone={AtSign}>{lead.instagram && <Externo href={instagramUrl(lead.instagram)}>{lead.instagram}</Externo>}</Linha>
        {lead.tiktok && (
          <Linha rotulo="TikTok" icone={Music2}>
            <Externo href={tiktokUrl(lead.tiktok)}>{lead.tiktok}</Externo>
            {tiktokPerfil(lead)?.seguidores != null && <span className="ml-2 text-ink-muted">{nfCompacto.format(tiktokPerfil(lead)!.seguidores!)} seg.</span>}
            {vendeNoTikTokShop(lead) && <span className="ml-2 rounded-full bg-garnet/15 px-1.5 py-0.5 text-[10px] font-medium text-garnet">TikTok Shop</span>}
          </Linha>
        )}
        <Linha rotulo="LinkedIn" icone={Briefcase}>{lead.linkedin && <Externo href={urlDe(lead.linkedin)}>Perfil</Externo>}</Linha>
        {lead.endereco && <Linha rotulo="Endereço" icone={MapPin}><span className="whitespace-normal">{lead.endereco}</span></Linha>}
      </section>

      <Detalhes extras={lead.extras ?? {}} />

      <section className="mt-6 space-y-2">
        <h3 className="text-xs font-medium uppercase tracking-wider text-ink-muted">Gestão</h3>
        <div className="flex flex-wrap gap-1.5">
          {STATUS.map((s) => (
            <button key={s.id} disabled={salvando} onClick={() => salvar({ status: s.id as LeadStatus })}
              className={`rounded-full border px-3 py-1 text-xs transition ${
                lead.status === s.id ? 'border-garnet bg-garnet/15 text-ink' : 'border-white/10 text-ink-muted hover:text-ink'}`}>
              {s.nome}
            </button>
          ))}
        </div>
        <textarea className="input min-h-[96px]" value={obs} onChange={(e) => setObs(e.target.value)} placeholder="Observações" />
        {obs !== (lead.observacoes ?? '') && (
          <button className="btn-primary" disabled={salvando} onClick={() => salvar({ observacoes: obs || null })}>Salvar observações</button>
        )}
        {erro && <p className="text-sm text-red-400">{erro}</p>}
      </section>

      <section className="mt-6 space-y-3">
        <h3 className="text-xs font-medium uppercase tracking-wider text-ink-muted">Histórico de contatos</h3>
        <div className="flex gap-2">
          <select className="input w-36" value={nova.canal} onChange={(e) => setNova({ ...nova, canal: e.target.value })}>
            {CANAIS.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
          <input className="input" placeholder="O que aconteceu?" value={nova.resumo}
            onChange={(e) => setNova({ ...nova, resumo: e.target.value })} onKeyDown={(e) => e.key === 'Enter' && registrar()} />
          <button className="btn-ghost px-2.5" onClick={registrar} title="Registrar"><Plus size={16} /></button>
        </div>
        <ul className="space-y-2">
          {interacoes.map((i) => (
            <li key={i.id} className="rounded-lg border border-white/10 bg-raised p-3 text-sm">
              <div className="flex justify-between text-xs text-ink-muted">
                <span className="capitalize">{i.canal}</span>
                <span>{new Date(i.created_at).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' })}</span>
              </div>
              <p className="mt-1">{i.resumo}</p>
            </li>
          ))}
          {!interacoes.length && <li className="text-sm text-ink-muted">Nenhum contato registrado.</li>}
        </ul>
      </section>

      <section className="mt-6 border-t border-white/10 pt-4 text-xs text-ink-muted">
        Origem: {lead.fonte === 'conhecimento_setorial' ? 'conhecimento do setor (verificar)' : lead.fonte}
        {lead.fonte_url && <> · <Externo href={lead.fonte_url}>ver fonte</Externo></>}
        <ContatoDoSite enr={lead.extras?.enriquecimento as Enriquecimento | undefined} />
      </section>
    </div>
  )
}

// rótulos dos campos extras vindos das planilhas
const EXTRAS: Record<string, string> = {
  tese: 'Tese de investimento',
  ticket: 'Ticket',
  precedentes: 'Já investiu em',
  target: 'Avaliação (target)',
  plataforma: 'Plataforma',
  tipo_contato: 'Tipo de contato',
  assessoria: 'Assessoria',
  link_bio: 'Link na bio',
  outros_emails: 'Outros e-mails',
  media_views_reels: 'Média de views (Reels)',
  preco_reels: 'Preço Reels',
  preco_pacote: 'Preço pacote',
  nota_google: 'Nota no Google',
  avaliacoes_google: 'Avaliações no Google',
  porte_funcionarios: 'Funcionários',
  faturamento_usd: 'Faturamento (USD)',
  ranking_planilha: 'Ranking na planilha',
  origem: 'Planilha de origem',
}
const MOEDA = new Set(['preco_reels', 'preco_pacote'])

function Detalhes({ extras }: { extras: Record<string, unknown> }) {
  const itens = Object.keys(EXTRAS).filter((k) => extras[k] != null && extras[k] !== '')
  const unidades = (extras.unidades as { nome: string; endereco?: string; telefone?: string }[] | undefined) ?? []
  const pessoas = (extras.pessoas_investimento as { nome: string; cargo?: string; linkedin?: string }[] | undefined) ?? []
  if (!itens.length && !unidades.length && !pessoas.length) return null
  const fmt = (k: string, v: unknown) =>
    MOEDA.has(k) && typeof v === 'number' ? v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
      : typeof v === 'number' ? nf.format(v) : String(v)
  return (
    <section className="mt-6 space-y-2">
      <h3 className="text-xs font-medium uppercase tracking-wider text-ink-muted">Detalhes</h3>
      {itens.map((k) => (
        <div key={k} className="flex gap-3 text-sm">
          <span className="w-40 shrink-0 text-ink-muted">{EXTRAS[k]}</span>
          <span className="min-w-0 break-words">{/^https?:\/\//.test(String(extras[k])) ? <Externo href={String(extras[k])}>abrir</Externo> : fmt(k, extras[k])}</span>
        </div>
      ))}
      {pessoas.length > 0 && (
        <div className="pt-1">
          <p className="mb-1.5 text-sm text-ink-muted">Quem decide os investimentos</p>
          <ul className="space-y-1.5">
            {pessoas.map((p) => (
              <li key={p.nome} className="flex items-center justify-between gap-2 rounded-lg border border-white/10 bg-raised p-2.5 text-xs">
                <div>
                  <div className="font-medium text-ink">{p.nome}</div>
                  {p.cargo && <div className="mt-0.5 text-ink-muted">{p.cargo}</div>}
                </div>
                {p.linkedin && <Externo href={p.linkedin}>LinkedIn</Externo>}
              </li>
            ))}
          </ul>
        </div>
      )}
      {unidades.length > 0 && (
        <div className="pt-1">
          <p className="mb-1.5 text-sm text-ink-muted">Unidades da rede ({unidades.length})</p>
          <ul className="space-y-1.5">
            {unidades.map((u) => (
              <li key={u.nome} className="rounded-lg border border-white/10 bg-raised p-2.5 text-xs">
                <div className="font-medium text-ink">{u.nome}</div>
                <div className="mt-0.5 text-ink-muted">{[u.endereco, u.telefone].filter(Boolean).join(' · ')}</div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  )
}

interface Enriquecimento { data?: string; paginas?: string[]; resultado?: string }

function ContatoDoSite({ enr }: { enr?: Enriquecimento }) {
  if (!enr?.data) return null
  const data = new Date(`${enr.data}T12:00:00`).toLocaleDateString('pt-BR')
  const pagina = enr.paginas?.[enr.paginas.length - 1]
  return (
    <div className="mt-1">
      {enr.resultado ? `Site visitado em ${data}: ${enr.resultado}.` : <>Contato encontrado no site em {data}</>}
      {!enr.resultado && pagina && <> · <Externo href={pagina}>página</Externo></>}
    </div>
  )
}

function Linha({ rotulo, icone: Icone, children }: { rotulo: string; icone?: typeof Mail; children?: React.ReactNode }) {
  const vazio = children == null || children === false || children === ''
  return (
    <div className="flex items-center gap-3 text-sm">
      <span className="flex w-24 shrink-0 items-center gap-1.5 text-ink-muted">{Icone && <Icone size={13} />}{rotulo}</span>
      <span className={vazio ? 'text-ink-muted/60' : 'min-w-0 truncate'}>{vazio ? 'não encontrado' : children}</span>
    </div>
  )
}

function Externo({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <a href={href} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 hover:text-garnet">
      {children}<ExternalLink size={11} />
    </a>
  )
}
