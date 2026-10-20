# busca-leads

Base de prospecção de clientes e fornecedores da **Garnet Cosméticos** (maquiagem compacta private label, foco em SP).

## Supabase
- Projeto: `busca-leads` · ref `papaicnydbcajkfghwem` · org `bialub2` · região `sa-east-1` (São Paulo)
- Tabelas: `segmentos`, `leads`, `interacoes`, `usuarios_permitidos` (RLS ativo; acesso só para e-mails permitidos)
- Schema: `supabase/migrations/`
- Cargas de leads: `supabase/seed/`

## Site (`web/`)
React + Vite + Tailwind + Framer Motion + Recharts, lendo direto do Supabase.
- Endereço: https://lubra-lucas.github.io/busca-leads/
- Publicação automática pelo GitHub Actions (`.github/workflows/pages.yml`) a cada push em `web/`.
- Acesso: login por e-mail/senha; só e-mails na tabela `usuarios_permitidos` veem os dados.
- Rodar local: `cd web && npm install && npm run dev`

## Fases
- **Fase 1 — coleta** (em andamento): ver [docs/fase1-coleta.md](docs/fase1-coleta.md)
