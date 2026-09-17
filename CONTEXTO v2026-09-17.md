# CONTEXTO — Calculadora Doppler Obstétrico

**Leia este arquivo inteiro antes de alterar qualquer coisa.**

Software clínico de apoio à decisão em ultrassonografia obstétrica. Arquivo HTML único,
hospedado no Vercel. Autor e único responsável clínico: Dr. Diogo S. Ribeiro
(obstetra/medicina fetal, CRM 5789-AL).

Última auditoria: 15–17/09/2026 · versão interna `v2026-09-17-audit2`
SHA-256 publicado nessa data: `cd19896a1a7a8a3e79dc30dc09eede527ee44be9a71e8b352c0c1ac73202552e`
(341.769 bytes)

---

## 0. Como trabalhar neste repositório

1. **Rode a suíte antes de começar.** `python3 suite_regressao_doppler.py Calculadora_Doppler_Obstetrico.html`
   Isso diz de onde você está partindo. Se já começa falhando, descubra por quê antes
   de escrever uma linha.
2. **Proponha antes de aplicar.** O autor exige liberação explícita para qualquer
   alteração — inclusive correção de bug que você mesmo encontrou. Apresente o achado,
   espere o "pode fazer".
3. **Rode a suíte antes de entregar.** E rode de novo depois de qualquer ajuste, por
   menor que pareça.
4. **Confirme cada achado no código** antes de tratá-lo como real. Auditorias externas
   deste app já chegaram descrevendo bugs que não existiam mais, ou que nunca existiram
   — e, ao menos uma vez, citando um documento próprio não verificável em vez do artigo
   primário (ver armadilha do Ciobanu, §2).
5. **Confira o SHA-256 antes de mandar para reauditoria externa.** Já aconteceu de uma
   versão desatualizada ser reenviada por engano — o hash no topo deste arquivo é a
   fonte da verdade de qual é a versão corrente.

---

## 1. Decisões fechadas — NÃO reabrir

Já foram adjudicadas pelo autor. Reabrir custa tempo e gera retrabalho.

| Tema | Decisão |
|---|---|
| IP da artéria umbilical | **Acharya 2005**, domínio 19–40 sem. Não migrar para Ciobanu. |
| IP da ACM (isolado) | **Arduini & Rizzo 1990**. Migração para Ciobanu discutida e adiada. |
| CPR (classificação) | **Ciobanu 2019/FMF**, p5 por IG. Corte absoluto <1,0 permanece só como radar. **Ancoragem temporal da tabela (semana × dia gestacional) congelada — ver §4.** |
| Queda longitudinal | Motor: estritamente **dq<-50 e intervalo ≥21 dias** (`DEC-LONG-001`). Duas auditorias externas propuseram tirar o gate de 21 dias — **recusado nas duas**. Texto da UI corrigido de "≥2 quartis" para "**>2 quartis**" (bate com o operador real); os 21 dias são documentados como **política de comparabilidade do serviço**, não parte literal do Delphi (que não define intervalo mínimo). |
| Diástole ausente/reversa na RCF tardia | `DEC-DOP-LATE-AEDF`: tratada como satisfazendo operacionalmente o componente UA-PI>p95 do Delphi (por definição, sem diástole o IP está acima de qualquer corte finito). **Não é** redação literal do Delphi — é decisão local documentada. Nunca atribuir essa equivalência ao consenso em si. |
| TN | Padrão **Faria 2004** (mm a mm, CCN 45–84), alternável para Snijders/FMF ao vivo, volta a Faria a cada exame. |
| Fórmula de peso (PFE) | Hadlock 4 parâmetros — matemática conferida coeficiente a coeficiente, correta. Percentil por motor híbrido calibrado por tabela (`DP_HADLOCK=0,1329`) — **deliberadamente não** é a equação log-linear pura do resumo do artigo Hadlock 1991 (essa equação, conferida contra Roberts 2025, classifica mais fetos como pequenos que a tabela impressa; o motor foi calibrado pra reproduzir a tabela, evitando esse viés). O aviso da `coer()` que descrevia isso ao contrário (dizendo que "a equação usada aqui" tinha o problema) foi corrigido — o texto agora descreve a calibração real. |
| Percentil da CA | **INTERGROWTH-21st** (Papageorghiou 2014). p3/p50/p97 por interpolação; **p10 diagnóstico usa a coluna oficial importada** (`T_CA_P10`, conferida contra intergrowth21.com célula a célula) — não mais aproximação contínua. O percentil *exibido* entre centis continua sendo estimado por reconstrução (`pctOf`, z=1,881) — a decisão diagnóstica sempre usa o valor oficial. |
| Datação oficial por biometria | Método formal (14–26 sem) é **HC+FL, INTERGROWTH-21st (Papageorghiou)** — recomendado pela ISUOG (Salomon 2019/2022, grau B; Khalil 2024 pro 3º tri). Não consegui confirmar os 3 coeficientes da fórmula numa fonte primária de acesso aberto (paywall) — confirmada independentemente só a recomendação ISUOG; formula testada por plausibilidade antes de entrar em uso. ≥26 sem: mesmo método, mas rotulado "IG biométrica tardia estimada" com incerteza explícita (interpolada de 3 pontos: ±12d/26sem, ±14,3d/30sem, ±16,5d/34sem) — não bloqueia, só muda a semântica. A composição antiga (cerebelo×3, DBP/CC/FL×2, sem artigo que a valide) **não estabelece mais IG oficial** — segue em uso só para *comparar* biometria atual contra uma IG já estabelecida (detecção de discordância/RCF), papel em que a granularidade por parâmetro é informação clínica. Confirmação sempre exige clique explícito, mesmo com `AUTO_BIO` ativo (nunca mais escreve `sem`/`dias` sozinho). |
| Comprimento fetal | **Vintzileos et al. 1984** (Obstet Gynecol 64(6):779-82) — confirmado no PubMed, fórmula `6,18+0,59×FL(mm)` é literal do artigo. Não é O'Brien & Queenan 1981 (que só publicaram FL→IG, nunca FL→comprimento). Auxiliar, fora da hierarquia, informativo — matemática intocada, só a atribuição foi corrigida. |
| Líquido amniótico | Perfil **FEBRASGO nº 82 (2018)**: oligoâmnio `< 2` cm (estrito). ISUOG 2024 usa `≤ 2` — é escolha de perfil, não bug. |
| Terminologia | "Restrição do crescimento fetal" (FEBRASGO). **Não** usar "CIUR". |

