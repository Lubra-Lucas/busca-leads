"""Onda 2 - grandes influenciadoras/celebridades: coleta gratuita de @, seguidores e contatos.

Uso: python3 -I scripts/onda2_influenciadoras_grandes.py coletar "Nome 1" "Nome 2" ... > saida.json
Para cada nome: relatório público do IQFluence (@ e seguidores do Instagram, com data), canal do YouTube
(e-mails/sites/links de redes da descrição), perfil público do TikTok e e-mails do site oficial.
Nada é gravado no banco aqui: os dados curados (CANDIDATOS_CURADOS, ao final) foram inseridos por SQL via MCP
depois de revisão manual (só entram leads com contato utilizável; nada inventado).
"""
import html
import json
import re
import sys
import time
import unicodedata
import urllib.parse

import requests

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'
H = {'User-Agent': UA, 'Accept-Language': 'pt-BR,pt;q=0.9', 'Cookie': 'CONSENT=YES+1; SOCS=CAI'}
EM = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[a-z]{2,}')
SOCIAL = re.compile(r'(instagram|facebook|twitter|x\.com|tiktok|kwai|youtube|youtu\.be|spotify|apple\.com|deezer|wa\.me|t\.me|orcd|smarturl|lnk\.to)', re.I)


def slug(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')


def iqfluence(nome, extras=()):
    """Relatório público gratuito: @, seguidores exatos do Instagram e data do relatório."""
    for s in dict.fromkeys([slug(nome), slug(nome).replace('-', '')] + [slug(x) for x in extras] + [x.lower() for x in extras]):
        try:
            r = requests.get(f'https://iqfluence.io/public/free-influencer-reports/{s}', headers=H, timeout=30)
        except requests.RequestException:
            continue
        if r.status_code != 200:
            continue
        t = r.text
        h = re.search(r'<title>([^<]*)</title>', t)
        handle = re.search(r'@([A-Za-z0-9_.]{2,30})\s+(?:Brazilian|[A-Z][a-z]+)', re.sub(r'<[^>]+>', ' ', t))
        exact = re.search(r'changed from [\d,]+ in \w+ \d{4} to ([\d,]+) in (\w+ \d{4})', t)
        short = re.search(r'([\d.]+)\s?([mk])\s+followers', re.sub(r'<[^>]+>', ' ', t))
        gen = re.search(r'Report generated on ([A-Za-z]+ \d+, \d{4})', re.sub(r'<[^>]+>', ' ', t))
        return {'url': r.url, 'titulo': h and html.unescape(h.group(1)), 'handle': handle and '@' + handle.group(1),
                'seguidores_exato': exact and int(exact.group(1).replace(',', '')),
                'seguidores_mes': exact and exact.group(2),
                'seguidores_curto': short and short.group(0), 'relatorio': gen and gen.group(1)}
    return None


def _initial(t):
    m = re.search(r'var ytInitialData = (\{.*?\});</script>', t, re.S)
    return json.loads(m.group(1)) if m else None


def _walk(o, key, out):
    if isinstance(o, dict):
        for k, v in o.items():
            if k == key:
                out.append(v)
            else:
                _walk(v, key, out)
    elif isinstance(o, list):
        for v in o:
            _walk(v, key, out)


def youtube(nome):
    r = requests.get('https://www.youtube.com/results?sp=EgIQAg%253D%253D&search_query=' + urllib.parse.quote(nome), headers=H, timeout=25)
    d = _initial(r.text)
    canais = []
    if d:
        _walk(d, 'channelRenderer', canais)
    if not canais:
        return None
    c = canais[0]
    url = c.get('navigationEndpoint', {}).get('commandMetadata', {}).get('webCommandMetadata', {}).get('url')
    if not url:
        return None
    t = requests.get('https://www.youtube.com' + url + '/about', headers=H, timeout=25).text
    d = re.search(r'"description":"((?:[^"\\]|\\.)*)"', t)
    desc = json.loads('"' + d.group(1) + '"') if d else ''
    links = [urllib.parse.unquote(x) for x in re.findall(r'q=(https?%3A%2F%2F[^"&\\]+)', t)]
    return {'canal': c['title']['simpleText'], 'url': 'https://www.youtube.com' + url, 'verificado': 'ownerBadges' in c,
            'inscritos': (c.get('videoCountText') or {}).get('simpleText'), 'emails': sorted(set(EM.findall(desc))),
            'ig': sorted(set(re.findall(r'instagram\.com/([A-Za-z0-9_.]+)', ' '.join(links)))),
            'tiktok': sorted(set(re.findall(r'tiktok\.com/@([A-Za-z0-9_.]+)', ' '.join(links)))),
            'sites': sorted(set(l for l in links if not SOCIAL.search(l)))[:4], 'desc': desc[:300]}


def tiktok(handle):
    sys.path.insert(0, __file__.rsplit('/', 1)[0])
    import tiktok_shop
    return tiktok_shop.perfil(handle, 1)


def emails_do_site(url):
    achados = {}
    base = url.rstrip('/')
    for p in ('', '/contato', '/contact', '/imprensa'):
        try:
            r = requests.get(base + p, headers=H, timeout=15)
            for e in EM.findall(r.text):
                if not re.search(r'\.(png|jpg|svg|webp)$|sentry|wixpress|example', e, re.I):
                    achados[e.lower()] = base + p
        except requests.RequestException:
            pass
    return achados


def coletar(nome):
    rec = {'nome': nome}
    try:
        rec['yt'] = youtube(nome)
    except Exception as e:  # noqa: BLE001
        rec['yt'] = {'erro': str(e)}
    yt = rec.get('yt') or {}
    try:
        rec['iq'] = iqfluence(nome, yt.get('ig') or [])
    except Exception as e:  # noqa: BLE001
        rec['iq'] = {'erro': str(e)}
    tk = (yt.get('tiktok') or [None])[0]
    if tk:
        rec['tt'] = tiktok(tk)
        rec['emails_tt'] = sorted(set(EM.findall((rec['tt'] or {}).get('bio') or '')))
    sites = {}
    for s in (yt.get('sites') or [])[:2]:
        sites.update(emails_do_site(s))
    rec['emails_sites'] = sites
    return rec


if __name__ == '__main__':
    if sys.argv[1] == 'coletar':
        saida = []
        for n in sys.argv[2:]:
            saida.append(coletar(n))
            time.sleep(1.5)
        json.dump(saida, sys.stdout, ensure_ascii=False, indent=1)
