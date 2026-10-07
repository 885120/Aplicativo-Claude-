# CONTEXTO — Calculadora Doppler Obstétrico

**Leia este arquivo inteiro antes de alterar qualquer coisa.**
Substitui o `CONTEXTO v2026-09-17.md`, que descrevia uma versão anterior (`v2026-09-17-audit2`,
SHA `cd19896a…`, 341.769 bytes) e ficou desatualizado em pontos importantes (ver §7).

Atualizado em 06/10/2026 · versão atual **R14.35**
`index.html` SHA-256 `47b3d14c74c611dd1fc44ee7b2e6a58700d856f6bc13cdb96edcd8d43879dbc4` (528.726 bytes)
(A R14.28 foi a última confirmada no ar, em 02/10/2026; publique a R14.35 renomeada para `index.html`.)
`sw.js` R14.23-SW2 SHA-256 `868972f473094deafe00372b44de52f1e35b2ff15a576d6222d5b39f70fcc840`
Autor e único responsável clínico: Dr. Diogo S. Ribeiro (obstetrícia/medicina fetal, CRM 5789-AL).

Fonte da verdade para referências e adjudicações: **`REFERENCIAS_R14_28.md`** (seções A–H).
Este arquivo resume; quando divergir, vale o `REFERENCIAS` e, acima dele, o código.

---

## 0. Como trabalhar neste repositório

1. **Rode a suíte antes de começar** — `python3 suite_regressao_doppler.py index.html`. Se já começa falhando, descubra por quê antes de escrever uma linha.
2. **Proponha antes de aplicar.** O autor exige liberação explícita para qualquer alteração — inclusive correção de bug encontrado por conta própria.
3. **Rode a suíte antes de entregar**, e de novo depois de qualquer ajuste.
4. **Confirme cada achado no código presente.** Auditorias externas já descreveram bugs inexistentes, ou de outra base.
5. **Confira o SHA-256** antes de mandar para reauditoria: o hash acima é a versão corrente.
6. **Publicação:** o HTML precisa se chamar exatamente `index.html` na raiz (ver `README.md`). Em 02/10/2026 o site deu 404 porque o arquivo estava como `Calculadora.html`.
7. **Construção reproduzível:** cada versão R14.x foi gerada por `patch.py` a partir da anterior, byte a byte; o pacote `testes_R14_xx.zip` de cada entrega contém o script, os testes e os resultados.

---

## 1. Referências em uso na R14.28 (resumo da tabela "Referências" do app)

**Hierarquia: FEBRASGO → CBR → ISUOG.** FMF e demais fontes complementam o que essa ordem não cobre; consensos Delphi entram onde a FEBRASGO não detalha o critério operacional. É a instrução do autor de 30/09/2026, registrada no app e no `REFERENCIAS`. *(O CONTEXTO de 17/09 registrava FEBRASGO → ISUOG → Rumack → CBR/SBR; para este app prevalece a instrução mais recente.)*

