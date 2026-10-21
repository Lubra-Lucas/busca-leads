"""Onda 2 - marcas de beleza brasileiras: descobre site, le contatos publicados e gera o INSERT para o Supabase.

Uso (python3 -I scripts/onda2_marcas_beleza.py ...):
  feira <expositores.json> <saida.json>  expositores da Beauty Fair (API do site, 491 em 2026) -> candidatos (site ou @ do link)
  nomes <nomes.txt> <saida.json>         "Nome|subsegmento|UF|grande(0/1)|site?" -> descobre o dominio (teste de
                                         dominios provaveis; so aceita se a pagina cita a marca e o ramo)
  coletar <candidatos.json> <saida.json> visita home + /contato, /atacado... e CNPJ do rodape (BrasilAPI) usando
                                         enriquecer_contatos.py; classifica o contato; descarta quem nao tem nenhum
  renderizado <candidatos.json> <paginas.json> <saida.json>
                                         igual a coletar, a partir do HTML salvo por renderizar_sites.mjs (sites em JS)
  sql <coletados.json> <lote> <tam>      imprime INSERT ... ON CONFLICT DO NOTHING (lote de <tam> marcas)
Regras: so entra marca com e-mail, WhatsApp ou telefone publicado na pagina oficial/CNPJ; nada e inventado.
"""
import importlib.util
import json
import re
import sys
import threading
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

AQUI = Path(__file__).resolve().parent
DATA = '2026-10-21'
FONTE = 'Busca onda 2 – marcas de beleza'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'


def carregar(nome):
    spec = importlib.util.spec_from_file_location(nome, AQUI / f'{nome}.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


EC = carregar('enriquecer_contatos')
ES = EC.ES
TT = carregar('tiktok_shop')

# domínios que não são marca própria (marketplaces, mídia, redes, varejistas multimarcas, plataformas)
BLOQUEIO = re.compile(
    r'(mercadolivre|amazon|shopee|magazineluiza|magalu|americanas|casasbahia|submarino|aliexpress|shein|olx|'
    r'instagram|facebook|tiktok|youtube|pinterest|linkedin|twitter|x\.com|wikipedia|reddit|google|bing|'
    r'belezanaweb|sephora|epocacosmeticos|amobeleza|drogasil|drogaraia|paguemenos|araujo|panvel|pacheco|saopaulo|'
    r'ultrafarma|onofre|renner|cea\.com|riachuelo|marisa|havan|carrefour|extra|paodeacucar|natura\.com|boticario|'
    r'elle\.|vogue|glamour|claudia|marieclaire|capricho|uol|globo|terra\.com|folha|estadao|exame|forbes|istoe|'
    r'mundodomarketing|meioemensagem|jusbrasil|reclameaqui|trustpilot|blogspot|wordpress|medium|substack|'
    r'shopify|vtex|nuvemshop|tray|lojaintegrada|wix|canva|bol\.com|tiendanube|hotmart|kiwify|cnpj|econodata|'
    r'casadosdados|empresaqui|solutudo|apontador|guiamais|telelistas|yelp|tripadvisor|maps|gov\.br|abihpec|'
    r'beautyfair|cosmoprof|fcecosmetique|incosmetics|anvisa|sebrae|infomoney|valor|istoedinheiro|startse|'
    r'ecommercebrasil|mobiletime|ampliar|pagbrasil|rdstation|zapier|kitsune)', re.I)
VAREJISTA = re.compile(r'maybelline|l.or[eé]al|dior|chanel|lanc[oô]me|mac cosmetics|nars|urban decay|benefit|estee|'
                       r'clinique|shiseido|kerastase|wella|schwarzkopf|vichy|la roche|nivea|dove|pantene|garnier|'
                       r'avene|bioderma|cerave|neutrogena|revlon|max factor|rimmel|bourjois|kiko|huda|fenty', re.I)
PRIVATE = re.compile(r'private label|terceiriza[cç][aã]o|fabricamos para|fabrica[cç][aã]o para terceiros|marca branca|f[aá]brica de cosm', re.I)
TERMOS = {
    'Maquiagem': r'batom|p[oó] compacto|blush|sombra|iluminador|bronzer|corretivo|base l[ií]quida|m[aá]scara de c[ií]lios|'
                 r'paleta|delineador|gloss|primer|maquiagem|makeup|make-up',
    'Skincare': r'skincare|s[eé]rum|hidratante facial|protetor solar|vitamina c|[aá]cido hialur|dermocosm|limpeza facial|'
                r'anti-?idade|antiacne|pele',
    'Cabelo': r'shampoo|condicionador|m[aá]scara capilar|leave-?in|cronograma capilar|progressiva|tratamento capilar|'
              r'cabelo|capilar|hair',
    'Unhas': r'esmalte|nail|unhas|manicure',
    'Perfumaria': r'perfume|body splash|col[oô]nia|[aá]gua de cheiro|fragr[aâ]ncia|eau de|desodorante col',
}
TL = threading.local()
_cnpj_orig = EC.cnpj_info


def _cnpj_guarda(c):
    info = _cnpj_orig(c)
    TL.cnpj = (re.sub(r'\D', '', c), info)
    return info


EC.cnpj_info = _cnpj_guarda


def norm(s):
    s = unicodedata.normalize('NFKD', str(s or '')).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]', '', s)


