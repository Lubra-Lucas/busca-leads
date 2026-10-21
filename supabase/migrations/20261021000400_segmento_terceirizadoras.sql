-- Concorrentes: outras fabricantes terceirizadas (private label) de cosméticos. Ficam como "cliente" porque
-- também podem terceirizar parte da produção ou indicar clientes; categoria própria no site.
insert into public.segmentos (id, tipo, nome, descricao, categoria, ordem) values
  ('terceirizadora', 'cliente', 'Terceirizadoras de cosméticos', 'Fabricantes private label / terceirização de cosméticos (concorrentes e possíveis parceiras)', 'Concorrentes', 25)
on conflict (id) do nothing;