**Hierarquia de fontes:** FEBRASGO → ISUOG → Rumack → CBR/SBR. `fetalmed.net` é a
referência secundária canônica do projeto. Fonte fora dessas quatro: avisar e não
implementar sem autorização.

**Escopo do projeto:** este HTML é **paralelo e independente** de qualquer outro projeto
(ex.: Codex/Flutter). Não herda hierarquia de fonte de fora, não é módulo de outro app.
Comparações externas continuam válidas como consulta, nunca como regra normativa daqui.

---

## 2. Armadilhas — parece bug, não é

Cada uma destas já enganou alguém (inclusive eu). Confirme antes de "corrigir".

**Órbitas com desvio fixo.** `T_DBO` tem p50−p5 = exatamente 5,0 mm em todas as linhas;
`T_DIO`, exatamente 3,0 mm. Parece percentil fabricado. **Não é.** Jeanty 1982 modelou
por regressão polinomial com desvio-padrão constante, então p5/p95 são mediana ∓1,645×DP
com DP invariante. A tabela do Fetalmed tem os mesmos offsets, e os valores do app batem
célula a célula. Eu classifiquei isso como erro grave antes de conferir a fonte — e estava
errado.

**Anomalia da semana 30 da placenta.** A média em 30 sem (3,4) é maior que em 31 (3,3),
quebrando a monotonicidade. **Está na fonte** (Bonilla-Musoles 1972, via Fetalmed). O app
reproduz fielmente. Mantido de propósito.

**Uterinas não contam na RCF tardia.** Só entram no critério da forma **precoce**
(<32 sem). Na tardia, C3 é `CPR<p5 OU IP-AU>p95` (mais `DEC-DOP-LATE-AEDF` acima para
diástole ausente/reversa). Não é esquecimento — é o critério Delphi/ISUOG.

**Placenta e o "limite" da semana 30.** Ver acima. E o módulo de placenta é
deliberadamente **informativo**: não emite "placenta espessa/fina" como diagnóstico,
porque a fonte é de 1972, publica média e variação (não percentis), e nenhum guideline
adota corte diagnóstico. Não "melhore" isso voltando a cravar o termo.

