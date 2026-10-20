-- Onda 1 de coleta (20/10/2026). Fontes públicas da web; nenhum contato pessoal foi comprado/enriquecido.
-- fonte = 'web' -> encontrado nesta coleta (fonte_url aponta a página)
-- fonte = 'conhecimento_setorial' -> player conhecido do setor, ainda não verificado nesta coleta
-- Score: ver docs/fase1-coleta.md

insert into public.leads (tipo, segmento_id, nome, cidade, uf, site, fonte, fonte_url, score, observacoes) values
-- ===================== CLIENTES =====================
-- Influenciadoras sem marca de maquiagem própria (maior potencial)
('cliente','influenciadora','Karol Resende',null,null,null,'web','https://www.favikon.com/blog/top-makeup-influencers-brazil',85,'Vende cursos online de maquiagem; audiência compradora. Sem marca própria. Levantar Instagram/contato comercial.'),
('cliente','influenciadora','Jessica Cardoso','São Paulo','SP',null,'web','https://www.favikon.com/blog/top-makeup-influencers-brazil',85,'Top 20 maquiagem BR (Favikon 2026), base em SP, sem marca própria.'),
('cliente','influenciadora','Camila Pudim',null,null,null,'web','https://www.favikon.com/blog/top-makeup-influencers-brazil',80,'Top 20 maquiagem BR, sem marca própria.'),
('cliente','influenciadora','Pamella Lunardi',null,null,null,'web','https://www.favikon.com/blog/top-makeup-influencers-brazil',80,'Top 20 maquiagem BR, sem marca própria.'),
('cliente','influenciadora','Bella Dias',null,null,null,'web','https://www.favikon.com/blog/top-makeup-influencers-brazil',80,'+5M inscritos YouTube ("Bella Makeup"); confirmar se já tem linha.'),
('cliente','influenciadora','Lisa Barcelos',null,null,null,'web','https://www.favikon.com/blog/top-makeup-influencers-brazil',75,'+12M TikTok; sem marca própria. Público jovem — compacto de entrada.'),
('cliente','influenciadora','Theulyn Reis',null,null,null,'web','https://www.favikon.com/blog/top-makeup-influencers-brazil',75,'+19M seguidores; sem marca própria.'),
('cliente','influenciadora','Letícia Gomes',null,null,null,'web','https://www.favikon.com/blog/top-makeup-influencers-brazil',70,'Top 20 maquiagem BR, sem marca própria.'),
('cliente','influenciadora','Julia Alvarenga',null,null,null,'web','https://www.favikon.com/blog/top-makeup-influencers-brazil',70,'Top 20 maquiagem BR, sem marca própria.'),
('cliente','influenciadora','Thais Braz',null,null,null,'web','https://www.favikon.com/blog/top-makeup-influencers-brazil',70,'Top 20 maquiagem BR, sem marca própria.'),
('cliente','influenciadora','Léo Silva','São Paulo','SP',null,'web','https://www.favikon.com/blog/top-makeup-influencers-brazil',70,'Criador de maquiagem em SP, sem marca própria.'),
('cliente','influenciadora','Ismeiow','São Paulo','SP',null,'web','https://www.favikon.com/blog/top-makeup-influencers-brazil',65,'SP; promove eventos próprios — possível linha para eventos/fãs.'),

-- Maquiadores profissionais
('cliente','maquiador','Diego Borges','São Paulo','SP',null,'web','https://www.oliberal.com/cultura/moda-e-beleza/conheca-diego-borges-o-maquiador-das-celebridades-1.565518',80,'Maquiador de celebridades em SP; perfil ideal para linha assinada (pó/contorno compacto).'),
('cliente','maquiador','Brigitte Calegari','São Paulo','SP',null,'web','https://elle.com.br/?p=10859',75,'SP desde 2020; aulas online e direção criativa de campanhas de beleza.'),
('cliente','maquiador','Shábilla Moura','São Paulo','SP',null,'web','https://mais.opovo.com.br/jornal/farol/2024/09/29/arte-cearense-nas-passarelas-do-spfw.html',60,'Equipe de maquiagem SPFW 2024; confirmar base atual.'),
('cliente','maquiador','Catharine Hill Academy','São Paulo','SP',null,'web','https://sopacultural.com/dia-do-maquiador-catharine-hill-academy-celebra-a-arte-e-profissao-dos-maquiadores/',55,'Escola no bairro Saúde. Marca já tem produtos; abordar para linha da academia/alunos ou reposição de compactos.'),

