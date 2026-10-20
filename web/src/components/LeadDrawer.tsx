import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { AtSign, ExternalLink, Globe, Briefcase, Mail, MessageCircle, Phone, Plus, X } from 'lucide-react'
import { supabase } from '../lib/supabase'
import { useData } from '../lib/data'
import { CANAIS, STATUS, type Interacao, type Lead, type LeadStatus } from '../lib/types'
import { instagramUrl, scoreTom, urlDe, whatsappUrl } from '../lib/format'

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
            {lead.tipo === 'cliente' ? 'Cliente' : 'Fornecedor'} · {segmento?.nome}
          </p>
          <h2 className="mt-1 text-xl font-semibold">{lead.nome}</h2>
          <p className="mt-1 text-sm text-ink-muted">{[lead.cidade, lead.uf].filter(Boolean).join(' / ') || 'Local não informado'}</p>
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
        <Linha rotulo="Instagram" icone={AtSign}>
          {lead.instagram && <Externo href={instagramUrl(lead.instagram)}>{lead.instagram}{lead.instagram_seguidores ? ` · ${lead.instagram_seguidores.toLocaleString('pt-BR')} seg.` : ''}</Externo>}
        </Linha>
        <Linha rotulo="LinkedIn" icone={Briefcase}>{lead.linkedin && <Externo href={urlDe(lead.linkedin)}>Perfil</Externo>}</Linha>
      </section>

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
      </section>
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
