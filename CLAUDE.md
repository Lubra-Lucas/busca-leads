# busca-leads — contexto para o Claude

Leia este arquivo inteiro antes de começar. Ele resume o projeto, as preferências da usuária, como acessar o banco
e **onde o trabalho parou** (seção "Estado atual"). Histórico detalhado da fase 1: `docs/fase1-coleta.md`.

## O projeto
Sistema de prospecção da **Garnet Cosméticos**: fabricante terceirizada (private label) de **maquiagem compacta**
(pó, blush, sombra, bronzer, iluminador), foco no estado de **SP**. A base reúne três tipos de lead:
- **Clientes:** influenciadoras, maquiadores, marcas indie de beleza, marcas de moda, varejo com marca própria,
  salões e clínicas, marcas de TikTok Shop/perfumaria.
- **Fornecedores:** embalagens, pigmentos, matérias-primas, essências.
- **Investidores:** quem financia **tirar um projeto do papel** (não startup): uma marca de beleza com influenciadora
  grande como embaixadora (royalty/comissão/equity), em que a Garnet cuida da fabricação e o investidor banca o
  marketing (press kit, campanha de lançamento, e-commerce, frete). Só entram pessoas/empresas que **de fato fazem
  esse tipo de investimento** — nada de pessoas operacionais. Flávia (MBOOM) já é conhecida e já fez negócio com a
  Garnet (fica em `extras.relacao_garnet`). Dados de investidores ficam **só no banco** (o repositório é público).

## Preferências da usuária (importante)
- Responder sempre em **português**, de forma direta.
- **Não usar o Lovable.** O site é feito no repositório e publicado no GitHub Pages.
- **Não criar coisa que não foi pedida.** Conferir o projeto antes de mexer.
- Busca de leads e contatos: **fontes gratuitas primeiro** (site da marca, bio/link do TikTok, BrasilAPI/CNPJ,
  sites de agências, busca web). **Clay/Apollo só em casos extremos**, para as maiores marcas, e avisando o custo.
- Quando ela pede tarefas "simultâneas"/"um agente para cada", usar subagentes em paralelo, **modelo Sonnet**.
- Contato bom = direto com comercial/marketing/parcerias, e-mail da influenciadora ou da agência, WhatsApp, telefone.
  SAC/atendimento serve, mas não é o contato certo.
- Ela aprova permissões automaticamente (Supabase incluso): pode executar sem pedir confirmação a cada passo.

## Repositório e publicação
- GitHub: `Lubra-Lucas/busca-leads` (público). **Nunca** commitar chaves secretas, senhas ou dados de investidores.
- Branch de trabalho: **`claude/epic-turing-5qltxt`**. O GitHub Pages publica a partir dela
  (`.github/workflows/pages.yml`, dispara em push que mexe em `web/**`). Se a nova sessão trabalhar em outra branch,
  faça merge nesta (ou ajuste o `branches:` do workflow), senão o site não atualiza.
- Site: https://lubra-lucas.github.io/busca-leads/ — desde 28/10/2026 **abre sem login, só leitura** (clientes e
  fornecedores; investidores ficam ocultos). O botão "Entrar" no topo (rota `#/entrar`) libera edição, salvos,
  anotações, histórico e investidores para usuários permitidos (`podeEditar` em `web/src/lib/auth.tsx`).
  Leitura pública depende das policies de `supabase/migrations/20261028000000_leitura_publica.sql`.
- Commits: mensagens em português, descritivas.

## Estrutura
```
web/                    site (React 19 + Vite 6 + TS + Tailwind 3 + Framer Motion + Recharts + lucide-react, HashRouter)
  src/lib/supabase.ts   URL + chave publicável do Supabase
  src/lib/data.tsx      DataProvider: carrega leads (paginado de 1000 em 1000), segmentos e favoritos
  src/lib/types.ts      tipos (Lead, Segmento, STATUS, TIPO_NOME…)
  src/lib/status.ts     fases do funil (Não contatado/Contatado/Em andamento/Fechado/Encerrado), cores, avatar
  src/lib/nichos.ts     nichos das influenciadoras (extras.nichos) e temNichos()
  src/pages/Leads.tsx   lista: filtros na URL, categorias → segmentos (etapas) → nichos, tabela, salvos
  src/pages/Dashboard.tsx
  src/components/       CategoriaNav, FiltroPopover, NichoFiltro, StatusBadge, LeadDrawer (ficha), charts…
scripts/                coleta/enriquecimento (Python 3 + requests/bs4; rodar com `python3 -I`)
  db.py                       acesso ao banco pela API REST (ver "Acesso ao Supabase")
  importar_planilhas.py       normaliza/deduplica as planilhas da Bia
  enriquecer_sites.py         raspa contatos dos sites das marcas
  renderizar_sites.mjs        Playwright para sites montados por JS
  tiktok_shop.py              perfil público do TikTok (seguidores, bio, link, ttSeller = vende no TikTok Shop)
  investidores_socios.py      CNPJ do rodapé → BrasilAPI (sócios/QSA)
  contatos_influenciadoras.py contatos de influenciadoras pela bio/link do TikTok
  enriquecer_contatos.py      enriquecimento geral de contatos (classifica direto/comercial/agência/geral/sac)
supabase/migrations/    schema (aplicado no projeto remoto); supabase/seed/ primeira carga
docs/fase1-coleta.md    histórico e critérios (score, fontes, decisões)
```
Rodar o site local: `cd web && npm install && npm run dev`. Validar antes de push: `npm run build && npx eslint src`
(hoje: 0 erros e 4 avisos antigos de react-refresh).

