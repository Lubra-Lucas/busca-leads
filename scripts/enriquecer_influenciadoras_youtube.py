"""Lê a página 'Sobre' do canal oficial do YouTube de cada lead e extrai descrição, links e e-mails.

Uso: python3 -I scripts/enriquecer_influenciadoras_youtube.py <leads.json> <saida.json>
  leads.json: [{id, nome, instagram?, tiktok?, handles?: [..]}]. Testa youtube.com/@handle para os @ informados
  (handles, tiktok, instagram, nome sem espaços). 'verificado' = título do canal bate com o nome OU os links do
  canal citam o instagram/tiktok do lead. Revise a saída antes de gravar no banco (ver CLAUDE.md).
"""
import json, re, sys, unicodedata, urllib.parse
from concurrent.futures import ThreadPoolExecutor
import requests

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0'
EMAIL = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+')


def norm(s):
    s = unicodedata.normalize('NFKD', str(s or '')).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]', '', s)


def canal(handle):
    try:
        r = requests.get(f'https://www.youtube.com/@{handle}/about', timeout=25, allow_redirects=True,
                         headers={'User-Agent': UA, 'Accept-Language': 'pt-BR'}, cookies={'CONSENT': 'YES+1'})
    except Exception:
        return None
    if r.status_code != 200:
        return None
    m = re.search(r'var ytInitialData = (\{.*?\});</script>', r.text, re.S)
    if not m:
        return None
    raw = m.group(1)
    d = json.loads(raw)
    meta = d.get('metadata', {}).get('channelMetadataRenderer', {})
    desc = meta.get('description', '')
    # a aba Sobre (descrição completa e links) vem por uma continuação da API interna do site
    links = set()
    try:
        key = re.search(r'"INNERTUBE_API_KEY":"([^"]+)"', r.text).group(1)
        ver = re.search(r'"INNERTUBE_CONTEXT_CLIENT_VERSION":"([^"]+)"', r.text).group(1)
        tok = re.search(r'"continuationCommand":\{"token":"([^"]+)","request":"CONTINUATION_REQUEST_TYPE_BROWSE"', raw).group(1)
        c = requests.post(f'https://www.youtube.com/youtubei/v1/browse?key={key}', timeout=25, headers={'User-Agent': UA},
                          json={'context': {'client': {'clientName': 'WEB', 'clientVersion': ver, 'hl': 'pt-BR', 'gl': 'BR'}},
                                'continuation': tok}).json()
        v = c['onResponseReceivedEndpoints'][0]['appendContinuationItemsAction']['continuationItems'][0][
            'aboutChannelRenderer']['metadata']['aboutChannelViewModel']
        desc = v.get('description') or desc
        for it in v.get('links', []):
            x = it.get('channelExternalLinkViewModel', {})
            links.add((x.get('title', {}).get('content', '') + ' ' + x.get('link', {}).get('content', '')).strip())
    except Exception:
        pass
    subs = re.search(r'"subscriberCountText":"([^"]+)"', raw)
    return {'handle': handle, 'titulo': meta.get('title'), 'url': meta.get('externalId'),
            'descricao': desc, 'links': sorted(links), 'emails': sorted(set(EMAIL.findall(desc))),
            'inscritos': subs.group(1) if subs else None}


def candidatos(l):
    hs = list(l.get('handles') or [])
    for k in ('tiktok', 'instagram'):
        if l.get(k):
            hs.append(l[k].lstrip('@'))
    hs.append(norm(l['nome']))
    out = []
    for h in hs:
        h = h.replace('.', '') if False else h
        if h and h.lower() not in [x.lower() for x in out]:
            out.append(h)
    return out


def processa(l):
    nome = norm(l['nome'])
    ig = norm(l.get('instagram', '').lstrip('@')) if l.get('instagram') else ''
    tt = norm(l.get('tiktok', '').lstrip('@')) if l.get('tiktok') else ''
    for h in candidatos(l):
        c = canal(h)
        if not c:
            continue
        links_n = norm(' '.join(c['links']))
        ok = (len(nome) >= 4 and (nome in norm(c['titulo']) or norm(c['titulo']) in nome)) or \
             (ig and ig in links_n) or (tt and tt in links_n)
        c['verificado'] = bool(ok)
        return {'id': l['id'], 'nome': l['nome'], **c}
    return {'id': l['id'], 'nome': l['nome'], 'canal': None}


if __name__ == '__main__':
    leads = json.load(open(sys.argv[1]))
    with ThreadPoolExecutor(6) as ex:
        res = list(ex.map(processa, leads))
    json.dump(res, open(sys.argv[2], 'w'), ensure_ascii=False, indent=1)
    print(sum(1 for r in res if r.get('verificado')), 'verificados de', len(res))