-- Marcas indie (já existem; oportunidade = segunda fonte, extensão de linha, compactos)
('cliente','marca_indie','Carmed (Cimed)',null,null,null,'web','https://negociosdebeleza.beautyfair.com.br/beauty-fair-2026-os-lancamentos-que-as-marcas-reservaram-para-a-feira/',85,'Estreando em maquiagem (glosses c/ Ana Castela). Próximo passo natural: pó/blush compacto. Alta prioridade.'),
('cliente','marca_indie','MBOOM',null,null,null,'web','https://cosmeticinnovation.com.br/mboom-leva-wearable-beauty-ao-spfw-com-dario-mittmann/',75,'Marca brasileira de "wearable beauty", collab SPFW out/2026.'),
('cliente','marca_indie','Vic Beauté',null,null,null,'web','https://www.meioemensagem.com.br/creatorsinfluencers/marcas-proprias-ou-collabs-impulsionam-atuacao-dos-influencers',70,'Marca de Vic Ceridono (SP). Verificar fabricante atual.'),
('cliente','marca_indie','Karen Bachini Beauty',null,null,null,'web','https://www.favikon.com/blog/top-makeup-influencers-brazil',65,'Marca de influenciadora; verificar portfólio de compactos.'),
('cliente','marca_indie','Petrizi',null,null,null,'web','https://www.favikon.com/blog/top-makeup-influencers-brazil',65,'Marca de Fernanda Petrizi.'),
('cliente','marca_indie','Boca Rosa Company','São Paulo','SP',null,'web','https://www.fashionbubbles.com/influencers/influenciadoras-que-criaram-marcas/',55,'Holding da Bianca Andrade (marca solo desde 2024). Grande; abordar como segunda fonte.'),
('cliente','marca_indie','Mari Maria Makeup',null,null,null,'web','https://www.fashionbubbles.com/influencers/influenciadoras-que-criaram-marcas/',55,'Marca grande de influenciadora; segunda fonte/lançamentos.'),
('cliente','marca_indie','BT Bruna Tavares',null,null,null,'web','https://www.fashionbubbles.com/influencers/influenciadoras-que-criaram-marcas/',55,'Marca desde 2016; forte em pó/base.'),
('cliente','marca_indie','Dailus','São Paulo','SP','dailus.com.br','web','https://www.linkedin.com/company/dailus',50,'Marca SP, 51-200 func., cruelty-free/vegana. Tem fábrica? verificar.'),
('cliente','marca_indie','Vizzela',null,'MG',null,'web','https://negociosdebeleza.beautyfair.com.br/beauty-fair-2026-os-lancamentos-que-as-marcas-reservaram-para-a-feira/',45,'Lançou linha FIX na Beauty Fair 2026; fora de SP.'),

-- Marcas de moda
('cliente','marca_moda','Vazz Modas',null,null,null,'web','https://www.favikon.com/blog/top-makeup-influencers-brazil',75,'Moda da influenciadora Josilene Vazz (top 20 maquiagem). Encaixe perfeito moda + beleza.'),
('cliente','marca_moda','Riachuelo','São Paulo','SP',null,'conhecimento_setorial',null,40,'Verificar se mantém linha de beleza própria e quem fabrica.'),
('cliente','marca_moda','Lojas Renner',null,'RS',null,'conhecimento_setorial',null,35,'Verificar existência de linha de beleza própria.'),
('cliente','marca_moda','C&A Brasil','Barueri','SP',null,'conhecimento_setorial',null,35,'Verificar linha de beleza própria.'),

-- Varejo com marca própria
('cliente','varejo_private','RD Saúde (Raia Drogasil)','São Paulo','SP',null,'conhecimento_setorial',null,50,'Maior rede de farmácias; tem marcas próprias. Verificar maquiagem no portfólio.'),
('cliente','varejo_private','Grupo DPSP (Drogarias Pacheco / São Paulo)','São Paulo','SP',null,'conhecimento_setorial',null,50,'Rede de farmácias SP/RJ; verificar programa de marca própria.'),
('cliente','varejo_private','GPA (Pão de Açúcar)','São Paulo','SP',null,'conhecimento_setorial',null,35,'Marca própria Qualitá; maquiagem é baixa prioridade.'),

-- ===================== FORNECEDORES =====================
-- Embalagens
('fornecedor','embalagens','Plasmedix',null,null,'plasmedix.com.br','web','https://plasmedix.com.br/plasmedix/embalagens-plasticas-para-cosmeticos/',85,'Fabrica estojo compacto ABS 5g e 12g; fábrica 2.000 m². Confirmar localização.'),
('fornecedor','embalagens','Apotek Embalagens','Campinas','SP','apotek.com.br','web','https://www.apotek.com.br/product-page/linha-estojo-p%C3%B3-solto',75,'Estojos de pó solto (MK15 30g). Ver se tem compacto.'),
('fornecedor','embalagens','Aptar do Brasil Embalagens','Jundiaí','SP',null,'web','https://cnpj.biz/06148069000143',70,'Multinacional; unidades Jundiaí e Cajamar (Aptar B&H). Pedido mínimo alto.'),
('fornecedor','embalagens','Vip Embalagens',null,null,'vipembalagens.com.br','web','https://vipembalagens.com.br/',65,'Distribuidora de embalagens farma/cosmética com linha de maquiagem; bom p/ lotes pequenos.'),
('fornecedor','embalagens','Pharmaprov Importação e Exportação','São Paulo','SP',null,'web','https://ensun.io/search/cosmetics-packaging/brazil',55,'Injeção plástica p/ cosmética — possível peça de estojo sob medida.'),
('fornecedor','embalagens','Mappel Indústria de Embalagens','Diadema','SP',null,'web','https://ensun.io/search/cosmetic-packaging/brazil',45,'Produtos não detalhados; checar.'),
('fornecedor','embalagens','Primera Design Packaging','São Paulo','SP',null,'web','https://ensun.io/search/cosmetic-packaging/brazil',45,'Embalagens para cosméticos (possivelmente cartonagem).'),

