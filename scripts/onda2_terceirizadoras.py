"""Onda 2 – fabricantes terceirizadas de cosméticos (segmento 'terceirizadora', categoria Concorrentes).

Uso (python3 -I scripts/onda2_terceirizadoras.py ...):
  coletar <cands.txt> <saida.json>   cands: "nome|site|cidade|uf" (cidade/uf opcionais). Lê home + /contato, /orcamento,
                                     /private-label, /terceirizacao, /maquiagem..., acha CNPJ do rodapé (BrasilAPI:
                                     situação, endereço, telefone/e-mail cadastral, sócios), produtos, pedido mínimo,
                                     certificações, Instagram/LinkedIn; classifica contatos e calcula o score.
  ajustar <saida.json> <manual.json> <final.json> [mais.json ...]
                                     junta resultados, aplica correções à mão (manual.json por site: maquiagem, compactos,
                                     excluir, contatos, uf, cidade, nota...), infere UF pelo DDD e recalcula o score.
  sql <final.json> [min_score]       imprime o INSERT ... ON CONFLICT DO NOTHING (só quem tem e-mail/WhatsApp/telefone
                                     e CNPJ não "baixado"; pula quem já está na base por domínio).
Score = 40 + maquiagem 20 (+10 se pó compacto/blush/sombra/iluminador) + SP 10 + contato comercial 10 (geral 5), teto 90.
Só entra contato publicado no site da própria empresa ou no CNPJ. Reaproveita enriquecer_contatos/enriquecer_sites.
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
FONTE = 'Busca onda 2 – terceirizadoras'


def carregar(nome):
    spec = importlib.util.spec_from_file_location(nome, AQUI / f'{nome}.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


EC = carregar('enriquecer_contatos')
ES = EC.ES
CNPJS = {}
_orig_cnpj = EC.cnpj_info


def _cnpj_cache(c):
    d = re.sub(r'\D', '', c)
    if d not in CNPJS:
        CNPJS[d] = _orig_cnpj(d)
    return CNPJS[d]


EC.cnpj_info = _cnpj_cache


def _baixar(sessao, url):
    """Como ES.baixar, mas acerta a codificação (vários sites não declaram charset) e lê WhatsApp montado por script."""
    try:
        r = sessao.get(url, timeout=ES.TIMEOUT, allow_redirects=True)
        if r.status_code >= 400 or 'html' not in r.headers.get('content-type', ''):
            return None, r.url
        if (r.encoding or '').lower() in ('', 'iso-8859-1'):
            r.encoding = r.apparent_encoding or 'utf-8'
        h = r.text
        for n in re.findall(r'(?:WA_NUMBER|whatsapp(?:Number|_number)?)\s*[=:]\s*["\'](\d{12,13})["\']', h):
            h += f' https://wa.me/{n} '
        return h, r.url
    except requests.RequestException:
        return None, url


ES.baixar = _baixar

CAMINHOS = ['/contato', '/contato/', '/fale-conosco', '/orcamento', '/solicite-orcamento', '/private-label', '/terceirizacao',
            '/terceirizacao-de-cosmeticos', '/maquiagem', '/sobre', '/quem-somos', '/a-empresa', '/empresa', '/institucional',
            '/servicos', '/produtos', '/marca-propria', '/home', '/blog']
MAQUIAGEM = re.compile(r'm[aá]quiagem|maquilhagem|make[- ]?up|batom|p[oó]s? compact|compactad|blush|sombra|iluminador|bronzer|'
                       r'r[ií]mel|m[aá]scara de c[ií]lios|delineador|gloss|corretivo|base (l[ií]quida|facial|em p[oó])|p[oó] facial|'
                       r'cosm[eé]ticos? (de cor|coloridos)', re.I)
COMPACTO = re.compile(r'p[oó]s? compact|compactad|blush|sombra|iluminador|bronzer|prensad', re.I)
PRODUTOS = [('pó compacto', r'p[oó]s? compact|compactad'), ('blush', r'\bblush'), ('sombra', r'\bsombras?\b'),
            ('iluminador', r'iluminador'), ('bronzer', r'bronzer'), ('batom', r'batom|batons'), ('base', r'base (l[ií]quida|facial|em p[oó])|\bbases\b'),
            ('corretivo', r'corretivo'), ('rímel', r'r[ií]mel|m[aá]scara de c[ií]lios'), ('delineador', r'delineador'),
            ('gloss', r'\bgloss|brilho labial'), ('esmalte', r'esmalte'), ('skincare', r'skin ?care|facial|s[eé]rum|hidratante facial|cuidados com a pele'),
            ('protetor solar', r'protetor solar|fotoprote'), ('cabelo', r'shampoo|xampu|condicionador|m[aá]scara capilar|capilar|progressiva'),
            ('corpo', r'hidratante corporal|corporal|sabonete|esfoliante'), ('perfumaria', r'perfum|col[oô]nia|fragr[aâ]ncia|body splash'),
            ('masculino', r'barba|masculin'), ('infantil', r'infantil|baby|beb[eê]'), ('aerossol', r'aeross')]
CERTS = [('ANVISA', r'anvisa'), ('AFE', r'\bAFE\b|autoriza[cç][aã]o de funcionamento'), ('ISO 9001', r'iso ?9001'),
         ('ISO 22716', r'iso ?22716'), ('BPF', r'boas pr[aá]ticas de fabrica|\bBPF\b|\bGMP\b'), ('vegano', r'vegan'),
         ('cruelty free', r'cruelty|n[aã]o testa em animais|livre de crueldade'), ('RDC 176', r'rdc ?176')]
MINIMO = re.compile(r'((?:pedido|lote|quantidade|produ[cç][aã]o|m[ií]nimo)[^.\n]{0,40}m[ií]nim[oa][^.\n]{0,90}?\d[\d.,]*\s?(?:unidades?|un\b|kg|quilos?|pe[cç]as|litros|l\b|reais|R\$)'
                    r'|m[ií]nimo (?:de|a partir de)[^.\n]{0,25}\d[\d.,]*\s?(?:unidades?|un\b|kg|quilos?|pe[cç]as|litros)'
                    r'|a partir de \d[\d.,]*\s?(?:unidades|un\b|kg|quilos|pe[cç]as)'
                    r'|MOQ[:\s]*\d[\d.,]*\s?\w*|sem (?:limite|pedido) m[ií]nimo)', re.I)
RAMO_TERC = re.compile(r'terceiriza|private label|marca pr[oó]pria|white label|fabrica[cç][aã]o (?:para|de) terceiros|industrializa|f[aá]brica de cosm', re.I)
SP_UF = 'SP'


def limpa(h):
    h = re.sub(r'(?is)<(script|style|svg|noscript)\b.*?</\1>', ' ', h)
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', h))


def baixar(c):
    s = requests.Session()
    s.headers.update({'User-Agent': ES.UA})
    site = c['site']
    paginas, vistos, final = [], set(), None
    for base in (f'https://www.{site}', f'https://{site}', f'http://{site}'):
        h, f = ES.baixar(s, base)
        if h:
            paginas.append((f, h))
            final = f
            break
    if not paginas:
        return c, [], None
    sopa_links = set(ES.extrair(paginas[0][1], final)[4])
    mesmo = [l for l in sopa_links if ES.dominio_base(l) == ES.dominio_base(final) and EC.LINKS_UTEIS.search(l)]
    cands = mesmo + [urljoin(final, p) for p in CAMINHOS]
    for l in cands:
        if len(paginas) >= 12:
            break
        if l in vistos:
            continue
        vistos.add(l)
        h, f = ES.baixar(s, l)
        if h and f not in {p[0] for p in paginas}:
            paginas.append((f, h))
    return c, paginas, final


def processar(args):
    c, paginas, final = args
    nome = c['nome']
    r = {'nome': nome, 'site': c['site'], 'cidade': c.get('cidade'), 'uf': c.get('uf'), 'site_final': final}
    if not paginas:
        r['erro'] = 'site não abriu'
        r['contatos'] = []
        return r
    lead = {'chave': c['site'], 'nome': nome, 'site': c['site'], 'email_atual': None}
    a = EC.analisar(lead, paginas)
    r.update({k: a.get(k) for k in ('email', 'whatsapp', 'telefone', 'contato_nome', 'contato_cargo', 'qualidade')})
    r['contatos'] = a['contatos']
    texto = ' '.join(limpa(h) for _, h in paginas)
    r['maquiagem'] = len(MAQUIAGEM.findall(texto))
    r['compactos'] = len(COMPACTO.findall(texto))
    r['produtos'] = [n for n, rx in PRODUTOS if re.search(rx, texto, re.I)]
    r['certificacoes'] = [n for n, rx in CERTS if re.search(rx, texto, re.I if n not in ('AFE', 'BPF') else 0)]
    r['terceirizacao'] = len(RAMO_TERC.findall(texto))
    m = MINIMO.findall(texto)
    r['pedido_minimo'] = re.sub(r'\s+', ' ', m[0]).strip()[:160] if m else None
    instas, lin = {}, None
    for u, h in paginas:
        for i in ES.extrair(h, u)[3]:
            instas[i] = instas.get(i, 0) + 1
        lm = re.search(r'linkedin\.com/company/[A-Za-z0-9_%.-]+', h)
        lin = lin or (lm.group(0) if lm else None)
    ig = [i for i, _ in sorted(instas.items(), key=lambda x: -x[1])
          if EC.norm(i)[:5] in EC.norm(nome) or EC.norm(nome)[:5] in EC.norm(i) or EC.norm(i)[:5] in EC.norm(c['site'])]
    r['instagram'] = ig[0] if ig else None
    r['linkedin'] = ('https://www.' + lin) if lin else None
    cn = re.findall(EC.CNPJ.pattern, texto[-80000:])
    r['cnpj_info'] = None
    if cn:
        # o CNPJ mais citado cujo cadastro é de empresa de cosméticos/química ativa
        for k in sorted(set(cn), key=cn.count, reverse=True)[:3]:
            info = _cnpj_cache(k)
            time.sleep(0.3)
            if info:
                r['cnpj_info'] = {x: info.get(x) for x in ('cnpj', 'razao_social', 'nome_fantasia', 'descricao_situacao_cadastral', 'cnae_fiscal_descricao',
                                                            'logradouro', 'numero', 'bairro', 'municipio', 'uf', 'cep')}
                break
    # endereço no cadastro: telefone/e-mail cadastrais entram em contatos via analisar
    return r


def score(r):
    s = 40
    if r.get('maquiagem'):
        s += 20
        if r.get('compactos'):
            s += 10
    if (r.get('uf') or '').upper() == SP_UF:
        s += 10
    q = r.get('qualidade')
    s += 10 if q in ('comercial', 'direto', 'agencia') else (5 if q == 'geral' else 0)
    return min(90, s)


def cmd_coletar(cands, saida):
    cs = []
    for l in Path(cands).read_text(encoding='utf-8').splitlines():
        p = (l.strip().split('|') + ['', '', ''])[:4]
        if p[0] and p[1]:
            cs.append({'nome': p[0], 'site': re.sub(r'^https?://(www\.)?|/.*$', '', p[1].lower()), 'cidade': p[2] or None, 'uf': p[3] or None})
    with ThreadPoolExecutor(8) as ex:
        baixados = list(ex.map(baixar, cs))
    res = []
    for i, b in enumerate(baixados, 1):
        r = processar(b)
        # cidade/UF do cadastro quando a lista não trouxe
        ci = r.get('cnpj_info') or {}
        if not r.get('uf') and ci.get('uf'):
            r['uf'], r['cidade'] = ci['uf'], (ci.get('municipio') or '').title()
        r['score'] = score(r)
        res.append(r)
        print(f"{i}/{len(cs)} {r['nome']}: {r.get('qualidade')} mq={r.get('maquiagem')} cnpj={'ok' if ci else '-'}", flush=True)
    Path(saida).write_text(json.dumps(res, ensure_ascii=False, indent=0), encoding='utf-8')


DDD_UF = {**{d: 'SP' for d in range(11, 20)}, 21: 'RJ', 22: 'RJ', 24: 'RJ', 27: 'ES', 28: 'ES', **{d: 'MG' for d in range(31, 39)},
          **{d: 'PR' for d in (41, 42, 43, 44, 45, 46)}, 47: 'SC', 48: 'SC', 49: 'SC', 51: 'RS', 53: 'RS', 54: 'RS', 55: 'RS', 61: 'DF',
          62: 'GO', 64: 'GO', 71: 'BA', 73: 'BA', 74: 'BA', 75: 'BA', 77: 'BA', 81: 'PE', 85: 'CE'}
CORES = {'pó compacto', 'blush', 'sombra', 'iluminador', 'bronzer'}


def cmd_ajustar(arq, manual, saida, extras=()):
    man = json.load(open(manual, encoding='utf-8'))
    base = {}
    for a in (arq, *extras):
        for r in json.load(open(a, encoding='utf-8')):
            base[r['site']] = r
    for site, m in man.items():
        base.setdefault(site, {'nome': m.get('nome', site), 'site': site, 'contatos': [], 'produtos': [], 'certificacoes': []})
    out = []
    for site, r in base.items():
        m = man.get(site, {})
        if m.get('excluir'):
            r['excluir'] = m['excluir']
        for k in ('nome', 'uf', 'cidade', 'instagram', 'linkedin', 'fonte_url', 'contato_nome', 'contato_cargo', 'pedido_minimo', 'subsegmento'):
            if m.get(k):
                r[k] = m[k]
        if m.get('nota'):
            r['observacao_extra'] = m['nota']
        r['produtos'] = sorted(set(r.get('produtos') or []) | set(m.get('produtos_extra') or []))
        cs = [c for c in r.get('contatos', []) if not (c.get('email') and c['email'] == m.get('email_remove'))]
        for c in m.get('contatos', []):
            c = {**c, 'manual': True}
            if c.get('telefone'):
                c['telefone'] = EC.e164(c['telefone']) or c['telefone']
            if c.get('whatsapp'):
                c['whatsapp'] = EC.e164(c['whatsapp']) or c['whatsapp']
            cs.append(c)
        mon = EC.montar({'chave': site, 'nome': r['nome'], 'email_atual': None}, cs)
        for k in ('email', 'whatsapp', 'telefone', 'qualidade'):
            r[k] = mon.get(k)
        r['contatos'] = mon['contatos']
        if r.get('contato_nome') is None and mon.get('contato_nome'):
            r['contato_nome'] = mon['contato_nome']
        prod = set(r['produtos'])
        mq = (len(prod & {'pó compacto', 'blush', 'sombra', 'batom', 'iluminador', 'bronzer', 'corretivo', 'rímel', 'delineador'}) >= 2
              or (r.get('maquiagem') or 0) >= 2 and bool(prod & {'pó compacto', 'blush', 'sombra', 'batom', 'iluminador', 'corretivo', 'base'}))
        r['faz_maquiagem'] = bool(m['maquiagem']) if 'maquiagem' in m else mq
        r['faz_compactos'] = bool(m['compactos']) if 'compactos' in m else bool(r['faz_maquiagem'] and (prod & CORES) and r.get('compactos', 0) >= 3)
        if r['faz_maquiagem']:
            r['produtos'] = sorted(set(r['produtos']) | {'maquiagem'})
        if not r.get('uf'):
            tel = r.get('telefone') or ''
            if tel.startswith('+55') and tel[3:5].isdigit():
                r['uf'] = DDD_UF.get(int(tel[3:5]))
        r['maquiagem'] = int(r['faz_maquiagem'])
        r['compactos'] = int(r['faz_compactos'])
        r['score'] = score(r)
        out.append(r)
    Path(saida).write_text(json.dumps(out, ensure_ascii=False, indent=0), encoding='utf-8')
    ok = [r for r in out if (r.get('email') or r.get('whatsapp') or r.get('telefone')) and not r.get('excluir')]
    print(f'{len(ok)} elegíveis de {len(out)} | maquiagem {sum(r["faz_maquiagem"] for r in ok)} | compactos {sum(r["faz_compactos"] for r in ok)} | SP {sum((r.get("uf") or "") == "SP" for r in ok)}')


def q(s):
    return 'null' if s in (None, '') else "'" + str(s).replace("'", "''") + "'"


def subsegmento(r):
    prod = set(r.get('produtos') or []) - {'maquiagem'}
    outros = prod - {'pó compacto', 'blush', 'sombra', 'iluminador', 'bronzer', 'batom', 'base', 'corretivo', 'rímel', 'delineador', 'gloss', 'esmalte'}
    if r.get('faz_maquiagem') and (r.get('faz_compactos') or len(outros) <= 3):
        return 'Private label maquiagem'
    if r.get('faz_maquiagem'):
        return 'Terceirização cosméticos em geral (inclui maquiagem)'
    if 'perfumaria' in prod and prod <= {'perfumaria', 'corpo'}:
        return 'Perfumaria'
    if 'cabelo' in prod and not {'skincare', 'corpo'} & prod:
        return 'Private label capilar'
    if 'skincare' in prod and len(prod) <= 3:
        return 'Private label skincare'
    return 'Terceirização cosméticos em geral'


def cmd_sql(arq, minimo=0):
    linhas = []
    for r in json.load(open(arq)):
        ci = r.get('cnpj_info') or {}
        if 'BAIXADA' in (ci.get('descricao_situacao_cadastral') or '').upper() or 'INAPTA' in (ci.get('descricao_situacao_cadastral') or '').upper():
            continue
        if not (r.get('email') or r.get('whatsapp') or r.get('telefone')) or r.get('score', 0) < int(minimo) or r.get('excluir'):
            continue
        cs = [{k: v for k, v in c.items() if k != 'manual'} | {'data': DATA, **({'fonte': re.sub(r'^https?://(www\.)?', '', c['fonte'])[:90]})}
              for c in sorted(r['contatos'], key=lambda c: -EC.RANK[c['tipo']])[:6]]
        end = ' '.join(x for x in (ci.get('logradouro'), ci.get('numero')) if x).title() or None
        if ci and EC.norm(ci.get('municipio')) != EC.norm(r.get('cidade')):
            ci = {**ci, 'bairro': None}  # CNPJ de outro estabelecimento: não usa o endereço dele
            end = None
        socios = r.get('socios') or []
        extras = {'contatos': cs, 'contato_qualidade': r.get('qualidade'), 'produtos': r.get('produtos'), 'faz_maquiagem': r.get('faz_maquiagem'), 'faz_compactos': r.get('faz_compactos'),
                  'enriquecimento': 'site + BrasilAPI (onda 2)',
                  'onda': 'onda2_2026-10-21'}
        if ci.get('cnpj'):
            extras['cnpj'] = ci['cnpj']
            extras['situacao_cnpj'] = ci.get('descricao_situacao_cadastral')
        for k in ('pedido_minimo', 'certificacoes', 'socios', 'observacao_extra'):
            if r.get(k):
                extras[k if k != 'observacao_extra' else 'obs'] = r[k]
        extras = {k: v for k, v in extras.items() if v}
        linhas.append(
            f"('{r['site']}',{q(r['nome'])},{q(r.get('contato_nome'))},{q(r.get('contato_cargo'))},{q(r.get('subsegmento') or subsegmento(r))},"
            f"{q(r.get('cidade'))},{q((r.get('uf') or '').upper())},{q((ci.get('bairro') or '').title())},{q(end)},{q(r.get('instagram'))},"
            f"{q(r.get('linkedin'))},{q(r.get('email'))},{q(r.get('telefone'))},{q(r.get('whatsapp'))},{q(r.get('fonte_url') or ('https://' + r['site']))},"
            f"{r['score']},{q(json.dumps(extras, ensure_ascii=False, separators=(',', ':')))})")
    print(SQL_BASE.format(fonte=FONTE, valores=',\n'.join(linhas)))
    print(f'-- {len(linhas)} linhas', file=sys.stderr)


SQL_BASE = """insert into public.leads (tipo, segmento_id, nome, contato_nome, contato_cargo, subsegmento, cidade, uf, bairro, endereco,
  site, instagram, linkedin, email, telefone, whatsapp, fonte, fonte_url, score, status, extras)
select 'cliente', 'terceirizadora', v.nome, v.cnome, v.ccargo, v.sub, v.cidade, v.uf, v.bairro, v.endereco,
  v.site, v.insta, v.lin, v.email, v.tel, v.zap, '{fonte}', v.furl, v.score, 'novo', v.extras::jsonb
from (values
{valores}
) as v(site, nome, cnome, ccargo, sub, cidade, uf, bairro, endereco, insta, lin, email, tel, zap, furl, score, extras)
where not exists (select 1 from public.leads l where regexp_replace(lower(coalesce(l.site,'')), '^https?://(www\\.)?|/.*$', '', 'g') = v.site)
on conflict do nothing;"""


def main():
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    if a[0] == 'coletar':
        cmd_coletar(a[1], a[2])
    elif a[0] == 'ajustar':
        cmd_ajustar(a[1], a[2], a[3], a[4:])
    elif a[0] == 'sql':
        cmd_sql(a[1], *(a[2:3]))
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