**Ciobanu citado como "confirmado" por documento não verificável.** Uma reauditoria
alegou ter a Table 2 original de Ciobanu 2019 com semana 30 = dia 213 (30+3, não 30+0),
citando "nosso registro mestre anterior" — um documento interno de outro projeto, não a
fonte primária. Os números tinham um padrão suspeito (+3 dias em toda semana citada).
Existe sim controvérsia publicada e revisada por pares sobre esse artigo — DeVore 2021
(UOG 57:349-350) vs. réplica Wright/Nicolaides (UOG 57:350-351) — mas ela é sobre
equação×tabela, não confirma por si só o deslocamento de 3 dias. **Ciobanu segue
congelado** até ler DeVore+réplica e decidir formalmente antes de mexer em `T_CPR`.

**AVISO GERAL:** durante a auditoria, **quatro vezes** um teste "falhou" e o aplicativo
estava certo — a expectativa do teste é que estava desatualizada ou mal calibrada (ex.:
uma ACM baixa que, sem eu perceber, também derrubava a CPR abaixo do p5 e legitimamente
fechava um componente; ou o teste "Pelve 0,5 isolada = A1", que testava exatamente o
cenário do bug de UTD trivalente e foi corrigido para `a1-inc` depois que o motor passou
a exigir cálices/parênquima/ureter/bexiga avaliados antes de fechar "A1").
Antes de alterar o app por causa de uma falha na suíte, verifique a expectativa do teste.

---

## 3. Bugs corrigidos que não podem voltar

Estão todos cobertos pela suíte (62 casos) ou por teste dirigido registrado na auditoria
da sessão. Listados porque entender a causa evita recriá-los.

**Padrão sistêmico — "não avaliado" virando "normal/presente/ausente":** apareceu de
forma independente em pelo menos 6 módulos diferentes, sempre pela mesma causa raiz
(campo com valor default não-vazio, ou checkbox desmarcado tratado como resposta):
- Checkbox "sem atividade cardíaca" (1º tri): desmarcado (nunca tocado) → laudo escrevia
  "atividade cardíaca presente". Virou select de 3 estados; `viabilidade()` e
  `segAnterior()` (que podia fechar "perda gestacional" pelo prazo temporal mesmo com a
  atividade atual não avaliada) têm ramo próprio para "não avaliada".