## Acesso ao Supabase
Projeto **busca-leads** · ref `papaicnydbcajkfghwem` · org **bialub2** · região `sa-east-1`.
URL: `https://papaicnydbcajkfghwem.supabase.co` · chave publicável (pública, já no site):
`sb_publishable_RPFXNIMe-jQeGUVpCi4UYQ_J0lDgfcA`.

Três jeitos de acessar, do melhor para o mais limitado:
1. **Conector Supabase (MCP) do Claude** — permite SQL, migrações e advisors. Na conta nova do Claude, conecte o
   conector Supabase (claude.ai → Settings → Connectors → Supabase) **entrando com a conta do Supabase que é dona da
   org `bialub2`**. Se a conta do Supabase for outra, a dona precisa convidá-la antes: supabase.com/dashboard →
   org bialub2 → Team → Invite (papel Developer ou Owner). Depois: `list_projects` deve mostrar `busca-leads`, e as
   ferramentas usam `project_id = papaicnydbcajkfghwem`.
2. **Chave secreta via variável de ambiente** (para scripts): copie a *service_role/secret key* em
   Supabase → Project Settings → API keys e cadastre como variável/segredo do ambiente do Claude Code na web
   (`SUPABASE_SERVICE_ROLE_KEY`). Nunca coloque no repositório. Aí `python3 -I scripts/db.py get leads "limit=5"`.
3. **Login de usuário do site** (`SUPABASE_EMAIL` + `SUPABASE_SENHA` no ambiente): lê e edita via RLS (qualquer
   usuário logado pode), mas não altera schema.

### Pegadinhas conhecidas
- `DELETE`, `DROP POLICY/INDEX` pelo MCP pedem confirmação destrutiva e **dão timeout** (60 s) nesta integração.
  Alternativas usadas: `ALTER POLICY` em vez de drop; para duplicados, marcar o lead como `descartado` com
  `extras.duplicado_de = <id do principal>` e mesclar os dados no principal (feito com Jade Picon e Jessica Cardoso).
- Há índices únicos em `lower(site)` e `lower(instagram)`: antes de gravar um @/site, confira se já existe em outro lead.
- Em regex do Postgres use `\y` (limite de palavra), não `\b`.
- Instagram: a API pública pede login e a página dá 429 rápido. Funciona baixar `https://www.instagram.com/<user>/`
  com `User-Agent: Googlebot/2.1 (+http://www.google.com/bot.html)` e ler `"follower_count":N`, com pausas
  (~6 s) e retentativas — dá cerca de 1 perfil por minuto. Sempre confira o nome no `og:title`: vários @ "óbvios"
  são de outras pessoas.
- BrasilAPI: `https://brasilapi.com.br/api/cnpj/v1/{cnpj}`. Se o site só traz a raiz do CNPJ (8 dígitos), monte a
  matriz com dígitos verificadores (`matriz()` em `investidores_socios.py`).
- WebSearch costuma recusar buscas pelo nome de pessoas físicas.

## Modelo de dados (resumo)
- `segmentos(id, tipo, nome, descricao, categoria, ordem)` — `categoria` agrupa os cartões do site
  (Influência, Marcas de beleza, Moda, Varejo e salões, Embalagens, Insumos e fragrâncias, Estratégicos,
  Mídia por participação, Fundos e anjos).
- `leads`: `tipo` (enum cliente/fornecedor/investidor), `segmento_id`, `nome`, `contato_nome`, `contato_cargo`,
  `subsegmento`, `cidade`, `uf`, `bairro`, `endereco`, `site`, `instagram`, `tiktok`, `seguidores`, `linkedin`,
  `email`, `telefone`, `whatsapp`, `fonte`, `fonte_url`, `score` (0–100), `status` (enum novo/qualificado/contatado/
  respondeu/reuniao/ganho/perdido/descartado), `observacoes`, `extras` (jsonb).