| Parâmetro | Referência na R14.28 |
|---|---|
| PFE | Hadlock 1985 — 4 parâmetros (curva Hadlock) ou 3 parâmetros (curva INTERGROWTH) |
| Percentil de peso | Hadlock 1991, ln(EFW), **SD = 0,12** (`HADLOCK_SD_LN`); Φ de dupla precisão (`phiPreciso`, R14.27) |
| Percentil da CA | INTERGROWTH-21st (Papageorghiou 2014), colunas oficiais p10 e p90 (`T_CA_P10`, `T_CA_P90`) |
| Artéria umbilical, ACM (IP), CPR | **Ciobanu 2019 (FMF)**, 20+0–41+6 sem; o p5 da CPR vem da **equação** (`ciobanuCPRref`), não da tabela `T_CPR` |
| PSV-ACM | Mari 2000 |
| Uterinas | duas referências selecionáveis (Gómez / Cavoretto), sempre o IP **médio** das duas |
| Ducto venoso | 2º/3º tri: Tongprasert 2012 · 1º tri: Pruksanusak 2014 |
| Critérios de RCF | Delphi (Gordijn 2016) · ISUOG 2020; FEBRASGO mostrada em paralelo quando diverge |
| Restrição seletiva (gemelar) | Delphi gemelar (Khalil 2019): solitário PFE < p3 **em qualquer corionicidade**; MC 2 de 4, DC 2 de 3 |
| Queda longitudinal | RCOG 2024 (> 2 quartis = 50 percentis) |
| Líquido amniótico | FEBRASGO nº 43 (2025) Tabela 1 (diagnóstico) · SMFM #46 Tabela 2 (graduação do polidrâmnio) |
| TN | Faria 2004 (padrão, população brasileira); FMF carta 1998 alternável |
| UTD | Nguyen 2021 (*Pediatr Radiol* 2022) — ureter/parênquima/bexiga só contam com pelve ≥ 4 mm ou cálices dilatados |
| Órbitas | Sukonpan & Phupong 2008 (p10/p50/p90) — fora de p10–p90 é alerta, não diagnóstico |
| Ossos longos | Chitty & Altman 2002 (p3/p50/p97) |
| Cerebelo, átrio | Snijders & Nicolaides 1994 |
| Placenta | Bonilla-Musoles 1972 via Fetalmed — informativo (média e variação, não percentis) |

---

## 2. Decisões fechadas vigentes — NÃO reabrir sem decisão do autor