def dominio(url):
    return ES.dominio_base(url)


# ---------------------------------------------------------------- descoberta de candidatos
MAPA_CAT = {'maquiagem': 'Maquiagem', 'cilios': 'Maquiagem', 'skincare': 'Skincare', 'protecao-solar-e-bronzeadores': 'Skincare',
            'cabelos': 'Cabelo', 'unhas': 'Unhas', 'perfume': 'Perfumaria', 'barber': 'Barba e masculino', 'sobrancelhas': 'Sobrancelhas', 'depilacao': 'Depilação',
            'estetica': 'Skincare'}


def baixar_feira(saida):
    """Baixa a lista de expositores da Beauty Fair (API publica do CMS)."""
    base = 'https://cms.beautyfair.com.br/beautyfair/wp-json/custom/v1/node?path=expositores&lang=pt'
    out, p = [], 1
    while p <= 60:
        d = requests.get(base, params={'category': '', 'paged': p, 'search': ''}, headers={'User-Agent': UA}, timeout=30).json()
        blk = next(b for b in d['fields']['blocks'] if b.get('type') == 'exhibitors')
        out += blk['list']
        if p >= blk['pagination']['total_pages']:
            break
        p += 1
    Path(saida).write_text(json.dumps(out, ensure_ascii=False), encoding='utf-8')


def cmd_feira(entrada, saida):
    exp = json.loads(Path(entrada).read_text(encoding='utf-8'))
    ok_cat = set(MAPA_CAT) | {'cosmeticos', 'higiene'}

    def um(x):
        cats = [k['value'] for k in x['categories']]
        if not set(cats) & ok_cat:
            return None
        u = ((x.get('link') or {}).get('url') or '').strip()
        c = {'nome': re.sub(r'\s+', ' ', x['title']).strip().title(), 'feira_cats': cats, 'fonte_url': 'https://beautyfair.com.br/expositores/',
             'fonte_nome': 'Beauty Fair 2026 (expositores)'}
        subs = [MAPA_CAT[k] for k in cats if k in MAPA_CAT]
        c['subseg'] = 'Maquiagem' if 'Maquiagem' in subs else (subs[0] if subs else None)
        m = ES.INSTA.search(u + ' ')
        if 'instagram.com' in u:
            if m and m.group(1).lower() not in ES.INSTA_LIXO:
                c['instagram'] = '@' + m.group(1).lower().rstrip('.')
            h = (c.get('instagram') or '').lstrip('@')
            for slug in dict.fromkeys([norm(h.replace('oficial', '')), norm(h)]):
                pass
            c['site'] = EC.descobrir_dominio(c['nome'])
        elif u:
            c['site'] = dominio(u)
        return c

    with ThreadPoolExecutor(8) as ex:
        res = [r for r in ex.map(um, exp) if r]
    print('candidatos', len(res), '| com site', sum(1 for r in res if r.get('site')))
    Path(saida).write_text(json.dumps(res, ensure_ascii=False), encoding='utf-8')


