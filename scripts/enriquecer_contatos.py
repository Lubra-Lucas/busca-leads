"""Procura o contato mais "quente" possível de cada lead (comercial/marketing/parcerias > geral > SAC).

Uso (python3 -I scripts/enriquecer_contatos.py ...):
  sites <leads.txt> <saida.json>        leads.txt: "chave|nome|site|email_atual" (chave = 8 primeiros chars do id).
                                        Lê home + páginas de contato/sobre/atacado/parcerias/imprensa, CNPJ do rodapé
                                        (BrasilAPI: telefone, e-mail cadastral, sócios) e classifica cada contato.
  renderizado <leads.txt> <paginas.json> <saida.json>
                                        mesmo processamento a partir do HTML salvo por scripts/renderizar_sites.mjs
                                        (leads.json com {id: chave, nome, site}).
  manual <manual.json> <saida.json>     contatos achados à mão (busca web, agências): [{chave, nome, email_atual?,
                                        contatos: [{nome,cargo,email,telefone,whatsapp,linkedin,tipo,fonte}]}]
  descobrir <alvos.txt> <sites.txt> <manual.json>
                                        alvos: "chave|nome|@tiktok|@instagram" sem site. Lê bio/link da bio do TikTok
                                        público (e-mail, wa.me) e testa domínios prováveis (nome.com.br etc.),
                                        aceitando só se a página citar a marca e o ramo (beleza/moda). Gera sites.txt
                                        para o comando "sites" e manual.json com o que veio da bio.
  sql <saida.json> [mais.json ...]      imprime o UPDATE ... FROM (VALUES ...) para o Supabase (só preenche vazios;
                                        e-mail melhor substitui o pior e o antigo vai para extras.contatos).

Tipos: direto (pessoa da marca/influenciadora), comercial (vendas/marketing/parcerias/B2B/imprensa), agencia,
geral (contato@...), sac (atendimento/SAC). Nada é adivinhado: só contato publicado pela própria fonte.
Reaproveita enriquecer_sites.py via importlib.
"""
import importlib.util
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urljoin

import requests

AQUI = Path(__file__).resolve().parent
DATA = '2026-10-21'


def carregar(nome):
    spec = importlib.util.spec_from_file_location(nome, AQUI / f'{nome}.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ES = carregar('enriquecer_sites')
RANK = {'direto': 5, 'comercial': 4, 'agencia': 3, 'geral': 2, 'sac': 1}

CAMINHOS = ['/contato', '/fale-conosco', '/sobre', '/quem-somos', '/institucional', '/atacado', '/seja-revendedor',
            '/revenda', '/parcerias', '/imprensa', '/b2b', '/pages/contato', '/pages/sobre', '/pages/atacado',
            '/pages/parcerias', '/pages/fale-conosco', '/pages/seja-um-revendedor', '/trabalhe-conosco']
LINKS_UTEIS = re.compile(r'contato|contact|fale[-_ ]?conosco|sobre|about|quem[-_ ]somos|institucional|atacado|revend|'
                         r'parceri|imprensa|press|b2b|comercial|distribuidor|representante|private|assessoria|midia', re.I)
PAGINA_B2B = re.compile(r'atacado|revend|parceri|imprensa|press|b2b|comercial|distribuidor|representante|midia|publi', re.I)
PAGINA_SAC = re.compile(r'atendimento|sac|ajuda|faq|suporte|troca|duvida', re.I)

L_COMERCIAL = re.compile(r'^(comercial|vendas?|marketing|parceri\w*|b2b|atacado|revend\w*|imprensa|press|publi\w*|midia|'
                         r'negocios|business|representante\w*|compras|distribuidor\w*|influencer\w*|influenciadores|'
                         r'relacionamento\.?comercial|mkt|contato\.?comercial|comercial\.\w+|marketing\.\w+)')
L_SAC = re.compile(r'^(sac|atendimento\w*|faleconosco|fale\.?conosco|suporte|cliente\w*|relacionamento|loja|pedidos?|'
                   r'trocas?|posvenda|pos\.?venda|ajuda|help|ecommerce|e-commerce|vendasonline|lojavirtual)')
L_GERAL = re.compile(r'^(contato|contact|contatos|ola|oi|hello|hi|info|informacoes|adm|administrativo|geral|'
                     r'faleconnosco|comunicacao|mail|email|secretaria|recepcao|agendamento\w*|reservas?)')
L_DESCARTA = re.compile(r'^(rh|vagas?|curriculo\w*|trabalheconosco|trabalhe\.?conosco|financeiro|cobranca|fiscal|nfe|'
                        r'lgpd|dpo|privacidade|ouvidoria|juridico|compliance|contabil\w*|contabilidade|webmaster|'
                        r'noreply|no-reply|abuse|postmaster)')
PROVEDORES = re.compile(r'^(gmail|hotmail|outlook|yahoo|uol|bol|icloud|terra|live|msn|ig)\.')
CNPJ = re.compile(r'\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b')
DESCARTA_DOM = re.compile(r'fundacao|instituto|contabil|contab|sentry|wix|shopify|vtex|nuvem|tray|loja ?integrada|yampi|wake|linx|dooca|'
                          r'agencia|digital|web|host|dominio|registro|google|facebook|instagram', re.I)


def norm(s):
    import unicodedata
    s = unicodedata.normalize('NFKD', str(s or '')).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]', '', s)


