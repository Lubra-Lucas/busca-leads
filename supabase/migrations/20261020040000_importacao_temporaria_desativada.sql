-- A carga das planilhas (20/10/2026) usou uma função temporária public.importacao_temp, protegida por token
-- e chamada por scripts/importar_planilhas.py via REST. Depois da carga ela foi desativada (estado abaixo).
-- Para uma nova carga, recrie a função com um token novo e desative de novo ao final.

create or replace function public.importacao_temp(p_token text, p_acao text, p_dados jsonb default '{}'::jsonb)
returns jsonb language plpgsql security definer set search_path = '' as $$
begin
  raise exception 'importação temporária desativada';
end;
$$;

revoke execute on function public.importacao_temp(text, text, jsonb) from anon, authenticated, public;
