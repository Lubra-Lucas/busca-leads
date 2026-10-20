# Fase 1 — Coleta de leads · Garnet Cosméticos

**Garnet Cosméticos:** fabricante terceirizada (private label) de maquiagem compacta (pó, blush, sombra, bronzer, iluminador). Foco geográfico: estado de SP.

## Perfis de lead

### Clientes
| Segmento (`segmento_id`) | Quem é | O que buscamos |
|---|---|---|
| `influenciadora` | Criadoras de conteúdo de beleza | Sem marca própria ainda, ou com marca e sem linha de compactos |
| `maquiador` | Maquiadores e escolas de maquiagem | Nome forte, dá aulas, quer linha assinada |
| `marca_indie` | Marcas pequenas/médias de beleza | Terceirizam produção; segunda fonte; extensão de linha |
| `marca_moda` | Marcas de moda/acessórios | Querem entrar em beleza |
| `varejo_private` | Farmácias, perfumarias, supermercados, e-commerce | Programa de marca própria |

### Fornecedores
| Segmento | Itens |
|---|---|
| `embalagens` | Estojo compacto, godê (pan), espelho, cartucho |
| `pigmentos` | Óxidos de ferro, micas, perolados, lacas (grau cosmético) |
| `materias_primas` | Talco, sericita, ligantes, conservantes |
| `essencias` | Fragrâncias para pós |

## Score (0–100)
Critério da onda 1 (manual):
- **+ encaixe**: compacto faz sentido para o produto/público; sem fabricante óbvio; empresa/pessoa em SP.
- **+ sinal recente**: lançamento ou entrada em maquiagem em 2025–2026.
- **− porte**: multinacionais e redes grandes têm pedido mínimo/processo de homologação pesado.
- **− incerteza**: `fonte = 'conhecimento_setorial'` (ainda não verificado) fica ≤ 50.

Faixas: 80+ abordar primeiro · 60–79 qualificar · <60 backlog.

## Onda 1 (20/10/2026)
55 leads (33 clientes, 22 fornecedores — ver `supabase/seed/20261020_leads_onda1.sql`).
Fontes: rankings de influenciadoras (Favikon 2026), imprensa de beleza (Beauty Fair 2026, SPFW, Meio & Mensagem), diretórios B2B (ensun, D&B, cnpj.biz), expositores da in-cosmetics Latin America.

### Lacunas conhecidas
- Faltam Instagram, e-mail e telefone em quase todos os leads — a próxima etapa é enriquecer.
- Pigmentos tem só 2 leads; vale buscar distribuidores de pigmentos cosméticos (Sun Chemical/ex-Merck, Sensient, Kobo etc.) e confirmar o grau cosmético.
- Moda e varejo vêm de conhecimento do setor; é preciso confirmar se cada empresa tem linha de beleza própria.

## Importação das planilhas da Bia (20/10/2026)
Fontes: `Leads_atualizado.xlsx` (influenciadoras + monitoramento de e-mails) e `Garnet_Potenciais_Leads.xlsx`
(cosméticos, vestuário, salões, TikTok Shop). Script: `scripts/importar_planilhas.py`.

- **Lidas:** 376 influenciadoras e 1.198 empresas. As abas "Contatos", "TOP 100" e "Resumo" são consolidações sem dado novo e foram ignoradas.
- **Resultado:** 1.539 leads novos, 15 leads já existentes completados (e-mail, site, decisor…), 35 duplicatas removidas, 30 respostas de e-mail viraram histórico de contatos.
- **Deduplicação:** por @ do Instagram/TikTok, domínio do site e nome normalizado. A influenciadora e a marca dela ficam separadas, a menos que dividam o mesmo @.
- **Redes de salões** (mesmo Instagram ou domínio) viram um lead só, com as unidades listadas na ficha.
- **Plataformas ignoradas:** o scraper do Google Maps às vezes trouxe o Instagram de plataformas de agendamento (`@trinksoficial`, `@bitly`), e esses foram descartados.
- **Status:** "envio de mensagem = sim" virou *Contatado*; quem respondeu e-mail virou *Respondeu* (ou *Perdido* se "seguir adiante = não"); as marcas que a própria planilha excluiu viraram *Descartado*, com o motivo nas observações.

- **Correção (20/10):** na primeira carga, quem tinha contato só por "DM" (ou "link na bio" / "Site: …") ficou com esse texto no campo assessoria e com +15 de score indevido. Isso foi corrigido no banco (65 influenciadoras: o texto foi tirado de assessoria, o link foi para "link na bio" e o score recalculado) e no script.

### Score das planilhas
- **Cosméticos e Vestuário (TOP):** Garnet Lead Score da planilha (0–100).
- **Reservas de Cosméticos/Vestuário:** 30 + 15 (decisor com LinkedIn) + 15 (e-mail) + 10 (WhatsApp) ou 5 (telefone) + 5 (site), com teto de 60.
- **Salões TOP:** score da planilha (0–1) × 60. Salões não são público prioritário da Garnet: revendem, não lançam linha própria.
- **Salões Reserva:** 20 + a mesma regra de contato, com teto de 45.
- **Influenciadoras:** 40 + contato (e-mail 25, telefone 20, assessoria 15, link na bio 10) + avaliação (Target +15, Não target −20) + seguidores (100 mil–1 milhão +10, 30–100 mil +5).
- **Lead que já existia no banco:** fica com o maior valor entre o score antigo e o da planilha.

## Próximos passos (fase 1, continuação)
1. Enriquecer os leads com score 80+: Instagram, contato comercial e e-mail (Apollo/Clay cobram créditos, então confirmar orçamento antes).
2. Onda 2: microinfluenciadoras de SP (10k–300k seguidores), que são o público mais provável a lançar uma primeira linha com lote mínimo baixo.
3. Fechar a lista de fornecedores de estojo compacto em SP com cotação de pedido mínimo (MOQ).