def cmd_nomes(nomes, saida):
    linhas = [(l.split('|') + [''] * 5)[:5] for l in Path(nomes).read_text(encoding='utf-8').splitlines()
              if l.strip() and not l.startswith('#')]

    def um(c):
        nome, sub, uf, grande, site = [x.strip() for x in c]
        fonte_url = None
        if not site:
            site = EC.descobrir_dominio(nome)
        return {'nome': nome, 'subseg': sub or None, 'uf': uf or None, 'grande': grande == '1', 'site': site,
                'fonte_url': fonte_url}

    with ThreadPoolExecutor(6) as ex:
        res = list(ex.map(um, linhas))
    print('com site:', sum(1 for r in res if r['site']), '/', len(res))
    Path(saida).write_text(json.dumps(res, ensure_ascii=False), encoding='utf-8')


# ---------------------------------------------------------------- coleta
def texto_de(html):
    html = re.sub(r'(?is)<(script|style|svg|noscript)\b.*?</\1>', ' ', html)
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', html))


def nome_da_pagina(html, site):
    m = re.search(r'property=["\']og:site_name["\'] content=["\']([^"\']{2,50})', html) or \
        re.search(r'content=["\']([^"\']{2,50})["\'] property=["\']og:site_name', html)
    if m:
        return m.group(1).strip()
    t = re.search(r'<title[^>]*>(.*?)</title>', html, re.S | re.I)
    if t:
        return re.split(r'\s[|\-–—:]\s', re.sub(r'\s+', ' ', t.group(1)).strip())[-1 if False else 0][:50]
    return site.split('.')[0].title()


def coletar_um(c, paginas=None):
    site = c['site']
    lead = {'chave': norm(site)[:12], 'nome': c.get('nome') or site, 'site': site, 'email_atual': ''}
    TL.cnpj = None
    if paginas is None:
        lead_, paginas = EC.baixar_site(lead)
    if not paginas:
        return {**c, 'erro': 'site fora do ar'}
    home = paginas[0][1]
    txt = ' '.join(texto_de(h) for _, h in paginas[:3])
    meta = ' '.join(re.findall(r'<(?:title|meta[^>]+(?:description|og:title)[^>]*)[^>]*>([^<]*)', home, re.I) + re.findall(r'content=["\']([^"\']{20,300})', home[:30000]))
    txt += ' ' + meta
    if not c.get('nome'):
        lead['nome'] = nome_da_pagina(home, site)
    n_ret = len(set(m.lower() for m in VAREJISTA.findall(txt)))
    if n_ret >= 4 and not c.get('grande'):
        return {**c, 'erro': 'multimarcas/varejista'}
    if PRIVATE.search(txt[:6000]):
        return {**c, 'erro': 'fabricante terceirizada (outro agente)'}
    cont = {k: len(re.findall(p, txt, re.I)) for k, p in TERMOS.items()}
    if sum(cont.values()) < 3:
        return {**c, 'erro': 'nao parece marca de beleza'}
    res = EC.analisar(lead, paginas)
    instas, tts = set(), set()
    for url, h in paginas:
        instas |= {i for i in ES.extrair(h, url)[3]}
        tts |= {t.lower() for t in TT.TIKTOK_LINK.findall(h)}
    info = getattr(TL, 'cnpj', None)
    out = {**c, 'nome': lead['nome'], 'res': res, 'cont': cont, 'instas': sorted(instas), 'tiktoks': sorted(tts),
           'paginas': [p[0] for p in paginas]}
    if info and info[1]:
        i = info[1]
        out['cnpj'] = info[0]
        out['cidade'] = (i.get('municipio') or '').title() or None
        out['uf_cnpj'] = i.get('uf')
        out['cnae'] = i.get('cnae_fiscal_descricao')
        out['razao'] = i.get('razao_social')
    return out