def e164(f):
    d = re.sub(r'\D', '', f or '')
    if re.search(r'(\d)\1{6,}', d):
        return None
    if d.startswith('0800') or not d:
        return None
    if d.startswith('55') and len(d) in (12, 13):
        d = d[2:]
    if len(d) not in (10, 11) or d[0] == '0' or d[:2] in ('80', '90') or not 11 <= int(d[:2]) <= 99:
        return None
    return f'+55{d}'


def dominio_coerente(email, site, nome):
    dom = email.split('@')[1].lower()
    if PROVEDORES.match(dom):
        return True
    raiz_dom = norm(dom.split('.')[0])
    alvos = [norm(ES.dominio_base(site).split('.')[0]), norm(nome)]
    for a in alvos:
        if len(a) >= 4 and len(raiz_dom) >= 4 and (a[:5] in raiz_dom or raiz_dom[:5] in a):
            return True
    # nome da marca em partes: "Bruna Tavares" -> "linhabrunatavares"
    for p in re.split(r'\W+', re.sub(r'\(.*?\)', ' ', nome.lower())):
        p = norm(p)
        if len(p) >= 5 and p in raiz_dom:
            return True
    return False


def tipo_email(email, pagina=''):
    local = email.split('@')[0].lower()
    if L_DESCARTA.match(local) or re.search(r'financ|fiscal|cobranc|faturamento|contabil|rh\b|vagas|recrut|curricul|talent', local):
        return None
    if L_COMERCIAL.match(local) or re.search(r'imprensa|parceria|comercial|vendas|marketing|atacado|revenda|publi', local):
        return 'comercial'
    if L_SAC.match(local):
        return 'sac'
    if L_GERAL.match(local):
        return 'comercial' if PAGINA_B2B.search(pagina) else 'geral'
    if re.fullmatch(r'[a-z]{3,}\.[a-z]{3,}', local) and not re.search(r'financ|produc|compra|fatur|logist|estoque|loja|site', local):
        return 'direto'  # nome.sobrenome
    return 'geral'


def tipo_existente(email):
    return tipo_email(email) or 'geral' if email else None


def cnpj_info(cnpj):
    d = re.sub(r'\D', '', cnpj)
    try:
        r = requests.get(f'https://brasilapi.com.br/api/cnpj/v1/{d}', timeout=20, headers={'User-Agent': ES.UA})
        return r.json() if r.status_code == 200 else None
    except (requests.RequestException, ValueError):
        return None


