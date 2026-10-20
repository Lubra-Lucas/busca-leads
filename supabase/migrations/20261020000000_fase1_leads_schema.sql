-- Fase 1: base de leads (clientes e fornecedores) da Garnet Cosméticos.
-- Aplicada no projeto Supabase "busca-leads" (ref papaicnydbcajkfghwem, org bialub2, sa-east-1).

create type public.lead_tipo as enum ('cliente', 'fornecedor');

create type public.lead_status as enum (
  'novo', 'qualificado', 'contatado', 'respondeu', 'reuniao', 'ganho', 'perdido', 'descartado'
);

create table public.segmentos (
  id text primary key,
  tipo public.lead_tipo not null,
  nome text not null,
  descricao text
);

insert into public.segmentos (id, tipo, nome, descricao) values
  ('influenciadora',   'cliente',    'Influenciadoras',            'Criadoras de conteúdo de beleza com potencial de lançar linha própria'),
  ('maquiador',        'cliente',    'Maquiadores profissionais',  'Maquiadores/escolas de maquiagem que querem marca própria'),
  ('marca_indie',      'cliente',    'Marcas indie de beleza',     'Marcas pequenas/médias que terceirizam produção'),
  ('marca_moda',       'cliente',    'Marcas de moda',             'Marcas de vestuário/acessórios que querem extensão em beleza'),
  ('varejo_private',   'cliente',    'Varejo com marca própria',   'Redes de farmácia, perfumaria, supermercado e e-commerce com private label'),
  ('embalagens',       'fornecedor', 'Embalagens',                 'Estojos de compacto, godês, caixas cartonadas, espelhos'),
  ('pigmentos',        'fornecedor', 'Pigmentos',                  'Óxidos, micas, perolados, lacas'),
  ('materias_primas',  'fornecedor', 'Matérias-primas',            'Talco, sericita, ligantes, conservantes, distribuidores químicos'),
  ('essencias',        'fornecedor', 'Essências',                  'Casas de fragrância');

create table public.leads (
  id uuid primary key default gen_random_uuid(),
  tipo public.lead_tipo not null,
  segmento_id text not null references public.segmentos(id),
  nome text not null,
  contato_nome text,
  contato_cargo text,
  cidade text,
  uf char(2),
  site text,
  instagram text,
  instagram_seguidores integer,
  linkedin text,
  email text,
  telefone text,
  whatsapp text,
  fonte text not null,
  fonte_url text,
  score smallint check (score between 0 and 100),
  status public.lead_status not null default 'novo',
  observacoes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create unique index leads_site_uniq on public.leads (lower(site)) where site is not null;
create unique index leads_instagram_uniq on public.leads (lower(instagram)) where instagram is not null;
create index leads_segmento_idx on public.leads (segmento_id);
create index leads_status_idx on public.leads (status);

create table public.interacoes (
  id uuid primary key default gen_random_uuid(),
  lead_id uuid not null references public.leads(id) on delete cascade,
  canal text not null check (canal in ('email', 'whatsapp', 'instagram', 'linkedin', 'telefone', 'presencial', 'outro')),
  resumo text not null,
  created_at timestamptz not null default now()
);

create index interacoes_lead_idx on public.interacoes (lead_id);

create function public.set_updated_at() returns trigger
language plpgsql set search_path = '' as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger leads_updated_at before update on public.leads
  for each row execute function public.set_updated_at();

alter table public.segmentos enable row level security;
alter table public.leads enable row level security;
alter table public.interacoes enable row level security;

create policy "autenticados leem segmentos" on public.segmentos for select to authenticated using (true);
create policy "autenticados gerenciam leads" on public.leads for all to authenticated using (true) with check (true);
create policy "autenticados gerenciam interacoes" on public.interacoes for all to authenticated using (true) with check (true);
