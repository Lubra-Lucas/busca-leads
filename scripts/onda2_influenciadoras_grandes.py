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


if __name__ == '__main__' and sys.argv[1] == 'coletar':
    if True:
        saida = []
        for n in sys.argv[2:]:
            saida.append(coletar(n))
            time.sleep(1.5)
        json.dump(saida, sys.stdout, ensure_ascii=False, indent=1)


# ---------------------------------------------------------------------------------------------
# Dados curados e inseridos em 2026-10-21 (revisados à mão a partir da coleta acima).
# seg_* = origem do número: 'IG' = Instagram (HypeAuditor/ranking de imprensa, 2026), 'TT'/'YT' = TikTok/YouTube
# lidos do perfil público em 21/10/2026 (usado quando não achamos o número do Instagram; é piso, não o total).
# contatos: (tipo, e-mail, nome/entidade, cargo, fonte)
# ---------------------------------------------------------------------------------------------
HOJE = '2026-10-21'
YT = 'descrição do canal do YouTube'
TTB = 'bio do TikTok'
CANDIDATOS_CURADOS = [
    dict(nome='Virginia Fonseca', ig='@virginia', tt='@virginiafonseca', seg=56100000, so='IG ranking Folhapress/Super Rádio Tupi (25/05/2026)', sub='Celebridade / Empresária (WePink)', nichos=['Lifestyle', 'Maternidade', 'Celebridade', 'Humor/Entretenimento'], url='https://www.youtube.com/@virginia',
         ct=[('agencia', 'comercial@agenciavfdigital.com.br', 'VF Digital', 'Agência/comercial', YT)]),
    dict(nome='Whindersson Nunes', ig='@whinderssonnunes', tt='@whinderssonnunes', seg=55000000, so='IG ranking Folhapress/Super Rádio Tupi (25/05/2026)', sub='Humor / Comediante', nichos=['Humor/Entretenimento', 'Celebridade'], url='https://www.youtube.com/@whindersson',
         ct=[('agencia', 'Mayara@nonstopproducoes.com.br', 'Non Stop Produções', 'Produtora/agenciamento', YT)]),
    dict(nome='Ivete Sangalo', ig='@ivetesangalo', tt='@ivetesangalo', seg=36400000, so='IG ranking Folhapress/Super Rádio Tupi (25/05/2026)', sub='Celebridade / Cantora', nichos=['Celebridade', 'Lifestyle'], url='https://www.youtube.com/@IveteSangalo',
         ct=[('geral', 'contato@iessi.com.br', 'Iessi (empresa da artista)', 'Contato geral', 'site oficial ivetesangalo.com/contato')]),
    dict(nome='Zé Felipe', ig='@zefelipe', tt='@zefelipe', seg=34400000, so='IG HypeAuditor (jul/2026)', sub='Celebridade / Cantor', nichos=['Celebridade', 'Lifestyle'], url='https://www.youtube.com/@zefelipe',
         ct=[('comercial', 'ailton@zefelipe.com.br', 'Equipe Zé Felipe', 'Comercial', YT + ' e site zefelipe.com.br')]),
    dict(nome='Lucas Rangel', ig='@lucasranngel', tt=None, seg=25558547, so='IG HypeAuditor (jul/2026)', sub='Humor / Lifestyle', nichos=['Humor/Entretenimento', 'Lifestyle'], url='https://www.youtube.com/@lucasranngel',
         ct=[('direto', 'contatolucasrangel@gmail.com', 'Lucas Rangel', 'Contato comercial', YT)]),
    dict(nome='Simaria', ig='@simaria', tt='@simaria', seg=25838578, so='IG HypeAuditor (jul/2026)', sub='Celebridade / Cantora', nichos=['Celebridade', 'Lifestyle', 'Maternidade'], url='https://www.youtube.com/@Simaria',
         ct=[('agencia', 'simaria@livetalentos.com.br', 'Live Talentos', 'Agência/contato', TTB)]),
    dict(nome='Claudia Leitte', ig='@claudialeitte', tt=None, seg=24434117, so='IG HypeAuditor (jul/2026)', sub='Celebridade / Cantora', nichos=['Celebridade', 'Lifestyle'], url='https://www.youtube.com/@claudialeitte',
         ct=[('comercial', 'publicidade@claudialeitte.com.br', 'Equipe Claudia Leitte', 'Publicidade', 'site oficial claudialeitte.com/imprensa')]),
    dict(nome='Ana Castela', ig='@anacastelacantora', tt='@anacastelacantora', seg=24800000, so='IG reportagem (ago/2026)', sub='Celebridade / Cantora', nichos=['Celebridade', 'Moda'], url='https://www.youtube.com/@anacastelaoficial',
         ct=[('agencia', 'albertoni@agroplaymusic.com.br', 'Agroplay Music', 'Gravadora/agenciamento', YT)]),
    dict(nome='Julio Cocielo', ig='@cocielo', tt=None, seg=23293559, so='IG HypeAuditor (jul/2026)', sub='Humor / Criador', nichos=['Humor/Entretenimento', 'Lifestyle'], url='https://www.youtube.com/@Cocielo',
         ct=[('agencia', 'cocielo@viralnation.com', 'Viral Nation Brasil', 'Agência/casting', YT)]),
    dict(nome='Gkay', ig='@gessica', tt='@gkay', seg=18811318, so='IG HypeAuditor (2026)', sub='Humor / Atriz', nichos=['Humor/Entretenimento', 'Celebridade', 'Lifestyle'], url='https://www.youtube.com/@gkay',
         ct=[('direto', 'gessicakayanev@gmail.com', 'Gkay (Gessica Kayane)', 'Contato profissional', TTB)]),
    dict(nome='Lore Improta', ig='@loreimprota', tt='@loreimprotaoficial', seg=17546299, so='IG HypeAuditor (jul/2026)', sub='Celebridade / Cantora e criadora', nichos=['Celebridade', 'Lifestyle', 'Humor/Entretenimento'], url='https://www.youtube.com/@LoreImprotaOficial',
         ct=[('comercial', 'comercial@loreimprota.com.br', 'Equipe Lore Improta', 'Comercial', TTB)]),
    dict(nome='Tati Zaqui', ig='@tatizaqui', tt=None, seg=13313628, so='IG HypeAuditor (jul/2026)', sub='Celebridade / Cantora', nichos=['Celebridade', 'Moda', 'Lifestyle'], url='https://www.youtube.com/@TATIZAQUIoficial',
         ct=[('agencia', 'tatizaqui@dmusic.com.br', 'D Music', 'Gravadora/agenciamento', YT)]),
    dict(nome='Sophia Valverde', ig='@sophiavalverde', tt='@valverdesophia', seg=13600000, so='IG HypeAuditor (2026)', sub='Celebridade / Atriz e streamer', nichos=['Celebridade', 'Moda', 'Lifestyle'], url='https://www.youtube.com/@Sophia.Valverde',
         ct=[('agencia', 'assessoriasophiavalverde@gmail.com', 'Assessoria Sophia Valverde', 'Assessoria', YT + ' e ' + TTB)]),
    dict(nome='Ingrid Ohara', ig='@oharaingrid', tt='@ingridohara', seg=12400000, so='IG HypeAuditor (jul/2026)', sub='Moda / Lifestyle', nichos=['Moda', 'Lifestyle', 'Maquiagem'], url='https://www.youtube.com/@IngridOharaTV',
         ct=[('comercial', 'work@ingridohara.com', 'Ingrid Ohara', 'Work/comercial', YT + ' e ' + TTB)]),
    dict(nome='Nah Cardoso', ig='@nahcardoso', tt=None, seg=10201803, so='IG HypeAuditor (jul/2026)', sub='Lifestyle / Moda', nichos=['Lifestyle', 'Moda', 'Maquiagem'], url='https://www.youtube.com/@nahcardosovideos',
         ct=[('agencia', 'assessoria@nahcardoso.com.br', 'Assessoria Nah Cardoso', 'Assessoria', YT)]),
    dict(nome='Hariany Almeida', ig='@hariany', tt='@harianyoficial', seg=10088550, so='IG HypeAuditor (jul/2026)', sub='Moda / Beleza (Hari Beauty)', nichos=['Moda', 'Maquiagem', 'Lifestyle'], url='https://www.youtube.com/@harianyoficial',
         ct=[('comercial', 'contato@hariany.com', 'Equipe Hariany', 'Comercial', TTB)]),
    dict(nome='Emilly Vick', ig='@emillyvickof', tt='@emillyvickof', seg=28400000, so='TT perfil público (21/10/2026)', sub='Lifestyle / Beleza', nichos=['Maquiagem', 'Lifestyle', 'Moda'], url='https://www.youtube.com/@emillyvickof',
         ct=[('comercial', 'emilly@grupodosrosa.com.br', 'Grupo dos Rosa', 'Comercial', YT + ' e ' + TTB)]),
    dict(nome='Tirullipa', ig='@tirullipa', tt='@tirullipa', seg=31200000, so='TT perfil público (21/10/2026)', sub='Humor / Comediante', nichos=['Humor/Entretenimento', 'Celebridade'], url='https://www.youtube.com/@TiruTV',
         ct=[('comercial', 'contato@tirullipashow.com', 'Tirullipa Show', 'Contato comercial', YT)]),
    dict(nome='Thais Carla', ig='@thaiscarla', tt='@thaiscarlaa_', seg=12900000, so='TT perfil público (21/10/2026)', sub='Lifestyle / Fitness', nichos=['Fitness', 'Lifestyle', 'Humor/Entretenimento'], url='https://www.youtube.com/@ThaisCarlaa',
         ct=[('comercial', 'contato@thaiscarla.com.br', 'Equipe Thais Carla', 'Contato', YT + ' e ' + TTB)]),
    dict(nome='Camilla de Lucas', ig='@camilladelucas', tt=None, seg=8446198, so='IG HypeAuditor (jul/2026)', sub='Lifestyle / Humor', nichos=['Lifestyle', 'Moda', 'Humor/Entretenimento'], url='https://www.youtube.com/@CamilladeLucas1',
         ct=[('direto', 'camilladelucas@gmail.com', 'Camilla de Lucas', 'Contato', YT)]),
    dict(nome='Fernanda Lima', ig='@fernandalima', tt=None, seg=5300000, so='IG HypeAuditor (sem data)', sub='Celebridade / Apresentadora', nichos=['Celebridade', 'Lifestyle', 'Moda'], url='https://www.youtube.com/@FernandaLimaOficial',
         ct=[('agencia', 'fernandalima@timelens.com.br', 'Timelens', 'Agenciamento', YT), ('agencia', 'meire@boring.digital', 'Boring Digital', 'Agência digital', YT), ('geral', 'contato@fernandalima.com.br', 'Equipe Fernanda Lima', 'Contato', 'site fernandalima.com.br/imprensa')]),
    dict(nome='Xuxa Meneghel', ig='@xuxameneghel', tt='@xuxameneghel', seg=4740000, so='YT canal verificado (21/10/2026)', sub='Celebridade / Apresentadora', nichos=['Celebridade', 'Lifestyle', 'Maternidade'], url='https://www.youtube.com/@Xuxa',
         ct=[('comercial', 'xs@xsproducoes.com', 'XS Produções', 'Produtora', TTB)]),
    dict(nome='Mirella Santos', ig='@misantosoficial', tt='@misantosoficial', seg=4300000, so='IG HypeAuditor (sem data)', sub='Lifestyle / Maternidade', nichos=['Lifestyle', 'Maternidade', 'Moda'], url='https://www.youtube.com/@MiNaReal',
         ct=[('agencia', 'digital@satorahal.com.br', 'Sato Rahal (digital)', 'Agência', YT)]),
    dict(nome='Gabi Prado', ig='@pradogabrielle', tt=None, seg=3100000, so='IG HypeAuditor (jul/2026)', sub='Moda / Lifestyle', nichos=['Moda', 'Lifestyle'], url='https://www.youtube.com/@gabiprado',
         ct=[('agencia', 'gabiprado@yziassessoria.com.br', 'YZI Assessoria', 'Assessoria', YT)]),
    dict(nome='Giulia Costa', ig='@giuliacosta', tt='@giuliacosta9', seg=2960000, so='IG HypeAuditor (jul/2026)', sub='Celebridade / Atriz', nichos=['Celebridade', 'Moda', 'Lifestyle'], url='https://www.youtube.com/@canalgiuliacosta',
         ct=[('agencia', 'atendimento@agenciafamily.com', 'Agência Family', 'Atendimento da agência', YT)]),
    dict(nome='Taty Girl', ig='@tatygirl', tt='@tatygirloficial', seg=2939766, so='IG HypeAuditor (jul/2026)', sub='Celebridade / Cantora', nichos=['Celebridade', 'Moda', 'Lifestyle'], url='https://www.youtube.com/@TatyGirl',
         ct=[('geral', 'bergpedrosa@tatygirl.com.br', 'Equipe Taty Girl', 'Contato (imprensa)', 'página de imprensa bfan.link/no-sertao-2/imprensa')]),
    dict(nome='Jade Seba', ig='@jadeseba', tt=None, seg=2370000, so='IG HypeAuditor (jul/2026)', sub='Moda / Lifestyle', nichos=['Moda', 'Lifestyle', 'Maquiagem'], url='https://www.youtube.com/@jadeseba',
         ct=[('agencia', 'assessoria@jadeseba.com.br', 'Assessoria Jade Seba', 'Assessoria', 'site jadeseba.com.br/contato')]),
    dict(nome='Rafa Brites', ig='@rafabrites', tt=None, seg=2300000, so='IG HypeAuditor (sem data)', sub='Celebridade / Apresentadora', nichos=['Maternidade', 'Lifestyle', 'Celebridade'], url='https://www.youtube.com/@rafabrites',
         ct=[('geral', 'contato@rafabrites.com.br', 'Equipe Rafa Brites', 'Contato', 'link da bio do canal YouTube')]),
    dict(nome='Danielle Noce', ig='@nocedanielle', tt=None, seg=2760000, so='YT canal verificado (21/10/2026)', sub='Lifestyle', nichos=['Lifestyle', 'Moda', 'Maternidade'], url='https://www.youtube.com/@nocedani',
         ct=[('comercial', 'comercial@paulocuenca.com.br', 'Equipe Danielle Noce', 'Comercial', YT)]),
    dict(nome='Bruna Vieira', ig='@brunavieira', tt='@bruvie', seg=1330000, so='YT canal (21/10/2026)', sub='Escritora / Lifestyle', nichos=['Lifestyle', 'Moda'], url='https://www.youtube.com/@depoisdosquinze',
         ct=[('geral', 'brunavieira@depoisdosquinze.com', 'Equipe Bruna Vieira', 'Contato', 'site depoisdosquinze.com/contato')]),
    dict(nome='Jout Jout', ig='@joutjout', tt=None, seg=1262381, so='IG HypeAuditor (2026)', sub='Humor / Criadora', nichos=['Humor/Entretenimento', 'Lifestyle'], url='https://www.youtube.com/@joutjout',
         ct=[('comercial', 'contato@oilupi.com', 'Oi Lupi', 'Contato', YT)]),
    dict(nome='Nathalia Arcuri (Me Poupe!)', ig=None, tt=None, seg=7740000, so='YT canal verificado (21/10/2026)', sub='Educação financeira / Lifestyle', nichos=['Lifestyle'], url='https://www.youtube.com/@MePoupe',
         ct=[('comercial', 'parcerias@mepoupe.com', 'Me Poupe!', 'Parcerias', YT)]),
    dict(nome='Mandy Candy', ig='@mandycandy', tt=None, seg=2120000, so='YT canal verificado (21/10/2026)', sub='Humor / Lifestyle', nichos=['Humor/Entretenimento', 'Lifestyle'], url='https://www.youtube.com/@mandycandy',
         ct=[('comercial', 'mandy@oilupi.com', 'Oi Lupi', 'Contato', YT)]),
    dict(nome='Bia Galvão', ig='@abiagalvao', tt='@abiagalvao', seg=1600000, so='TT perfil público (21/10/2026)', sub='Maternidade / Lifestyle', nichos=['Maternidade', 'Lifestyle'], url='https://www.youtube.com/@abiagalvao',
         ct=[('geral', 'contato@biadocdb.com', 'Equipe Bia Galvão', 'Contato', TTB)]),
    dict(nome='Allana Menezes', ig='@allanamenezzes', tt='@allanamenezzes', seg=2200000, so='TT perfil público (21/10/2026)', sub='Cabelo / Lifestyle', nichos=['Cabelo', 'Unhas', 'Lifestyle'], url='https://www.youtube.com/@allanamenezzes',
         ct=[('agencia', 'allana@lenziassessoria.com', 'Lenzi Assessoria', 'Assessoria', TTB)]),
    dict(nome='Bia Amaral', ig='@bbiamarall', tt='@bbiamarall', seg=2800000, so='TT perfil público (21/10/2026)', sub='Maquiagem / Lifestyle', nichos=['Maquiagem', 'Cabelo', 'Lifestyle'], url='https://www.youtube.com/@bbiamarall',
         ct=[('comercial', 'comercial@bbiamarall.com', 'Equipe Bia Amaral', 'Comercial', TTB)]),
    dict(nome='Gi Robatini', ig=None, tt=None, seg=1110000, so='YT canal verificado (21/10/2026)', sub='Lifestyle / Moda', nichos=['Lifestyle', 'Moda'], url='https://www.youtube.com/@girobatini',
         ct=[('comercial', 'girobatini.comercial@gmail.com', 'Gi Robatini', 'Comercial', YT)]),
    dict(nome='Ester Lima', ig='@byesterlima', tt='@byesterlima', seg=2400000, so='TT perfil público (21/10/2026)', sub='Moda / Lifestyle', nichos=['Moda', 'Lifestyle', 'Maquiagem'], url='https://www.youtube.com/@byesterlima',
         ct=[('agencia', 'esterlima@agenciabye.com', 'Agência Bye', 'Agência', TTB), ('direto', 'contatoesterlima1@gmail.com', 'Ester Lima', 'Contato', YT)]),
    dict(nome='Sabrina Brito', ig='@_sabrina.brito', tt='@_sabrina.brito', seg=1200000, so='TT perfil público (21/10/2026)', sub='Lifestyle', nichos=['Lifestyle', 'Moda'], url='https://www.youtube.com/@_sabrinabrito',
         ct=[('direto', 'contatosabrinabrito@gmail.com', 'Sabrina Brito', 'Contato', YT + ' e ' + TTB)]),
    dict(nome='Lucas Guedes', ig='@olucas.guedes', tt='@olucas.guedes', seg=3800000, so='TT perfil público (21/10/2026)', sub='Humor / Criador', nichos=['Humor/Entretenimento', 'Lifestyle'], url='https://www.youtube.com/@LucasGuedess',
         ct=[('agencia', 'comercial@startcreators.ag', 'Start Creators', 'Agência', YT), ('direto', 'comercial.lucasguedes@gmail.com', 'Lucas Guedes', 'Comercial', YT)]),
    dict(nome='Life by Lufe', ig='@lifebylufe', tt=None, seg=1200000, so='YT canal verificado (21/10/2026)', sub='Lifestyle', nichos=['Lifestyle', 'Moda'], url='https://www.youtube.com/@LifebyLufe',
         ct=[('comercial', 'lifebylufe@gmail.com', 'Life by Lufe', 'Contato', YT + ' e link da bio')]),
]