def analisar(lead, paginas, com_cnpj=True):
    """paginas: [(url, html)]. Devolve o dicionário de resultado do lead."""
    site, nome = lead['site'], lead['nome']
    achados, cnpjs = {}, []
    fones, zaps = {}, {}
    for url, html in paginas:
        emails, whats, tels, _, _ = ES.extrair(html, url)
        limpo = re.sub(r'(?is)<(script|style|svg)\b.*?</\1>', ' ', html)
        texto = re.sub(r'<[^>]+>', ' ', limpo)[:300000]
        emails |= {e.lower() for e in ES.EMAIL.findall(texto)}
        for e in emails:
            e = re.sub(r'^mailto:', '', e.strip().strip('.').lower())
            if '@' not in e or ES.EMAIL_LIXO.search(e) or len(e) > 60 or DESCARTA_DOM.search(e.split('@')[1]):
                continue
            if not dominio_coerente(e, site, nome):
                continue
            t = tipo_email(e, url)
            if t and (e not in achados or RANK[t] > RANK[achados[e][0]]):
                achados[e] = (t, url)
        for w in whats:
            if e164(w):
                zaps.setdefault(e164(w), url)
        for f in tels:
            if e164(f):
                fones.setdefault(e164(f), url)
        cnpjs += CNPJ.findall(re.sub(r'\s+', ' ', texto[-60000:]))
    contatos, extra_nome = [], {}
    for e, (t, url) in achados.items():
        contatos.append({'email': e, 'tipo': t, 'fonte': url})
    # e-mails colados no texto (ex.: "nimprensa@" = "n" + "imprensa@"): fica o mais curto que o contém
    emails_ach = list(achados)
    for e in emails_ach:
        if any(o != e and e.endswith(o.split('@')[0][-6:] + '@' + o.split('@')[1]) and len(e) == len(o) + 1 for o in emails_ach):
            del achados[e]
    contatos = [c for c in contatos if not c.get('email') or c['email'] in achados]
    for z, url in zaps.items():
        t = 'comercial' if PAGINA_B2B.search(url) else ('sac' if PAGINA_SAC.search(url) else 'geral')
        contatos.append({'whatsapp': z, 'telefone': z, 'tipo': t, 'fonte': url})
    for f, url in fones.items():
        if f not in zaps:
            t = 'comercial' if PAGINA_B2B.search(url) else ('sac' if PAGINA_SAC.search(url) else 'geral')
            contatos.append({'telefone': f, 'tipo': t, 'fonte': url})
    if com_cnpj and cnpjs:
        c = max(set(cnpjs), key=cnpjs.count)
        info = cnpj_info(c)
        time.sleep(0.4)
        if info:
            url = 'brasilapi.com.br/cnpj/' + re.sub(r'\D', '', c)
            em = (info.get('email') or '').lower().strip()
            if em and not DESCARTA_DOM.search(em.split('@')[1]) and dominio_coerente(em, site, nome) and tipo_email(em):
                if em not in achados:
                    contatos.append({'email': em, 'tipo': 'geral', 'fonte': url + ' (e-mail cadastral)'})
            tel = e164(info.get('ddd_telefone_1') or '')
            if tel and tel not in fones and tel not in zaps:
                contatos.append({'telefone': tel, 'tipo': 'geral', 'fonte': url + ' (telefone cadastral)'})
            socios = [q for q in info.get('qsa') or [] if q.get('nome_socio')]
            adm = next((q for q in socios if 'administrador' in (q.get('qualificacao_socio') or '').lower()), None)
            if adm or socios:
                q = adm or socios[0]
                extra_nome = {'contato_nome': q['nome_socio'].title(), 'contato_cargo': (q.get('qualificacao_socio') or 'Sócio').title(),
                              'fonte_nome': url}
    n_tel = 0
    for c in list(contatos):  # no máximo 3 telefones por lead (lojas listam dezenas de revendedoras)
        if c.get('telefone') and not c.get('email'):
            n_tel += 1
            if n_tel > 3:
                contatos.remove(c)
    return montar(lead, contatos, extra_nome)


def montar(lead, contatos, extra_nome=None):
    old = (lead.get('email_atual') or '').lower()
    melhor = max((c for c in contatos if c.get('email')), key=lambda c: RANK[c['tipo']], default=None)
    r_old = RANK[tipo_existente(old)] if old else 0
    out = {'chave': lead['chave'], 'nome': lead['nome'], 'email': None, 'old_email': old or None}
    if melhor and RANK[melhor['tipo']] > r_old:
        out['email'] = melhor['email']
        if old:  # guarda o e-mail genérico antigo
            contatos.append({'email': old, 'tipo': tipo_existente(old), 'fonte': 'cadastro anterior'})
    out['whatsapp'] = next((c['whatsapp'] for c in contatos if c.get('whatsapp')), None)
    tels = [c['telefone'] for c in contatos if c.get('telefone')]
    out['telefone'] = out['whatsapp'] or next((t for t in tels if len(t) == 14 and t[5] == '9'), None) or (tels[0] if tels else None)
    out.update(extra_nome or {})
    vistos, limpos = set(), []
    for c in contatos:
        k = (c.get('email'), c.get('telefone'), c.get('whatsapp'))
        if k in vistos:
            continue
        vistos.add(k)
        limpos.append(c)
    out['contatos'] = limpos
    tipos = [c['tipo'] for c in limpos] + ([tipo_existente(old)] if old else [])
    out['qualidade'] = max(tipos, key=lambda t: RANK[t]) if tipos else None
    return out


