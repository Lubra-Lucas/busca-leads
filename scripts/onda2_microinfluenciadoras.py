"""Onda 2: capta microinfluenciadoras (10 mil a 1 milhão) com contato fora de DM e gera o SQL de inserção.

Uso (python3 -I scripts/onda2_microinfluenciadoras.py ...):
  coletar <saida.json> [cidade/categoria ...]   baixa as páginas públicas da Modash (cidade x categoria) e extrai
                                                 {nome, instagram, bio, seguidores, e-mails da bio}. Sem args: SP inteiro.
  tiktok  <candidatos.json> <saida.json>        tenta o mesmo @ no TikTok (scripts/tiktok_shop.perfil); só aceita se o
                                                 nome do perfil bate com o nome; soma e-mail da bio/link e seguidores.
  sql     <revisados.json> <saida.sql>          gera INSERT ... ON CONFLICT DO NOTHING (rode pelo MCP/SQL editor).

Regras: só entra quem tem e-mail/WhatsApp/telefone publicado pela própria pessoa (bio) ou pela agência. Nada de DM.
Score = 40 + contato (e-mail 25, WhatsApp/tel 20, agência +15) + seguidores (100k–1M +10, 30k–100k +5) + beleza +10 + SP +5, teto 90.
"""
import json
import re
import subprocess
import sys
import time
import unicodedata
import urllib.parse

DATA = '2026-10-21'
FONTE = 'Busca onda 2 – microinfluenciadoras'
EMAIL = re.compile(r'[\w.+-]+@[\w-]+(?:\.[\w-]+)+', re.I)
CIDADES = ['são-paulo', 'rio-de-janeiro', 'belo-horizonte', 'brasília', 'salvador', 'fortaleza']  # só estas têm página completa
CATEGORIAS = ['beauty', 'beauty/affiliates', 'micro', 'micro/affiliates', 'fashion', 'fashion/affiliates', 'fitness',
              'fitness/affiliates', 'food', 'food/affiliates', 'mom', 'affiliates', '']
# a página traz os perfis em dois formatos: JS (fullName:"..",bio:`..`) e JSON ("fullName":"..","bio":"..")
BLOCO = re.compile(r'"?fullName"?:')
CAMPO_NOME = re.compile(r'^\s*"((?:[^"\\]|\\.)*)"')
CAMPO_USER = re.compile(r'"?username"?:"([^"]+)"')
CAMPO_BIO = re.compile(r'"?bio"?:(?:`([^`]*)`|("(?:[^"\\]|\\.)*"))')
CAMPO_SEG = re.compile(r'"?followers"?:(\d+)')


def desescapar(txt):
    try:
        return json.loads('"' + txt + '"') if not txt.startswith('"') else json.loads(txt)
    except ValueError:
        return txt


def perfis(html):
    partes = BLOCO.split(html)[1:]
    for parte in partes:
        parte = parte[:60000]
        n, u, b, f = CAMPO_NOME.search(parte), CAMPO_USER.search(parte), CAMPO_BIO.search(parte), CAMPO_SEG.search(parte)
        if not (n and u and f):
            continue
        # o username/bio/followers têm de ser do mesmo perfil: aparecem antes do bloco seguinte
        if u.start() > 400:
            continue
        bio = (b.group(1) if b and b.group(1) is not None else desescapar(b.group(2)) if b else '')
        yield desescapar(n.group(1)), u.group(1), bio, f.group(1)


def baixar(url):
    return subprocess.run(['curl', '-sL', '-m', '40', url], capture_output=True, text=True).stdout


def emails_de(texto):
    achados = [e.rstrip('.').lower() for e in EMAIL.findall(texto or '')]
    return list(dict.fromkeys(e for e in achados if not e.endswith(('.png', '.jpg')) and '@modash' not in e))


def coletar(saida, alvos):
    alvos = alvos or [f'{c}/{k}'.rstrip('/') for c in CIDADES for k in CATEGORIAS]
    achados = {}
    for alvo in alvos:
        cidade = alvo.split('/')[0]
        html = baixar('https://www.modash.io/find-influencers/brazil/' + urllib.parse.quote(alvo))
        n = 0
        for nome, user, bio, seg in perfis(html):
            n += 1
            ig = user.lower()
            if ig not in achados:
                achados[ig] = {'nome': nome, 'instagram': '@' + ig, 'bio': bio, 'seguidores': int(seg),
                               'emails': emails_de(bio), 'alvo': alvo}
        print(alvo, n, file=sys.stderr)
        time.sleep(1)
    json.dump(list(achados.values()), open(saida, 'w'), ensure_ascii=False, indent=1)


def norm(s):
    s = unicodedata.normalize('NFKD', str(s or '')).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]', '', s)