# Grandes sem contato utilizável achado de graça (candidatas a rodada paga). Seguidores IG aproximados (fontes 2026).
SEM_CONTATO = [
    ('Neymar Jr (@neymarjr)', 233e6), ('Ronaldinho Gaúcho (@ronaldinho)', 77e6), ('Tatá Werneck já na base', 0),
    ('Gusttavo Lima (@gusttavolima)', 44.9e6), ('Simone Mendes (@simonemendes)', 40e6), ('Wesley Safadão (@wesleysafadao)', 39.9e6),
    ('Paolla Oliveira (@paollaoliveira)', 38.4e6), ('Carlinhos Maia (@carlinhosmaia)', 35.3e6), ('Luan Santana (@luansantana)', 36.7e6),
    ('Luísa Sonza (@luisasonza)', 29.2e6), ('Bianca Andrade / Boca Rosa (@bianca)', 18.6e6), ('Pabllo Vittar (@pabllovittar)', 0),
    ('Ludmilla (@ludmilla)', 0), ('Gio Ewbank (@gioewbank)', 0), ('Maya Massafera (@mayamassafera)', 0), ('Sandy (@sandyoficial)', 0),
    ('Lexa (@lexa)', 0), ('Kéfera (@kefera)', 0), ('Camila Loures (@camilaloures)', 0), ('Rafa Kalimann (@rafakalimann)', 0),
    ('Manu Gavassi (@manugavassi)', 0), ('Mari Gonzalez (@marigonzalez; só e-mail da produtora Romme, sem n.º IG)', 0),
]