def cmd_renderizado(entrada, paginas_json, saida):
    cands = {norm(dominio(c['site']))[:12]: c for c in json.loads(Path(entrada).read_text(encoding='utf-8')) if c.get('site')}
    res = []
    for r in json.loads(Path(paginas_json).read_text(encoding='utf-8')):
        c = cands.get(r['id'])
        if c and r['paginas']:
            res.append(coletar_um(c, [(p['url'], p['html']) for p in r['paginas']]))
    Path(saida).write_text(json.dumps(res, ensure_ascii=False), encoding='utf-8')
    print('renderizados', len(res), '| com contato', sum(1 for r in res if r.get('res') and r['res']['contatos']))


def cmd_coletar(entrada, saida):
    cands = json.loads(Path(entrada).read_text(encoding='utf-8'))
    cands = [c for c in cands if c.get('site')]
    vistos, uni = set(), []
    for c in cands:
        d = dominio(c['site'])
        if d not in vistos:
            vistos.add(d)
            uni.append(c)
    with ThreadPoolExecutor(8) as ex:
        res = list(ex.map(lambda c: (lambda: coletar_um(c))() if True else None, uni))
    Path(saida).write_text(json.dumps(res, ensure_ascii=False), encoding='utf-8')
    ok = [r for r in res if r.get('res') and r['res']['contatos']]
    print('visitados', len(res), '| com contato', len(ok))


# ---------------------------------------------------------------- SQL
def q(s):
    return 'null' if s in (None, '') else "'" + str(s).replace("'", "''") + "'"


def montar_registro(r):
    res = r['res']
    contatos = res['contatos']
    for c in contatos:
        c['data'] = DATA
    cont = r['cont']
    sub = r.get('subseg') if r.get('feira_cats') else None
    if r.get('subseg') == 'Marca de influenciadora':
        sub = r['subseg']
    if not sub:
        sub = 'Maquiagem' if cont['Maquiagem'] >= 15 or cont['Maquiagem'] == max(cont.values()) else max(cont, key=cont.get)
    dica = re.search(r'make|maquiag|nail|esmalt|hair|cabel|cacho|derm|skin|perfum|parfum|aroma|lash', r['nome'] + ' ' + r['site'], re.I)
    if dica and not r.get('feira_cats') and r.get('subseg') != 'Marca de influenciadora':
        sub = {'make': 'Maquiagem', 'maquiag': 'Maquiagem', 'nail': 'Unhas', 'esmalt': 'Unhas', 'hair': 'Cabelo', 'cabel': 'Cabelo',
               'cacho': 'Cabelo', 'derm': 'Skincare', 'skin': 'Skincare', 'perfum': 'Perfumaria', 'parfum': 'Perfumaria',
               'aroma': 'Perfumaria', 'lash': 'Maquiagem'}[dica.group(0).lower()]
    uf = r.get('uf_cnpj')
    sp = uf == 'SP'
    pontos = 40
    pontos += 15 if sub in ('Maquiagem', 'Marca de influenciadora') and cont['Maquiagem'] >= 2 else (5 if sub in ('Skincare', 'Cabelo') else 0)
    tipo = res.get('qualidade')
    pontos += {'direto': 15, 'comercial': 15, 'agencia': 10, 'geral': 10, 'sac': 5}.get(tipo, 0)
    pontos += 5 if res.get('whatsapp') else 0
    pontos += 5 if sp else 0
    pontos -= 15 if r.get('grande') else 0
    pontos = min(pontos, 90)
    cats = [k.lower() for k, v in sorted(cont.items(), key=lambda kv: -kv[1]) if v >= 3]
    seg = 'tiktok_perfumaria' if sub == 'Perfumaria' else 'marca_indie'
    ch = norm(re.sub(r'\b(cosm[eé]ticos?|brasil|professional|oficial)\b', '', r['nome'], flags=re.I))[:5] or norm(r['nome'])[:4]
    ch = ch if len(ch) >= 4 else norm(r['nome'])[:4]
    insta = r.get('instagram') or next((i for i in r['instas'] if ch in norm(i) or norm(r['site'].split('.')[0])[:5] in norm(i)), None)
    tk = next((t for t in r['tiktoks'] if ch in norm(t)), None)
    tk = '@' + tk if tk else None
    extras = {'contatos': contatos, 'contato_qualidade': tipo, 'enriquecimento': r['paginas'], 'cnpj': r.get('cnpj'),
              'fonte_origem': r.get('fonte_nome'), 'categorias_produto': cats, 'feira_categorias': r.get('feira_cats'), 'onda': 'onda2_2026-10-21'}
    if r.get('razao'):
        extras['razao_social'] = r['razao']
    site = dominio(r['site'])
    return dict(seg=seg, nome=r['nome'], site=site, insta=insta, tk=tk, email=res.get('email'),
                whats=res.get('whatsapp'), tel=res.get('telefone'), cnome=res.get('contato_nome'),
                ccargo=res.get('contato_cargo'), cidade=r.get('cidade'), uf=uf, sub=sub, fonte_url=r.get('fonte_url') or
                f"https://{site}", score=pontos, extras=extras)


