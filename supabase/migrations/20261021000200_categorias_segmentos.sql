-- Categorias para organizar os segmentos no site (Tipo → Categoria → Segmento) e ordem de exibição.

alter table public.segmentos add column categoria text, add column ordem smallint;

update public.segmentos s set categoria = v.categoria, ordem = v.ordem
from (values
  ('influenciadora',    'Influência',               10),
  ('maquiador',         'Influência',               11),
  ('marca_indie',       'Marcas de beleza',         20),
  ('tiktok_perfumaria', 'Marcas de beleza',         21),
  ('marca_moda',        'Moda',                     30),
  ('varejo_private',    'Varejo e salões',          40),
  ('salao_beleza',      'Varejo e salões',          41),
  ('embalagens',        'Embalagens',               50),
  ('pigmentos',         'Insumos e fragrâncias',    60),
  ('materias_primas',   'Insumos e fragrâncias',    61),
  ('essencias',         'Insumos e fragrâncias',    62),
  ('inv_marcas',        'Estratégicos',             70),
  ('inv_corporate',     'Estratégicos',             71),
  ('inv_media_equity',  'Mídia por participação',   80),
  ('inv_fundo_vc',      'Fundos e anjos',           90),
  ('inv_rede_anjos',    'Fundos e anjos',           91)
) as v(id, categoria, ordem)
where s.id = v.id;
