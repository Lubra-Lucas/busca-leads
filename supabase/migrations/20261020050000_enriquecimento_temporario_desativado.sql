-- O enriquecimento pelos sites (20/10/2026) usou uma função temporária public.enriquecimento_temp, protegida por token
-- e chamada via REST. Depois da carga ela foi desativada (estado abaixo). Para rodar de novo, recrie-a com um token novo
-- (ações "listar" e "atualizar", que só preenchem campos vazios) e desative ao final.

create or replace function public.enriquecimento_temp(p_token text, p_acao text, p_dados jsonb default '[]'::jsonb)
returns jsonb language plpgsql security definer set search_path = '' as $$
begin
  raise exception 'enriquecimento temporário desativado';
end;
$$;

revoke execute on function public.enriquecimento_temp(text, text, jsonb) from anon, authenticated, public;
