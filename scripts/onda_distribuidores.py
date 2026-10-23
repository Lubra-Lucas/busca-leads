"""Onda de distribuidores (23/10/2026): junta os JSON gerados pelos agentes (um por fatia: atacado, profissional,
farma, importadores, revenda, regional), deduplica entre si e com o banco (site, @, nome) e gera final.json.
Depois: marcas puras vão para marca_indie, redes varejistas para varejo_private, e a carga é feita em lotes de 20."""
import json, glob, re, subprocess, unicodedata, urllib.parse
import sys
D = (sys.argv[1] if len(sys.argv) > 1 else 'dist').rstrip('/') + '/'  # pasta com os JSON (fora do repositório)
def db(*a): return json.loads(subprocess.run(['python3','-I','scripts/db.py',*a],capture_output=True,text=True,cwd='/home/user/busca-leads').stdout or '[]')
def norm(s): return re.sub(r'[^a-z0-9]','',unicodedata.normalize('NFKD',(s or '').lower()).encode('ascii','ignore').decode())
def dom(s):
    s=(s or '').lower().strip(); s=re.sub(r'^https?://','',s); s=re.sub(r'^www\.','',s); return s.split('/')[0] or None
def ig(s):
    s=(s or '').strip()
    if not s: return None
    s=re.sub(r'^https?://(www\.)?instagram\.com/','',s).strip('/').lstrip('@')
    return '@'+s.split('/')[0].split('?')[0] if s else None
# base atual (todos os leads, inclusive descartados, para não ferir os índices únicos)
base=[]; off=0
while True:
    p=db('get','leads',f'select=id,nome,site,instagram,segmento_id,status&order=id&limit=1000&offset={off}')
    base+=p; off+=1000
    if len(p)<1000: break
sites={dom(l['site']):l for l in base if l['site']}
igs={(l['instagram'] or '').lower():l for l in base if l['instagram']}
nomes={norm(l['nome']):l for l in base}
vistos={}; rows=[]; dup=[]
for f in sorted(glob.glob(D+'*.json')):
    if f.endswith('final.json'): continue
    for l in json.load(open(f)):
        l['site']=dom(l.get('site')); l['instagram']=ig(l.get('instagram'))
        k=l['site'] or norm(l['nome'])
        ex=sites.get(l['site']) or igs.get((l['instagram'] or '').lower()) or nomes.get(norm(l['nome']))
        if ex: dup.append((l['nome'],ex['nome'],ex['segmento_id'],ex['status'])); continue
        if k in vistos:  # duplicado entre agentes: completa campos vazios do primeiro
            p=vistos[k]
            for c,v in l.items():
                if not p.get(c) and v: p[c]=v
            continue
        vistos[k]=l; rows.append(l)
out=[]
for l in rows:
    cont=l.get('contatos') or []
    tipos=[c.get('tipo') for c in cont]
    ex={k:l.get(k) for k in ['marcas_distribuidas','marca_propria','area_atuacao','portal_fornecedor','cnpj','contatos'] if l.get(k)}
    ex.update(onda='distribuidores_2026-10-23', origem='Busca de distribuidores (23/10/2026)',
              contato_qualidade=next((t for t in ['direto','comercial','geral','sac'] if t in tipos), None))
    r={k:l.get(k) for k in ['nome','subsegmento','cidade','uf','endereco','site','instagram','linkedin','email','telefone','whatsapp','contato_nome','contato_cargo','fonte','fonte_url','score','observacoes']}
    r.update(tipo='cliente', segmento_id='distribuidor', status='novo', extras=ex)
    out.append(r)
json.dump(out,open(D+'final.json','w'),ensure_ascii=False)
print('novos:',len(out),'| já na base:',len(dup))
for d in dup: print('  já existe:',d)
semc=[r['nome'] for r in out if not (r['email'] or r['telefone'] or r['whatsapp'])]
print('sem contato:',semc)
