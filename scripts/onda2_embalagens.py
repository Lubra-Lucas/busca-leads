"""Onda 2 – fornecedores de EMBALAGENS para cosméticos/maquiagem (segmento 'embalagens', tipo fornecedor).

Uso (python3 -I scripts/onda2_embalagens.py ...):
  coletar <cands.txt> <saida.json>   cands: "nome|site|cidade|uf" (cidade/uf opcionais). Lê home + páginas de produtos/contato,
                                     CNPJ do rodapé (BrasilAPI: situação, endereço, telefone/e-mail cadastral, sócios),
                                     produtos/materiais, pedido mínimo, personalização, importador; classifica contatos.
  ajustar <saida.json> <manual.json> <final.json> [mais.json ...]
                                     junta resultados e aplica correções à mão (manual.json por site: nome, uf, cidade,
                                     subsegmento, produtos_extra, contatos, excluir, importador, pedido_minimo...).
  sql <final.json> [min_score]       imprime INSERT ... ON CONFLICT DO NOTHING (só com e-mail/WhatsApp/telefone, CNPJ não
                                     baixado, e sem duplicata por domínio, @ ou nome normalizado).
Score = 40 + estojo/godê/paleta 25 (cartucho/rótulo 10, frasco/pote 5) + SP 15 + contato comercial 10 (geral 5)
        + pedido mínimo baixo (<=1000 un) 5, teto 95. Só contato publicado no site da empresa ou no CNPJ.
Reaproveita onda2_terceirizadoras (download), enriquecer_contatos e enriquecer_sites.
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
DATA = '2026-10-21'
FONTE = 'Busca onda 2 – fornecedores de embalagens'


def carregar(nome):
    spec = importlib.util.spec_from_file_location(nome, AQUI / f'{nome}.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


T = carregar('onda2_terceirizadoras')
EC, ES = T.EC, T.ES
q = T.q
# páginas extras onde fabricantes de embalagem listam produtos/contato
T.CAMINHOS += ['/estojos', '/estojo', '/maquiagem', '/cosmeticos', '/catalogo', '/linha-cosmetica', '/embalagens', '/embalagens-para-cosmeticos',
               '/orcamento-online', '/solicitar-orcamento', '/representantes', '/fale-com-a-gente', '/atendimento']

PRODUTOS = [
    ('estojo compacto', r'estojos? (?:para |de )?(?:p[oó]s? )?compact|p[oó]s? compact\w*|compactos? (?:vazio|para p[oó])|base compacta|compact case|pancake'),
    ('estojo', r'\bestojos?\b'), ('paleta de sombra', r'paletas?(?: de| para)? (?:sombra|maquiagem)|palete de sombra|quarteto|estojo (?:para )?sombra'),
    ('godê', r'god[eê]s?\b|godets?|\bpans?\b (?:de|para) (?:sombra|blush|alum)'), ('espelho', r'espelhos? (?:para|de) (?:estojo|compact|bolsa)|estojo com espelho'),
    ('peneira', r'peneiras?|sifter'), ('pote para pó', r'pote (?:para |de )?p[oó]|loose powder|p[oó] solto'),
    ('batom', r'estojo (?:de |para )?batom|\bbatons?\b|lipstick|bisnaga labial'), ('gloss', r'\bgloss\b|brilho labial'),
    ('rímel', r'r[ií]mel|m[aá]scara de c[ií]lios|mascara'), ('refil', r'refil|recarreg[aá]vel|refill'),
    ('frasco', r'\bfrascos?\b'), ('pote', r'\bpotes?\b'), ('bisnaga', r'bisnagas?|tubos? (?:laminado|pl[aá]stico)'), ('tampa', r'\btampas?\b'),
    ('válvula', r'v[aá]lvulas?|bombas? dosadora|\bpump\b|spray|aerossol'), ('airless', r'airless'), ('conta-gotas', r'conta[- ]gotas'),
    ('cartucho', r'cartuchos?|papel[- ]cart[aã]o|triplex|cartonagem|caixa r[ií]gida|caixas? (?:de )?papel'), ('rótulo', r'r[oó]tulos?|etiquetas?'),
    ('caixa de transporte', r'caixas? (?:de )?(?:papel[aã]o|transporte|e-?commerce|remessa)|papel[aã]o ondulado'), ('vidro', r'\bvidro\b|frascos? de vidro'),
    ('pincel', r'pinc[eé]is|pincel'), ('amostra', r'amostras? (?:de |para )?cosm|sach[eê]s?')]
MATERIAIS = [('plástico', r'pl[aá]sticos?'), ('PP', r'\bPP\b|polipropileno'), ('PS', r'\bPS\b|poliestireno'), ('ABS', r'\bABS\b'),
             ('acrílico', r'acr[ií]lic'), ('PET', r'\bPET\b'), ('PEAD', r'\bPEAD\b|polietileno de alta'), ('alumínio', r'alum[ií]nio'),
             ('metal', r'\bmetal\b|met[aá]lic|folha[- ]de[- ]flandres|estanho'), ('vidro', r'\bvidro\b'), ('papel-cartão', r'papel[- ]cart[aã]o|triplex|cartonagem'),
             ('papelão', r'papel[aã]o'), ('bioplástico', r'bioplast|biodegrad|compost[aá]vel|PCR|reciclad')]
PERSONALIZACAO = [('hot stamping', r'hot[- ]?stamp|hot stamping|estampagem a quente'), ('serigrafia', r'serigraf'), ('tampografia', r'tampograf'),
                  ('impressão personalizada', r'impress[aã]o personaliz|personaliza[cç][aã]o|personalizad'), ('metalização', r'metaliza[cç]'),
                  ('cores personalizadas', r'cores? (?:sob medida|personaliz|pantone)|pantone'), ('molde exclusivo', r'molde (?:pr[oó]prio|exclusiv)|ferramental'),
                  ('offset', r'\boffset\b'), ('verniz UV/hot stamping', r'verniz (?:uv|localizado)|relevo')]
COSM = re.compile(r'cosm[eé]tic|maquiagem|beleza|perfum|batom|skincare|higiene pessoal', re.I)
EMBAL = re.compile(r'embalag|estojo|frasco|r[oó]tulo|etiqueta|cartucho|bisnaga|tampa|godê|godê', re.I)
IMPORT = re.compile(r'importad|importa[cç][aã]o|importamos|trading|direto da china', re.I)
MINIMO = re.compile(r'((?:pedido|lote|quantidade|compra|produ[cç][aã]o)\s+m[ií]nim[oa][^.\n]{0,70}?\d[\d.]*\s?(?:unidades?|un\b|pe[cç]as|pcs|kits?)'
                    r'|m[ií]nimo\s+(?:de|a partir de)[^.\n]{0,20}\d[\d.]*\s?(?:unidades?|un\b|pe[cç]as|kits?)'
                    r'|a partir de \d[\d.]*\s?(?:unidades|un\b|pe[cç]as)|MOQ[:\s]*\d[\d.]*\s?\w*|sem (?:pedido|quantidade|lote) m[ií]nim[oa])', re.I)
ATIVAS = ('ATIVA',)


def limpar_contatos(cs):
    """Tira números de exemplo (123456789), e-mails com %20 e duplicatas."""
    out = []
    for c in cs:
        c = dict(c)
        if c.get('email'):
            c['email'] = re.sub(r'^(?:%20|\s)+', '', c['email'])
        for k in ('telefone', 'whatsapp'):
            if c.get(k) and re.search(r'123456789|987654321|0000000', c[k]):
                c.pop(k)
        if c.get('email') or c.get('telefone') or c.get('whatsapp'):
            out.append(c)
    return out


def processar(args):
    c, paginas, final = args
    nome = c['nome']
    r = {'nome': nome, 'site': c['site'], 'cidade': c.get('cidade'), 'uf': c.get('uf'), 'site_final': final}
    if not paginas:
        r.update(erro='site não abriu', contatos=[])
        return r
    lead = {'chave': c['site'], 'nome': nome, 'site': c['site'], 'email_atual': None}
    a = EC.analisar(lead, paginas)
    r.update({k: a.get(k) for k in ('email', 'whatsapp', 'telefone', 'contato_nome', 'contato_cargo', 'qualidade')})
    r['contatos'] = limpar_contatos(a['contatos'])
    for k in ('email', 'whatsapp', 'telefone'):
        if r.get(k) and not any(c.get(k) == r[k] for c in r['contatos']) and k != 'email':
            r[k] = next((c[k] for c in r['contatos'] if c.get(k)), None)
    if r.get('email') and not any(c.get('email') == r['email'] for c in r['contatos']):
        r['email'] = next((c['email'] for c in r['contatos'] if c.get('email')), None)
    texto = ' '.join(T.limpa(h) for _, h in paginas)
    r['cosm'] = len(COSM.findall(texto))
    r['embal'] = len(EMBAL.findall(texto))
    r['produtos'] = [n for n, rx in PRODUTOS if re.search(rx, texto, re.I)]
    r['materiais'] = [n for n, rx in MATERIAIS if re.search(rx, texto, 0 if n in ('PP', 'PS', 'ABS', 'PET', 'PEAD', 'PCR') else re.I)]
    r['personalizacao'] = [n for n, rx in PERSONALIZACAO if re.search(rx, texto, re.I)]
    r['importador'] = bool(IMPORT.search(texto))
    m = MINIMO.findall(texto)
    r['pedido_minimo'] = re.sub(r'\s+', ' ', m[0]).strip()[:140] if m else None
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
    for k in sorted(set(cn), key=cn.count, reverse=True)[:3]:
        info = T._cnpj_cache(k)
        time.sleep(0.3)
        if info:
            r['cnpj_info'] = {x: info.get(x) for x in ('cnpj', 'razao_social', 'nome_fantasia', 'descricao_situacao_cadastral', 'cnae_fiscal_descricao',
                                                        'logradouro', 'numero', 'bairro', 'municipio', 'uf', 'cep')}
            r['socios'] = [f"{s['nome_socio'].title()} ({(s.get('qualificacao_socio') or 'Sócio').title()})" for s in (info.get('qsa') or [])[:4] if s.get('nome_socio')]
            break
    return r


def minimo_baixo(txt):
    if not txt:
        return False
    if re.search(r'sem (?:pedido|quantidade|lote)', txt, re.I):
        return True
    n = re.findall(r'\d[\d.]*', txt)
    try:
        return bool(n) and int(n[-1].replace('.', '')) <= 1000
    except ValueError:
        return False


def subsegmento(r):
    p = set(r.get('produtos') or [])
    if r.get('importador') and (p & {'estojo compacto', 'estojo', 'paleta de sombra', 'godê', 'batom', 'gloss', 'rímel'}):
        return 'Importador de embalagens'
    if p & {'godê'} and not p & {'estojo compacto', 'paleta de sombra'}:
        return 'Godês e pans'
    if p & {'estojo compacto', 'paleta de sombra', 'godê', 'espelho', 'peneira', 'pote para pó'}:
        return 'Estojos compactos'
    if p & {'cartucho'} and not p & {'frasco', 'pote', 'bisnaga'}:
        return 'Cartuchos e papel-cartão'
    if p & {'rótulo'} and not p & {'frasco', 'pote', 'bisnaga', 'cartucho'}:
        return 'Rótulos'
    if p & {'caixa de transporte'} and not p & {'frasco', 'pote', 'bisnaga'}:
        return 'Embalagem de transporte'
    if p & {'batom', 'gloss', 'rímel', 'estojo'}:
        return 'Embalagens de maquiagem (batom, gloss, rímel)'
    if r.get('importador'):
        return 'Importador de embalagens'
    return 'Frascos e potes'


def score(r):
    sub = r.get('subsegmento') or subsegmento(r)
    s = 40
    if sub in ('Estojos compactos', 'Godês e pans') or (set(r.get('produtos') or []) & {'estojo compacto', 'godê', 'paleta de sombra'}):
        s += 25
    elif sub in ('Cartuchos e papel-cartão', 'Rótulos', 'Embalagem de transporte', 'Embalagens de maquiagem (batom, gloss, rímel)'):
        s += 10
    else:
        s += 5
    if (r.get('uf') or '').upper() == 'SP':
        s += 15
    q_ = r.get('qualidade')
    s += 10 if q_ in ('comercial', 'direto', 'agencia') else (5 if q_ == 'geral' else 0)
    if minimo_baixo(r.get('pedido_minimo')):
        s += 5
    return min(95, s)


def cmd_coletar(cands, saida):
    cs = []
    for l in Path(cands).read_text(encoding='utf-8').splitlines():
        p = (l.strip().split('|') + ['', '', ''])[:4]
        if p[0] and p[1] and not l.startswith('#'):
            cs.append({'nome': p[0], 'site': re.sub(r'^https?://(www\.)?|/.*$', '', p[1].lower()), 'cidade': p[2] or None, 'uf': p[3] or None})
    with ThreadPoolExecutor(8) as ex:
        baixados = list(ex.map(T.baixar, cs))
    res = []
    for i, b in enumerate(baixados, 1):
        r = processar(b)
        ci = r.get('cnpj_info') or {}
        if not r.get('uf') and ci.get('uf'):
            r['uf'], r['cidade'] = ci['uf'], (ci.get('municipio') or '').title()
        r['subsegmento_auto'] = subsegmento(r)
        r['score'] = score(r)
        res.append(r)
        print(f"{i}/{len(cs)} {r['nome']}: {r.get('qualidade')} cosm={r.get('cosm')} emb={r.get('embal')} {r['subsegmento_auto']} cnpj={'ok' if ci else '-'}", flush=True)
    Path(saida).write_text(json.dumps(res, ensure_ascii=False, indent=0), encoding='utf-8')


def cmd_ajustar(arq, manual, saida, extras=()):
    man = json.load(open(manual, encoding='utf-8'))
    base = {}
    for a in (arq, *extras):
        for r in json.load(open(a, encoding='utf-8')):
            base[r['site']] = r
    for site, m in man.items():
        base.setdefault(site, {'nome': m.get('nome', site), 'site': site, 'contatos': [], 'produtos': [], 'materiais': []})
    out = []
    for site, r in base.items():
        m = man.get(site, {})
        for k in ('nome', 'uf', 'cidade', 'instagram', 'linkedin', 'fonte_url', 'contato_nome', 'contato_cargo', 'pedido_minimo', 'subsegmento', 'excluir', 'importador'):
            if k in m:
                r[k] = m[k]
        if m.get('nota'):
            r['obs'] = m['nota']
        r['produtos'] = sorted((set(r.get('produtos') or []) | set(m.get('produtos_extra') or [])) - set(m.get('produtos_remove') or []))
        r['materiais'] = sorted(set(r.get('materiais') or []) | set(m.get('materiais_extra') or []))
        cs = [c for c in r.get('contatos', []) if not (c.get('email') and c['email'] in (m.get('email_remove') or []))]
        for c in m.get('contatos', []):
            c = {**c, 'manual': True}
            for k in ('telefone', 'whatsapp'):
                if c.get(k):
                    c[k] = EC.e164(c[k]) or c[k]
            cs.append(c)
        mon = EC.montar({'chave': site, 'nome': r['nome'], 'email_atual': None}, cs)
        for k in ('email', 'whatsapp', 'telefone', 'qualidade'):
            r[k] = mon.get(k)
        r['contatos'] = mon['contatos']
        if not r.get('contato_nome') and mon.get('contato_nome'):
            r['contato_nome'], r['contato_cargo'] = mon['contato_nome'], mon.get('contato_cargo')
        if not r.get('uf'):
            tel = r.get('telefone') or ''
            if tel.startswith('+55') and tel[3:5].isdigit():
                r['uf'] = T.DDD_UF.get(int(tel[3:5]))
        r['subsegmento'] = r.get('subsegmento') or subsegmento(r)
        r['score'] = score(r)
        out.append(r)
    Path(saida).write_text(json.dumps(out, ensure_ascii=False, indent=0), encoding='utf-8')
    ok = [r for r in out if (r.get('email') or r.get('whatsapp') or r.get('telefone')) and not r.get('excluir')]
    print(f'{len(ok)} elegíveis de {len(out)} | SP {sum((r.get("uf") or "") == "SP" for r in ok)}')


def cmd_sql(arq, minimo=0):
    linhas = []
    for r in json.load(open(arq)):
        ci = r.get('cnpj_info') or {}
        sit = (ci.get('descricao_situacao_cadastral') or '').upper()
        if 'BAIXADA' in sit or 'INAPTA' in sit or 'SUSPENSA' in sit or 'NULA' in sit:
            continue
        if not (r.get('email') or r.get('whatsapp') or r.get('telefone')) or r.get('score', 0) < int(minimo) or r.get('excluir'):
            continue
        cs = [{k: v for k, v in c.items() if k != 'manual'} | {'data': DATA, 'fonte': re.sub(r'^https?://(www\.)?', '', c.get('fonte', ''))[:90]}
              for c in sorted(r['contatos'], key=lambda c: -EC.RANK[c['tipo']])[:6]]
        end = ' '.join(x for x in (ci.get('logradouro'), ci.get('numero')) if x).title() or None
        bairro = (ci.get('bairro') or '').title()
        if ci and EC.norm(ci.get('municipio')) != EC.norm(r.get('cidade')):
            end, bairro = None, ''  # CNPJ de outro estabelecimento: não usa o endereço dele
        extras = {'contatos': cs, 'contato_qualidade': r.get('qualidade'), 'produtos': r.get('produtos'), 'materiais': r.get('materiais'),
                  'pedido_minimo': r.get('pedido_minimo'), 'personalizacao': r.get('personalizacao'), 'importador': bool(r.get('importador')),
                  'socios': r.get('socios'), 'obs': r.get('obs'), 'enriquecimento': 'site + BrasilAPI (onda 2 embalagens)', 'onda': 'onda2_2026-10-21'}
        if ci.get('cnpj'):
            extras['cnpj'] = ci['cnpj']
            extras['situacao_cnpj'] = ci.get('descricao_situacao_cadastral')
        extras = {k: v for k, v in extras.items() if v not in (None, '', [], {})} | {'importador': bool(r.get('importador'))}
        linhas.append(
            f"('{r['site']}',{q(r['nome'])},{q(r.get('contato_nome'))},{q(r.get('contato_cargo'))},{q(r.get('subsegmento'))},"
            f"{q(r.get('cidade'))},{q((r.get('uf') or '').upper())},{q(bairro)},{q(end)},{q(r.get('instagram'))},"
            f"{q(r.get('linkedin'))},{q(r.get('email'))},{q(r.get('telefone'))},{q(r.get('whatsapp'))},{q(r.get('fonte_url') or ('https://' + r['site']))},"
            f"{r['score']},{q(json.dumps(extras, ensure_ascii=False, separators=(',', ':')))})")
    print(SQL_BASE.format(fonte=FONTE, valores=',\n'.join(linhas)))
    print(f'-- {len(linhas)} linhas', file=sys.stderr)


SQL_BASE = """insert into public.leads (tipo, segmento_id, nome, contato_nome, contato_cargo, subsegmento, cidade, uf, bairro, endereco,
  site, instagram, linkedin, email, telefone, whatsapp, fonte, fonte_url, score, status, extras)
select 'fornecedor', 'embalagens', v.nome, v.cnome, v.ccargo, v.sub, v.cidade, v.uf, v.bairro, v.endereco,
  v.site, v.insta, v.lin, v.email, v.tel, v.zap, '{fonte}', v.furl, v.score, 'novo', v.extras::jsonb
from (values
{valores}
) as v(site, nome, cnome, ccargo, sub, cidade, uf, bairro, endereco, insta, lin, email, tel, zap, furl, score, extras)
where not exists (select 1 from public.leads l where regexp_replace(lower(coalesce(l.site,'')), '^https?://(www\\.)?|/.*$', '', 'g') = v.site
    or (v.insta is not null and lower(l.instagram) = lower(v.insta))
    or regexp_replace(translate(lower(l.nome), 'áàâãäéèêëíìîïóòôõöúùûüç', 'aaaaaeeeeiiiiooooouuuuc'), '[^a-z0-9]', '', 'g')
      = regexp_replace(translate(lower(v.nome), 'áàâãäéèêëíìîïóòôõöúùûüç', 'aaaaaeeeeiiiiooooouuuuc'), '[^a-z0-9]', '', 'g'))
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
