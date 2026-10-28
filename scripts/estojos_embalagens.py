"""Varre o site dos fornecedores de embalagem atrás de evidência de ESTOJO para maquiagem compacta
(estojo compacto, paleta, godê/pan, book, case de pó/blush/sombra).

Uso: python3 -I scripts/estojos_embalagens.py <entrada.json> <saida.json>
  entrada: lista de leads {id,nome,site,...} (ex.: db.py get leads "segmento_id=eq.embalagens&select=id,nome,site")
Abre a home e até 8 links internos de produto/catálogo/maquiagem e conta os termos achados (com trecho de contexto).
"""
import json, re, sys
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36'}
FORTES = [r'estojos? compactos?', r'estojos? (?:para|de) (?:p[oó]|blush|sombras?|maquiagem|make|iluminador|bronzer)',
          r'paletas? (?:de|para) (?:sombras?|maquiagem|make|blush|contorno)', r'\bpaletas?\b(?! ?de ?madeira)',
          r'\bgod[eê]s?\b', r'\bpans?\b(?= (?:de|para|met))', r'\bcompactos?\b', r'\bbook (?:de|para)? ?(?:maquiagem|sombras?)',
          r'\bcase (?:de|para) (?:p[oó]|maquiagem|blush)', r'p[oó] compacto', r'estojos? magn[eé]tico']
FRACOS = [r'maquiagem', r'\bmake ?up\b', r'\bbatom', r'r[ií]mel|m[aá]scara de c[ií]lios', r'\bgloss\b', r'\bsombra', r'\bblush\b']
LINKS = re.compile(r'produto|catalog|maquiag|make|linha|cosm[eé]t|estojo|beleza|portf|solu', re.I)


def baixar(url):
    try:
        r = requests.get(url, headers=UA, timeout=20)
        if r.ok and 'html' in r.headers.get('content-type', ''):
            return r.text
    except requests.RequestException:
        pass
    return None


def analisar(lead):
    site = (lead.get('site') or '').strip()
    res = {'id': lead['id'], 'nome': lead['nome'], 'site': site, 'abriu': False, 'paginas': 0, 'fortes': {}, 'fracos': {}, 'trechos': []}
    if not site:
        return res
    base = site if site.startswith('http') else 'https://' + site
    html = baixar(base) or baixar(base.replace('https://', 'http://'))
    if not html:
        return res
    res['abriu'] = True
    paginas = [html]
    soup = BeautifulSoup(html, 'html.parser')
    host = urlparse(base).netloc.replace('www.', '')
    vistos = set()
    for a in soup.find_all('a', href=True):
        u = urljoin(base, a['href']).split('#')[0]
        if host in urlparse(u).netloc and (LINKS.search(u) or LINKS.search(a.get_text(' '))) and u not in vistos:
            vistos.add(u)
        if len(vistos) >= 8:
            break
    for u in vistos:
        h = baixar(u)
        if h:
            paginas.append(h)
    res['paginas'] = len(paginas)
    for h in paginas:
        texto = re.sub(r'\s+', ' ', BeautifulSoup(h, 'html.parser').get_text(' ')).lower()
        for grupo, termos in (('fortes', FORTES), ('fracos', FRACOS)):
            for t in termos:
                for m in re.finditer(t, texto):
                    res[grupo][t] = res[grupo].get(t, 0) + 1
                    if grupo == 'fortes' and len(res['trechos']) < 6:
                        res['trechos'].append(texto[max(0, m.start() - 60): m.end() + 60])
    return res


def main():
    leads = json.load(open(sys.argv[1]))
    with ThreadPoolExecutor(12) as ex:
        out = list(ex.map(analisar, leads))
    json.dump(out, open(sys.argv[2], 'w'), ensure_ascii=False, indent=1)
    for r in sorted(out, key=lambda r: -sum(r['fortes'].values())):
        print(sum(r['fortes'].values()), sum(r['fracos'].values()), 'ok' if r['abriu'] else 'X', '|', r['nome'], '|', r['site'])


if __name__ == '__main__':
    main()