-- Pigmentos
('fornecedor','pigmentos','Colormix Indústria e Comércio de Pigmentos','Barueri','SP',null,'web','https://www.dunsguide.com/company/bda164cb4ca2aa9e0b82c9c40e591ccf/colormix-industria-e-comercio-de-pigmentos-ltda',70,'Perolados, inorgânicos, dispersões; expositora in-cosmetics LatAm. Confirmar grau cosmético.'),
('fornecedor','pigmentos','Flamex','São Caetano do Sul','SP',null,'web','https://flamex.brazilsouth.cloudapp.azure.com/carta_flamex.pdf',40,'Importa/distribui pigmentos desde 1984, foco tintas/plásticos. Confirmar grau cosmético.'),

-- Matérias-primas
('fornecedor','materias_primas','Sarfam Indústria Comércio e Importação','Diadema','SP',null,'web','https://www.dunsguide.com/company/3a35269a0026fd2611a3726d45c9f145/sarfam-industria-comercio-e-importacao-ltda',70,'Distribui MP e ativos p/ cosmética há 20+ anos. Perguntar talco/sericita.'),
('fornecedor','materias_primas','AQIA Química Inovativa','Guarulhos','SP','aqia.net','web','https://aqia.net/',65,'Fabricante de insumos com fábrica em Guarulhos.'),
('fornecedor','materias_primas','IMCD Brasil','São Paulo','SP',null,'web','https://www.quimica.com.br/in-cosmetics-latin-america-conceito-holistico-domina/',70,'Distribuidor global de especialidades; costuma ter linha de pigmentos/minerais cosméticos.'),
('fornecedor','materias_primas','Tovani Benzaquen (Barentz)','São Paulo','SP',null,'web','https://distribuicao.abad.com.br/negocios/tovani-benzaquen-adquire-distribuidora-especializada-em-insumos-cosmeticos-e-farmaceuticos-no-brasil/',65,'Grupo Barentz; absorveu Chemspecs e Volp (personal care).'),
('fornecedor','materias_primas','EBPM Imp Exp Repr','São Paulo','SP',null,'web','https://pt.slideshare.net/EBPM',50,'MP para perfumaria/cosméticos (essências, óleos, extratos).'),
('fornecedor','materias_primas','Mapric',null,'SP',null,'web','https://www.ingredientescosmeticos.com.br/buscador',50,'Listada no buscador Ingredientes Cosméticos.'),
('fornecedor','materias_primas','Galena',null,'SP',null,'web','https://www.quimica.com.br/in-cosmetics-latin-america-conceito-holistico-domina/',55,'Expositora in-cosmetics LatAm.'),
('fornecedor','materias_primas','Dinaco',null,'SP',null,'web','https://www.quimica.com.br/in-cosmetics-latin-america-conceito-holistico-domina/',55,'Expositora in-cosmetics LatAm.'),
('fornecedor','materias_primas','Focus Química',null,null,null,'web','https://www.quimica.com.br/in-cosmetics-latin-america-conceito-holistico-domina/',50,'Expositora in-cosmetics LatAm.'),

-- Essências
('fornecedor','essencias','Givaudan do Brasil','São Paulo','SP',null,'web','https://www.econodata.com.br/consulta-empresa/56206444000485-givaudan-do-brasil-industria-e-comercio-de-aromas-e-fragrancias-ltda',55,'Av. Eng. Billings 2185, Jaguaré. Grande; mínimo alto — pedir linha de fragrâncias de catálogo.'),
('fornecedor','essencias','Symrise Aromas e Fragrâncias','São Paulo','SP',null,'web','https://www.solutudo.com.br/empresas/sp/s-paulo/industrias/symrise-aromas-e-fragrancias-ltda-12274822',55,'R. Domingos Jorge 1000, Socorro.'),
('fornecedor','essencias','IFF Essências e Fragrâncias','Taubaté','SP',null,'web','https://4637-br.all.biz/',45,'Cadastro possivelmente desatualizado.'),
('fornecedor','essencias','Studio D Essences','São Paulo','SP',null,'web','https://www.solutudo.com.br/empresas/sp/s-paulo/perfumarias-cosmeticos/studio-d-essences-comercio-fabricacao-importacao-exportacao-de-cosmeticos-ltda-16696512',60,'CNPJ 12.115.152/0001-19, Vila Mariana. Porte menor — bom p/ lotes pequenos.');
