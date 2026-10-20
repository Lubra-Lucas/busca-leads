-- Campos para receber as planilhas da Bia (influenciadoras, marcas, moda, salões).

alter table public.leads rename column instagram_seguidores to seguidores;

alter table public.leads
  add column subsegmento text,
  add column bairro text,
  add column endereco text,
  add column tiktok text,
  add column extras jsonb not null default '{}'::jsonb;  -- dados específicos de cada planilha (preço de Reels, nota no Google, unidades da rede…)

insert into public.segmentos (id, tipo, nome, descricao) values
  ('salao_beleza',      'cliente', 'Salões e clínicas de estética', 'Salões, esmalterias e clínicas (revenda / linha própria do salão)'),
  ('tiktok_perfumaria', 'cliente', 'TikTok Shop e perfumaria',      'Marcas fortes em live commerce e perfumaria');

create index leads_tiktok_idx on public.leads (lower(tiktok)) where tiktok is not null;