def _score(c):
    s = 40 + 25  # todos têm e-mail
    if any(t == 'agencia' for t, *_ in c['ct']):
        s += 15
    s += 20 if c['seg'] >= 10_000_000 else 15 if c['seg'] >= 1_000_000 else 10 if c['seg'] >= 100_000 else 0
    return min(s, 95)


def _q(v):
    return 'null' if v is None else "'" + str(v).replace("'", "''") + "'"


def gerar_sql():
    """INSERT ... ON CONFLICT DO NOTHING com os candidatos curados (rodar via MCP/psql; sem DELETE)."""
    ordem = {'comercial': 0, 'agencia': 1, 'direto': 2, 'geral': 3}
    linhas = []
    for c in CANDIDATOS_CURADOS:
        cts = sorted(c['ct'], key=lambda x: ordem[x[0]])
        principal = cts[0]
        contatos = [dict(nome=n, cargo=cg, email=e, tipo=t, fonte=f, data=HOJE)
                    for t, e, n, cg, f in cts]
        pl = c['so'].split()[0]
        extras = dict(nichos=c['nichos'], nicho_principal=c['nichos'][0], contatos=contatos,
                      contato_qualidade='agencia' if principal[0] == 'agencia' else principal[0],
                      contato_fonte=principal[4], plataforma='Instagram', onda='onda2_2026-10-21',
                      seguidores_fonte=dict(origem=c['so'], data=HOJE, plataforma_numero={'IG': 'Instagram', 'TT': 'TikTok', 'YT': 'YouTube'}[pl]))
        linhas.append('(' + ', '.join([
            _q(c['nome']), _q(principal[2]), _q(principal[3]), _q(c['sub']), _q(c['ig']), _q(c['tt']), str(c['seg']),
            _q(principal[1]), _q('Busca onda 2 – grandes influenciadoras'), _q(c['url']), str(_score(c)),
            "'" + json.dumps(extras, ensure_ascii=False, separators=(',', ':')).replace("'", "''") + "'::jsonb"]) + ')')
    return ("insert into leads (tipo, segmento_id, status, nome, contato_nome, contato_cargo, subsegmento, instagram, tiktok, "
            "seguidores, email, fonte, fonte_url, score, extras)\nselect 'cliente'::lead_tipo, 'influenciadora', 'novo'::lead_status, v.* from (values\n"
            + ',\n'.join(linhas) + "\n) as v(nome, contato_nome, contato_cargo, subsegmento, instagram, tiktok, seguidores, email, fonte, fonte_url, score, extras)\n"
            "on conflict do nothing;")


if __name__ == '__main__' and sys.argv[1] == 'sql':
    print(gerar_sql())
