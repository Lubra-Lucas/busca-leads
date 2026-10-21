# busca-leads

> Para o Claude: leia o [`CLAUDE.md`](CLAUDE.md) — contexto, acesso ao Supabase e onde o trabalho parou.

Base de prospecção de clientes e fornecedores da **Garnet Cosméticos** (maquiagem compacta private label, foco em SP).

## Supabase
- Projeto: `busca-leads` · ref `papaicnydbcajkfghwem` · org `bialub2` · região `sa-east-1` (São Paulo)
- Tabelas: `segmentos`, `leads` (com `extras` jsonb para campos específicos de cada fonte), `interacoes`, `favoritos`, `usuarios_permitidos` (RLS ativo; acesso para qualquer usuário logado)
- Schema: `supabase/migrations/`
- Cargas de leads: `supabase/seed/` e `scripts/importar_planilhas.py` (planilhas da Bia)

## Site (`web/`)
React + Vite + Tailwind + Framer Motion + Recharts, lendo direto do Supabase.
- Endereço: https://lubra-lucas.github.io/busca-leads/
- Publicação automática pelo GitHub Actions (`.github/workflows/pages.yml`) a cada push em `web/`.
- Acesso: login por e-mail/senha; por enquanto qualquer conta criada tem acesso (função `usuario_permitido`; a tabela `usuarios_permitidos` fica pronta para restringir depois).
- Rodar local: `cd web && npm install && npm run dev`

## Fases
- **Fase 1 — coleta** (em andamento): ver [docs/fase1-coleta.md](docs/fase1-coleta.md)
