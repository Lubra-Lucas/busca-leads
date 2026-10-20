"""Enriquece leads visitando o site de cada um: e-mail, WhatsApp, telefone e Instagram.

Uso:  python3 scripts/enriquecer_sites.py <leads.json> <saida.json>
      python3 scripts/enriquecer_sites.py --renderizado <leads.json> <paginas.json> <saida.json>

<leads.json> é uma lista de {id, nome, site, instagram, ...}. Para cada site o script lê a página
inicial e até 4 páginas de contato (links com "contato", "atendimento", "fale conosco" etc.),
sem login e sem formulários. Só guarda o que está publicado no próprio site da empresa.
"""
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'
TIMEOUT = 15
MAX_PAGINAS_CONTATO = 4

PALAVRAS_CONTATO = re.compile(r'contato|contate|fale[-_ ]?conosco|atendimento|contact|sac\b|central[-_ ]de[-_ ]ajuda|'
                              r'quem[-_ ]somos|sobre|about|trabalhe|revend|atacado|parceri', re.I)
CAMINHOS_PADRAO = ['/contato', '/fale-conosco', '/pages/contato', '/atendimento']

EMAIL = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
EMAIL_LIXO = re.compile(r'\.(png|jpe?g|gif|svg|webp|css|js)$|@\dx\.|sentry|wixpress|example\.|exemplo|seuemail|seu-email|'
                        r'email@email|nome@|usuario@|user@|teste@|test@|domain\.com|dominio|godaddy|@sentry|noreply|no-reply|'
                        r'privacy@|lgpd@|dpo@|encarregado|ouvidoria@|@vtex|@shopify|@nuvemshop|@tray|@loja|cliente@cliente|^your@|^seu@|@email$|'
                        r'sualoja|minhaloja|suaempresa|\.comm(\.|$)', re.I)
FONE_LINK = re.compile(r'(?:wa\.me/|api\.whatsapp\.com/send\?phone=|whatsapp\.com/send\?phone=|web\.whatsapp\.com/send\?phone=)\+?(\d{10,13})')
FONE_TEXTO = re.compile(r'(?:\+?55[\s.-]?)?\(\d{2}\)\s?9?\d{4}[\s.-]?\d{4}|\+55[\s.-]?\d{2}[\s.-]?9?\d{4}[\s.-]?\d{4}|0800[\s.-]?\d{3}[\s.-]?\d{4}')
INSTA = re.compile(r'instagram\.com/([A-Za-z0-9_.]{2,30})/?(?:[?#"\'\s]|$)')
INSTA_LIXO = {'p', 'reel', 'reels', 'explore', 'stories', 'accounts', 'tv', 'share', 'instagram', 'direct', 'about'}

# ordem de preferência para abordagem B2B
PREFERIDOS = ['comercial', 'parceria', 'b2b', 'atacado', 'marketing', 'vendas', 'contato', 'contact', 'ola', 'oi',
              'hello', 'falecom', 'faleconosco', 'atendimento', 'sac', 'suporte']


def dominio_base(url):
    d = urlparse(url if '://' in url else f'https://{url}').netloc.lower()
    return re.sub(r'^(www|loja|shop)\.', '', d)


def baixar(sessao, url):
    try:
        r = sessao.get(url, timeout=TIMEOUT, allow_redirects=True)
        tipo = r.headers.get('content-type', '')
        if r.status_code >= 400 or 'html' not in tipo:
            return None, r.url
        return r.text, r.url
    except requests.RequestException:
        return None, url


def decodificar_cfemail(cod):
    """E-mails protegidos pelo Cloudflare (data-cfemail)."""
    try:
        chave = int(cod[:2], 16)
        return ''.join(chr(int(cod[i:i + 2], 16) ^ chave) for i in range(2, len(cod), 2))
    except ValueError:
        return None