RAMO = re.compile(r'cosm[eé]tic|maquiag|beleza|beauty|skincare|cabelo|esmalte|perfum|moda|roupa|fashion|colec[aã]o|'
                  r'make|hair|pele|embalag|fragr|ess[eê]ncia|pigment|mat[eé]ria|qu[ií]mic|farm[aá]cia|varejo|drogaria', re.I)
GENERICAS = re.compile(r'\b(cosmeticos|cosmetics|professional|profissional|makeup|make|beauty|brasil|oficial|studio|'
                       r'modas?|by|do|da|de|e|and|grupo|industria|comercio)\b')


def descobrir_dominio(nome):
    base = re.sub(r'\(.*?\)', ' ', nome.lower())
    cheio = norm(base)
    curto = norm(GENERICAS.sub(' ', __import__('unicodedata').normalize('NFKD', base).encode('ascii', 'ignore').decode()))
    s = requests.Session()
    s.headers.update({'User-Agent': ES.UA, 'Accept-Language': 'pt-BR,pt;q=0.9'})
    vistos = set()
    for slug in dict.fromkeys([cheio, curto]):
        if len(slug) < 4:
            continue
        for pre in ('', 'loja', 'use'):
            for tld in ('.com.br', '.com'):
                host = f'{pre}{slug}{tld}'
                if host in vistos:
                    continue
                vistos.add(host)
                try:
                    r = s.get(f'https://www.{host}', timeout=8, allow_redirects=True)
                except requests.RequestException:
                    continue
                if r.status_code >= 400 or 'html' not in r.headers.get('content-type', ''):
                    continue
                raiz = norm(ES.dominio_base(r.url).split('.')[0])
                if not (slug[:6] in raiz or raiz[:6] in slug):
                    continue  # redirecionou para outro lugar
                topo = norm(re.sub(r'<script.*?</script>|<style.*?</style>', ' ', r.text[:60000], flags=re.S | re.I))
                titulo = norm((re.search(r'<title[^>]*>(.*?)</title>', r.text, re.S | re.I) or [0, ''])[1])
                if (slug in titulo or slug in topo[:3000]) and len(RAMO.findall(r.text[:40000])) >= (2 if len(slug) <= 5 else 1):
                    return ES.dominio_base(r.url)
    return None


def cmd_descobrir(alvos, sites_out, manual_out):
    TT = carregar('tiktok_shop')
    leads = [(l.split('|') + [''] * 4)[:4] for l in Path(alvos).read_text(encoding='utf-8').splitlines() if l]

    def um(l):
        chave, nome, tt, ig = l
        r = {'chave': chave, 'nome': nome, 'contatos': []}
        perfil = None
        for h in dict.fromkeys(x for x in (tt, ig) if x):
            p = TT.perfil(h)
            if p and not p.get('erro') and (h == tt or TT.parecido(nome, p['handle'], p['nome_perfil'])):
                perfil = p
                break
        if perfil:
            url = f"https://www.tiktok.com/{perfil['handle']}"
            bio = perfil.get('bio') or ''
            for e in {e.lower() for e in ES.EMAIL.findall(bio)}:
                t = tipo_email(e)
                if t and not ES.EMAIL_LIXO.search(e):
                    r['contatos'].append({'email': e, 'tipo': t, 'fonte': url + ' (bio TikTok)'})
            for m in ES.FONE_LINK.findall(bio):
                if e164(m):
                    r['contatos'].append({'whatsapp': e164(m), 'telefone': e164(m), 'tipo': 'geral', 'fonte': url + ' (bio TikTok)'})
            lb = (perfil.get('link_bio') or '').strip()
            if lb and not re.search(r'instagram\.com|tiktok\.com|youtu|linktr|beacons|wa\.me|whatsapp', lb, re.I):
                r['site'] = lb if lb.startswith('http') else 'https://' + lb
        if not r.get('site'):
            d = descobrir_dominio(nome)
            if d:
                r['site'] = d
        return r

    with ThreadPoolExecutor(4) as ex:
        res = list(ex.map(um, leads))
    Path(sites_out).write_text('\n'.join(f"{r['chave']}|{r['nome']}|{r['site']}|" for r in res if r.get('site')), encoding='utf-8')
    Path(manual_out).write_text(json.dumps([{'chave': r['chave'], 'nome': r['nome'], 'contatos': r['contatos']}
                                            for r in res if r['contatos']], ensure_ascii=False), encoding='utf-8')
    print(f"sites: {sum(1 for r in res if r.get('site'))}/{len(res)} | bio com contato: {sum(1 for r in res if r['contatos'])}")