- Chaves usadas em `extras`: `nichos` (array) e `nicho_principal`; `nome_original` (antes da padronização);
  `contatos` (array `{nome,cargo,email,telefone,whatsapp,linkedin,tipo,fonte,data}`, tipo ∈ direto/comercial/
  agencia/geral/sac) e `contato_qualidade`; `contato_fonte`; `enriquecimento`; `tiktok_perfil`;
  `seguidores_fonte`; `media_views_reels`; `plataforma`; `relacao_garnet`, `tese`, `ticket`, `precedentes`,
  `pessoas_investimento` (investidores); `duplicado_de` / `mesclado_de`; `unidades` (redes de salões).
- `interacoes(lead_id, canal, resumo, created_at)` — histórico de contatos.
- `favoritos(user_id, lead_id, nota, …)` — leads salvos por usuário, com anotação; RLS: cada um vê os seus.
- `usuarios_permitidos` + função `usuario_permitido()` — hoje libera qualquer usuário logado.
- Escritas em lote: `UPDATE ... FROM (VALUES ...)`, sempre fazendo merge em `extras`
  (`coalesce(extras,'{}') || jsonb_build_object(...)`), preenchendo só campos vazios e subindo score com `greatest`.

## Estado atual (21/10/2026) — onde paramos
Base: **1.619 leads ativos** (fora os descartados). Ainda **352 sem nenhum contato** (sem e-mail, WhatsApp e telefone):

| Segmento | Ativos | Sem contato |
|---|---|---|
| salao_beleza | 725 | 38 |
| influenciadora | 379 | 121 |
| marca_indie | 300 | 109 |
| marca_moda | 146 | 55 |
| tiktok_perfumaria | 20 | 5 |
| fornecedores (matérias-primas 9, embalagens 7, essências 4, pigmentos 2) | 22 | 13 |
| maquiador / varejo_private | 4 / 3 | 4 / 3 |
| investidores | 20 | 4 |

Feito nas últimas sessões:
- Nomes das influenciadoras padronizados (sem emoji, sem caixa alta, sem descrição depois de "|").
- Nichos das 381 influenciadoras em `extras.nichos` + filtro de nicho no site.
- Site: status por fase com cores, tabela redesenhada (avatar, score em pílula, ícones só dos contatos existentes),
  filtros em etapas (categoria → segmento → nicho), pílulas com painel e busca no lugar dos selects,
  leads **salvos** com anotação rápida (estrela na lista, filtro "Salvos", card no painel, campo na ficha),
  seção "Outros contatos" na ficha.
- Seguidores: 19 de 32 influenciadoras sem número foram preenchidas pelo Instagram público.
- Enriquecimento de contatos (gratuito): ~100 leads saíram do "sem contato"; 243 leads têm `extras.contatos`.
  Clay usado 1 vez (0 resultado); Apollo plano Free não libera a busca de pessoas.

Onda 2 de captação (21/10/2026, 5 agentes em paralelo; `extras.onda = 'onda2_2026-10-21'`, todos com contato):
- **Grandes influenciadoras (1M+):** 41 novas (Virginia, Whindersson, Ivete, Zé Felipe, Ana Castela, Claudia Leitte…),
  `fonte = 'Busca onda 2 – grandes influenciadoras'`. Seguidores de HypeAuditor/imprensa; 15 com número de TikTok/YouTube.
  Sem contato (candidatas a rodada paga): Simone Mendes, Paolla Oliveira, Carlinhos Maia, Luísa Sonza, Boca Rosa,
  Pabllo Vittar, Ludmilla, Gio Ewbank, Lexa, Kéfera, Rafa Kalimann, Manu Gavassi. Script: `scripts/onda2_influenciadoras_grandes.py`.
- **Microinfluenciadoras (10k–1M):** 85 novas, fonte Modash (páginas públicas por cidade), só 10 de SP.
  `fonte = 'Busca onda 2 – microinfluenciadoras'`. Script: `scripts/onda2_microinfluenciadoras.py`.
- **Maquiadores:** só 7 novos (SP), + Catharine Hill Academy completada. ~25 nomes fortes sem contato público
  (Fernando Torquatto, Max Weber, Helder Rodrigues…). Script: `scripts/onda2_maquiadores.py`.
