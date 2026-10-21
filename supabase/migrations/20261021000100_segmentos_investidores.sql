-- Separado da migração anterior: o Postgres não deixa usar um valor novo de enum na mesma transação.
-- Campos específicos ficam em leads.extras: tese, ticket, precedentes, pessoas_investimento [{nome, cargo, linkedin}].

insert into public.segmentos (id, tipo, nome, descricao) values
  ('inv_marcas',        'investidor', 'Investidores estratégicos de marcas', 'Constroem, licenciam ou financiam marcas (inclusive de influenciadoras)'),
  ('inv_media_equity',  'investidor', 'Media for equity',                    'Entram com mídia/marketing em troca de participação'),
  ('inv_corporate',     'investidor', 'Corporate venture (beleza)',          'Fundos de investimento de grandes grupos do setor'),
  ('inv_fundo_vc',      'investidor', 'Fundos de venture capital',           'Fundos que já investiram em marcas de beleza/consumo'),
  ('inv_rede_anjos',    'investidor', 'Redes de investidores-anjo',          'Grupos de anjos que aportam em projetos no início');
