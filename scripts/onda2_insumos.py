"""Onda 2 – fornecedores de insumos cosméticos (pigmentos, matérias-primas, essências; tipo 'fornecedor').

Uso (python3 -I scripts/onda2_insumos.py ...):
  coletar <cands.txt> <saida.json>      reaproveita onda2_terceirizadoras.coletar ("nome|site|cidade|uf"): lê o site, CNPJ/BrasilAPI e contatos.
  sql <saida.json> [mais.json ...]      aplica a curadoria (CUR: segmento, subsegmento, produtos, UF, pedido mínimo, exclusões),
                                        calcula o score e imprime o INSERT ... ON CONFLICT DO NOTHING.
Score = 40 + insumo direto p/ pó compacto (pigmento/mica/talco/sericita/ligante) 25 (outros 10) + SP 15 + contato comercial/direto 10
(geral 5) + atende pequenos lotes 5, teto 95. Só entra quem tem e-mail/WhatsApp/telefone publicado no site oficial ou no CNPJ.
"""
import importlib.util
import json
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('terc', AQUI / 'onda2_terceirizadoras.py')
T = importlib.util.module_from_spec(spec)
spec.loader.exec_module(T)
EC = T.EC
FONTE = 'Busca onda 2 – fornecedores de insumos'
DATA = '2026-10-21'

