-- Site é público (GitHub Pages): leitura/escrita só para e-mails na lista de permitidos.

create table public.usuarios_permitidos (
  email text primary key,
  created_at timestamptz not null default now()
);

alter table public.usuarios_permitidos enable row level security;

insert into public.usuarios_permitidos (email) values ('bialub02@gmail.com');

create function public.usuario_permitido() returns boolean
language sql stable security definer set search_path = '' as $$
  select exists (
    select 1 from public.usuarios_permitidos
    where email = lower(auth.jwt() ->> 'email')
  );
$$;

revoke execute on function public.usuario_permitido() from public, anon;
grant execute on function public.usuario_permitido() to authenticated;

alter policy "autenticados leem segmentos" on public.segmentos rename to "permitidos leem segmentos";
alter policy "permitidos leem segmentos" on public.segmentos using ((select public.usuario_permitido()));

alter policy "autenticados gerenciam leads" on public.leads rename to "permitidos gerenciam leads";
alter policy "permitidos gerenciam leads" on public.leads using ((select public.usuario_permitido())) with check ((select public.usuario_permitido()));

alter policy "autenticados gerenciam interacoes" on public.interacoes rename to "permitidos gerenciam interacoes";
alter policy "permitidos gerenciam interacoes" on public.interacoes using ((select public.usuario_permitido())) with check ((select public.usuario_permitido()));

create policy "usuario ve o proprio cadastro" on public.usuarios_permitidos for select to authenticated using (email = lower(auth.jwt() ->> 'email'));
