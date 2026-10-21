"""Etapa 1 da busca de investidores: quem é sócio das marcas de beleza de influenciadoras.

Uso:  python3 scripts/investidores_socios.py <marcas.json> <saida.json>

<marcas.json>: lista de {marca, influenciadora, sites: [...], cnpj?}. Para cada marca o script:
  1. confirma qual site abre e acha o CNPJ no rodapé / páginas institucionais (e-commerce é obrigado a exibir);
  2. consulta o quadro de sócios (QSA) na base pública da Receita via BrasilAPI;
  3. quando um sócio é empresa (holding, fundo, grupo), consulta também os sócios dela.
CPFs vêm mascarados pela própria Receita; guardamos só nome e qualificação.
"""
import json
import re
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin

import requests

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'
# formatado (xx.xxx.xxx/xxxx-xx) ou logo depois da palavra CNPJ: números soltos no código da página são falsos positivos
CNPJ_RE = re.compile(r'\b(\d{2})\.(\d{3})\.(\d{3})/(\d{4})-(\d{2})\b|CNPJ[^0-9]{0,20}(\d{14})\b', re.I)
PAGINAS = re.compile(r'pol[ií]tica|privacidade|termos|quem[-_ ]somos|sobre|institucional|troca|contato|atendimento', re.I)


def cnpj_valido(c):
    if len(c) != 14 or len(set(c)) == 1:
        return False
    def dv(base, pesos):
        s = sum(int(d) * p for d, p in zip(base, pesos)) % 11
        return '0' if s < 2 else str(11 - s)
    p1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    return c[12] == dv(c[:12], p1) and c[13] == dv(c[:13], [6] + p1)


def achar_cnpjs(texto):
    return [''.join(m[:5]) or m[5] for m in CNPJ_RE.findall(texto)]


def matriz(raiz):
    """A Receita mostra só a raiz (8 dígitos) do CNPJ de sócio empresa: monta o da matriz (0001) com os dígitos."""
    base = raiz.zfill(8) + '0001'
    for _ in range(2):
        pesos = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2][-len(base):]
        s = sum(int(d) * p for d, p in zip(base, pesos)) % 11
        base += '0' if s < 2 else str(11 - s)
    return base


def baixar(url):
    try:
        r = requests.get(url, timeout=15, headers={'User-Agent': UA, 'Accept-Language': 'pt-BR'})
        return (r.text, r.url) if r.status_code < 400 else (None, url)
    except requests.RequestException:
        return None, url


def cnpjs_do_site(site):
    url = site if site.startswith('http') else f'https://{site}'
    html, final = baixar(url)
    if not html:
        return None, Counter()
    achados = Counter(achar_cnpjs(html))
    if not achados:  # tenta páginas institucionais
        links = {urljoin(final, h) for h in re.findall(r'href="([^"#]+)"', html) if PAGINAS.search(h)}
        for link in sorted(links, key=len)[:5]:
            h, _ = baixar(link)
            if h:
                achados.update(achar_cnpjs(h))
    return final, Counter({c: n for c, n in achados.items() if cnpj_valido(c)})


def receita(cnpj, tentativas=3):
    for i in range(tentativas):
        try:
            r = requests.get(f'https://brasilapi.com.br/api/cnpj/v1/{cnpj}', timeout=25)
            if r.status_code == 200:
                d = r.json()
                return {
                    'cnpj': cnpj, 'razao_social': d.get('razao_social'), 'nome_fantasia': d.get('nome_fantasia'),
                    'municipio': d.get('municipio'), 'uf': d.get('uf'), 'abertura': d.get('data_inicio_atividade'),
                    'capital_social': d.get('capital_social'), 'atividade': d.get('cnae_fiscal_descricao'),
                    'situacao': d.get('descricao_situacao_cadastral'),
                    'socios': [{'nome': s.get('nome_socio'), 'qualificacao': s.get('qualificacao_socio'),
                                'documento': s.get('cnpj_cpf_do_socio'), 'entrada': s.get('data_entrada_sociedade')}
                               for s in d.get('qsa') or []],
                }
            if r.status_code == 404:
                return None
        except (requests.RequestException, ValueError):
            pass
        time.sleep(3 * (i + 1))  # BrasilAPI limita requisições seguidas
    return {'cnpj': cnpj, 'erro': 'sem resposta'}


def processar(m):
    site_ok, contagem = None, Counter()
    for s in m.get('sites', []):
        site_ok, contagem = cnpjs_do_site(s)
        if site_ok:
            break
    cnpj = m.get('cnpj') or (contagem.most_common(1)[0][0] if contagem else None)
    empresa = receita(cnpj) if cnpj else None
    if empresa and 'socios' in empresa:
        for s in empresa['socios']:  # sócio pessoa jurídica: abre um nível
            doc = re.sub(r'\D', '', s['documento'] or '')
            if 'Pessoa Jurídica' in (s['qualificacao'] or '') or (len(doc) == 8 and '*' not in (s['documento'] or '')):
                if 'Exterior' in (s['qualificacao'] or ''):
                    continue  # empresa estrangeira não está na base da Receita
                doc = matriz(doc) if len(doc) == 8 else doc
                time.sleep(1.5)
                s['empresa'] = receita(doc)
    return {**m, 'site_confirmado': site_ok, 'cnpjs_no_site': dict(contagem), 'empresa': empresa}


def main():
    marcas = json.load(open(sys.argv[1]))
    with ThreadPoolExecutor(max_workers=3) as pool:
        res = list(pool.map(processar, marcas))
    json.dump(res, open(sys.argv[2], 'w'), ensure_ascii=False, indent=1)
    print(f'marcas: {len(res)} | com CNPJ: {sum(1 for r in res if r["empresa"])} | '
          f'com sócio empresa: {sum(1 for r in res if r["empresa"] and any(s.get("empresa") for s in r["empresa"].get("socios", [])))}')


if __name__ == '__main__':
    main()
