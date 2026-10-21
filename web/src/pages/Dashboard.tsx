import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { ArrowUpRight, Building2, Contact, Gauge, Landmark, Star, Truck, Users } from 'lucide-react'
import AnimatedNumber from '../components/AnimatedNumber'
import { AZUL, ChartCard, Dica, EIXO, GRADE, Legenda, SERIE, eixoTick } from '../components/charts'
import { useData } from '../lib/data'
import { STATUS, temContato } from '../lib/types'
import { scoreTom } from '../lib/format'

const ORDEM_TIPO = { cliente: 0, fornecedor: 1, investidor: 2 }

const FAIXAS = [
  { nome: '0–39', min: 0, max: 39 },
  { nome: '40–59', min: 40, max: 59 },
  { nome: '60–79', min: 60, max: 79 },
  { nome: '80–100', min: 80, max: 100 },
]

export default function Dashboard() {
  const { leads, segmentos, carregando, favoritos } = useData()
  const navigate = useNavigate()

  const k = useMemo(() => {
    const comScore = leads.filter((l) => l.score != null)
    return {
      total: leads.length,
      clientes: leads.filter((l) => l.tipo === 'cliente').length,
      fornecedores: leads.filter((l) => l.tipo === 'fornecedor').length,
      investidores: leads.filter((l) => l.tipo === 'investidor').length,
      contato: leads.filter(temContato).length,
      scoreMedio: comScore.length ? Math.round(comScore.reduce((s, l) => s + (l.score ?? 0), 0) / comScore.length) : 0,
    }
  }, [leads])

  const porSegmento = useMemo(
    () =>
      segmentos
        .map((s) => ({ id: s.id, nome: s.nome, tipo: s.tipo, total: leads.filter((l) => l.segmento_id === s.id).length }))
        .sort((a, b) => ORDEM_TIPO[a.tipo] - ORDEM_TIPO[b.tipo] || b.total - a.total),
    [leads, segmentos],
  )

  const porStatus = useMemo(
    () => STATUS.map((s) => ({ id: s.id, nome: s.nome, total: leads.filter((l) => l.status === s.id).length })),
    [leads],
  )

  const porFaixa = useMemo(
    () => FAIXAS.map((f) => ({ ...f, total: leads.filter((l) => l.score != null && l.score >= f.min && l.score <= f.max).length })),
    [leads],
  )

  const prioridades = leads.filter((l) => (l.score ?? 0) >= 80).slice(0, 8)
  const salvos = useMemo(
    () => leads.filter((l) => favoritos.has(l.id))
      .sort((a, b) => favoritos.get(b.id)!.updated_at.localeCompare(favoritos.get(a.id)!.updated_at)).slice(0, 5),
    [leads, favoritos],
  )
  const nomeSeg = (id: string) => segmentos.find((s) => s.id === id)?.nome ?? id

  if (carregando && !leads.length) return <Carregando />

  const kpis = [
    { nome: 'Leads', valor: k.total, icone: Users },
    { nome: 'Clientes', valor: k.clientes, icone: Building2 },
    { nome: 'Fornecedores', valor: k.fornecedores, icone: Truck },
    { nome: 'Investidores', valor: k.investidores, icone: Landmark },
    { nome: 'Com contato direto', valor: k.contato, icone: Contact, extra: k.total ? `${Math.round((k.contato / k.total) * 100)}%` : '' },
    { nome: 'Score médio', valor: k.scoreMedio, icone: Gauge },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Visão geral</h1>
        <p className="mt-1 text-sm text-ink-muted">Base de prospecção da Garnet Cosméticos · foco em SP</p>
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-6">
        {kpis.map((c, i) => (
          <motion.div key={c.nome}
            initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: i * 0.06 }}
            whileHover={{ y: -2 }}
            className="card p-4">
            <div className="flex items-center justify-between text-ink-muted">
              <span className="text-xs">{c.nome}</span>
              <c.icone size={15} />
            </div>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-3xl font-semibold"><AnimatedNumber value={c.valor} /></span>
              {c.extra && <span className="text-xs text-ink-muted">{c.extra}</span>}
            </div>
          </motion.div>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-5">
        <div className="lg:col-span-3">
          <ChartCard titulo="Leads por segmento" sub="Clique numa barra para ver os leads" delay={0.1}
            legenda={<Legenda itens={[{ cor: SERIE.cliente, nome: 'Clientes' }, { cor: SERIE.fornecedor, nome: 'Fornecedores' }, { cor: SERIE.investidor, nome: 'Investidores' }]} />}>
            <ResponsiveContainer width="100%" height={porSegmento.length * 34 + 20}>
              <BarChart data={porSegmento} layout="vertical" margin={{ left: 8, right: 24 }} barCategoryGap={6}>
                <CartesianGrid horizontal={false} stroke={GRADE} />
                <XAxis type="number" allowDecimals={false} tick={eixoTick} axisLine={{ stroke: EIXO }} tickLine={false} />
                <YAxis type="category" dataKey="nome" width={140} tick={eixoTick} axisLine={false} tickLine={false} />
                <Tooltip cursor={{ fill: 'rgba(255,255,255,0.04)' }}
                  content={<Dica rotulo={(p) => String(p.nome)} valor={(p) => `${p.total} leads`} />} />
                <Bar dataKey="total" radius={[0, 4, 4, 0]} className="cursor-pointer"
                  onClick={(d) => navigate(`/leads?segmento=${(d as unknown as { id: string }).id}`)}>
                  {porSegmento.map((s) => <Cell key={s.id} fill={SERIE[s.tipo]} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>

        <div className="space-y-4 lg:col-span-2">
          <ChartCard titulo="Pipeline" sub="Leads em cada etapa da prospecção" delay={0.15}>
            <ResponsiveContainer width="100%" height={porStatus.length * 26 + 20}>
              <BarChart data={porStatus} layout="vertical" margin={{ left: 0, right: 16 }} barCategoryGap={4}>
                <CartesianGrid horizontal={false} stroke={GRADE} />
                <XAxis type="number" allowDecimals={false} tick={eixoTick} axisLine={{ stroke: EIXO }} tickLine={false} />
                <YAxis type="category" dataKey="nome" width={86} tick={eixoTick} axisLine={false} tickLine={false} />
                <Tooltip cursor={{ fill: 'rgba(255,255,255,0.04)' }}
                  content={<Dica rotulo={(p) => String(p.nome)} valor={(p) => `${p.total} leads`} />} />
                <Bar dataKey="total" fill={AZUL} radius={[0, 4, 4, 0]} className="cursor-pointer"
                  onClick={(d) => navigate(`/leads?status=${(d as unknown as { id: string }).id}`)} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard titulo="Distribuição de score" sub="80+ = abordar primeiro" delay={0.2}>
            <ResponsiveContainer width="100%" height={170}>
              <BarChart data={porFaixa} margin={{ left: -20, right: 4 }}>
                <CartesianGrid vertical={false} stroke={GRADE} />
                <XAxis dataKey="nome" tick={eixoTick} axisLine={{ stroke: EIXO }} tickLine={false} />
                <YAxis allowDecimals={false} tick={eixoTick} axisLine={false} tickLine={false} />
                <Tooltip cursor={{ fill: 'rgba(255,255,255,0.04)' }}
                  content={<Dica rotulo={(p) => `Score ${p.nome}`} valor={(p) => `${p.total} leads`} />} />
                <Bar dataKey="total" fill={AZUL} radius={[4, 4, 0, 0]} className="cursor-pointer"
                  onClick={(d) => navigate(`/leads?scoreMin=${(d as unknown as { min: number }).min}`)} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>
      </div>

      {salvos.length > 0 && (
        <ChartCard titulo="Meus salvos" sub="Os últimos contatos que você marcou" delay={0.2}
          legenda={<button onClick={() => navigate('/leads?salvos=1')} className="btn-ghost text-xs">Ver todos <ArrowUpRight size={13} /></button>}>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-5">
            {salvos.map((l) => (
              <motion.button key={l.id} whileHover={{ y: -2 }} onClick={() => navigate(`/leads?lead=${l.id}`)}
                className="min-w-0 rounded-xl border border-white/10 bg-raised p-3 text-left transition hover:border-white/20">
                <div className="flex items-start gap-1.5">
                  <Star size={13} className="mt-0.5 shrink-0 fill-amber-400 text-amber-400" />
                  <span className="truncate text-sm font-medium leading-tight">{l.nome}</span>
                </div>
                <div className="mt-1 truncate text-xs text-amber-200/70">{favoritos.get(l.id)?.nota || <span className="text-ink-muted">sem anotação</span>}</div>
              </motion.button>
            ))}
          </div>
        </ChartCard>
      )}

      <ChartCard titulo="Prioridades" sub="Leads com score 80 ou mais" delay={0.25}
        legenda={<button onClick={() => navigate('/leads?scoreMin=80')} className="btn-ghost text-xs">Ver todos <ArrowUpRight size={13} /></button>}>
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
          {prioridades.map((l) => (
            <motion.button key={l.id} whileHover={{ y: -2 }}
              onClick={() => navigate(`/leads?lead=${l.id}`)}
              className="rounded-xl border border-white/10 bg-raised p-3 text-left transition hover:border-white/20">
              <div className="flex items-start justify-between gap-2">
                <span className="text-sm font-medium leading-tight">{l.nome}</span>
                <span className={`tabular text-sm font-semibold ${scoreTom(l.score)}`}>{l.score}</span>
              </div>
              <div className="mt-1 text-xs text-ink-muted">{nomeSeg(l.segmento_id)}{l.cidade ? ` · ${l.cidade}` : ''}</div>
            </motion.button>
          ))}
          {!prioridades.length && <p className="text-sm text-ink-muted">Nenhum lead com score 80+ ainda.</p>}
        </div>
      </ChartCard>
    </div>
  )
}

function Carregando() {
  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-6">
      {Array.from({ length: 6 }).map((_, i) => <div key={i} className="card h-24 animate-pulse" />)}
    </div>
  )
}
