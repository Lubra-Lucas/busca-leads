-- Novo tipo de lead: investidores (quem financia projetos/marcas). Os registros em si ficam só no banco:
-- o repositório é público e a lista de investidores é estratégia comercial.

alter type public.lead_tipo add value if not exists 'investidor';