| Tema | Decisão (conferida na R14.28) |
|---|---|
| Queda longitudinal | `DEC-LONG-001`: estritamente **queda > 50 percentis e intervalo ≥ 21 dias**. Os 21 dias são política de comparabilidade do serviço, não texto literal do Delphi. |
| Tamanho fetal | Classificado por **PFE + CA** (R14.20–R14.22). Sem CA: não fecha AIG ("classificação de tamanho incompleta"); CA isolada pode fechar o que a regra permite. |
| Líquido | Oligoâmnio MBV < 2 / ILA < 5; polidrâmnio MBV ≥ 8 / ILA ≥ 24 (FEBRASGO, "Ultrassonografia obstétrica do terceiro trimestre", Femina 2025, DOI 10.61622/0100-7254536202507, Tabela 1 — "nº 43" sozinho é ambíguo); graduação SMFM #46. |
| Comparações nos cortes | Igualdade nunca é "abaixo/acima": `cmpMedida(a,b)` (tolerância `16 × EPSILON × max(1,|a|,|b|)`, só neutraliza ruído de ponto flutuante) em 26 comparações. **Não arredondar medidas nem alterar `valmm()`** — as tabelas têm literais com ruído próprio. |
| Percentil de peso | `phiPreciso()` só em `pctPesoFromZ()`; o `phi()` genérico (Doppler, CA, uterinas) foi mantido de propósito. Ponto nominal neutralizado em `|z − Z| < 1e-10`. |
| Discordância gemelar | Valor **bruto** preservado (ex.: 24,999999999999996); categoria por `discCat()`; exibição por `discFmt()` (inteiro → 2 → 3 → 4 casas, aceita só se o número exibido ficar na categoria do bruto; senão "<20%"/"<25%"). |
| Outro feto | `fetoOutro()` aplica o mesmo gate de PFE de `peso()` (finito, 50–7000 g inclusive). |
| IG ausente/inválida + AEDF/REDF | Estado próprio `aedf-ig-desconhecida`: mantém o achado de gravidade, não presume forma precoce/tardia, pede IG. |
| Terminologia | "Restrição do crescimento fetal" (FEBRASGO). Não usar "CIUR". |
| Worker | `sw.js` R14.23-SW2 mantido byte a byte desde a R14.23; HTML e worker têm versões independentes. |
| Rótulo de percentil (R14.32) | Função única `rotP()`: perto de um corte, se o número arredondado cairia no corte ou do lado errado, mostra o lado (`< p10`, `> p90`), a partir da **mesma comparação que decide a classe** (peso por q; CA por valor bruto × cortes oficiais; Doppler e cerebelo por valor × p5/p95; uterinas por `cmpMedida`). Vale em cartões, barras, barra do topo, síntese, conclusão e laudo. Depois de `<`/`>` vai espaço fino U+202F — sem ele, `<p10` dentro de `innerHTML` vira etiqueta e some. |
| Data do exame (R14.31) | Três campos numéricos dia/mês/ano, sem seletor nativo. `dtHoje` virou campo oculto em ISO, lido por todos os consumidores; data inválida ou incompleta deixa `dtHoje` vazio e suspende datas, IG por DUM/exame anterior e velocidade. Datas exibidas em dd/mm/aaaa (R14.30); a concepção na tela da paciente continua por mês, de propósito. |
| Átrio (R14.33) | < 10 mm é normal em qualquer IG; 9–9,9 mm deixou de ser "limite superior" com retorno em 3–4 semanas (sem fonte). Leve [10,13), moderada [13,15], grave > 15 mm — tradução operacional da SMFM #45. |
| Colo (R14.33) | Corte de 25 mm só na janela (IG < 24 sem): "colo curto". Fora dela ou sem IG: estado `red`, "comprimento cervical reduzido", sem categoria de risco. Sem rótulo separado de 15 mm (na ISUOG, < 15 mm é de gestante sintomática). 26–30 mm "limítrofe" só na janela. Sem conduta automática. |
| PSV-ACM (R14.33) | MoM calculado de 15+0 a 40+6; validação diagnóstica de Mari 2000 foi 15–36 sem (o texto diz isso). ≥ 35 sem: PSV alta → aviso de falso-positivo (inclui pós-transfusão); PSV normal → aviso de que não exclui anemia (Maisonneuve 2017). 1,3–1,49 MoM é faixa de atenção do app, não corte diagnóstico. |
| Hadlock 1991 (C0-A) | Equação em ln(PFE), σ ln 0,12; Tabela 1 só histórica. Não é decisão pendente. Aviso na tela: 5,1%/176.060 → Roberts 2025; p10 da equação ≈ p17 da tabela → Adu-Bredu 2026 (atribuição corrigida na R14.33). |
| Janelas de marcadores (R14.34) | Osso nasal, ducto venoso e tricúspide do 1º trimestre: classificados só de 11+0 a 13+6; fora disso, registro sem classificar e fora do laudo. Osso nasal do 2º trimestre: corte de 4,5 mm (FEBRASGO, morfológico) só de 20+0 a 24+6, junto com a razão PFN/ON. Prega nucal: campo só de 16 a 24 sem (já era assim). |
| Valor × corte exibidos (R14.35) | `casasPar`/`fxVal`/`fxCorte`: quando valor e corte arredondados a 2 casas pareceriam iguais com brutos diferentes, ambos ganham casas (até 5). Vale para MoM da PSV (cortes 1,3 e 1,5), CPR (p5, 1,0 e 1,3), faixa p5/p50/p95 dos vasos e IP médio das uterinas (3 casas da média de dois lados). Classificação inalterada. Operador da PSV: o app usa ≥ 1,5 e a fonte escreve > 1,5 — sem efeito prático (o MoM nunca é exatamente 1,5); mantido. |
| Colo na conclusão (R14.35) | `achadosTxt()`: colo curto e comprimento cervical reduzido aparecem como "achado materno", separados dos achados morfológicos fetais; o título da síntese vira "Peso adequado, achado materno" quando é o único achado. |

---

## 3. Armadilhas — parece bug, não é

- **Discordância bruta 24,999999999999996 no caso 2000,20 / 1500,15 g:** representação binária; a decisão por categoria está correta (346.417/346.417). Um teste que exija `ST.disc.v ≥ 25` no bruto falha por contrato, não por defeito.
- **44 "falhas" residuais da bateria numérica de pesos:** todas no recorte de 6 casas de grama, a até **≈ 47,4 ng** do corte (Hadlock, 39+0, p97, 4304,237291 g). É a neutralização nominal preexistente, não erro de Φ.
- **CPR:** o corte p5 é irracional (equação de Ciobanu). Uma razão de dois IPs digitados nunca é exatamente igual a ele (menor distância 7,3e-8 em 13,1 milhões de pares).
- **Worker 8/10 no Playwright 1.56 com `set_offline`:** artefato da simulação de offline do driver. Com transporte realmente interrompido o worker passa 10/10.
- **WebKit no Linux não é Safari/iPhone.** Resultado de WebKit não substitui teste no aparelho.
- **Teste falhando com o app certo:** já aconteceu muitas vezes (expectativa desatualizada, texto de interface que mudou, cenário sem CA). Ver §5.

