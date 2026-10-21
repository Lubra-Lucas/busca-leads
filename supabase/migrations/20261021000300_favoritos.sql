-- Leads salvos ("favoritos") de cada usuário, com uma anotação rápida do porquê.
-- Cada pessoa vê e edita só os próprios.

create table if not exists public.favoritos (
  user_id    uuid not null default auth.uid() references auth.users (id) on delete cascade,
  lead_id    uuid not null references public.leads (id) on delete cascade,
  nota       text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (user_id, lead_id)
);

create index if not exists favoritos_lead_idx on public.favoritos (lead_id);

alter table public.favoritos enable row level security;

create policy favoritos_proprios on public.favoritos
  for all to authenticated
  using (user_id = (select auth.uid()))
  with check (user_id = (select auth.uid()));

grant select, insert, update, delete on public.favoritos to authenticated;
