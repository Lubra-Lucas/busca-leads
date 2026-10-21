"""Enriquecimento de contatos de EMPRESAS já existentes (marcas, fornecedores, salões, varejo, investidores).

Reaproveita enriquecer_contatos.py (leitura de site, CNPJ/BrasilAPI, classificação direto/comercial/agencia/geral/sac).
Fluxo usado (arquivos "chave|nome|site|email_atual", chave = 8 primeiros chars do id):
  1. python3 -I scripts/enriquecer_contatos.py sites leads.txt saida.json         (leitura simples)
  2. node renderizar_sites.mjs leads.json paginas.json  +  enriquecer_contatos.py renderizado ...   (sites com 403/JS)
  3. python3 -I scripts/enriquecer_empresas.py sql saida.json [mais.json ...]     (imprime o UPDATE para o Supabase)
  4. python3 -I scripts/enriquecer_empresas.py cnpj <cnpj> [site]                 (confere razão social/sócios/telefone)

Diferenças do `sql` do enriquecer_contatos.py: score só sobe (+10 se ganhou o primeiro contato, +5 se passou a ter
contato comercial/direto/agência), `contato_qualidade` nunca piora, e o contato_nome do CNPJ só entra se o campo
estiver vazio. Sem DELETE. Nada é adivinhado: só contato publicado pela própria fonte.
"""
import importlib.util
import json
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('ec', AQUI / 'enriquecer_contatos.py')
EC = importlib.util.module_from_spec(spec)
spec.loader.exec_module(EC)

SQL = """update public.leads l set
  email = case when v.email is not null and (coalesce(l.email,'')='' or lower(l.email)=v.old) then v.email else l.email end,
  telefone = coalesce(nullif(l.telefone,''), v.tel),
  whatsapp = coalesce(nullif(l.whatsapp,''), v.zap),
  contato_nome = coalesce(nullif(l.contato_nome,''), v.cnome),
  contato_cargo = coalesce(nullif(l.contato_cargo,''), v.ccargo),
  linkedin = coalesce(nullif(l.linkedin,''), v.lin),
  score = least(100, greatest(coalesce(l.score,0), coalesce(l.score,0)
     + case when coalesce(l.email,'')='' and coalesce(l.telefone,'')='' and coalesce(l.whatsapp,'')=''
              and (v.email is not null or v.tel is not null or v.zap is not null) then 10 else 0 end
     + case when v.qual in ('comercial','direto','agencia') and coalesce(l.extras->>'contato_qualidade','') not in ('comercial','direto','agencia') then 5 else 0 end)),
  extras = coalesce(l.extras,'{{}}'::jsonb) || jsonb_build_object(
    'contato_qualidade', case when coalesce(array_position(array['sac','geral','agencia','comercial','direto'], v.qual),0)
        > coalesce(array_position(array['sac','geral','agencia','comercial','direto'], l.extras->>'contato_qualidade'),0) then v.qual
        else coalesce(l.extras->>'contato_qualidade', v.qual) end,
    'contatos', coalesce(l.extras->'contatos','[]'::jsonb) || (select coalesce(jsonb_agg(c || '{{"data":"2026-10-21"}}'::jsonb), '[]'::jsonb)
       from jsonb_array_elements(v.cs::jsonb) c
       where not exists (select 1 from jsonb_array_elements(coalesce(l.extras->'contatos','[]'::jsonb)) e
         where coalesce(e->>'email','')=coalesce(c->>'email','') and coalesce(e->>'telefone','')=coalesce(c->>'telefone','')
           and coalesce(e->>'whatsapp','')=coalesce(c->>'whatsapp',''))))
from (values
{valores}
) as v(k, email, old, tel, zap, cnome, ccargo, lin, qual, cs)
where left(l.id::text,8)=v.k;"""


def cmd_sql(arqs):
    q = EC.q
    linhas = []
    for arq in arqs:
        for r in json.load(open(arq)):
            cs = [c for c in r.get('contatos', []) if c.get('fonte') != 'cadastro anterior']
            if not cs:
                continue
            cs = [{**{k: v for k, v in c.items() if k != 'manual'},
                   'fonte': re.sub(r'^https?://(www\.)?', '', c['fonte'].split('?')[0])[:80]}
                  for c in sorted(cs, key=lambda c: -EC.RANK[c['tipo']])[:6]]
            linhas.append(f"({q(r['chave'])},{q(r.get('email'))},{q(r.get('old_email') or '')},{q(r.get('telefone'))},"
                          f"{q(r.get('whatsapp'))},{q(r.get('contato_nome'))},{q(r.get('contato_cargo'))},{q(r.get('linkedin'))},"
                          f"{q(r.get('qualidade'))},{q(json.dumps(cs, ensure_ascii=False, separators=(',', ':')))})")
    print(SQL.format(valores=',\n'.join(linhas)))


def cmd_cnpj(cnpj, site=''):
    d = EC.cnpj_info(cnpj)
    if not d:
        sys.exit('CNPJ não encontrado')
    print(d.get('razao_social'), '|', d.get('nome_fantasia'), '|', d.get('descricao_situacao_cadastral'), '|',
          d.get('municipio'), d.get('uf'), '|', d.get('ddd_telefone_1'), '|',
          [(s['nome_socio'], s['qualificacao_socio']) for s in d.get('qsa', [])][:4])
    if site:
        import requests
        r = requests.get(site if site.startswith('http') else f'https://www.{site}', timeout=20, headers={'User-Agent': EC.ES.UA})
        achados = set(EC.CNPJ.findall(re.sub(r'<[^>]+>', ' ', r.text)))
        print('CNPJ no rodapé do site:', achados or 'nenhum', '| confere:', re.sub(r'\D', '', cnpj) in {re.sub(r'\D', '', a) for a in achados})


if __name__ == '__main__':
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    {'sql': lambda: cmd_sql(a[1:]), 'cnpj': lambda: cmd_cnpj(*a[1:3])}[a[0]]()
