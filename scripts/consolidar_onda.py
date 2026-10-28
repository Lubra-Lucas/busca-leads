"""Consolida os JSON gerados pelos agentes de uma onda de captação e grava no banco.

Uso: python3 -I scripts/consolidar_onda.py <pasta_json> <tipo> <segmento_id> <onda> [--gravar]
  ex.: python3 -I scripts/consolidar_onda.py /tmp/.../emb2 fornecedor embalagens embalagens_2026-10-28 --gravar

Deduplica entre os arquivos (site, ou nome normalizado) e contra TODA a base (site, @ e nome, inclusive descartados,
por causa dos índices únicos em lower(site)/lower(instagram)). Campos extras do agente (cnpj, contatos, moq, marcas…)
vão para `extras`. Sem --gravar, só gera <pasta>/final.json e mostra o resumo. A carga é feita em lotes de 20.
"""
import glob, json, re, subprocess, sys, unicodedata

COLUNAS = ['nome', 'subsegmento', 'cidade', 'uf', 'endereco', 'site', 'instagram', 'linkedin', 'email', 'telefone',
           'whatsapp', 'contato_nome', 'contato_cargo', 'fonte', 'fonte_url', 'score', 'observacoes', 'segmento_id']


def db(*a):
    out = subprocess.run(['python3', '-I', 'scripts/db.py', *a], capture_output=True, text=True).stdout
    return out


def norm(s):
    return re.sub(r'[^a-z0-9]', '', unicodedata.normalize('NFKD', (s or '').lower()).encode('ascii', 'ignore').decode())


# hospedagens genéricas: o domínio sozinho não identifica a empresa, então compara também o caminho
GENERICOS = ('sites.google.com', 'linktr.ee', 'wixsite.com', 'ueniweb.com', 'offstore.me', 'instagram.com', 'facebook.com')


def dominio(s):
    s = re.sub(r'^https?://', '', (s or '').lower().strip())
    s = re.sub(r'^www\.', '', s).rstrip('/')
    return (s if s.split('/')[0].endswith(GENERICOS) else s.split('/')[0]) or None


def arroba(s):
    s = re.sub(r'^https?://(www\.)?instagram\.com/', '', (s or '').strip()).strip('/').lstrip('@')
    s = s.split('/')[0].split('?')[0]
    return '@' + s if s else None


def main():
    pasta, tipo, segmento, onda = sys.argv[1:5]
    base, off = [], 0
    while True:
        p = json.loads(db('get', 'leads', f'select=nome,site,instagram,segmento_id&order=id&limit=1000&offset={off}'))
        base += p
        off += 1000
        if len(p) < 1000:
            break
    sites = {dominio(l['site']): l for l in base if l['site']}
    igs = {l['instagram'].lower(): l for l in base if l['instagram']}
    nomes = {norm(l['nome']): l for l in base}

    vistos, novos, ja = {}, [], []
    for f in sorted(glob.glob(pasta.rstrip('/') + '/*.json')):
        if f.endswith('final.json'):
            continue
        for l in json.load(open(f)):
            l['site'], l['instagram'] = dominio(l.get('site')), arroba(l.get('instagram'))
            ex = sites.get(l['site']) or igs.get((l['instagram'] or '').lower()) or nomes.get(norm(l['nome']))
            if ex:
                ja.append((l['nome'], ex['nome'], ex['segmento_id']))
                continue
            chave = l['site'] or norm(l['nome'])
            if chave in vistos:  # repetido entre agentes: completa o primeiro
                for c, v in l.items():
                    if v and not vistos[chave].get(c):
                        vistos[chave][c] = v
                continue
            vistos[chave] = l
            novos.append(l)

    linhas = []
    for l in novos:
        tipos = [c.get('tipo') for c in (l.get('contatos') or [])]
        extras = {k: v for k, v in l.items() if k not in COLUNAS and v not in (None, '', [])}
        extras.update(onda=onda, contato_qualidade=next((t for t in ['direto', 'comercial', 'geral', 'sac'] if t in tipos), None))
        linha = {k: l.get(k) for k in COLUNAS}
        linha.update(tipo=tipo, segmento_id=l.get('segmento_id') or segmento, status='novo', extras=extras)
        linhas.append(linha)
    json.dump(linhas, open(pasta.rstrip('/') + '/final.json', 'w'), ensure_ascii=False)
    print(f'novos: {len(linhas)} | já na base: {len(ja)}')
    for j in ja:
        print('  já existe:', j)
    if '--gravar' in sys.argv:
        for i in range(0, len(linhas), 20):
            print(db('post', 'leads', json.dumps(linhas[i:i + 20], ensure_ascii=False)).strip() or 'ERRO no lote', i)


if __name__ == '__main__':
    main()