- Marcadores 2º tri (foco ecogênico, intestino, plexo coroide, artéria umbilical única):
  mesmo padrão — checkbox virou select trivalente. "Achado isolado" (SMFM #57) agora só
  é declarado quando os demais marcadores relevantes foram genuinamente avaliados
  (`falta.length===0`), não só quando `n===1`.
- `alt1` (marcadores 1º tri — TN/ON/DV/tricúspide): array vazio por nenhum marcador
  avaliado gerava a mesma conclusão "sem alterações" que array vazio por avaliação
  completa e normal. Agora distingue nenhum/parcial/completo avaliado.
- UTD: `eCal`/`ePar2` nasciam em "Ausente"/"Normal" (1ª opção do select) — pelve em faixa
  A1 fechava classificação mesmo com cálices/parênquima nunca checados. Agora exige os
  4 componentes (Nguyen 2014: cálices, parênquima, ureter, bexiga) avaliados; incompleto
  vira `a1-inc`, propagado até o laudo final (não fecha "UTD A1" formalmente).
- sFGR gemelar: `seletiva()` já calculava `ST.sfgr` corretamente, mas o laudo escrevia
  incondicionalmente "não foram avaliados critérios de restrição seletiva" — inclusive
  com o card da tela mostrando "critérios contributivos preenchidos" ao mesmo tempo.
  Também corrigido: `seletiva()` não gravava `ST.sfgr` quando nenhum critério fechava
  (`C.length===0`), deixando esse caso indistinguível de "nunca avaliado".
- CPR<p5: entrava na síntese clínica (radar de RCF) mas não entrava no array que decide
  se o laudo escreve "Doppler sem alterações" — podiam coexistir. Mesma causa raiz já
  tinha aparecido em PSV-ACM (nunca entrava no `radar[]` de `sintese()` quando o peso
  também estava baixo) e no ducto venoso (`falta`/badge ignoravam o IP quando só ele,
  sem a onda, tinha sido medido).

**Outros:**
- **Diástole descartada.** `diastValor()` retornava `'na'` quando o campo do IP estava
  vazio. Com diástole reversa selecionada e IP em branco, o app concluía "Doppler não
  avaliado" num feto p8. Era o pior bug da série. A guarda original fazia sentido quando
  o default do seletor era "presente"; depois que o default virou "não avaliada", ela
  passou a destruir dado real.
- **RCF dependia do PFE.** Faltando o peso, o motor só via AEDF e CA<p3. Agora fecha pela
  CA nas duas formas. Cuidado: os flags `auAlto`/`cprBx`/`quedaDelphi` precisam estar
  declarados **antes** do ramo sem PFE (são `var`, içadas como `undefined` — a falha é
  silenciosa).
- **GIG apagava CA<p3.** O ramo de peso >p90 retornava antes da RCF formal. Agora, peso
  alto com CA<p3 gera `bloqueado-remedir`, não GIG.
- **Longitudinal na curva errada.** `velocidade()` usava Hadlock mesmo com INTERGROWTH
  ativo. Use sempre `pctAtivo()`/`medAtivo()`.
- **Laudo gemelar com dado velho.** `laudo()` rodava antes de `discordancia()`/`seletiva()`.
  A ordem em `run()` importa: gemelar → síntese → laudo.
- **UTD não classificava por ureter isolado.** Pelve normal + ureter dilatado dizia
  "Normal" na tela enquanto o outro card dizia "A2-3".
- **CA no p3 exato disparava `<p3`.** Percentil contínuo aproximado gerava 2,9986.
  Classificação agora é por valor bruto contra corte bruto.
- **CA<p10 sem PFE ficava mudo.** Estado `ca-sem-criterio` cobre isso.
- **Mensagem de domínio das uterinas desatualizada.** Dizia "tabela cobre 11–31 sem"; a
  tabela (`T_UT`) real vai até 41 (11–31 direto de Gómez 2008, 32–41 pela equação
  derivada) — só a mensagem de aviso tinha ficado pra trás.
- **Seletor de origem "Direto" não navegava para Medidas.** Só "Biometria" pulava direto
  pra aba de biometria; "Direto" (digitar semanas/dias manualmente) ficava preso na aba
  de Datação. Os dois agora navegam, e ambos respeitam o contexto (1º tri → aba `p4`,
  2º/3º tri → `p1` — antes `origBio` sempre mandava pra `p1`, quebrando no 1º tri).

---

## 4. Pendências abertas

| Item | Estado |
|---|---|
| **Ciobanu — ancoragem temporal** | `T_CPR` indexado por semana inteira; pode haver deslocamento de 3 dias (semana "30" = dia 213 = 30+3, não 30+0) na Table 2 original. **Congelado.** Antes de mexer: ler DeVore 2021 (UOG 57:349-350) + réplica Wright/Nicolaides (UOG 57:350-351), decidir formalmente equação×tabela, só então (se confirmado) reindexar por dia gestacional real. |
| Gómez — uterinas direita/esquerda individuais | A referência (Gómez 2008) é pro **IP médio das duas**. O app também percentila e classifica direita/esquerda isoladas pela mesma tabela — não validado pela fonte. Proposta: só o médio recebe percentil formal; lateral mostra valor bruto. |
| Gómez — tabela híbrida 32–41 sem | 11–31 sem é a Table 2 publicada; 32–41 foi recalculado pela equação contínua (`Loge(PI)=1,39−0,012·IG(d)+IG²·0,0000198`), gerando pequenas diferenças (~0,01) contra a Table 2 original nesse trecho. Escolher uma arquitetura única (tabela publicada inteira, ou equação contínua em toda a faixa) — ainda não decidido. |
| PSV-ACM 1,29–1,49 MoM | Texto atual chama de "limítrofe — acompanhar tendência". Mari 2000 na verdade dá ~1,29 MoM como limiar de anemia **leve** (distinto do limiar formal de moderada/grave, 1,50). Texto deveria refletir isso sem virar conduta genérica. |
| Incisura uterina — peso no laudo | Incisura bilateral persistente pode sozinha virar "Doppler alterado" no laudo mesmo com IP médio normal. RCOG 2024/ISUOG preferem IP médio; incisura deveria ser achado secundário/descritivo. |
| "Sequência de deterioração" Doppler | Linguagem determinística ("ordem previsível", "estágio final") é válida como modelo didático pra RCF precoce grave, mas a RCF tardia não segue essa progressão linear (ISUOG). Reescrever abertura do texto. |
| Domínio 11–14 sem (TN/ON/DV/tricúspide) | Marcadores do rastreio aparecem disponíveis mesmo fora de 11+0–13+6/CCN 45–84mm (contexto 1º tri cobre IG<14, incluindo 6–10 sem). Criar checagem de domínio única aplicada aos 4. |
| Doppler antes de 11 sem | DV e tricúspide fetal ficam acessíveis mesmo abaixo de 11 sem — ISUOG não recomenda uso rotineiro nessa janela. |
| FCF — faixas atribuídas genericamente a Doubilet/Benson | A fonte sustenta bem 6–8 sem; faixas de 8–14 sem parecem vir de outro lugar (possível série brasileira, Araujo Jr. 2014, não conferida). Atribuição por segmento de IG pendente. |
| Léxico SRU 2024 | Texto afirma que "gestação anembrionada" foi aposentada — **incorreto**, o termo abandonado é "blighted ovum/ovo cego". Revisar bloco teórico inteiro. |
| Colo curto — conduta sem contexto obstétrico | `≤15mm`/`≤25mm` disparam texto de indicação de progesterona sem o app saber singleton/gemelar, antecedente de parto prematuro, sintomas, dilatação. SMFM 2024 diferencia esses cenários. Sem esses dados, deveria só descrever o achado. |
| Ventriculomegalia — bordas | Categorias atuais incluem "9–9,9mm = limítrofe" (não existe — <10mm é normal, ISUOG) e cortes de leve/moderada/grave que não batem com SMFM (10–12/13–15/>15). |
| Gemelar — ambos os fetos <p10 | `seletiva()` pode fechar "restrição seletiva" só pelo critério solitário (PFE<p3 de um) sem checar antes se os DOIS estão <p10 — nesse caso ISUOG 2025 pede rótulo "ambos pequenos para a IG", não sFGR direto. |
| Restos ovulares — escada terapêutica por mm | `≤15/15–20/>20mm` como degraus de conduta cirúrgica; ACOG e OMS dizem que espessura isolada tem baixa acurácia e não deve determinar esvaziamento sozinha. Também: "alteração do hemograma" como gatilho é vago demais — trocar por hemorragia/instabilidade/infecção. |
| Osso nasal 2º tri — corte 4,5mm | Fonte FEBRASGO citada ainda não foi aberta/conferida diretamente. Não remover o corte até confirmar se é específico de uma janela ou regra geral (nesse caso, percentil/MoM seria mais defensável). |
| Estado/persistência (não auditado nesta rodada) | `CURVA`/`CURVA_TN` podem não sobreviver à recuperação de sessão (número volta, referência clínica não); modo Embrião/Só-saco depende de CSS, não de estado semântico; `eColo`/`ePla` estão em `CAMPOS_FETAIS` (por feto) quando são dado materno/de corionicidade; `dias` fora de 0–6 vira 0 silenciosamente; `dtHoje` não atualiza se o PWA fica aberto depois da meia-noite. Levantado por auditoria externa, nenhum item verificado no código ainda. |
| Infra (P2/P3, não verificado) | `sw.js` nunca foi auditado (registro de service worker engole erro); persistência local sem TTL/versionamento; zoom bloqueado no viewport; reentrância de `run()→ctxAuto()→setCtx()→run()`. |
| Cadência de seguimento da RCF | App sugere 3–4 sem; FEBRASGO nº 35/2018 diz **14 dias**. O app avisa da divergência, mas os números não foram alinhados — decisão clínica pendente. |

---

## 5. Escopo — o que este repositório é e não é

Este HTML é o aplicativo **em produção**, usado pelo autor no SUS em Alagoas.

Existe em paralelo um projeto Flutter/Codex, mantido por outra equipe/IA. Os dois são
**independentes** — este app não herda a governança de fonte de lá, nem o inverso.
Correções feitas aqui não são importadas automaticamente para lá, e auditorias vindas de
lá descrevem um código diferente deste — já chegaram apontando bugs desta base que não
existiam mais, ou citando documentos internos daquele projeto como se fossem fonte
primária (ver §2). Sempre confirme no código presente.

Esta calculadora também vem funcionando, na prática, como banco de "failure modes" pro
Codex: padrões de bug encontrados aqui (estado trivalente, completude de avaliação,
laudo derivado do mesmo estado da classificação, cutpoint por valor bruto) valem a pena
levar pra lá — mas como regra, não como código copiado.

```
EXTERNAL_REFERENCE_APP (este HTML) = em produção
PROJECT_FLUTTER_CLINICAL_ENGINE    = independente, não autorizado a partir daqui
```

---

## 6. Preferências do autor

- Responder em português brasileiro.
- Análise crítica: apresentar contraponto antes de concordar. Se ele estiver errado,
  dizer diretamente.
- Nunca aplicar alteração sem liberação explícita.
- Respostas curtas (ele usa celular). Entregas em poucas linhas descrevendo o que mudou.
- Modo de teste silencioso: reportar só as falhas.
- Perguntar o escopo antes de "revisar tudo" — exceto validação de fonte e dado clínico,
  que é sempre completa.
