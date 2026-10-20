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
55 leads (34 clientes, 22 fornecedores — ver `supabase/seed/20261020_leads_onda1.sql`).
Fontes: rankings de influenciadoras (Favikon 2026), imprensa de beleza (Beauty Fair 2026, SPFW, Meio & Mensagem), diretórios B2B (ensun, D&B, cnpj.biz), expositores da in-cosmetics Latin America.

### Lacunas conhecidas
- Faltam Instagram, e-mail e telefone em quase todos os leads — a próxima etapa é enriquecer.
- Pigmentos tem só 2 leads; vale buscar distribuidores de pigmentos cosméticos (Sun Chemical/ex-Merck, Sensient, Kobo etc.) e confirmar o grau cosmético.
- Moda e varejo vêm de conhecimento do setor; é preciso confirmar se cada empresa tem linha de beleza própria.

## Próximos passos (fase 1, continuação)
1. Enriquecer os leads com score 80+: Instagram, contato comercial e e-mail (Apollo/Clay cobram créditos, então confirmar orçamento antes).
2. Onda 2: microinfluenciadoras de SP (10k–300k seguidores), que são o público mais provável a lançar uma primeira linha com lote mínimo baixo.
3. Fechar a lista de fornecedores de estojo compacto em SP com cotação de pedido mínimo (MOQ).