P, M, E = 'pigmentos', 'materias_primas', 'essencias'
# site: (segmento, subsegmento, direto_po, pequenos_lotes, produtos, extras)
CUR = {
    'forscher.com.br': (P, 'Pigmentos e micas', 1, 0, ['mica', 'sericita', 'talco', 'óxidos de ferro', 'dióxido de titânio', 'pigmentos orgânicos e inorgânicos'], {}),
    'botticabotanika.com.br': (P, 'Óxidos de ferro e micas (pequenos lotes)', 1, 1, ['óxidos de ferro', 'micas', 'pigmentos naturais', 'conservantes', 'emolientes'], {}),
    'imperiodasessencias.com.br': (P, 'Micas e pigmentos (pequenos lotes)', 1, 1, ['micas', 'pigmentos cosméticos', 'glitter', 'essências', 'silicones'], {'pedido_minimo': 'Lote mínimo: 100 unidades'}),
    'colormake.com.br': (P, 'Glitter cosmético e pigmentos', 1, 1, ['glitter biodegradável', 'pigmentos perolados', 'micas'], {'obs': 'atacado só com CNPJ'}),
    'allpigments.com.br': (P, 'Pigmentos e efeitos', 1, 0, ['pigmentos', 'pigmentos de efeito', 'glitter'], {}),
    'sensient-beauty.com': (P, 'Pigmentos e cores cosméticas', 1, 0, ['pigmentos inorgânicos', 'pigmentos naturais', 'pós sensoriais'], {}),
    'koboproductsinc.com': (P, 'Pós tratados e pigmentos de superfície', 1, 0, ['pigmentos tratados', 'pós funcionais', 'nitreto de boro', 'micas'], {'uf': 'SP', 'obs': 'unidade brasileira da Kobo Products'}),
    'harmoniearomaterapia.com.br': (P, 'Óxidos de ferro (pequenos lotes)', 1, 1, ['óxidos de ferro', 'insumos cosméticos'], {}),
    'adrivan.com.br': (M, 'Cargas minerais e matérias-primas', 1, 0, ['talco', 'óxido de ferro', 'dióxido de titânio', 'estearato'], {}),
    'bianquimica.com.br': (M, 'Cargas minerais (talco) e estearatos', 1, 1, ['talco', 'estearato', 'micas', 'bases'], {}),
    'brasquim.com.br': (M, 'Distribuidora de matérias-primas', 1, 0, ['micas', 'matérias-primas cosméticas'], {'uf': 'SP'}),
    'chemyunion.com': (M, 'Ativos e matérias-primas', 0, 0, ['ativos cosméticos', 'conservantes', 'emolientes'], {}),
    'mundiquimica.com.br': (M, 'Distribuidora de matérias-primas', 0, 0, ['matérias-primas cosméticas', 'conservantes', 'espessantes'], {}),
    'ipquimicos.com.br': (M, 'Distribuidora de matérias-primas', 0, 0, ['silicones', 'conservantes', 'matérias-primas cosméticas'], {}),
    'royalmarck.com.br': (M, 'Silicones, emolientes e espessantes', 0, 0, ['silicones', 'emolientes', 'espessantes'], {}),
    'delmontequimica.com.br': (M, 'Distribuidora de matérias-primas', 0, 0, ['matérias-primas cosméticas'], {}),
    'polyser.com': (M, 'Distribuidora de matérias-primas', 0, 0, ['matérias-primas cosméticas'], {'uf': 'SP'}),
    'distriol.com.br': (M, 'Óleos e extratos vegetais', 0, 0, ['óleos vegetais', 'extratos'], {}),
    'cosmoquimica.com.br': (M, 'Matérias-primas cosméticas', 0, 0, ['matérias-primas cosméticas'], {'uf': 'SP'}),
    'anastacio.com.br': (M, 'Distribuidora de matérias-primas', 0, 0, ['matérias-primas cosméticas'], {'uf': 'SP'}),
    'alphaquimica.com.br': (M, 'Distribuidora de matérias-primas', 0, 0, ['matérias-primas cosméticas'], {'uf': 'PR', 'cidade': ''}),
    'safic-alcan.com.br': (M, 'Distribuidora de ingredientes cosméticos', 0, 0, ['ingredientes de beleza e cuidado pessoal'], {'uf': 'SP'}),
    'dpsquimica.com.br': (M, 'Óleos, argilas e silicones', 0, 1, ['óleos', 'argilas', 'silicones'], {'pedido_minimo': 'a partir de 1 kg'}),
    'saberquimica.com.br': (M, 'Distribuidora de químicos especiais', 0, 0, ['químicos especiais', 'dióxido de titânio'], {}),
    'rudnik.com.br': (M, 'Distribuidora de matérias-primas', 0, 0, ['especialidades químicas', 'cosméticos e cuidado pessoal'], {}),
    'chemax.com.br': (M, 'Insumos cosméticos', 0, 0, ['insumos cosméticos'], {'uf': 'SP'}),
    'lookquimica.com.br': (M, 'Ativos cosméticos', 0, 0, ['ativos cosméticos'], {'uf': 'SP'}),
    'nanovetores.com.br': (M, 'Ativos encapsulados', 0, 0, ['ativos nanoencapsulados', 'filtros solares'], {'uf': 'SC'}),
    'foxessencias.com.br': (E, 'Casa de fragrâncias', 0, 0, ['essências para cosméticos', 'perfumaria', 'limpeza'], {}),
    'ramosfragrancias.com.br': (E, 'Casa de fragrâncias', 0, 0, ['fragrâncias finas', 'higiene corporal'], {}),
    'artsessencias.com.br': (E, 'Casa de fragrâncias', 0, 0, ['fragrâncias para cosméticos e perfumaria'], {}),
    'paraisodasessencias.com.br': (E, 'Essências (varejo e atacado)', 0, 1, ['essências', 'insumos'], {}),
    'casadasessencias.com.br': (E, 'Essências (varejo e atacado)', 0, 1, ['essências', 'micas'], {}),
    'artefeita.com.br': (E, 'Essências (pequenos lotes)', 0, 1, ['essências', 'difusores'], {}),
    'mixdasessencias.com.br': (E, 'Essências e matérias-primas', 0, 1, ['essências', 'matérias-primas'], {}),
    'apcom.com.br': (E, 'Casa de fragrâncias', 0, 0, ['essências', 'fragrâncias'], {'uf': 'GO'}),
    'phytoessence.com.br': (E, 'Casa de fragrâncias', 0, 0, ['perfumaria fina', 'personal care', 'home care'], {}),
    'aromallis.com.br': (E, 'Casa de fragrâncias', 0, 0, ['fragrâncias', 'óleos essenciais'], {}),
    'isan.com.br': (E, 'Casa de fragrâncias', 0, 0, ['perfumaria fina', 'personal care'], {}),
    'karph.com.br': (E, 'Casa de fragrâncias', 0, 0, ['fragrâncias'], {}),
    'viaaroma.com.br': (E, 'Casa de fragrâncias', 0, 0, ['fragrâncias'], {'uf': 'RS'}),
    'aromaty.com.br': (E, 'Casa de fragrâncias', 0, 0, ['fragrâncias'], {'uf': 'SP'}),
    'vollmens.com.br': (E, 'Fragrâncias e aromas', 0, 0, ['fragrâncias'], {'uf': 'SP'}),
}
CUR = {k: v for k, v in CUR.items() if v}