def linha_sql(m):
    return '(' + ','.join([q(m['seg']), q(m['nome']), q(m['site']), q(m['insta']), q(m['tk']), q(m['email']), q(m['whats']),
                           q(m['tel']), q(m['cnome']), q(m['ccargo']), q(m['cidade']), q(m['uf']), q(m['sub']),
                           q(FONTE), q(m['fonte_url']), str(m['score']),
                           q(json.dumps({k: v for k, v in m['extras'].items() if v not in (None, [], '')}, ensure_ascii=False, separators=(',', ':'))) + '::jsonb']) + ')'


COLS = ('segmento_id,nome,site,instagram,tiktok,email,whatsapp,telefone,contato_nome,contato_cargo,cidade,uf,subsegmento,'
        'fonte,fonte_url,score,extras')


def cmd_sql(arq, ini, tam):
    regs = [montar_registro(r) for r in json.loads(Path(arq).read_text(encoding='utf-8'))
            if r.get('res') and r['res']['contatos']]
    lote = regs[int(ini):int(ini) + int(tam)]
    sel = ('v.segmento_id,v.nome,v.site,v.instagram,v.tiktok,v.email,v.whatsapp,v.telefone,v.contato_nome,v.contato_cargo,'
           'v.cidade,v.uf::bpchar,v.subsegmento,v.fonte,v.fonte_url,v.score::smallint,v.extras')
    print(f"insert into leads (tipo,{COLS},status) select 'cliente'::lead_tipo,{sel},'novo'::lead_status from (values\n" +
          ',\n'.join(linha_sql(m) for m in lote) + f"\n) as v({COLS}) on conflict do nothing;")


def main():
    a = sys.argv[1:]
    cmd = {'feira': cmd_feira, 'baixar_feira': baixar_feira, 'nomes': cmd_nomes, 'coletar': cmd_coletar, 'renderizado': cmd_renderizado, 'sql': cmd_sql}.get(a[0] if a else '')
    if not cmd:
        print(__doc__)
        return
    cmd(*a[1:])


if __name__ == '__main__':
    main()