def normalizar_fone(digitos):
    d = re.sub(r'\D', '', digitos)
    if d.startswith('0800'):
        return f'0800 {d[4:7]} {d[7:]}' if len(d) == 11 else None
    if d.startswith('55') and len(d) in (12, 13):
        d = d[2:]
    if len(d) not in (10, 11) or d[0] == '0':
        return None
    return f'+55 {d[:2]} {d[2:-4]}-{d[-4:]}'


def eh_celular(fone):
    d = re.sub(r'\D', '', fone or '')[2:]
    return len(d) == 11 and d[2] == '9'


def extrair(html, base):
    sopa = BeautifulSoup(html, 'html.parser')
    texto = sopa.get_text(' ', strip=True)
    emails, whats, fones, instas, links = set(), set(), set(), set(), set()

    for a in sopa.find_all('a', href=True):
        h = a['href'].strip()
        if h.lower().startswith('mailto:'):
            emails.add(h[7:].split('?')[0].strip())
        elif h.lower().startswith('tel:'):
            f = normalizar_fone(h[4:])
            if f:
                fones.add(f)
        else:
            m = FONE_LINK.search(h)
            if m and (f := normalizar_fone(m.group(1))):
                whats.add(f)
            m = INSTA.search(h + ' ')
            if m and m.group(1).lower() not in INSTA_LIXO:
                instas.add('@' + m.group(1).lower().rstrip('.'))
            rotulo = (a.get_text(' ', strip=True) + ' ' + h)[:200]
            if PALAVRAS_CONTATO.search(rotulo):
                links.add(urljoin(base, h).split('#')[0])

    for el in sopa.select('[data-cfemail]'):
        if (e := decodificar_cfemail(el['data-cfemail'])):
            emails.add(e)
    emails.update(EMAIL.findall(texto))
    for m in FONE_TEXTO.findall(texto):
        if (f := normalizar_fone(m)):
            fones.add(f)
    for m in FONE_LINK.findall(html):  # botões de WhatsApp montados por script
        if (f := normalizar_fone(m)):
            whats.add(f)
    return emails, whats, fones, instas, links


def melhor_email(emails, dominio):
    validos = []
    for e in emails:
        e = re.sub(r'^mailto:', '', e.strip().strip('.').lower())
        if '@' not in e or EMAIL_LIXO.search(e) or len(e) > 60:
            continue
        validos.append(e)
    if not validos:
        return None, []
    raiz = dominio.split('.')[0]

    def nota(e):
        local, dom = e.split('@', 1)
        n = 0
        if raiz and raiz in dom:
            n += 10  # e-mail do próprio domínio da marca
        for i, p in enumerate(PREFERIDOS):
            if local.startswith(p):
                n += len(PREFERIDOS) - i
                break
        return n

    validos = sorted(set(validos), key=nota, reverse=True)
    return validos[0], validos


def enriquecer(lead):
    site = lead['site'].strip()
    url = site if site.startswith('http') else f'https://{site}'
    dominio = dominio_base(url)
    sessao = requests.Session()
    sessao.headers.update({'User-Agent': UA, 'Accept-Language': 'pt-BR,pt;q=0.9'})

    html, final = baixar(sessao, url)
    if html is None and not site.startswith('http'):
        html, final = baixar(sessao, f'https://www.{site}')
    if html is None:
        return {'id': lead['id'], 'nome': lead['nome'], 'erro': 'site não abriu'}

    emails, whats, fones, instas, links = extrair(html, final)
    visitadas = [final]
    mesmo_site = [l for l in links if dominio_base(l) == dominio_base(final)]
    candidatos = sorted(mesmo_site, key=lambda l: (not re.search(r'contato|contact|fale', l, re.I), len(l)))
    if not candidatos:
        candidatos = [urljoin(final, c) for c in CAMINHOS_PADRAO]
    for link in candidatos[:MAX_PAGINAS_CONTATO]:
        h, f = baixar(sessao, link)
        if h:
            e2, w2, f2, i2, _ = extrair(h, f)
            emails |= e2
            whats |= w2
            fones |= f2
            instas |= i2
            visitadas.append(f)

    return montar_resultado(lead, dominio, emails, whats, fones, instas, visitadas, 'site da empresa')


