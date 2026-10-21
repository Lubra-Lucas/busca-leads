"""Onda 2 – maquiadores: raspa contatos (e-mail, WhatsApp, telefone, @Instagram/TikTok) do site de cada
candidato e calcula o score. Uso: python3 -I scripts/onda2_maquiadores.py <urls.txt> <saida.json>
(urls.txt: uma URL por linha). Gera JSON para revisão manual antes do INSERT (ver CLAUDE.md)."""
import json, re, sys, time
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0', 'Accept-Language': 'pt-BR,pt;q=0.9'}
EMAIL = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[a-z]{2,}')
WA = re.compile(r'(?:wa\.me/|api\.whatsapp\.com/send\?phone=|whatsapp\.com/send\?phone=)(\d{10,13})')
TEL = re.compile(r'\(?\b(\d{2})\)?\s?(9?\d{4})[-\s]?(\d{4})\b')
IG = re.compile(r'instagram\.com/([A-Za-z0-9_.]{2,30})')
TT = re.compile(r'tiktok\.com/@([A-Za-z0-9_.]{2,24})')
RUIM = ('example', 'sentry', 'wixpress', '.png', '.jpg', 'domain.com', 'email.com', 'seuemail')
IGRUIM = {'p', 'reel', 'reels', 'explore', 'accounts', 'sharer', 'share', 'tv', 'stories'}


def get(u):
    try:
        r = requests.get(u, headers=UA, timeout=20)
        return r.text if r.ok else ''
    except Exception:
        return ''


def raspa(url):
    base = url if url.startswith('http') else 'https://' + url
    urls = [base]
    h = get(base)
    soup = BeautifulSoup(h, 'html.parser')
    for a in soup.find_all('a', href=True):
        t = (a.get_text(' ') + a['href']).lower()
        if re.search(r'contato|contact|fale|curso|sobre|about|agenda', t) and urlparse(urljoin(base, a['href'])).netloc == urlparse(base).netloc:
            u = urljoin(base, a['href']).split('#')[0]
            if u not in urls and len(urls) < 4:
                urls.append(u)
    txt = h
    for u in urls[1:]:
        txt += get(u)
        time.sleep(1)
    emails = sorted({e.lower() for e in EMAIL.findall(txt) if not any(x in e.lower() for x in RUIM)})
    was = sorted(set(WA.findall(txt)))
    tels = sorted({f'({a}) {b}-{c}' for a, b, c in TEL.findall(re.sub(r'<[^>]+>', ' ', txt)) if a in {'11','12','13','14','15','16','17','18','19','21','31','41','51'}})[:4]
    igs = [i for i in dict.fromkeys(IG.findall(txt)) if i.lower() not in IGRUIM][:3]
    tts = list(dict.fromkeys(TT.findall(txt)))[:2]
    return {'url': base, 'emails': emails[:4], 'whatsapps': was[:3], 'telefones': tels, 'instagram': igs, 'tiktok': tts,
            'titulo': (soup.title.string.strip() if soup.title and soup.title.string else '')}


def score(email, wa, tel, seg, cursos, sp):
    s = 40 + (15 if email else 0) + (10 if wa else (5 if tel else 0))
    s += 20 if (seg or 0) >= 500000 else 15 if (seg or 0) >= 100000 else 10 if (seg or 0) >= 30000 else 5 if (seg or 0) >= 10000 else 0
    return min(90, s + (10 if cursos else 0) + (5 if sp else 0))


if __name__ == '__main__':
    out = []
    for u in open(sys.argv[1]).read().split():
        out.append(raspa(u)); print(json.dumps(out[-1], ensure_ascii=False), flush=True)
    json.dump(out, open(sys.argv[2], 'w'), ensure_ascii=False, indent=1)