def score(c, r):
    seg, sub, direto, pl, prod, ex = c
    uf = (ex.get('uf') or r.get('uf') or '').upper()
    s = 40 + (25 if direto else 10) + (15 if uf == 'SP' else 0)
    s += 10 if r.get('qualidade') in ('comercial', 'direto', 'agencia') else (5 if r.get('qualidade') == 'geral' else 0)
    return min(95, s + (5 if pl else 0))


def linhas(arqs):
    base = {}
    for a in arqs:
        for r in json.load(open(a, encoding='utf-8')):
            base[r['site']] = r
    out = []
    for site, c in CUR.items():
        r = base.get(site)
        if not r or not (r.get('email') or r.get('whatsapp') or r.get('telefone')):
            continue
        seg, sub, direto, pl, prod, ex = c
        ci = r.get('cnpj_info') or {}
        uf = ex.get('uf') or r.get('uf')
        cidade = ex['cidade'] or None if 'cidade' in ex else r.get('cidade')
        if not uf and (r.get('telefone') or '').startswith('+55'):
            uf = T.DDD_UF.get(int(r['telefone'][3:5]))
        cs = [{k: v for k, v in x.items() if k != 'manual'} | {'data': DATA, 'fonte': re.sub(r'^https?://(www\.)?', '', x.get('fonte') or site)[:90]}
              for x in sorted(r['contatos'], key=lambda x: -EC.RANK[x['tipo']])[:3]]
        extras = {'contatos': cs, 'contato_qualidade': r.get('qualidade'), 'produtos': prod, 'enriquecimento': 'site + BrasilAPI (onda 2 insumos)',
                  'onda': 'onda2_2026-10-21', 'insumo_direto_po_compacto': bool(direto), 'pequenos_lotes': bool(pl)}
        if ci.get('cnpj') and EC.norm(ci.get('municipio')) == EC.norm(cidade):
            extras['cnpj'] = ci['cnpj']
        if ex.get('pedido_minimo') or r.get('pedido_minimo'):
            extras['pedido_minimo'] = ex.get('pedido_minimo') or r['pedido_minimo']
        if ex.get('obs'):
            extras['obs'] = ex['obs']
        q = T.q
        lin = r.get('linkedin')
        if lin and re.search(r'company/(google|manuchar)', lin):
            lin = None  # página errada
        linhas_ = (f"({q(seg)},{q(site)},{q(r['nome'])},{q(r.get('contato_nome'))},{q(r.get('contato_cargo'))},{q(sub)},{q(cidade)},{q((uf or '').upper())},"
                   f"{q(r.get('instagram'))},{q(lin)},{q(r.get('email'))},{q(r.get('telefone'))},{q(r.get('whatsapp'))},{q('https://' + site)},"
                   f"{score(c, r)},{q(json.dumps(extras, ensure_ascii=False, separators=(',', ':')))})")
        out.append(linhas_)
    return out


SQL = """insert into public.leads (tipo, segmento_id, nome, contato_nome, contato_cargo, subsegmento, cidade, uf, site, instagram, linkedin,
  email, telefone, whatsapp, fonte, fonte_url, score, status, extras)
select 'fornecedor', v.seg, v.nome, v.cnome, v.ccargo, v.sub, v.cidade, v.uf, v.site, v.insta, v.lin, v.email, v.tel, v.zap,
  '{fonte}', v.furl, v.score, 'novo', v.extras::jsonb
from (values
{valores}
) as v(seg, site, nome, cnome, ccargo, sub, cidade, uf, insta, lin, email, tel, zap, furl, score, extras)
where not exists (select 1 from public.leads l where regexp_replace(lower(coalesce(l.site,'')), '^https?://(www\\.)?|/.*$', '', 'g') = v.site)
on conflict do nothing;"""


def main():
    a = sys.argv[1:]
    if a[:1] == ['coletar']:
        T.cmd_coletar(a[1], a[2])
    elif a[:1] == ['sql']:
        ls = linhas(a[1:])
        print(SQL.format(fonte=FONTE, valores=',\n'.join(ls)))
        print(f'-- {len(ls)} linhas', file=sys.stderr)
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
