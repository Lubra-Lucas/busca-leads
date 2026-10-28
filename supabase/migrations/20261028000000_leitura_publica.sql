-- Site sem login (decisão de 28/10/2026): qualquer visitante LÊ clientes e fornecedores.
-- Investidores continuam só para usuários permitidos. Editar, salvos, anotações e histórico seguem exigindo login.
create policy "publico le segmentos" on public.segmentos
  for select to anon using (tipo <> 'investidor');

create policy "publico le leads" on public.leads
  for select to anon using (tipo <> 'investidor');

grant select on public.segmentos, public.leads to anon;