---

## 4. Bugs corrigidos que não podem voltar (linha R14)

Cobertos pela `suite_regressao_doppler.py` (grupos 2–12; 57.284 checagens na R14.35) ou pelos pacotes de teste das entregas.

- **Igualdade decimal virando "abaixo/acima" do corte** (CA p3/p10/p90/p97, ossos p3, DIO p10/p90, gemelar CA, TN p5/p95, razões CF/CA e CF/DBP, uterinas, PFN/ON, CT/CA, diferença saco–CCN). Ex.: 24+0 com CA 17,33 cm fechava "RCF por CA < p3". R14.24–R14.26.
- **F01** PFE inválido do outro feto chegava a discordância/sFGR. **F02** `phi()` aproximado trocava o lado do corte (até 2,1e-5 pontos percentuais). **F03** IG ausente tratada como "tardia". **F04** `var outroId` só no ramo biométrico → escopo errado da AU do outro feto. **F05** discordância exibida cruzando o corte (19,996% como "20,00%"). R14.27–R14.28.
- **Rótulo de percentil contradizendo a classe** (R14.31 e anteriores): "p10 · PIG" com q = 9,996; no laudo, "(p10) — pequeno" já com q = 9,5, porque lá o arredondamento era inteiro. Ocorria em cerca de 2% dos exames, em peso, CA, Doppler, uterinas, cerebelo e ossos. R14.32.
- **Padrão sistêmico "não avaliado ≠ normal"** — princípio geral do app; qualquer campo nunca tocado deve permanecer "não avaliado" no estado, no cartão e no laudo.

---

## 5. Pendências abertas

**5.1 Suíte de 17/09 (legado — renomeie o arquivo antigo `suite regressao doppler.py` para `suite_legado_2026-09-17.py`; não use como critério de aprovação):** na R14.28 passa **47/62**. Classificação das 15 falhas (Claude, 02/10/2026):

| Falha | Classificação |
|---|---|
| UTD "pelve 0,5 isolada = A1 incompleto" → teste lê `ST.estr.pel` | **Resolvida (05/10/2026): não é regressão.** `ST.estr.pel` é só a faixa bruta da pelve; a classificação formal (`ST.utd`) fica `incompleto` e lista o que falta até cálices, parênquima, ureter, bexiga e oligoâmnio serem avaliados. Tela e laudo dizem "Avaliação UTD incompleta". |
| Órbitas: "biocular alto registrado no laudo" | **Conferido (06/10/2026):** biocular acima do p90 entra no laudo (Sukonpan 2008); o teste antigo procurava outro texto. |
| UTD "pelve normal + ureter dilatado = A2-3" e "laudo registra A2-3" | Mudança documentada: Nguyen 2021 (REFERENCIAS A.5). |
| UTD "[neg] pelve normal = ok" | Teste incompatível: o estado na R14 se chama `normal`. |
| TN "FMF p95 em CCN 84 = 2,8 mm" (app: 3,116) | Mudança documentada: carta FMF 1998 (equação log10, MoM 1,57). |
| 5 casos de "falsos negativos" (PFE p8 + uterinas/AEDF; PFE p50 + AEDF; uterinas na tardia) | **Conferido (06/10/2026):** os cinco cenários foram reproduzidos e todos seguem o Delphi; não é regressão. |
| Gemelar "sem corionicidade não conta" | Mudança documentada no próprio app: critério solitário vale em qualquer corionicidade (Khalil 2019). |
| Gemelar "MC exige 2 de 4" / "DC exige 2 de 3" | Teste procura texto que mudou no cartão; a lógica é coberta pelas matrizes gemelares da auditoria (235.224 casos). |
| 1 grupo aborta (elemento de interface inexistente) | Incompatibilidade do teste com a interface da R14. |