def montar_resultado(lead, dominio, emails, whats, fones, instas, visitadas, fonte):
    email, todos_emails = melhor_email(emails, dominio)
    whatsapp = sorted(whats)[0] if whats else next((f for f in sorted(fones) if eh_celular(f)), None)
    telefone = whatsapp or next(iter(sorted(fones)), None)
    raiz = re.sub(r'[^a-z0-9]', '', dominio.split('.')[0])
    # Instagram da própria marca: o @ precisa lembrar o domínio (evita @ de parceiros ou da agência do site)
    insta = next((i for i in sorted(instas) if raiz[:5] and raiz[:5] in re.sub(r'[^a-z0-9]', '', i)), None)
    return {
        'id': lead['id'], 'nome': lead['nome'], 'email': email, 'whatsapp': whatsapp, 'telefone': telefone,
        'instagram': insta if not lead.get('instagram') else None,
        'enriquecimento': {'data': date.today().isoformat(), 'fonte': fonte, 'paginas': visitadas[:5],
                           'emails_encontrados': todos_emails[:5], 'telefones_encontrados': sorted(fones)[:5]},
    }


def de_paginas_renderizadas(lead, paginas):
    """Mesmo processamento, a partir do HTML que o navegador (scripts/renderizar_sites.mjs) salvou."""
    emails, whats, fones, instas, visitadas = set(), set(), set(), set(), []
    for p in paginas:
        e, w, f, i, _ = extrair(p['html'], p['url'])
        emails |= e
        whats |= w
        fones |= f
        instas |= i
        visitadas.append(p['url'])
    return montar_resultado(lead, dominio_base(paginas[0]['url']), emails, whats, fones, instas, visitadas,
                            'site da empresa (navegador)')


def main():
    if sys.argv[1] == '--renderizado':
        # python3 enriquecer_sites.py --renderizado <leads.json> <paginas.json> <saida.json>
        leads = {l['id']: l for l in json.load(open(sys.argv[2]))}
        saida = [de_paginas_renderizadas(leads[r['id']], r['paginas']) for r in json.load(open(sys.argv[3])) if r['paginas']]
        json.dump(saida, open(sys.argv[4], 'w'), ensure_ascii=False, indent=1)
        print(f'renderizados: {len(saida)} | e-mail: {sum(1 for s in saida if s["email"])} | '
              f'WhatsApp: {sum(1 for s in saida if s["whatsapp"])} | telefone: {sum(1 for s in saida if s["telefone"])}')
        return
    leads = json.load(open(sys.argv[1]))
    saida = []
    with ThreadPoolExecutor(max_workers=16) as pool:
        futuros = {pool.submit(enriquecer, l): l for l in leads}
        for i, fut in enumerate(as_completed(futuros), 1):
            try:
                saida.append(fut.result())
            except Exception as e:  # um site com problema não derruba os outros
                l = futuros[fut]
                saida.append({'id': l['id'], 'nome': l['nome'], 'erro': f'{type(e).__name__}: {e}'[:200]})
            if i % 50 == 0:
                print(f'{i}/{len(leads)}', flush=True)
    json.dump(saida, open(sys.argv[2], 'w'), ensure_ascii=False, indent=1)
    ok = [s for s in saida if 'erro' not in s]
    print(f'sites lidos: {len(ok)}/{len(saida)} | e-mail: {sum(1 for s in ok if s["email"])} | '
          f'WhatsApp: {sum(1 for s in ok if s["whatsapp"])} | telefone: {sum(1 for s in ok if s["telefone"])} | '
          f'Instagram novo: {sum(1 for s in ok if s["instagram"])}')


if __name__ == '__main__':
    main()