def ler_leads(arq):
    for l in Path(arq).read_text(encoding='utf-8').splitlines():
        c = (l.split('|') + [''] * 4)[:4]
        if c[0]:
            yield {'chave': c[0], 'nome': c[1], 'site': c[2], 'email_atual': c[3]}


def baixar_site(lead):
    site = lead['site']
    url = site if site.startswith('http') else f'https://{site}'
    s = requests.Session()
    s.headers.update({'User-Agent': ES.UA, 'Accept-Language': 'pt-BR,pt;q=0.9'})
    html, final = ES.baixar(s, url)
    if html is None and not site.startswith('http'):
        html, final = ES.baixar(s, f'https://www.{site}')
    if html is None:
        return lead, []
    paginas, vistos = [(final, html)], {final}
    _, _, _, _, links = ES.extrair(html, final)
    cands = [l for l in links if ES.dominio_base(l) == ES.dominio_base(final) and LINKS_UTEIS.search(l)]
    cands += [urljoin(final, c) for c in CAMINHOS]
    for l in cands:
        if len(paginas) >= 9:
            break
        if l in vistos:
            continue
        vistos.add(l)
        h, f = ES.baixar(s, l)
        if h and f not in {p[0] for p in paginas}:
            paginas.append((f, h))
    return lead, paginas


def cmd_sites(leads_txt, saida):
    leads = list(ler_leads(leads_txt))
    res = []
    with ThreadPoolExecutor(12) as ex:
        for i, (lead, paginas) in enumerate(ex.map(baixar_site, leads), 1):
            r = analisar(lead, paginas) if paginas else {'chave': lead['chave'], 'nome': lead['nome'], 'erro': 'site não abriu',
                                                          'contatos': [], 'email': None, 'old_email': lead['email_atual'] or None}
            res.append(r)
            if i % 40 == 0:
                print(f'{i}/{len(leads)}', flush=True)
    Path(saida).write_text(json.dumps(res, ensure_ascii=False, indent=0), encoding='utf-8')
    resumo(res)


def cmd_renderizado(leads_txt, paginas_json, saida):
    leads = {l['chave']: l for l in ler_leads(leads_txt)}
    res = []
    for r in json.load(open(paginas_json)):
        if r['paginas'] and r['id'] in leads:
            res.append(analisar(leads[r['id']], [(p['url'], p['html']) for p in r['paginas']]))
    Path(saida).write_text(json.dumps(res, ensure_ascii=False, indent=0), encoding='utf-8')
    resumo(res)


def cmd_manual(manual, saida):
    res = []
    for m in json.load(open(manual)):
        cs = []
        for c in m['contatos']:
            c = {k: v for k, v in c.items() if v}
            c['manual'] = True  # tipo definido por quem achou: não reclassificar
            if c.get('telefone'):
                c['telefone'] = e164(c['telefone']) or c['telefone']
            if c.get('whatsapp'):
                c['whatsapp'] = e164(c['whatsapp']) or c['whatsapp']
            cs.append(c)
        r = montar({'chave': m['chave'], 'nome': m.get('nome', ''), 'email_atual': m.get('email_atual')}, cs)
        for k in ('contato_nome', 'contato_cargo', 'linkedin', 'tiktok', 'instagram'):
            if m.get(k):
                r[k] = m[k]
        res.append(r)
    Path(saida).write_text(json.dumps(res, ensure_ascii=False, indent=0), encoding='utf-8')
    resumo(res)


def resumo(res):
    com = [r for r in res if r.get('contatos')]
    tipos = {}
    for r in com:
        tipos[r['qualidade']] = tipos.get(r['qualidade'], 0) + 1
    print(f'{len(com)}/{len(res)} com contato | melhor tipo: {tipos} | falhas de site: {sum(1 for r in res if r.get("erro"))}')


def q(s):
    return 'null' if s in (None, '') else "'" + str(s).replace("'", "''") + "'"