def tiktok(entrada, saida):
    sys.path.insert(0, __file__.rsplit('/', 1)[0])
    import tiktok_shop
    lista = json.load(open(entrada))
    for c in lista:
        p = tiktok_shop.perfil(c['instagram'].lstrip('@'), tentativas=2)
        time.sleep(1)
        if p and 'erro' not in p:
            a, b = norm(c['nome']), norm(p['nome_perfil'])
            if (a[:6] and a[:6] in b) or (b[:6] and b[:6] in a) or norm(c['instagram']) == norm(p['handle']) and a[:4] in b:
                c['tiktok_perfil'] = p
                c['emails'] = list(dict.fromkeys(c['emails'] + emails_de(p['bio'])))
    json.dump(lista, open(saida, 'w'), ensure_ascii=False, indent=1)


def q(v):
    if v is None:
        return 'null'
    return "'" + str(v).replace("'", "''") + "'"


def sql(entrada, saida):
    """Cada item revisado: nome, instagram, seguidores, emails, [whatsapp, telefone, agencia, cidade, uf, subsegmento, nichos,
    plataforma, seguidores_origem, fonte_url, tiktok_perfil]. Gera SQL compacto (constantes do extras montadas no banco)."""
    linhas = []
    for c in json.load(open(entrada)):
        ag = c.get('agencia')
        contatos = [{'nome': ag or c['nome'], 'cargo': 'Agência' if ag else 'Influenciadora', 'email': e,
                     'tipo': 'agencia' if ag else 'direto', 'fonte': 'bio do perfil público', 'data': DATA} for e in c['emails']]
        if c.get('whatsapp'):
            contatos.append({'nome': c['nome'], 'whatsapp': c['whatsapp'], 'tipo': 'direto', 'fonte': 'bio do perfil público', 'data': DATA})
        seg, nichos = c['seguidores'], c.get('nichos') or ['Lifestyle']
        score = 40 + (25 if c['emails'] else 20) + (15 if ag else 0)
        score += 10 if seg >= 100000 else 5 if seg >= 30000 else 0
        score += 10 if nichos[0] in ('Maquiagem', 'Skincare', 'Cabelo', 'Unhas') else 0
        score += 5 if c.get('uf') == 'SP' else 0
        t = c.get('tiktok_perfil')
        ttj = json.dumps({'seguidores': t['seguidores'], 'verificado': t['verificado'], 'tiktok_shop': t['tiktok_shop'],
                          'link_bio': t['link_bio'], 'data': DATA}, ensure_ascii=False, separators=(',', ':')) if t else None
        linhas.append('(' + ', '.join([
            q(c['nome']), q(c['instagram'].lower()), q(t['handle'] if t else None), str(seg), str(min(score, 90)),
            q(c['emails'][0] if c['emails'] else None), q(c.get('whatsapp')), q(c.get('telefone')), q(ag),
            q('Agência' if ag else None), q(c.get('cidade')), q(c.get('uf')), q(c.get('subsegmento')), q(c.get('fonte_url')),
            q('|'.join(nichos)), q(c.get('seguidores_origem', 'Modash (Instagram)')), q(c.get('plataforma', 'Instagram')),
            q('agencia' if ag else 'direto'), q(json.dumps(contatos, ensure_ascii=False, separators=(',', ':'))), q(ttj)]) + ')')
    cab = ("insert into leads (tipo, segmento_id, status, fonte, nome, instagram, tiktok, seguidores, score, email, whatsapp, telefone, "
           "contato_nome, contato_cargo, cidade, uf, subsegmento, fonte_url, extras)\n"
           "select 'cliente','influenciadora','novo'," + q(FONTE) + ", v.nome, v.ig, v.tt, v.seg, v.score, v.email, v.wa, v.tel, v.cn, "
           "v.cargo, v.cidade, v.uf, v.sub, v.url,\n"
           "  jsonb_build_object('nichos', to_jsonb(string_to_array(v.nichos,'|')), 'nicho_principal', split_part(v.nichos,'|',1),\n"
           "    'contatos', v.contatos::jsonb, 'contato_qualidade', v.cq, 'seguidores_fonte', jsonb_build_object('origem', v.orig, 'data', '" + DATA + "'),\n"
           "    'plataforma', v.plat, 'onda', 'onda2_" + DATA + "')\n"
           "  || case when v.ttj is null then '{}'::jsonb else jsonb_build_object('tiktok_perfil', v.ttj::jsonb) end\n"
           "from (values\n")
    rod = ("\n) as v(nome, ig, tt, seg, score, email, wa, tel, cn, cargo, cidade, uf, sub, url, nichos, orig, plat, cq, contatos, ttj)\n"
           "where not exists (select 1 from leads l where lower(l.instagram)=v.ig or (v.tt is not null and lower(l.tiktok)=v.tt))\n"
           "on conflict do nothing returning nome;")
    open(saida, 'w').write(cab + ',\n'.join(linhas) + rod)


if __name__ == '__main__':
    cmd, args = (sys.argv[1] if len(sys.argv) > 1 else ''), sys.argv[2:]
    if cmd == 'coletar' and args:
        coletar(args[0], args[1:])
    elif cmd == 'tiktok' and len(args) == 2:
        tiktok(*args)
    elif cmd == 'sql' and len(args) == 2:
        sql(*args)
    else:
        print(__doc__)
