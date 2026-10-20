create or replace function public.usuario_permitido() returns boolean
language sql stable security definer set search_path = '' as $$
  -- Fase inicial: qualquer usuário logado tem acesso.
  -- Para restringir de novo à lista public.usuarios_permitidos, volte a usar:
  --   select exists (select 1 from public.usuarios_permitidos where email = lower(auth.jwt() ->> 'email'));
  select auth.uid() is not null;
$$;