def revalidar(r):
    """Reaplica as regras atuais de classificação a um resultado já salvo (sem baixar nada de novo)."""
    cs = []
    for c in r.get('contatos', []):
        c = dict(c)
        if c.get('email') and c['fonte'] != 'cadastro anterior' and not c.get('manual'):
            t = tipo_email(c['email'], c['fonte'])
            if not t:
                continue
            c['tipo'] = t
        for k in ('telefone', 'whatsapp'):
            if c.get(k) and not e164(c[k]):
                c.pop(k)
        if c.get('email') or c.get('telefone') or c.get('whatsapp'):
            cs.append(c)
    novo = montar({'chave': r['chave'], 'nome': r['nome'], 'email_atual': r.get('old_email')},
                  [c for c in cs if c['fonte'] != 'cadastro anterior'])
    for k in ('contato_nome', 'contato_cargo', 'fonte_nome', 'linkedin'):
        if r.get(k):
            novo[k] = r[k]
    return novo


def cmd_sql(arqs):
    """Uma linha de VALUES por lead que tem o que gravar; imprime a instrução completa."""
    linhas = []
    for arq in arqs:
        for r in map(revalidar, json.load(open(arq))):
            if not any(c['fonte'] != 'cadastro anterior' for c in r.get('contatos', [])):
                continue  # nada novo além do que o lead já tinha
            cs = [{**{k: v for k, v in c.items() if k != 'manual'}, 'fonte': re.sub(r'^https?://(www\.)?', '', c['fonte'].split('?')[0])[:80]}
                  for c in sorted(r['contatos'], key=lambda c: -RANK[c['tipo']])[:6]]
            linhas.append(f"({q(r['chave'])},{q(r.get('email'))},{q((r.get('old_email') or ''))},{q(r.get('telefone'))},"
                          f"{q(r.get('whatsapp'))},{q(r.get('contato_nome'))},{q(r.get('contato_cargo'))},{q(r.get('linkedin'))},"
                          f"{q(r.get('qualidade'))},{q(json.dumps(cs, ensure_ascii=False, separators=(',', ':')))})")
    print(SQL_BASE.format(valores=',\n'.join(linhas)))


SQL_BASE = """update public.leads l set
  email = case when v.email is not null and (coalesce(l.email,'')='' or lower(l.email)=v.old) then v.email else l.email end,
  telefone = coalesce(nullif(l.telefone,''), v.tel),
  whatsapp = coalesce(nullif(l.whatsapp,''), v.zap),
  contato_nome = coalesce(nullif(l.contato_nome,''), v.cnome),
  contato_cargo = coalesce(nullif(l.contato_cargo,''), v.ccargo),
  linkedin = coalesce(nullif(l.linkedin,''), v.lin),
  score = case when coalesce(l.email,'')='' and coalesce(l.telefone,'')='' and coalesce(l.whatsapp,'')='' and (v.email is not null or v.tel is not null or v.zap is not null) then least(100, coalesce(l.score,0)+10) else l.score end,
  extras = coalesce(l.extras,'{{}}'::jsonb) || jsonb_build_object('contato_qualidade', v.qual,
    'contatos', coalesce(l.extras->'contatos','[]'::jsonb) || (select coalesce(jsonb_agg(c || '{{"data":"2026-10-21"}}'::jsonb), '[]'::jsonb) from jsonb_array_elements(v.cs::jsonb) c
       where not exists (select 1 from jsonb_array_elements(coalesce(l.extras->'contatos','[]'::jsonb)) e
         where coalesce(e->>'email','')=coalesce(c->>'email','') and coalesce(e->>'telefone','')=coalesce(c->>'telefone','') and coalesce(e->>'whatsapp','')=coalesce(c->>'whatsapp',''))))
from (values
{valores}
) as v(k, email, old, tel, zap, cnome, ccargo, lin, qual, cs)
where left(l.id::text,8)=v.k;"""


def main():
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    {'sites': lambda: cmd_sites(a[1], a[2]), 'renderizado': lambda: cmd_renderizado(a[1], a[2], a[3]),
     'manual': lambda: cmd_manual(a[1], a[2]), 'sql': lambda: cmd_sql(a[1:]), 'descobrir': lambda: cmd_descobrir(a[1], a[2], a[3])}[a[0]]()


if __name__ == '__main__':
    main()
