"""Acesso rápido ao banco do busca-leads pela API REST do Supabase (sem depender do conector MCP).

Credenciais SEMPRE por variável de ambiente (o repositório é público, nunca grave chave aqui):
  SUPABASE_URL                 https://papaicnydbcajkfghwem.supabase.co (padrão, se não definida)
  SUPABASE_SERVICE_ROLE_KEY    chave secreta (Supabase > Project Settings > API keys) — ignora RLS, leitura e escrita
  ou SUPABASE_EMAIL + SUPABASE_SENHA   conta de usuário do site — passa pelo RLS (qualquer usuário logado lê e edita)

Uso (python3 -I scripts/db.py ...):
  get    <tabela> [query]          ex.: get leads "select=nome,email&segmento_id=eq.influenciadora&limit=5"
  count  <tabela> [query]          ex.: count leads "email=is.null&whatsapp=is.null&telefone=is.null"
  patch  <tabela> <query> <json>   ex.: patch leads "id=eq.<uuid>" '{"status":"contatado"}'
  post   <tabela> <json>           insere uma linha (ou lista de linhas)

Filtros seguem o PostgREST: https://postgrest.org/en/stable/references/api/tables_views.html
"""
import json
import os
import sys
import urllib.request

URL = os.environ.get('SUPABASE_URL', 'https://papaicnydbcajkfghwem.supabase.co').rstrip('/')
PUBLICAVEL = 'sb_publishable_RPFXNIMe-jQeGUVpCi4UYQ_J0lDgfcA'  # chave pública, já usada pelo site


def _req(metodo, caminho, corpo=None, cabecalhos=None, chave=None):
    h = {'apikey': chave or PUBLICAVEL, 'Content-Type': 'application/json'}
    h.update(cabecalhos or {})
    dados = json.dumps(corpo).encode() if corpo is not None else None
    r = urllib.request.Request(URL + caminho, data=dados, method=metodo, headers=h)
    with urllib.request.urlopen(r, timeout=60) as resp:
        texto = resp.read().decode()
        return resp.headers, (json.loads(texto) if texto else None)


def autenticar():
    secreta = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
    if secreta:
        return secreta, {'Authorization': f'Bearer {secreta}'}
    email, senha = os.environ.get('SUPABASE_EMAIL'), os.environ.get('SUPABASE_SENHA')
    if not (email and senha):
        sys.exit('Defina SUPABASE_SERVICE_ROLE_KEY ou SUPABASE_EMAIL + SUPABASE_SENHA (ver CLAUDE.md).')
    _, sessao = _req('POST', '/auth/v1/token?grant_type=password', {'email': email, 'password': senha})
    return PUBLICAVEL, {'Authorization': f"Bearer {sessao['access_token']}"}


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    acao, tabela, resto = sys.argv[1], sys.argv[2], sys.argv[3:]
    chave, auth = autenticar()
    base = f'/rest/v1/{tabela}'
    if acao == 'get':
        _, dados = _req('GET', f"{base}?{resto[0] if resto else 'limit=20'}", cabecalhos=auth, chave=chave)
        print(json.dumps(dados, ensure_ascii=False, indent=1))
    elif acao == 'count':
        q = resto[0] + '&' if resto else ''
        cab, _ = _req('GET', f'{base}?{q}select=id&limit=1', cabecalhos={**auth, 'Prefer': 'count=exact'}, chave=chave)
        print(cab.get('Content-Range', '').split('/')[-1])
    elif acao == 'patch':
        _, dados = _req('PATCH', f'{base}?{resto[0]}', json.loads(resto[1]),
                        {**auth, 'Prefer': 'return=representation'}, chave)
        print(f'{len(dados or [])} linha(s) alterada(s)')
    elif acao == 'post':
        _, dados = _req('POST', base, json.loads(resto[0]), {**auth, 'Prefer': 'return=representation'}, chave)
        print(f'{len(dados or [])} linha(s) inserida(s)')
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