**5.2 Científicas (06/10/2026):** o estado módulo a módulo está no `01_ESTADO_CIENTIFICO_R14_35.md` do dossiê científico R14.35. Ciobanu equações × tabela: fechado. Hadlock 1985 e INTERGROWTH 2020: conferidos no original. Átrio, colo, PSV e aviso de Hadlock: resolvidos na R14.33. Faltam só documentos: carta DeVore 2021 e réplica, corpo de Mari 1995, Hadlock 1992 (CCN), Table S2 do INTERGROWTH, corpo de Roberts 2025 e Adu-Bredu 2026.

**5.3 Validação:** iPhone/Safari físico, atualização e uso offline no aparelho, validação clínica formal.

**5.4 Herdadas do CONTEXTO de 17/09 — auditadas em 06/10/2026** (relatório `05_AUDITORIA_FILA_HERDADA_R14_35.md` do dossiê científico; pente fino geral em `06_PENTE_FINO_R14_35.md`). Erros E1 e E2 corrigidos na R14.34; E3 (prega nucal) não era erro. Fica em aberto só o **D3**: zoom bloqueado na meta viewport (sem efeito no iPhone; só alterar com teste no aparelho). A frase da FEBRASGO sobre o desempenho do ILA no polidrâmnio segue citada como "nº 43 (2025)" até confirmar de qual documento vem.

---

## 6. Escopo e preferências do autor

- Este HTML é o aplicativo **em produção**, independente do projeto Flutter/Codex — não herda governança de lá, nem o inverso. Auditorias vindas de lá podem descrever outro código.
- Português brasileiro; análise crítica (contraponto antes de concordar; se o autor estiver errado, dizer diretamente); nunca aplicar alteração sem liberação; respostas curtas (uso no celular); modo de teste silencioso; perguntar o escopo antes de "revisar tudo" — validação de fonte e de dado clínico é sempre completa.

---

## 7. O que mudou em relação ao CONTEXTO de 17/09 (para não reabrir por engano)

| Antes (17/09) | Agora (R14.28) |
|---|---|
| AU por Acharya 2005; ACM por Arduini & Rizzo | AU, ACM e CPR por Ciobanu 2019 (FMF) |
| Percentil de peso por motor híbrido, `DP_HADLOCK = 0,1329` | Hadlock 1991 ln(EFW), `HADLOCK_SD_LN = 0,12`, Φ preciso |
| Órbitas por Jeanty (desvio fixo) | Sukonpan & Phupong 2008 |
| Líquido FEBRASGO nº 82 | FEBRASGO nº 43 (2025) + SMFM #46 |
| UTD Nguyen 2014 com estado `a1-inc` | Nguyen 2021; completude exigida em `ST.utd` (estado `incompleto`) |
| Hierarquia FEBRASGO → ISUOG → Rumack → CBR/SBR | FEBRASGO → CBR → ISUOG |
| Suíte de 62 casos | `suite_regressao_doppler.py` da linha R14 + pacotes de teste por versão |

Histórico R14 recente (SHA-256 do HTML): R14.24 `fd6b301d…` · R14.25 `0d7b9c8f…` · R14.26 `e2775edb…` · R14.27 `bd54755a…` · R14.28 `3e9aee8b…` · R14.29 `c54a1b0a…` (data do exame no topo) · R14.30 `2a6c0173…` (datas dd/mm/aaaa) · R14.31 `c1369b9a…` (data digitada em dia/mês/ano) · R14.32 `f93989ff…` (rótulo de percentil; "falta/faltam" no UTD) · R14.33 `bef7664b…` (átrio, colo, PSV, aviso de Hadlock e referências) · R14.34 `4152a234…` (janelas de IG do osso nasal e da tricúspide; citações FEBRASGO) · R14.35 `47b3d14c…` (valor × corte exibidos; colo como achado materno).