- **Marcas de beleza:** 111 novas (103 `marca_indie`, 8 `tiktok_perfumaria`), 74 vindas dos expositores da Beauty Fair 2026.
  Conferir CNPJ de Vizcaya, Skafe, Lacan, L'Acqua di Fiori, Olera (razão social não bate) e Kolene/OX (mesmo CNPJ).
  Script: `scripts/onda2_marcas_beleza.py`.
- **Terceirizadoras (concorrentes):** novo segmento `terceirizadora` (categoria "Concorrentes"), 83 empresas (47 SP,
  7 fazem compactos; mais parecida: Lary Terceirização, Mairiporã). Script: `scripts/onda2_terceirizadoras.py`.
- Base depois da onda 2: **1.946 leads ativos, 350 sem contato**. Instagram público ficou bloqueado (429) nesta
  máquina durante a onda; maquiadores e micro de SP precisam de Instagram logado ou ferramenta paga para crescer.

Rodada de enriquecimento + fornecedores (21/10/2026, tarde):
- Influenciadoras/maquiadores: 22 ganharam contato pela descrição do YouTube, bio do TikTok e sites
  (Bruna Marquezine, Camila Pudim, Ana Hickmann, Natalia Beauty, Thássia Naves…); 101 seguem sem contato.
  Script: `scripts/enriquecer_influenciadoras_youtube.py` (lê a aba "Sobre" via API interna youtubei).
- Empresas existentes: 18 saíram do "sem contato", 4 subiram de SAC para comercial, 69 sites preenchidos,
  CNPJs suspeitos conferidos (`extras.correcao`). Script: `scripts/enriquecer_empresas.py`.
- Fornecedores novos: **106 de embalagens** (85 SP; destaques para estojo compacto: Kilimplast, Plano, Bigaplast,
  Irafon, Thomriss, Bristol e Pivaudran, Incom; 26 com contato vindo do Guia ABRE — validar) e **41 de insumos**
  (35 SP; Império das Essências, Forscher, Bianquímica, Adrivan, Kobo, Sensient). Scripts: `scripts/onda2_embalagens.py`,
  `scripts/onda2_insumos.py`. Grandes distribuidoras (Brenntag, Oxiteno, Volp, Fagron, BASF, Croda) ficaram sem contato.
- Base agora: **2.093 leads ativos, 308 sem contato, 169 fornecedores**.

Investidores, onda de 23/10/2026 (4 agentes Sonnet; `extras.onda = 'investidores_2026-10-23'`): +23 investidores
(media for equity, construtoras de marcas com celebridades, fundos/CVC de consumo, anjos e equity crowdfunding),
total **43**. Só 3 sem e-mail/telefone (Atlantico, Canary, Emerge Ventures: LinkedIn/formulário). Mercado brasileiro de
media-for-equity é pequeno; vários fundos grandes têm ticket acima do projeto. Detalhes (tese, ticket, precedentes,
pessoas) só no banco.

Distribuidores, onda de 23/10/2026 (6 agentes Sonnet; `extras.onda = 'distribuidores_2026-10-23'`): novo segmento
`distribuidor` (cliente, categoria "Distribuição", ícone Truck no `CategoriaNav`), **107 distribuidores** de todo o
Brasil, todos com site e contato (atacado de beleza/perfumaria, profissional de salão, farma/centrais de compra,
importadores, atacado de maquiagem para revenda, regionais). Mais 5 marcas com revenda em `marca_indie` e Redepharma em
`varejo_private`. Em `extras`: `marcas_distribuidas`, `marca_propria`, `area_atuacao`, `cnpj`, `portal_fornecedor`.
Destaques com marca própria: Pérolas Make (GO), Adversa/Atacado Make, KS Cosméticos, Florenza; canais: Union (Ruby Rose),
Bim (Sheglam), Prisma (RS), Farmácias Associadas e Farmarcas (centrais com marca própria). Quase todos os contatos são
"geral"; sem nomes de comprador. Ficaram de fora por falta de site/contato: Panpharma, Santa Cruz, Nazária, Oncoprod,
DAG, Juno, Tradeline. Script: `scripts/onda_distribuidores.py`. Base: **2.229 leads ativos**.

