-- A busca de TikTok Shop (20/10/2026) usou uma função temporária public.manutencao_temp (ações listar / atualizar /
-- inserir), protegida por token e chamada via REST. Depois da carga ela foi desativada (estado abaixo).

create or replace function public.manutencao_temp(p_token text, p_acao text, p_dados jsonb default '[]'::jsonb)
returns jsonb language plpgsql security definer set search_path = '' as $$
begin
  raise exception 'manutenção temporária desativada';
end;
$$;

revoke execute on function public.manutencao_temp(text, text, jsonb) from anon, authenticated, public;
