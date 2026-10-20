"""Descobre o TikTok de cada marca e verifica se ela vende no TikTok Shop (dados públicos do perfil).

Uso:
  python3 scripts/tiktok_shop.py existentes <leads.json> <saida.json>
      leads já cadastrados ({id, nome, site, instagram, tiktok}); procura o @ no rodapé do site,
      depois testa o mesmo @ do Instagram.
  python3 scripts/tiktok_shop.py candidatos <candidatos.json> <saida.json>
      marcas novas ({nome, site?, handles?: [...]}); testa os @ informados e variações do nome.

O perfil público do TikTok traz seguidores, verificado, link da bio e o indicador "ttSeller" (conta
vendedora do TikTok Shop). Só aceitamos um @ quando ele veio do site da marca ou quando o nome do perfil
bate com o nome da marca.
"""
import json
import random
import re
import sys
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor

import requests

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'
TIKTOK_LINK = re.compile(r'tiktok\.com/@([A-Za-z0-9_.]{2,24})')
GENERICAS = re.compile(r'\b(oficial|official|brasil|brazil|br|cosmeticos|cosmetics|cosmetic|beauty|makeup|make|store|loja|'
                       r'shop|professional|profissional|by|the|de|da|do|e)\b')


def norm(s):
    s = unicodedata.normalize('NFKD', str(s or '')).encode('ascii', 'ignore').decode().lower()
    s = re.sub(r'\(.*?\)', ' ', s)
    return re.sub(r'[^a-z0-9]', '', GENERICAS.sub(' ', s))


def parecido(nome, handle, apelido):
    n = norm(nome)
    if len(n) < 3:
        return False
    alvos = [norm(handle), norm(apelido)]
    return any(n in a or (len(a) >= 4 and a in n) for a in alvos if a)


def perfil(handle, tentativas=3):
    handle = handle.lstrip('@').lower()
    for i in range(tentativas):
        try:
            r = requests.get(f'https://www.tiktok.com/@{handle}', timeout=25,
                             headers={'User-Agent': UA, 'Accept-Language': 'pt-BR,pt;q=0.9'})
            m = re.search(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>', r.text, re.S)
            if m:
                u = json.loads(m.group(1)).get('__DEFAULT_SCOPE__', {}).get('webapp.user-detail', {})
                if u.get('statusCode') not in (0, None):
                    return None  # perfil não existe
                ui = u.get('userInfo', {})
                user, st = ui.get('user', {}), ui.get('stats', {})
                if not user.get('uniqueId'):
                    return None
                return {
                    'handle': '@' + user['uniqueId'].lower(), 'nome_perfil': user.get('nickname'),
                    'verificado': bool(user.get('verified')), 'seguidores': st.get('followerCount'),
                    'curtidas': st.get('heartCount'), 'videos': st.get('videoCount'),
                    'bio': (user.get('signature') or '')[:300], 'link_bio': (user.get('bioLink') or {}).get('link'),
                    'tiktok_shop': bool(user.get('ttSeller')),
                    'conta_comercial': bool((user.get('commerceUserInfo') or {}).get('commerceUser')),
                    'privado': bool(user.get('privateAccount')),
                }
        except (requests.RequestException, ValueError):
            pass
        time.sleep(2 + i * 3 + random.random())  # página sem dados costuma ser limite temporário
    return {'erro': 'sem resposta'}


def handles_do_site(site):
    url = site if site.startswith('http') else f'https://{site}'
    try:
        r = requests.get(url, timeout=15, headers={'User-Agent': UA})
        achados = [h.lower().rstrip('.') for h in TIKTOK_LINK.findall(r.text)]
        # links quebrados ("tiktok.com/@https") e padrões de template de site ("@wix") não são da marca
        lixo = {'tiktok', 'share', 'discover', 'https', 'http', 'www', 'wix', 'shopify', 'nuvemshop', 'vtex', 'username', 'seuperfil'}
        return list(dict.fromkeys(h for h in achados if h not in lixo and '.com' not in h))
    except requests.RequestException:
        return []


def variacoes(nome):
    base = norm(nome)
    if len(base) < 3:
        return []
    return [base, f'{base}oficial', f'{base}.oficial', f'{base}_oficial', f'{base}brasil', f'{base}.br', f'{base}br']


def resolver(lead, modo):
    tentativas = []  # (handle, veio_do_site)
    if lead.get('tiktok'):
        tentativas.append((lead['tiktok'].lstrip('@'), True))
    if lead.get('site'):
        tentativas += [(h, True) for h in handles_do_site(lead['site'])]
    tentativas += [(h.lstrip('@'), False) for h in lead.get('handles', [])]
    if lead.get('instagram'):
        tentativas.append((lead['instagram'].lstrip('@'), False))
    if modo == 'candidatos':
        tentativas += [(h, False) for h in variacoes(lead['nome'])]

    vistos = set()
    for h, confiavel in tentativas:
        if h.lower() in vistos:
            continue
        vistos.add(h.lower())
        p = perfil(h)
        time.sleep(0.6 + random.random())
        if not p or 'erro' in p:
            continue
        # sem vir do site, um perfil quase sem seguidores costuma ser homônimo, não a marca
        if confiavel or (parecido(lead['nome'], p['handle'], p['nome_perfil']) and (p['seguidores'] or 0) >= 100):
            p['origem_handle'] = 'site da marca' if confiavel else 'nome/Instagram conferido'
            return {**lead, 'tiktok_encontrado': p}
    return {**lead, 'tiktok_encontrado': None}


def main():
    modo, entrada, saida = sys.argv[1:4]
    leads = json.load(open(entrada))
    with ThreadPoolExecutor(max_workers=4) as pool:
        res = list(pool.map(lambda l: resolver(l, modo), leads))
    json.dump(res, open(saida, 'w'), ensure_ascii=False, indent=1)
    achados = [r for r in res if r['tiktok_encontrado']]
    print(f'leads: {len(res)} | TikTok encontrado: {len(achados)} | vendem no TikTok Shop: '
          f'{sum(1 for r in achados if r["tiktok_encontrado"]["tiktok_shop"])}')


if __name__ == '__main__':
    main()
