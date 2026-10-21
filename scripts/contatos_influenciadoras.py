"""Busca gratuita de contatos comerciais de influenciadoras sem e-mail/telefone/WhatsApp.

Uso:  python3 -I scripts/contatos_influenciadoras.py <alvo.txt> <saida.json> [--sem-instagram]
      <alvo.txt>: uma influenciadora por linha, campos separados por "|":
      nome|instagram|tiktok|link_bio|assessoria|seguidores

Ordem: (1) bio do perfil público do TikTok (ou o mesmo @ do Instagram no TikTok, se o nome bater);
(2) link da bio / site (linktree, beacons, site próprio): e-mails, mailto: e wa.me/;
(3) página pública do Instagram (se pedir login, para na hora, sem contornar).
Só guarda contato comercial publicado pela própria pessoa; nada de adivinhar e-mail.
Reaproveita tiktok_shop.py e enriquecer_sites.py via importlib.
"""
import importlib.util
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

AQUI = Path(__file__).resolve().parent


def carregar(nome):
    spec = importlib.util.spec_from_file_location(nome, AQUI / f'{nome}.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


TT = carregar('tiktok_shop')
ES = carregar('enriquecer_sites')

OFUSCADO = re.compile(r'([\w.+-]+)\s*[\[\(\{]\s*(?:at|arroba)\s*[\]\)\}]\s*([\w-]+(?:\s*[\[\(\{]\s*(?:dot|ponto)\s*[\]\)\}]\s*[\w-]+)+)', re.I)
PLATAFORMAS = re.compile(r'linktr\.ee|beacons\.ai|linktree|tiktok|instagram|youtube|facebook|gmail\.com\.br|sentry|'
                         r'@2x|\.png|\.jpg|wix|squarespace|canva|hotmart|shopify|bitly|lnk\.to|stan\.store|vsco', re.I)
CONTATO_URL = re.compile(r'contato|contact|parceri|midia|media-?kit|publi', re.I)
NAO_COMERCIAL = re.compile(r'^(sac|suporte|atendimento|ouvidoria|rh|trabalhe|vagas|financeiro|cobranca|lgpd|dpo|privacidade)')
SEM_LINK = re.compile(r'^(link instagram na bio|ver link na bio)$', re.I)
UA = ES.UA


def emails_texto(txt):
    achados = set(ES.EMAIL.findall(txt or ''))
    for m in OFUSCADO.finditer(txt or ''):
        dom = re.sub(r'\s*[\[\(\{]\s*(?:dot|ponto)\s*[\]\)\}]\s*', '.', m.group(2), flags=re.I)
        achados.add(f'{m.group(1)}@{dom}')
    return {e.strip('.').lower() for e in achados}


def limpar_emails(emails, dominio=''):
    bons = []
    for e in emails:
        if PLATAFORMAS.search(e.split('@')[-1]) and not e.endswith('@gmail.com'):
            continue
        if NAO_COMERCIAL.match(e.split('@')[0]):
            continue
        bons.append(e)
    return ES.melhor_email(bons, dominio)[0]


def url_valida(u):
    u = (u or '').strip()
    if not u or SEM_LINK.match(u):
        return None
    u = u.split(' | ')[0].strip()
    if re.search(r'instagram\.com|tiktok\.com|youtube\.com|youtu\.be|vs\.co|facebook\.com', u, re.I):
        return None
    if '.' not in u:
        return None
    return u if u.startswith('http') else 'https://' + u


def ler_pagina(sessao, url):
    html, final = ES.baixar(sessao, url)
    if not html:
        return None
    emails, whats, fones, _, links = ES.extrair(html, final)
    emails |= emails_texto(html)
    return {'emails': emails, 'whats': whats, 'fones': fones, 'links': links, 'url': final}


def da_pagina(sessao, url, seguir=True):
    """Lê a página e, se for site próprio (não agregador), até 2 páginas de contato/mídia kit."""
    p = ler_pagina(sessao, url)
    if not p:
        return None
    agregador = re.search(r'linktr\.ee|beacons|linkbio|lnk\.to|mov\.me|bio\.|links?-?\d*', url, re.I)
    if seguir and not agregador and not (p['emails'] or p['whats']):
        for l in [x for x in p['links'] if CONTATO_URL.search(x)][:2]:
            time.sleep(1)
            q = ler_pagina(sessao, l)
            if q:
                p['emails'] |= q['emails']
                p['whats'] |= q['whats']
                p['fones'] |= q['fones']
                if q['emails'] or q['whats']:
                    p['url'] = q['url']
                    break
    return p


def processar(lead):
    s = requests.Session()
    s.headers.update({'User-Agent': UA, 'Accept-Language': 'pt-BR,pt;q=0.9'})
    r = {'nome': lead['nome'], 'chave': (lead['instagram'] or lead['tiktok']).lower(), 'achados': []}
    handle_tt, perfil = lead['tiktok'], None
    if handle_tt:
        perfil = TT.perfil(handle_tt)
    elif lead['instagram']:
        cand = lead['instagram'].lstrip('@')
        p = TT.perfil(cand)
        if p and not p.get('erro') and len(TT.norm(lead['nome'])) >= 6 and TT.parecido(lead['nome'], p['handle'], p['nome_perfil']):
            seg_ig = lead['seguidores'] or 0
            if (p['seguidores'] or 0) >= max(20000, 0.15 * seg_ig):
                perfil = p
                r['tiktok_novo'] = p['handle']
    urls = []
    if perfil and not perfil.get('erro'):
        r['tiktok_url'] = f"https://www.tiktok.com/{perfil['handle']}"
        bio = perfil.get('bio') or ''
        e = limpar_emails(emails_texto(bio))
        if e:
            r['achados'].append(('email', e, 'bio TikTok', r['tiktok_url']))
        for m in ES.FONE_LINK.findall(bio):
            f = ES.normalizar_fone(m)
            if f:
                r['achados'].append(('whatsapp', f, 'bio TikTok', r['tiktok_url']))
        if perfil.get('link_bio'):
            urls.append(perfil['link_bio'])
    urls.append(lead['link_bio'])
    vistos = set()
    for u in urls:
        u = url_valida(u)
        if not u or u in vistos or any(a[0] == 'email' for a in r['achados']) and any(a[0] == 'whatsapp' for a in r['achados']):
            continue
        vistos.add(u)
        p = da_pagina(s, u)
        time.sleep(1)
        if not p:
            continue
        metodo = 'link da bio' if re.search(r'linktr\.ee|beacons|linkbio|lnk\.to|mov\.me|bio|links', u, re.I) else 'site'
        e = limpar_emails(p['emails'], ES.dominio_base(u))
        if e and not any(a[0] == 'email' for a in r['achados']):
            r['achados'].append(('email', e, metodo, p['url']))
        if p['whats'] and not any(a[0] == 'whatsapp' for a in r['achados']):
            r['achados'].append(('whatsapp', sorted(p['whats'])[0], metodo, p['url']))
    return r


def instagram(lead, sessao):
    """Uma tentativa na página pública; devolve (email|None, bloqueado)."""
    h = lead['instagram'].lstrip('@')
    try:
        resp = sessao.get(f'https://www.instagram.com/{h}/', timeout=15, allow_redirects=True)
    except requests.RequestException:
        return None, True
    if resp.status_code != 200 or 'login' in resp.url:
        return None, True
    m = re.search(r'<meta (?:property="og:description"|name="description") content="([^"]*)"', resp.text)
    e = limpar_emails(emails_texto(m.group(1))) if m else None
    return e, False


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    alvos = []
    for linha in Path(sys.argv[1]).read_text(encoding='utf-8').splitlines():
        c = (linha.split('|') + [''] * 6)[:6]
        alvos.append({'nome': c[0], 'instagram': c[1] or None, 'tiktok': c[2] or None, 'link_bio': c[3] or None,
                      'assessoria': c[4] or None, 'seguidores': int(c[5]) if c[5] else None})
    with ThreadPoolExecutor(3) as ex:
        resultados = list(ex.map(processar, alvos))
    if '--sem-instagram' not in sys.argv:
        s = requests.Session()
        s.headers.update({'User-Agent': UA, 'Accept-Language': 'pt-BR,pt;q=0.9'})
        for lead, r in zip(alvos, resultados):
            if r['achados'] or not lead['instagram']:
                continue
            e, bloqueado = instagram(lead, s)
            if bloqueado:
                print('Instagram exige login; seguindo sem ele.')
                break
            if e:
                r['achados'].append(('email', e, 'bio Instagram', f"https://www.instagram.com/{lead['instagram'].lstrip('@')}/"))
            time.sleep(3)
    Path(sys.argv[2]).write_text(json.dumps(resultados, ensure_ascii=False, indent=1), encoding='utf-8')
    com = sum(1 for r in resultados if r['achados'])
    print(f'{com} de {len(resultados)} com contato novo; TikTok novo: {sum(1 for r in resultados if r.get("tiktok_novo"))}')


if __name__ == '__main__':
    main()