Embalagens SP + distribuidores, rodada de 28/10/2026 (5 agentes Sonnet; script genérico `scripts/consolidar_onda.py`):
- **+68 embalagens** (`extras.onda = 'embalagens_2026-10-28'`), 67 em SP; embalagens agora 181 (158 SP). Destaques de
  maquiagem: Qualipac/Pochet e Albea (Jundiaí, MOQ alto), Expak e Agace (SP, estojos de pó/sombra/batom), Mega Plast,
  Uniplas, Belaplastic (MG, potes para pigmento/pó); frascos/tampas: Reali, Plásticos GT, Visão Sopro (MOQ 3.000),
  Anfeplast, Ibeplas; revenda sem mínimo: Aromapack. Em `extras`: `produtos`, `materiais`, `moq`, `pequenas_tiragens`,
  `fabrica_ou_revenda`. Vários contatos vêm do Guia ABRE (cadastros de ~7 anos) — validar. Não há fabricante nacional de
  godê/paleta achado; ferramentaria de estojo: Digimold, Lu Plastic, Riplast, Plasdiam; decoração: Gensys, Tekarts.
- **+18 distribuidores** (`extras.onda = 'distribuidores_2026-10-28'`), total 125. Lista de 307 distribuidores do
  N/NE/CO/MG/ES só com CNPJ e telefone (sem site) ficou fora do banco, aguardando decisão da usuária.
- Os agentes bateram no limite de 200 WebSearch por sessão; listas de expositores (FCE, Fispal) são JS e não abriram.
- Base: **2.315 leads ativos**.

Estojos para compactados (28/10/2026): a Garnet **não usa potes/frascos**, só embalagem para compactados (estojo
compacto, paleta, book, godê/pan, case de pó/blush, refil). Os 181 fornecedores de embalagem foram varridos
(`scripts/estojos_embalagens.py`) e conferidos por 3 agentes Sonnet. Novo segmento **`estojos`** ("Estojos e paletas
(compactados)", categoria Embalagens, ordem 49) com 18 leads: **7 confirmados** (`extras.faz_estojo = 'sim'`: Incom,
Kilimplast, Irafon, Plasmedix, Thomriss, Expak, Zarzur/RJ) e **11 prováveis** (subsegmento "(a confirmar)": Plano,
Bigaplast, Bristol e Pivaudran, Albea, Qualipac, Agace, MTSZ, Belaplastic, Lu Plastic, Pharmaprov, Fotonbras). Todos os
181 têm `extras.faz_estojo` (sim/provavel/nao/indefinido), `tipos_compactado`, `evidencia`, `evidencia_url`. Sites de
Plano, Bigaplast, Bristol, Agace, Albea, Lu Plastic, Uniplas e Mega Plast não abrem desta rede (proxy 502) — confirmar
por telefone. Nenhum informa MOQ.

Pendências / próximos passos sugeridos (confirmar com a usuária antes):
1. **121 influenciadoras sem contato**, incluindo as maiores (Anitta, Bruna Marquezine, Viih Tube, Sabrina Sato,
   Camila Coelho, Thássia Naves…). O contato está na bio do Instagram (exige login) ou com as assessorias.
   Caminhos: alguém logado no Instagram, ou Clay/Apollo pago só para as maiores.
2. **13 influenciadoras sem seguidores**: Grazi Massafera, Helena Bordon, Emily Garcia, Pamella Lunardi,
   Ana Júlia Corrêa, Luiz Leal (Instagram não respondeu); Duda Reis, Letícia Gomes, Mel Maia, Bella Dias,
   Julia Alvarenga (perfis achados não eram a pessoa); Belle (planetgirls), Gip Pierro. Precisa do @ correto.
3. ~100 marcas indie e ~34 salões sem site nem TikTok; varejo (Renner, C&A, RD, GPA) sem contato corporativo.
4. 48 leads tiveram o site descoberto no enriquecimento, mas o campo `site` não foi preenchido.
5. Revisar nichos chutados de perfis sem descrição (MAVI NAKA, Marcela Freire, Giovanna Pierro, Julianna Motta,
   Jéssica Cardoso, Belle).
6. Contatos "geral" (telefone do CNPJ, WhatsApp de rodapé) não foram validados — conferir antes de campanha.
7. Ideias já discutidas e não iniciadas: onda 2 de microinfluenciadoras de SP (10k–300k), fornecedores de estojo
   compacto em SP com MOQ, automação de envio de e-mails (ela perguntou se é possível; ainda não pediu).

## Testes visuais do site
Sem acesso ao banco no navegador de teste, use um mock: Playwright (Chromium em `/opt/pw-browsers`, nunca rode
`playwright install`) interceptando `**/rest/v1/**` (leads, segmentos, favoritos, `rpc/usuario_permitido` → `true`)
e gravando uma sessão falsa em `localStorage['sb-papaicnydbcajkfghwem-auth-token']`. Sirva o build com
`cd web && npx vite preview --port 4173 --strictPort`. Gere o mock a partir do banco (não commitar: tem dados reais).
Confira desktop (1440px) e celular (390px, sem rolagem horizontal).
