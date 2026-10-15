# REFERÊNCIAS — de onde vem cada número do app

**Calculadora Doppler Obstétrico · versão R15.2**
`index.html` SHA-256 `6fc209264d36558b58f7601b2fc173fe9b978bab9745554b1796a6333611b63c` (627.737 bytes) · `sw.js` R14.23-SW2 `868972f4…`
Atualizado em 15/10/2026 (R15.0–R15.2: reorganização da interface e correções de digitação, **nenhuma fonte, corte ou operador mudou**; muda só a regra do título do laudo e a prega nucal fora da janela — ver Parte 7.3 e Parte 10). Conteúdo das Partes 0–9 revisado em 12/10/2026 sobre a R14.56. Substitui o REFERENCIAS de 26/09/2026, que parava na R14.11. Aquele conteúdo está preservado, sem alteração, na **Parte 11 (arquivo histórico)**.
Autor e único responsável clínico: Dr. Diogo S. Ribeiro (CRM 5789-AL).

---

## Para que serve este arquivo

O app mostra as fontes de forma resumida na tela **Referências e limitações**. Este arquivo é a versão longa, escrita para quem precisar **auditar, manter ou reimplementar** o app (o próprio médico, outra IA, um revisor). Para cada parâmetro ele responde a cinco perguntas:

1. **Qual é a fonte**, com citação completa.
2. **O que o app usa dela** (tabela, equação ou corte) e **em que nome de variável ou função** isso está no código.
3. **Em que faixa** de idade gestacional (ou de CCN) a fonte vale, e o que o app faz fora dela.
4. **Qual corte decide** e **com qual operador** (estrito ou inclusivo). Na prática, é aqui que mora a maioria dos erros.
5. **Quão firme é a proveniência**, pelo nível de evidência abaixo.

Os documentos irmãos são o `CONTEXTO.md` (decisões fechadas, armadilhas, pendências) e o `README.md` (publicação e testes). Quando este arquivo e o código discordarem, **vale o código da versão adotada**, e a divergência deve ser corrigida aqui.

---

# PARTE 0 — Como ler

## 0.1 Hierarquia de fontes deste app

**FEBRASGO → CBR → ISUOG** (instrução do médico de 30/09/2026, registrada no app).
- A FMF e as demais fontes **complementam** o que essa ordem não cobre (ex.: curvas de Doppler, TN, ossos longos).
- Os **consensos Delphi** entram onde a FEBRASGO não detalha o critério operacional (ex.: critérios de RCF, restrição seletiva gemelar).
- Fonte **fora da hierarquia** só entra com autorização explícita do médico e fica identificada como tal (ex.: comprimento fetal de Vintzileos, item 7.1).
- Quando duas fontes da hierarquia divergem, o app **não escolhe em silêncio**: mostra as duas leituras ou registra a divergência (Parte 8).

> Antes de 30/09 a ordem registrada era FEBRASGO → ISUOG → Rumack → CBR/SBR. Para este app vale a ordem acima.

## 0.2 Níveis de evidência usados aqui

| Nível | Significa |
|---|---|
| PRIMARY_FULLTEXT | Lido no texto integral da fonte original. |
| PRIMARY_TABLE / PRIMARY_FIGURE | Tabela ou figura da fonte original conferida diretamente (célula a célula, quando dito). |
| PRIMARY_ABSTRACT | Só o resumo da fonte original foi lido. |
| GUIDELINE_CONSENSUS | Diretriz ou consenso de sociedade (FEBRASGO, ISUOG, SMFM, RCOG, Delphi). |
| AUTHORIAL_REPRODUCTION | Reprodução feita pelos próprios autores em outra publicação. |
| SECONDARY_REPRODUCTION | Valores vistos em reprodução de terceiros (artigo, site como o Fetalmed), não no original. |
| EQUIPMENT_REPRODUCTION | Valores vistos só em manual de equipamento. |
| APP_POLICY | Decisão do app ou do médico, não dos autores (ex.: os 21 dias da queda longitudinal). |
| APP_HEURISTIC | Heurística interna, sem validação publicada. Nunca decide nada clínico. |
| UNKNOWN_ORIGIN | Origem não localizada. Valor removido ou rebaixado a descritivo. |
| **PENDENTE** | O app usa, mas a proveniência ainda não foi registrada ou conferida nesta linha (Parte 9). |

## 0.3 Como o app aplica um corte (vale para todos os módulos)

Estas regras explicam por que o mesmo número pode aparecer "igual" ao corte e ainda assim ter um lado definido.

1. **Decisão no valor bruto, nunca no número arredondado da tela.** O valor medido é comparado ao corte bruto da referência. O percentil exibido serve só para mostrar.
2. **Operador estrito por padrão.** "Abaixo do p10" é `valor < p10`, e o valor exatamente no p10 **não** está abaixo. As exceções inclusivas estão escritas em cada linha (ex.: queda longitudinal ≥ 50 percentis, MBV ≥ 8 cm, PSV ≥ 1,5 MoM).
3. **Ruído de ponto flutuante neutralizado.** As comparações de medida usam `cmpMedida(a,b)`, com tolerância de 16 × EPSILON × max(1,|a|,|b|). Ela só apaga o erro de representação binária e **nunca arredonda a medida**.
4. **Percentil de peso com Φ de dupla precisão** (`phiPreciso`, erro ≈ 8e-16). Um peso que está matematicamente no p10 recebe exatamente 10 (`pctPesoRawFromZ`, tolerância 1e-10 no z).
5. **O número exibido nunca cruza o corte que decide a classe:**
   - `rotP()`: perto do corte mostra o lado (`< p10`, `> p90`) em vez de um número arredondado para o lado errado;
   - `fxVal`/`fxCorte`/`casasPar`: valor e corte ganham casas decimais até ficarem distinguíveis;
   - `discFmt()`: discordância gemelar;
   - `ptsTrunc()`: título da trajetória com 1 casa truncada, desde a R14.53;
   - "Valores da IG": cada corte aparece como o último valor digitável ainda alterado ou o primeiro já alterado.
6. **Sem extrapolação.** Fora do domínio publicado, o app mostra "fora da faixa" ou "sem referência nesta IG" e não classifica.
7. **"Não avaliado" ≠ normal; "sem referência" ≠ alterado.** Campo vazio fica fora do laudo (entrada por exceção). Medida sem referência aplicável não vira achado.
8. **Regra do laudo:** nada entra no laudo se não estiver visível na interface clínica.
9. **Unidade:** o motor calcula sempre em **cm** (internamente em mm, via `valmm`). A chave cm | mm da R14.55 só muda a digitação e desloca a vírgula no texto, sem conta em ponto flutuante. O número que chega ao motor é idêntico ao digitado em cm.
10. **Percentil exibido** é limitado a p0,4–p99,4 (`pctPesoFromZ`). As regras que dependem da distância entre percentis (queda longitudinal) usam o valor **sem** esse limite (`pctAtivoRaw`).

---

# PARTE 1 — Datação e idade gestacional

| Item | Fonte | O que o app usa · onde no código | Faixa | Corte / regra | Nível |
|---|---|---|---|---|---|
| IG pelo CCN | Hadlock FP et al. *Radiology* 1992;182:501-505 | ln(IG sem) = 1,684969 + 0,315646·C − 0,049306·C² + 0,004057·C³ − 0,000120456·C⁴ (C = CCN em cm) · `igPorCCN` | CCN 0,2–12,0 cm (fora: não calcula). O botão "Usar esta IG" só aparece com CCN ≤ 8,4 cm | Acima de 8,4 cm o CCN deixa de ser o método de escolha (ACOG CO 700) | PRIMARY (equação) · Robinson & Fleming fica só como comparação histórica |
| IG pela biometria (datação) | Papageorghiou AT et al. INTERGROWTH-21st. *Ultrasound Obstet Gynecol* 2016;48:719-726, Equação 2 (CC + fêmur) · recomendada pela ISUOG (Salomon 2019/2022) | ln(IG em dias) = 0,03243·(ln CC)² + 0,001644·F·ln CC + 3,813 (CC e F em mm) · `igBioHCFL` | Oferecida a partir de 14+0 sem, **só sem datação prévia** (botão "Datar pela biometria" no cartão "Leitura da biometria") | Incerteza (95%) = 1,96 × (0,04009·IG em dias − 1,149), de 14 a 34 sem (`incertezaHCFLDias`). De 26 a 34 sem aparece o aviso ACOG de gestação "subotimamente datada" | PRIMARY + GUIDELINE |
| Gemelar: qual feto data | ISUOG Practice Guidelines 2025 (gemelaridade, DOI 10.1002/uog.29166) | CC do **maior** feto (`gemDatacao`). Se a IG atual está mais perto do feto menor, o app avisa e oferece "Datar pelo feto X (maior CC)" | — | — | GUIDELINE (lida na íntegra, R14.46) |
| Redatação | ACOG/AIUM/SMFM Committee Opinion 700 (Methods for estimating the due date) | `limiarRedata`: redatar pelo US quando a diferença com a DUM passa de **5 dias** antes de 9+0; **7 dias** de 9+0 a 15+6; **10 dias** de 16+0 a 21+6; **14 dias** de 22+0 a 27+6; **21 dias** a partir de 28+0 | — | O app sinaliza; quem decide é o médico | GUIDELINE |
| Idade por parâmetro (DBP, CC, CA, F) | Hadlock FP et al. 1984 (polinômios por parâmetro isolado, os mesmos dos aparelhos) | `IGP` · mostrada ao lado de cada campo, com seta ↑/↓ | — | **Descritiva:** sem cor e sem corte (decisão R14 B.6 / R14.6) | PRIMARY (equações) · uso APP_POLICY |
| Média ponderada da biometria | — | `igBio` (cerebelo ×3, DBP/CC/F ×2) | — | **Heurística sem validação:** só número neutro, não aciona nada (R14 B.6) | APP_HEURISTIC |
| Datas da gestação | Convenção obstétrica | Concepção = DUM + 14 dias; DPP = DUM + 280 dias | — | Texto para a paciente; não entra no laudo | APP_POLICY |

**Origem da IG.** O app guarda de onde veio a IG (`IGSRC`: informada, DUM, ultrassom anterior, biometria atual, CCN) e mostra isso no topo. A grade de botões Direto · DUM · Exame anterior · Biometria **continua na R14.56** (a R14.57, que a retirava, não foi adotada).

---

# PARTE 2 — Peso fetal, crescimento e restrição

## 2.1 Peso fetal estimado (PFE)

- **Fonte:** Hadlock FP, Harrist RB, Sharman RS, Deter RL, Park SK. *Am J Obstet Gynecol* 1985;151:333-337, Tabela II.
- **Duas fórmulas, conforme a curva escolhida no cartão de peso (`CURVA`):**
  - curva **Hadlock** (padrão): 4 parâmetros, `hadlock4`: log10 PFE = 1,3596 − 0,00386·CA·F + 0,0064·CC + 0,00061·DBP·CA + 0,0424·CA + 0,174·F (cm). É a fórmula do Rumack.
  - curva **INTERGROWTH-21st**: 3 parâmetros, `hadlock3`: log10 PFE = 1,326 + 0,0107·CC + 0,0438·CA + 0,158·F − 0,00326·CA·F (cm). É a fórmula pressuposta pelo padrão INTERGROWTH.
- **Plausibilidade:** o cartão só classifica PFE entre **50 e 7.000 g**, inclusive (`peso()`). O mesmo limite vale para o outro feto no gemelar (`fetoOutro`). Abaixo de 1.000 g, a linha do cartão avisa que a fórmula perde precisão e tende a subestimar (R14.51).
- **Margem do método:** ±10% exibida no cartão. É APP_POLICY de comunicação, não corte.
- **Nível:** PRIMARY (equações).

## 2.2 Percentil do peso

| Curva | Fonte | Modelo · código | Faixa | Observações |
|---|---|---|---|---|
| **Hadlock** (padrão) | Hadlock FP, Harrist RB, Martinez-Poyer J. *Radiology* 1991;181:129-133 | Equação original: ln(PFE) com média 0,578 + 0,332·IG − 0,00354·IG² e **DP = 0,12** na escala ln (`hadlockMuLn`, `HADLOCK_SD_LN`, `pctP`) | 10 a 41 sem. A tabela original vai até 40 sem; de 40+1 a 41+0 o app usa a extensão da equação e **avisa no Confira** | A **Tabela 1 impressa** do mesmo artigo não é matematicamente equivalente à equação e fica só como referência histórica. Roberts AW et al., *AJOG* 2025 (o p10 da equação não reproduz o da tabela) e Adu-Bredu et al., *BJOG* 2026 (p10 da equação ≈ p17 da tabela; atribuição corrigida na R14.33). O aviso "Percentil de peso perto do p10" aparece entre p6 e p16 |
| **INTERGROWTH-21st** | Stirnemann J, Salomon LJ, Papageorghiou AT. *Ultrasound Obstet Gynecol* 2020;56:946-948, equações da Table S1 | Modelo LMS: λ, μ e σ em função da IG (`ig21Lambda`, `ig21Mu`, `ig21Sigma`, `ig21Z`) | 18 a 41 sem. A faixa recomendada é 18–40; a extensão até 41 segue a política INTERGROWTH 2025, com aviso | Alternativa **prescritiva**, não o padrão. Em dez/2025 o NHS England (alerta divulgado pelo RCOG) orientou deixar de usar as curvas de peso INTERGROWTH-21st por identificarem menos fetos pequenos |

- **Cortes:** < p3, < p10 (PIG), > p90 (GIG), > p97, todos **estritos**, sobre o percentil de `pctAtivo`.
- **Por que Hadlock é o padrão:** é a curva da tabela de referência do Fetalmed e a referência populacional do protocolo de medicina fetal da FEBRASGO. O Protocolo FEBRASGO nº 90 (2026) aponta Hadlock como a tabela mais usada para o PFE.

## 2.3 Circunferência abdominal (CA)

- **Fonte:** INTERGROWTH-21st. Papageorghiou AT et al. *Lancet* 2014;384:869-879. Tabela oficial de centis (intergrowth21.com, `grow_fetal-ct_ac_table.pdf`).
- **Tabelas no código (mm):**
  - `T_CA` = p3/p50/p97 por semana;
  - `T_CA_P10` e `T_CA_P90` = colunas **oficiais** do p10 e do p90, conferidas linha a linha (27 semanas sem divergência).
  - Interpolação linear entre semanas.
- **Faixa:** 14+0 a 40+0 sem. Fora disso, não classifica.
- **Cortes:** < p3, < p10, > p90, > p97, estritos, pelo **valor bruto** contra a coluna oficial (`caPercentil`, `cmpMedida`). O percentil contínuo exibido é reconstruído de p3/p50/p97 e pode errar o corte oficial em até ±0,25 ponto. Por isso **ele não decide**.
- **Limitação declarada:** com a curva de peso em Hadlock, CA e PFE vêm de referências diferentes, e o app sinaliza isso. Com INTERGROWTH, as duas vêm da mesma fonte.
- **Nível:** PRIMARY_TABLE.

## 2.4 Tamanho fetal e critérios de RCF

| Item | Fonte | Regra no app | Nível |
|---|---|---|---|
| Classificação de tamanho | FEBRASGO (Protocolo nº 43, 2025, conforme o código), citando ISUOG 2019: AIG = PFE **e** CA entre p10 e p90; PIG = PFE **ou** CA < p10; GIG = PFE **ou** CA > p90 (`tamanhoFetal`, R14.20–R14.22) | Um parâmetro em cada extremo = "conflito" (nunca decidido pela ordem). PFE entre p10 e p90 sem CA classificável = "classificação de tamanho incompleta": não afirma AIG | GUIDELINE |
| RCF: duas leituras | FEBRASGO, Protocolo de Obstetrícia **nº 90**, Restrição do crescimento fetal, *Femina* 2026;54(5):391-9 | **RCF suspeita:** CA e/ou PFE < p10. **Diagnóstico formal:** Tabela 2 do protocolo, adaptada do consenso Delphi. Quando as duas divergem, o app mostra as duas | GUIDELINE |
| Critérios formais (Delphi) | Gordijn SJ et al. *Ultrasound Obstet Gynecol* 2016;48:333-339 · FEBRASGO nº 90, Tabela 2 · ISUOG Practice Guidelines 2020 (Lees CC et al., DOI 10.1002/uog.22134) | Pressupõem **ausência de anomalia congênita** (com anomalia marcada, o app não aplica a definição automaticamente). **Precoce (< 32 sem):** isolado = CA/PFE < p3 **ou** diástole ausente/reversa na AU; combinado = CA/PFE < p10 com IP-AU > p95 e/ou IP médio das uterinas > p95. **Tardia (≥ 32 sem):** isolado = CA/PFE < p3; combinado = 2 de 3: CA/PFE < p10 · queda ≥ 2 quartis (2.5) · IP-AU > p95 **ou** CPR < p5 (porta alternativa, nunca conta duas vezes). A partir de 32 sem a diástole ausente não é critério isolado, mas é achado de alta gravidade | GUIDELINE |
| Terminologia | FEBRASGO | "Restrição do crescimento fetal". Não usar "CIUR" | GUIDELINE |
| Intervalo de reavaliação | FEBRASGO nº 90 (2026): crescimento quinzenal na RCF e no PIG (substitui o protocolo de RCF de 2018) | O app **não sugere** intervalos; o texto fica como referência para o médico | GUIDELINE |
| Vigilância e manejo | ISUOG 2020 (diástole ausente/reversa: a cada 2–3 dias antes de 34 sem) | Não automatizado | GUIDELINE |

## 2.5 Queda longitudinal ("2 quartis") — DEC-LONG-002

- **Fontes:** FEBRASGO nº 90 (2026), Tabela 2: "≥ 2 quartis" (no texto, "2 quartis ou 50 percentis") · RCOG Green-top Guideline nº 31 (2024) · Delphi (Gordijn 2016).
- **Regra (R14.49):** queda de **50 percentis ou mais** (operador **inclusivo**: `dq <= −50`), calculada no **percentil bruto** dos dois exames (`pctAtivoRaw`, sem o limite de exibição p0,4–p99,4), **pela mesma curva** nos dois exames. Exige intervalo de **≥ 21 dias**.
- **Os 21 dias** são APP_POLICY de comparabilidade do serviço, apoiada na ISUOG 2019 (Salomon LJ et al., *UOG* 2019;53:715-723: intervalo tipicamente de pelo menos 3 semanas). A FEBRASGO recomenda crescimento quinzenal no seguimento, sem definir intervalo para este critério. Abaixo de 21 dias, a queda aparece só como informação.
- **Faixas visuais do cartão** (APP_POLICY, não critério): queda ≥ 20 "desaceleração importante"; ≥ 10 "desaceleração"; subida ≥ 15 "aceleração".
- **Título (R14.53):** 1 casa decimal **truncada** (`ptsTrunc`), para nunca mostrar "50" com queda bruta de 49,97. O laudo não traz esse número.
- **Histórico:** a DEC-LONG-001 (set/2026: corte estrito > 50) foi **substituída** e não deve ser restaurada.
- **Nível:** GUIDELINE (corte) + APP_POLICY (21 dias, faixas visuais).

---

# PARTE 3 — Doppler

| Vaso | Fonte | O que o app usa · código | Faixa | Corte / operador | Nível |
|---|---|---|---|---|---|
| **Artéria umbilical — IP** | Ciobanu A, Wright A, Syngelaki A, Wright D, Akolekar R, Nicolaides KH. *Ultrasound Obstet Gynecol* 2019;53:465-472 (FMF) | Equações em dias: mediana = 1,6473 − 0,003005·d; DP(log10) = 0,08713 − 0,0002936·d + 0,0000009355·d² (`ciobanuAU`, `ciobanuQuantile`) | 20+0 a 41+6 (140–293 dias, `CIOBANU_GD_MIN/MAX`) | **Alterado:** IP > p95 (estrito). **Limítrofe:** IP ≥ p90 bruto | PRIMARY (equações) |
| **Cerebral média — IP** | Ciobanu 2019 (idem) | log10 mediana e DP em função dos dias (`ciobanuMCA`) | 20+0 a 41+6 | **Alterado:** IP < p5 (estrito). **Limítrofe:** IP ≤ p10 bruto. Acima do p95 = baixa resistência, sem valor patológico isolado | PRIMARY |
| **Relação cerebroplacentária (CPR)** | Ciobanu 2019 (equação da CPR) · critério ISUOG/Delphi e FEBRASGO nº 90 | CPR = IP-ACM ÷ IP-AU; p5 pela **equação** (`ciobanuCPRref`), não pela tabela `T_CPR` | 20+0 a 41+6 | **< p5** = componente de RCF tardia (`inv`). **< 1,0 com p5 ou mais** = alerta só na tela, fora do laudo (`inv-abs`). Sem referência = "não classificável". O antigo corte de **1,3 saiu** na R14.49 por não ter fonte | PRIMARY + GUIDELINE |
| **PSV da cerebral média** | Mari G et al. *N Engl J Med* 2000;342:9-14 · SMFM Clinical Guideline #8 · Maisonneuve E et al. *Fetal Diagn Ther* 2017;42:225-231 | Mediana = e^(2,31 + 0,046·IG) cm/s; MoM = PSV ÷ mediana (`medPSV`, `psvMoMDe`) | Calcula de **15+0 a 40+6**. A validação diagnóstica de Mari foi de 15 a 36 sem, e o texto diz isso | **≥ 1,5 MoM** = anemia moderada/grave. **1,3 a 1,49** = faixa de atenção do app, não corte diagnóstico. A partir de 35 sem: PSV alta pode ser falso-positivo e PSV normal não exclui anemia (Maisonneuve) | PRIMARY + APP_POLICY (1,3) |
| **Artérias uterinas (2º/3º e 1º tri)** | **Duas referências selecionáveis** (`CURVA_UT`, padrão Gómez), nenhuma tratada como padrão internacional: Gómez O et al. *Ultrasound Obstet Gynecol* 2008;32:128-132 (transversal, 620 gestantes, p5/p50/p95; citada nas diretrizes ISUOG) · Cavoretto PI et al. *Ultrasound Obstet Gynecol* 2023;61:474-480 (longitudinal, 476 gestantes/2.045 exames, Table 3 com p3–p97) | **Sempre o IP médio** das duas artérias (`uterinaMediaV`), nunca um lado isolado (C0-B2). Tabelas `T_UT` (Gómez) e `T_UT_CAV` (Cavoretto, Table 3 publicada, não o modelo contínuo) | Gómez: **11–14 sem via transvaginal; 15–41 via transabdominal**. Cavoretto: 10–39 sem, só transabdominal. Fora da combinação curva × via × IG: "referência incompatível" (`utRefCompativel`) | **IP médio > p95** (`cmpMedida`). A via transabdominal vem pré-selecionada (R14.36). A barrinha por lado é **só de consulta** e não classifica | PRIMARY_TABLE |
| **Ducto venoso — IP (2º/3º tri)** | Tongprasert F, Srisupundit K, Luewan S, Wanapirak C, Tongsong T. *Gynecol Obstet Invest* 2012;73:32-37 | Tabela `T_DV` p5/p50/p95. Equação de checagem: PIV = 17,2947·e^(−0,2512·IG) + 0,6053 (difere < 0,001 da tabela) | 14–40 sem | IP > p95 = alterado. Papel clínico pela ISUOG 2020: **vigilância**, não critério diagnóstico de RCF | PRIMARY_TABLE |
| **Ducto venoso — onda 'a'** | ISUOG 2020 / FEBRASGO | Seletor qualitativo (anterógrada, ausente, reversa) | — | Reversa = comprometimento avançado | GUIDELINE |
| **Territórios hemodinâmicos** | FEBRASGO, US obstétrica do 3º trimestre · ISUOG 2020 · FIGO 2021 (Melamed N et al., DOI 10.1002/ijgo.13522) | Quadro de territórios avaliados, sem "escada" obrigatória (R14 B.10) | — | A RCF tardia altera ACM/CPR com AU normal, e isso é o esperado, não uma etapa pulada | GUIDELINE |

**Referências históricas fora do motor:** Acharya 2005 (AU) e Arduini & Rizzo 1990 (ACM). Ficam como consulta (`T_AU`, `T_ACM`) e não decidem nada desde o C0-B1.

---

# PARTE 4 — Primeiro trimestre

| Item | Fonte | Regra no app | Nível |
|---|---|---|---|
| Perda gestacional precoce | Doubilet PM et al., painel SRU. *N Engl J Med* 2013;369:1443-1451 · léxico multissociedades 2024 | Sem atividade cardíaca: o critério "fecha" com CCN ≥ 7 mm por via transvaginal ou ≥ 15 mm por via transabdominal. Sem via informada, o app só descreve | GUIDELINE · a regra da via transabdominal está **PENDENTE** de conferência (Parte 9) |
| FCF — prognóstico precoce | Doubilet PM, Benson CB. *J Ultrasound Med* 1995;14:431-434 · resumo autoral de Doubilet | Limite inferior 100/120 bpm; faixa "poor" < 90/< 110 | PRIMARY_ABSTRACT |
| FCF — FC rápida | Doubilet PM, Benson CB, Chow JS. *AJR* 2000;175:67-69 | ≥ 135/≥ 155 bpm, bom prognóstico isolado | PRIMARY_ABSTRACT |
| FCF — fisiologia 6+0–9+6 | Silva & Bailão. *RBGO* 2000;22(9), Tab. 2 | −2DP/média/+2DP por meia semana; classifica só quando as duas alocações plausíveis dos dias concordam | PRIMARY_TABLE + APP_POLICY |
| FCF — 10+0–13+6 | Pettersen & Faria. *RBGO* 2001;23:567 | p5/p50/p95 por semana completa | PRIMARY_TABLE |
| FCF — 14+0–19+6 | — | Sem referência pontual validada: só registro | — |
| FCF — ≥ 20 sem | FIGO 2015 · Pildner von Steinburg 2013 | 110–160 bpm como alerta (faixa basal de CTG) | GUIDELINE |
| FCF no laudo (R14.48) | Modelo de laudo CBR-FEBRASGO 2026 | "CCN de X mm e atividade cardíaca presente, com frequência de Y bpm". FCF digitada com atividade em branco marca "Presente"; com "Ausente", a FCF fica fora do laudo e o Confira aponta a contradição | APP_POLICY |
| **Translucência nucal** | Padrão **Faria 2004** (população brasileira; reprodução autoral Pettersen & Faria, *RBUS* 2010, 119/119 células) · alternativa **FMF**: Nicolaides KH, Snijders RJM, Cuckle HS, carta, *Prenat Diagn* 1998 (log10 TN = −0,3599 + 0,0127·CCN − 0,000058·CCN²) · técnica: FEBRASGO, Protocolo 63 | p5/p50/p95 pelo CCN, de **45 a 84 mm** (`tabTN`, `CURVA_TN`). **TN > p95** (estrito) = acima do esperado; **TN ≥ 3,5 mm** = aumentada em qualquer CCN. Sem zona limítrofe reconstruída | PRIMARY / AUTHORIAL_REPRODUCTION |
| Osso nasal, ducto venoso, tricúspide | FEBRASGO, Protocolo 77, Ultrassonografia no 1º trimestre | Classificados **só de 11+0 a 13+6**. Fora da janela: registro, sem classificar e fora do laudo (R14.34) | GUIDELINE |
| Ducto venoso — IP (1º tri) | Pruksanusak N et al. *Gynecol Obstet Invest* 2014;78:22-25, Tabela 2 (p. 24), lida no texto integral | PIV p5 **0,69** · p50 **0,92** · p95 **1,13**, constantes para CCN **45,9–75,5 mm**. Onda 'a' interpretada à parte | PRIMARY_TABLE |
| Regurgitação tricúspide | Fetal Medicine Foundation | Corte de **60 cm/s** | GUIDELINE (FMF) |
| Uterinas no 1º tri | Gómez 2008 (via transvaginal até 14+6) ou Cavoretto 2023 (transabdominal) | O aviso para confirmar a via aparece até o primeiro toque (R14.36) | PRIMARY_TABLE |
| Risco combinado | FEBRASGO remete ao software da FMF | **Não calculado** pelo app | — |
| Diâmetro médio do saco | ACOG/AIUM/SMFM CO 700: o saco **não** serve para estimar a data | Informativo; não existe rota que transforme o saco em IG (C0-C1B-07) | GUIDELINE |

---

# PARTE 5 — Morfologia, estruturas, líquido, placenta e colo

## 5.1 Checklist e valores do morfológico

**Fonte geral:** FEBRASGO, Ultrassonografia morfológica do segundo trimestre, **Protocolo de Obstetrícia nº 43 (2025)**; antes nº 78 (2018).

| Estrutura | Fonte | Regra no app | Nível |
|---|---|---|---|
| **Átrio do ventrículo lateral** | FEBRASGO nº 43 (2025) e ISUOG 2020 (Malinger G et al., *UOG* 2020;56:476-484): normal < 10 mm · graduação: SMFM Consult Series #45 | Normal **< 10 mm** em qualquer IG. Leve: **10 a < 13 mm**; moderada: **13 a 15 mm** (inclusive); grave: **> 15 mm**. As faixas decimais sem lacuna são tradução operacional do app. A faixa 9–9,9 mm é **normal**, sem retorno automático (Sharon-Weiner 2022) | GUIDELINE |
| **Cisterna magna** | Checklist FEBRASGO nº 43, conforme a tela do app | Normal **2 a 10 mm**. **< 2 mm** = obliterada; **> 10 mm** = aumentada | GUIDELINE · célula a célula **PENDENTE** |
| **Prega nucal** | Checklist FEBRASGO nº 43 / marcadores SMFM #57, conforme a tela do app | Campo só de **16 a 24 sem**; normal **< 6 mm** | GUIDELINE · **PENDENTE** de conferência fina |
| **Osso nasal (2º tri)** | FEBRASGO nº 43 (2025) | Normal **≥ 4,5 mm**, aplicado **só de 20+0 a 24+6** (fora disso o osso cresce com a IG: só registro, R14.34) | GUIDELINE |
| **Razão prega pré-nasal / osso nasal** | **Sem fonte registrada no app** | Normal **< 0,80** (≥ 0,80 = aumentada, `cmpMedida`) | **PENDENTE** (Parte 9) |
| **Cerebelo (diâmetro transverso)** | Snijders RJ, Nicolaides KH. *Ultrasound Obstet Gynecol* 1994;4(1):34-48, via tabela do Fetalmed (conferida) | Tabela `T_CER` p5/p50/p95, **14 a 38 sem** (sem extrapolar). Alterado < p5 ou > p95 | SECONDARY_REPRODUCTION conferida |
| **Ossos longos** | Chitty LS, Altman DG. *BJOG* 2002 | Tabelas p3/p50/p97 (úmero, rádio, ulna, tíbia, fíbula), **14 a 40 sem** transcritas (a publicação vai de 12 a 42; fora da faixa, o osso aparece sem classificação). **< p3 = abaixo** (decidido pelo valor bruto); **até ~p10 = limítrofe** (percentil reconstruído a partir de p3/p50/p97, só alerta). Osso longo comprido isolado não alarma. A razão úmero/fêmur foi **removida** por não ter fonte (R14 B.5) | PRIMARY_TABLE |
| **Órbitas (DIO, DBO)** | Sukonpan K, Phupong V. *J Med Assoc Thai* 2008;91(9):1318-22, Tabelas 1 e 2 (156/156 células conferidas) | p10/p50/p90 da **semana completa**, 15–40 sem. Fora de p10–p90 = alerta amarelo, não diagnóstico | PRIMARY_TABLE |
| **Razões biométricas** | CF/CA: Hadlock 1983 (*AJR* 141:979-984), faixa normal 20–24% a partir de 22+0 · CF/DBP: Hohler & Quetel 1981 (*AJOG* 141:759-762), faixa publicada 71–87% a partir de 23+0 · CC/CA: Campbell & Thoms 1977 (*BJOG* 84:165-174), descritiva por bloco de 2 sem, 17–41 · CF/CC: Hadlock 1984, descritiva | Ver detalhes em B.1–B.4 e B.9 (Parte 11) | PRIMARY_ABSTRACT / variados |
| **Marcadores de aneuploidia** | SMFM Consult Series #57 | Marcadores descritos; sem cálculo de risco | GUIDELINE |

## 5.2 Trato urinário

| Item | Fonte | Regra no app | Nível |
|---|---|---|---|
| **UTD (dilatação do trato urinário)** | Nguyen HT et al. 2021 update on the UTD classification system. *Pediatr Radiol* 2022;52:740-751, **Figura 1** (correção 2023;53:1217) | Começa em **16+0 sem**. APRPD de 16 a 27+6: normal < 4 mm · A1 4 a < 7 · A2-3 ≥ 7. A partir de 28 sem: normal < 7 · A1 7 a < 10 · A2-3 ≥ 10. Ureter, parênquima, bexiga e oligoâmnio **só contam** com APRPD ≥ 4 mm ou cálices dilatados. Sem todos os componentes = "avaliação incompleta" | PRIMARY_FIGURE |
| **Ureter (mm)** | — | **Só descritivo.** Os cortes de 4 e 7 mm foram removidos (R14 B.11). O UTD qualitativo é a única classificação | — |
| **Bexiga (megacistia)** | **Proveniência não registrada no app** | 1º tri: megacistia **≥ 7 mm**. 2º/3º tri: maior que **IG em semanas + 12 mm** | **PENDENTE** |
| **Parede vesical** | **Proveniência não registrada no app** | Espessada **> 3 mm**. O campo só aparece com megacistia | **PENDENTE** |

## 5.3 Líquido amniótico

- **Diagnóstico:** FEBRASGO, Ultrassonografia obstétrica do terceiro trimestre (*Femina* 2025, DOI 10.61622/0100-7254536202507), **Tabela 1** (`laClsMbv`, `laClsIla`):
  - **oligoâmnio:** MBV **< 2 cm** ou ILA **< 5 cm**;
  - **polidrâmnio:** MBV **≥ 8 cm** ou ILA **≥ 24 cm**.
- **Graduação do polidrâmnio:** SMFM Consult Series #46 (*AJOG* 2018;219(4):B2-B18), **Tabela 2**, limites inferiores inclusivos:
  - MBV: 8–11,99 leve · 12–15,99 moderado · ≥ 16 grave;
  - ILA: 24–29,9 leve · 30–34,9 moderado · ≥ 35 grave.
- **Oligoâmnio sem grau automático:** não há fonte contemporânea para "moderado/acentuado" (R14 B.7).
- **Método preferencial para oligoâmnio:** MBV (Cochrane CD006593, Nabhan & Abdelmoula 2008). Se o MBV foi medido, só ele confirma oligoâmnio (`laOligoFormal`).
- **Histórico:** FEBRASGO nº 82 (2018) fica como referência histórica e técnica. O REFERENCIAS de 26/09 registrava MBV ≤ 2 e > 8; os operadores atuais são < 2 e ≥ 8, pela tabela de 2025.
- **Nível:** GUIDELINE.

## 5.4 Placenta e colo

| Item | Fonte | Regra no app | Nível |
|---|---|---|---|
| **Placenta prévia** | FEBRASGO, US do 3º trimestre (*Femina* 2025;53(6):831-5) · FEBRASGO nº 26 (2018) · RCOG Green-top 27a | Prévia = borda **≤ 20 mm** do orifício interno, ou recobrindo. Janelas: **< 16 sem** sem classificação (RCOG); **16 a 27+6** "suspeita", com reavaliação transvaginal com 32 sem; **≥ 28 sem** "placenta prévia". Via transvaginal = padrão-ouro (aviso e item no Confira se a via for transabdominal). Entrada por exceção: vazio = normal e nada no laudo | GUIDELINE |
| **Acretismo e vasa prévia** | FEBRASGO 2025 | Prévia com cesárea anterior: pesquisar acretismo. Vasa prévia: via transvaginal com Doppler colorido na prévia, placenta bilobada, lobo acessório, inserção velamentosa ou gemelar | GUIDELINE |
| **Espessura placentária** | Bonilla-Musoles F. *Diagnóstico con Ultrasonidos en Obstetricia y Ginecología*. Valencia, 1972, via Fetalmed (`T_PLA`, 16–38 sem) | **Só descritivo:** média e variação, não percentis. Nenhuma diretriz adota corte diagnóstico, e o app não laudará placenta "espessa" ou "fina" | SECONDARY_REPRODUCTION |
| **Colo uterino** | FEBRASGO nº 43 (2025): corte de 25 mm antes de 24 sem · ISUOG 2022 (Coutinho CM et al., *UOG* 2022;60:435-456) · SMFM Consult Series #70 (2024) | **≤ 25 mm com IG < 24 sem** = colo curto; 26–30 mm = limítrofe, só na janela. Fora da janela ou sem IG: "comprimento cervical reduzido", sem categoria de risco. Sem rótulo separado de 15 mm (na ISUOG, < 15 mm é da gestante sintomática). Sem conduta automática. Na conclusão aparece como **achado materno** | GUIDELINE |
| **Restos ovulares** | Sundararajan S et al. *AJOG* 2024 (DOI 10.1016/j.ajog.2023.11.1243) · Blyth et al. *Hum Fertil* 2025 (DOI 10.1080/14647273.2025.2522054) · Durfee et al. 2005 | Descritivo | GUIDELINE / PRIMARY |

---

# PARTE 6 — Gemelaridade

| Item | Fonte | Regra no app | Nível |
|---|---|---|---|
| Curvas de crescimento | Mesmas de feto único (2.2, 2.3) | Sem ajuste para gemelar (limitação declarada) | — |
| **Discordância de peso** | ISUOG 2025 · Delphi gemelar | Categorias **≥ 20%** e **≥ 25%** (`discCat`, `cmpMedida`). Valor bruto preservado; exibição por `discFmt`, que nunca cruza a categoria. Encaminhamento com discordância ≥ 25% ou PFE de um feto < p10 | GUIDELINE |
| **Restrição seletiva** | Khalil A et al., consenso Delphi gemelar. *Ultrasound Obstet Gynecol* 2019;53:47-54 | **Solitário em qualquer corionicidade:** PFE de um feto < p3. **Monocoriônica:** 2 de 4 contributivos (PFE < p10, CA < p10, discordância ≥ 25%, IP-AU do menor > p95). **Dicoriônica:** 2 de 3 (sem a CA). Corionicidade não informada = "corionicidade não informada" no laudo (item obrigatório) | GUIDELINE |
| Nomenclatura SGA | ISUOG 2025 (DOI 10.1002/uog.29166) | Se os dois fetos têm PFE < p10, ambos são descritos como SGA. Pode sobrepor o Delphi, e o app **não** resolve essa sobreposição sozinho | GUIDELINE |
| Início e tipo da restrição seletiva | ISUOG 2025 · Gratacós | Precoce: < 24 sem na MC e < 32 na DC. **Tipos I/II/III de Gratacós** pela diástole da AU do feto menor, só na MC | GUIDELINE |
| **Transfusão feto-fetal** | FEBRASGO 2023, fluxograma "Gestação múltipla monocoriônica" · ISUOG 2025 | Só na MC diamniótica, pelo maior bolsão de cada feto: doador **< 2 cm** e receptor **> 8 cm**. Exatamente 2 ou 8 cm = "no limite". Estágio III de Quintero com Doppler crítico (diástole ausente, reversa ou intermitente; onda 'a' reversa). ISUOG 2025: receptor ≥ 10 cm após 20 sem (Europa) e diferença de bolsões ≥ 4 cm como sinal de atenção | GUIDELINE (ISUOG lida na íntegra; fluxogramas FEBRASGO só por trechos curtos) |
| **TAPS** | FEBRASGO 2023 · consenso Delphi (ISUOG 2025) | Qualquer MC. Estágio 1: PSV-ACM do doador > 1,5 MoM e do receptor < 1,0 MoM. Estágio 2: > 1,7 e < 0,8. Estágio 3: Doppler crítico no doador. Delphi (≥ 1,5 e ≤ 0,8, ou diferença ≥ 1,0 MoM) sem o critério FEBRASGO = "no limite" | GUIDELINE |
| Datação | ISUOG 2025 | CC do maior feto (Parte 1) | GUIDELINE |

---

# PARTE 7 — Fontes fora da hierarquia, políticas do app e ferramentas de apresentação

## 7.1 Fontes fora da hierarquia (autorizadas)

| Item | Fonte | Uso | Autorização |
|---|---|---|---|
| **Tamanho do bebê (só para a paciente)** | Vintzileos AM et al. *Obstet Gynecol* 1984;64:779-82 (PMID 6390277) · erro ≈ ±6% (Milner 1994) | Comprimento (cm) = 6,18 + 0,59 × fêmur (mm), com fêmur de 30 a 90 mm. Linha "Para a paciente" na aba Medidas. **Nunca no laudo**, na conclusão ou na cópia | Médico, 10/10/2026 (nenhuma fonte da hierarquia traz fórmula) |

## 7.2 Políticas do app (APP_POLICY) em vigor

| Política | O quê | Por quê |
|---|---|---|
| 21 dias na queda longitudinal | Intervalo mínimo para o critério de 2 quartis | Comparabilidade; apoio na ISUOG 2019 |
| PSV 1,3–1,49 MoM | Faixa de atenção | Não é corte diagnóstico; o validado é 1,5 |
| CPR < 1,0 com p5 ou mais | Alerta só na tela | Radar informativo, fora do laudo |
| Faixas visuais da trajetória | 10/20 de queda, 15 de subida | Leitura do cartão, não critério |
| Gate CF/CA ≥ 22+0 e CF/DBP ≥ 23+0 | Primeiro dia operacional de "after 21/22 weeks" | As fontes não definem o dia |
| Semana completa nas órbitas | Sem interpolar | A fonte é por semana |
| Bloco de Campbell | Por par de semanas, sem interpolar | Tabela em blocos |
| Zona 6+2 da FCF e alocação dupla de meia-semana | Indeterminado / classificar só quando concordam | As fontes não definem |
| Via transabdominal pré-selecionada nas uterinas | Começo de todo exame novo | Decisão do médico (R14.36) |
| Entrada por exceção | Campo vazio = normal, fora do laudo; o que falta aparece no Confira | Decisão do médico (R14.42/R14.47) |
| Faixa de plausibilidade da entrada | DBP 1,5–10,5 · CC 7–38 · CA 6–40 · F 1–8,5 cm; IP-AU 0,35–3,20; IP-ACM 0,55–3,80; IP uterino 0,25–4,20; PSV 12–100 cm/s; peso 50–7.000 g. Fora disso: "confirme o valor" | Integridade de digitação, não corte clínico |
| Mínimos do modo mm (R14.55) | TN = metade da mediana para o CCN (0,6 mm sem CCN); prega nucal e pré-nasal 1,5; ureter 2; parede vesical 0,6; cisterna 2; átrio e pelve 3; bexiga 1/5 do limite de megacistia da IG (1,5 no 1º tri); interocular 4; placenta 6 mm | Pegar o valor em cm digitado por engano com a chave em mm. **Não são cortes clínicos** |

## 7.3 Ferramentas de apresentação (não são fontes)

- **Valores da IG (R14.54):** consulta inversa dos cortes na IG atual. Usa as mesmas funções e operadores do motor (seções 2–3), sem tabela paralela, e mostra os cortes na grade do campo. Só leitura.
- **Barrinha por lado das uterinas (R14.36):** consulta visual pela mesma curva, via e IG do IP médio. Não classifica.
- **Rótulos que nunca cruzam o corte:** ver 0.3, item 5.
- **Título do laudo (R15.0):** política do app, sem fonte clínica própria. "Ultrassonografia morfológica" quando a sequência de praxe é preenchida (DBO, úmero, rádio, ulna, tíbia ou fíbula; cerebelo sozinho não conta, porque também serve para datar); "do 2º trimestre" abaixo de 28+0 e "do 3º trimestre" a partir de 28+0 (divisão usual dos trimestres); "com Dopplervelocimetria" com qualquer campo de Doppler preenchido. O médico corrige na aba Laudo. A janela FEBRASGO do morfológico do 2º trimestre (20 a 24+6) segue citada nas referências, mas não gera mais aviso na tela, porque o app também atende o morfológico do 3º trimestre (que a FEBRASGO chama de "ultrassonografia obstétrica do 3º trimestre").

---

# PARTE 8 — Divergências entre fontes (registradas, não resolvidas em silêncio)

| Tema | Fonte A | Fonte B | O que o app faz |
|---|---|---|---|
| **RCF: suspeita × formal** | FEBRASGO nº 90: CA e/ou PFE < p10 = RCF suspeita | Delphi / Tabela 2 do mesmo protocolo: exige critério adicional | Mostra as duas leituras |
| **Restrição seletiva × SGA no gemelar** | Delphi gemelar (Khalil 2019) | ISUOG 2025: os dois fetos < p10 = ambos SGA | Mostra o Delphi; registra a sobreposição |
| **Placenta prévia × inserção baixa** | FEBRASGO US 3º tri (2025): borda ≤ 20 mm = **prévia** | FEBRASGO nº 26 (2018) e RCOG 27a: **inserção baixa** quando não recobre | Segue a FEBRASGO 2025; a divergência está na tela |
| **Polidrâmnio pelo ILA** | FEBRASGO 2025, Tabela 1: ILA **≥ 24** | FEBRASGO nº 82 (2018): tabela começa em 25 | Segue 2025: 24,00 já é polidrâmnio (grau leve pela SMFM) |
| **Polidrâmnio pelo MBV, operador** | FEBRASGO 2025: **≥ 8** | Registro antigo: > 8 | Segue ≥ 8 (o REFERENCIAS de 26/09 registrava > 8) |
| **Transfusão feto-fetal, receptor** | FEBRASGO 2023: receptor > 8 cm | ISUOG 2025 (Europa): ≥ 10 cm após 20 sem | Usa a FEBRASGO; o ISUOG fica como nota |
| **TAPS** | FEBRASGO 2023: > 1,5 e < 1,0 MoM (estágio 1) | Delphi (ISUOG 2025): ≥ 1,5 e ≤ 0,8, ou diferença ≥ 1,0 MoM | Critério FEBRASGO classifica; Delphi sem FEBRASGO = "no limite" |
| **PSV-ACM, operador** | App: ≥ 1,5 MoM | Mari 2000: > 1,5 | Sem efeito prático (o MoM nunca dá exatamente 1,5); mantido |
| **Hadlock 1991: equação × tabela** | Equação ln (o app usa) | Tabela 1 impressa | Equação; a tabela fica histórica. Aviso no Confira perto do p10 (Roberts 2025; Adu-Bredu 2026) |
| **Intervalo da queda longitudinal** | App: ≥ 21 dias (ISUOG 2019) | FEBRASGO nº 90: crescimento quinzenal no seguimento, sem intervalo para o critério | 21 dias como política; abaixo disso, só informação |
| **Curva de peso padrão** | Hadlock (FEBRASGO nº 90: a mais usada) | INTERGROWTH-21st (prescritiva; NHS England 2025 recomendou deixar de usar) | Hadlock padrão; INTERGROWTH selecionável |
| **Colo < 15 mm** | ISUOG 2022: valores fixos como < 15 mm são da gestante sintomática | Uso corrente como rótulo próprio | Sem rótulo de 15 mm; só o corte de 25 mm na janela |

---

# PARTE 9 — Pendências de proveniência e limitações

## 9.1 Cortes em uso cuja fonte não está registrada ou não foi conferida

Nenhum destes muda a classificação **sem** o médico autorizar. Ficam aqui para a próxima auditoria científica, que deve seguir a cadeia fonte → dado → regra exata → trecho do app → divergência → decisão → teste.

| Corte no app | Situação | O que falta |
|---|---|---|
| Razão prega pré-nasal / osso nasal **< 0,80** | Sem fonte no código nem na tela de Referências | Localizar a fonte primária (provavelmente da literatura de razão espessura pré-nasal/osso nasal, ex.: de Jong-Pleij et al. — **não conferido**) e o operador |
| Megacistia: **≥ 7 mm** (1º tri) e **> IG + 12 mm** (2º/3º tri) | Sem fonte no código | Fonte primária e operador (≥ ou >) |
| Parede vesical espessada **> 3 mm** | Sem fonte no código | Fonte primária |
| Perda gestacional por via **transabdominal**: CCN ≥ 15 mm sem atividade cardíaca | O painel SRU 2013 trata da via transvaginal | Fonte do corte transabdominal |
| Prega nucal **< 6 mm** (16–24 sem) e cisterna magna **2–10 mm** | Atribuídos ao checklist FEBRASGO nº 43 na tela | Conferir no texto do protocolo, célula a célula |
| Numeração "**Protocolo nº 43 (2025)**" | O app usa o número para o morfológico do 2º tri **e** para a "US obstétrica do 3º trimestre" (*Femina* 2025;53(6):831-5, DOI 10.61622/0100-7254536202507) | Confirmar a numeração oficial e corrigir a citação onde for o caso |

## 9.2 Documentos ainda não obtidos ou lidos só em parte

- Fluxogramas FEBRASGO 2023 de gemelaridade (mono e dicoriônica): conferidos só por trechos curtos. Falta conferir os sinais < / ≤ no original.
- Carta DeVore 2021 e réplica; corpo do artigo de Mari 1995; Hadlock 1992 (CCN, texto integral); Table S2 do INTERGROWTH; corpo de Roberts 2025 e Adu-Bredu 2026.
- PDFs originais de Campbell 1977, Hadlock 1984 (*JUM*), Hadlock 1983 (texto completo), Hohler 1981 (texto completo) e BAPU 2014 (Tabela 1). A auditoria da R14 usou resumos e fragmentos.
- Tabela corrigida OMS/Kiserud para CF/CC: não extraída, e por isso CF/CC segue descritivo.
- Texto integral de Nguyen 2022 (UTD) sobre o cálice central antenatal. Não bloqueia a regra, que se apoia na Fig. 1.
- A frase da FEBRASGO sobre o desempenho do ILA no polidrâmnio segue citada como "nº 43 (2025)" até confirmar de qual documento vem.

## 9.3 Limitações declaradas no app

- Curvas de peso de feto único, sem ajuste para gemelar.
- O percentil satura nas caudas (exibição limitada a p0,4–p99,4). Nesses casos o app mostra a distância do limiar, e as regras de distância usam o valor bruto.
- Um resultado negativo vale só para os parâmetros avaliados.
- Risco combinado do 1º trimestre não calculado (FEBRASGO remete ao software da FMF).
- Conduta, seguimento e momento do parto não são automatizados.
- **Validação no aparelho real (iPhone/Safari) e uso sem internet no iPhone:** pendentes. Os testes automatizados rodam em Chromium e WebKit no Linux.

## 9.4 Pequeno defeito de texto encontrado nesta revisão (não corrigido, aguarda liberação)

- **Cerebelo:** fora da tabela (acima de 38 sem), o cartão diz "Fora da faixa da tabela (**14–40 sem**)", mas a tabela vai de 14 a **38** sem e o app não classifica acima de 38. Só a frase está errada; a regra está certa.

---

# PARTE 10 — Linha do tempo das mudanças de fonte e de regra (R14.12 → R15.2)

**Da R14.12 à R14.23** (sem SHA registrado aqui; ver `CONTEXTO.md`): inventário de plausibilidade das entradas (`PL_HARD`, R14.13); CPR só alimenta "atenção" com referência aplicável (R14.15–R14.16); tamanho fetal por PFE + CA e colunas oficiais do p10/p90 da CA (R14.20–R14.22); líquido amniótico pela FEBRASGO 2025 e graduação SMFM #46 (R14.21–R14.22); worker `sw.js` R14.23-SW2, mantido byte a byte até hoje.

| Versão | SHA-256 (início) | O que mudou em fonte ou regra |
|---|---|---|
| R14.24–R14.26 | `fd6b301d…` · `0d7b9c8f…` · `e2775edb…` | Igualdade decimal nunca vira "abaixo/acima" (`cmpMedida`) em CA, ossos, DIO, gemelar, TN, razões, uterinas |
| R14.27 | `bd54755a…` | Φ de dupla precisão no peso (F02); gate de PFE do outro feto (F01); IG ausente com diástole ausente/reversa (F03); escopo da AU do outro feto (F04) |
| R14.28 | `3e9aee8b…` | Discordância exibida nunca cruza o corte (`discFmt`) |
| R14.29–R14.31 | `c54a1b0a…` · `2a6c0173…` · `c1369b9a…` | Data do exame (sem efeito em fonte) |
| R14.32 | `f93989ff…` | Rótulo de percentil nunca contradiz a classe (`rotP`) |
| R14.33 | `bef7664b…` | Átrio < 10 mm normal (9–9,9 deixou de ser limítrofe); colo: 25 mm só na janela; PSV 15+0–40+6 com Maisonneuve; atribuição Roberts/Adu-Bredu corrigida |
| R14.34 | `4152a234…` | Janelas: osso nasal, ducto e tricúspide do 1º tri só de 11+0 a 13+6; osso nasal do 2º tri só de 20+0 a 24+6 |
| R14.35 | `47b3d14c…` | Valor × corte exibidos com casas suficientes (`casasPar`); colo como achado materno |
| R14.36 | `ab7a5936…` | Uterinas: via transabdominal pré-selecionada; barrinha por lado só de consulta; incisura por quadradinho (laudo cita só a presença) |
| R14.39 | `1a92da24…` | Tamanho do bebê (Vintzileos, fora da hierarquia, autorizado) |
| R14.42 | `e370523e…` | Placenta prévia pela FEBRASGO 2025 (≤ 20 mm), janelas 16/28 sem, acretismo, vasa prévia |
| R14.44 | `ca65295b…` | Tipo de exame (sem efeito em fonte) |
| R14.46 | `9a7a2788…` | Gemelar revisado contra ISUOG 2025 (lida na íntegra) e FEBRASGO 2023: transfusão feto-fetal, TAPS, Gratacós, início da restrição seletiva, datação pelo maior feto |
| R14.47 | `13314891…` | Campo em branco fora do laudo; UTD por exceção; 1º tri com a IG do exame |
| R14.48 | `23c04770…` | FCF embrionária no laudo; referências de datação CC + F, redatação ACOG CO 700, gemelar, placenta, UTD (Nguyen 2022) |
| R14.49 | `5c6f7525…` | **FEBRASGO nº 90 (2026)**; queda ≥ 50 percentis no **percentil bruto** (DEC-LONG-002); **CPR sem o corte de 1,3**; Hadlock acima de 40 sem como extensão com aviso |
| R14.50–R14.52 | `74a1ef9d…` · `a4bbc521…` · `f095499f…` | Apresentação; aviso único "perto do p10"; peso < 1.000 g no cartão (sem regra nova) |
| R14.53 | `ee06d8e6…` | Título da trajetória truncado (`ptsTrunc`); comentários da DEC-LONG-001 marcados como superados |
| R14.54 | `824ba890…` | "Valores da IG" (consulta inversa, só leitura) |
| R14.55 | `7675f2b7…` | Chave cm \| mm; mínimos de digitação do modo mm (não são cortes clínicos) |
| **R14.56 (adotada)** | `969f8c93…` | Confira sem atalhos (sem efeito em fonte) |
| R14.57 | `f9221f23…` | **Não adotada** (retirava do topo a grade "Origem da IG") |
| **R15.0** | `4c7a9969…` | Reorganização (sem efeito em fonte, corte ou operador). **Título do laudo** pelos dados: "morfológica do 2º trimestre" (< 28 sem) ou "do 3º trimestre" (≥ 28) quando a sequência de praxe (DBO ou ossos além do fêmur) é preenchida; "com Dopplervelocimetria" com Doppler preenchido; correção manual na aba Laudo. O aviso "fora da janela do morfológico (FEBRASGO 20–24 sem)" saiu da tela. **Prega nucal** fora de 16–24 sem: o valor não é mais apagado; fica sem classificação e fora do laudo (a janela continua a mesma). Campos vazios fora da janela somem (prega 16–24; osso nasal do 2º tri 20+0–24+6; TN 11+0–13+6) |
| **R15.1** | `56b259c2…` | Quadro da IG de volta ao cabeçalho (sem efeito em fonte) |
| **R15.2** | `6fc20926…` | Gemelar: decimal digitado não se perde com o outro feto preenchido (antes, "4,2" virava "42" e podia entrar no laudo nos campos sem teto de plausibilidade); apagar volta ao campo anterior (sem efeito em fonte) |

---

# PARTE 11 — Arquivo histórico: REFERENCIAS de 26/09/2026 (R14 a R14.11), sem alteração

> Mantido como foi escrito em 26/09/2026, para rastreabilidade. **Onde este arquivo histórico e as Partes 0–10 discordarem, valem as Partes 0–10**. Exemplos: a hierarquia citada na Parte C antiga (FEBRASGO > ISUOG > Rumack > CBR/SBR) foi substituída em 30/09; os operadores do líquido (B.7/B.8) mudaram com a FEBRASGO 2025; o `sw.js` (F.5) foi auditado depois.

# REFERÊNCIAS — cadeia de proveniência das tabelas e regras do motor

Calculadora Doppler Obstétrico · baseline de saída **R14 (corrigida)** · schema 13
Última auditoria: 2026-09-26 (C3b.2a + R14 inicial + correções pós-revisão externa).
Cumulativo: mantém o detalhamento de C3b.2a (órbitas, DV1, FCF, TN, UTD) e adiciona as 10 adjudicações da R14. Nenhum PDF de editora está neste repositório — PDFs licenciados ficam em armazenamento privado do responsável, fora da pasta de deploy (o Vercel serve publicamente tudo que está na pasta de deploy).

Níveis de evidência: PRIMARY_FULLTEXT · PRIMARY_TABLE · PRIMARY_FIGURE · PRIMARY_ABSTRACT · GUIDELINE_CONSENSUS · AUTHORIAL_REPRODUCTION · SECONDARY_REPRODUCTION · SECONDARY_REVIEW · EQUIPMENT_REPRODUCTION · APP_POLICY (decisão do app, não dos autores) · APP_HEURISTIC (heurística interna, sem validação publicada) · UNKNOWN_ORIGIN.

---
---

# PARTE A — Módulos já auditados no C3b.2a (base congelada, não reaberta na R14)

## A.1 Órbitas — distância interocular (DIO) e binocular (DBO)

- **Referência:** Sukonpan K, Phupong V. Fetal ocular distance in normal pregnancies. *J Med Assoc Thai* 2008;91(9):1318-1322. PMID 18843858.
- **Local:** Tabela 1 (interocular) e Tabela 2 (binocular).
- **Como foi conferido:** imagem das duas tabelas extraída do PDF publicado (servidor de figuras da Semantic Scholar). 156/156 células de p10/p50/p90 idênticas ao motor; soma dos n = 595, igual ao artigo.
- **Domínio:** 15–40 semanas; linha da semana **completa**, sem interpolar (APP_POLICY_COMPLETED_WEEK).
- **Estatística:** p10/p50/p90 empíricos por semana. A fonte **não** publica p5/p95: fora de p10–p90 é alerta amarelo, não diagnóstico.
- **Status:** CONFIRMADO — PRIMARY_TABLE.
- **Fonte anterior descartada:** tabela "Jeanty 1982" da Fetalmed, identificada como reconstrução com bandas fixas ±5,0/±3,0 mm — não é transcrição do artigo original.

## A.2 Ducto venoso — PIV no 1º trimestre

- **Referência:** Pruksanusak N, Kor-anantakul O, Suntharasaj T, Suwanrath C, Hanprasertpong T, Pranpanus S, Geater A. A reference for ductus venosus blood flow at 11–13+6 weeks of gestation. *Gynecol Obstet Invest* 2014;78(1):22-25. DOI 10.1159/000362273.
- **Local:** p. 24, Tabela 2 ("Values of S/a, PIV, PLI, and PVIV with CRL 45.9–75.5 mm"), lida no texto integral.
- **Valores no motor:** PIV p5 **0,69** (IC95% 0,64–0,73) · p50 **0,92** (0,90–0,94) · p95 **1,13** (1,08–1,19).
- **Domínio:** CCN **45,9–75,5 mm** (faixa observada). Fora disso: IP registrado, sem classificação. Sem percentil intermediário.
- **Não usar:** Sachin et al. 2025 (IJCPR 17(3), Tab. 7) atribui 0,64/0,84/1,01 ao PIV — é a linha do **PVIV**.
- **Status:** CONFIRMADO — PRIMARY_TABLE.
- **Comportamento congelado (verificado por regressão, 200 cenários, 0 divergências em toda a R14):** onda A interpretada à parte do PIV; onda A positiva + IP acima do p95 → cartão amarelo com "IP acima do p95" (não "Normal"); IP abaixo do p5 → neutro; sem IP → "Normal".

## A.3 Frequência cardíaca fetal (FCF)

- **Prognóstico precoce (6+0–7+0):** Doubilet PM, Benson CB. *J Ultrasound Med* 1995;14:431-434 — limite inferior 100/120 bpm — e faixa "poor" do resumo autoral de Doubilet (<90/<110).
- **FC rápida (6+0–7+0):** Doubilet, Benson & Chow. *AJR* 2000;175:67-69 — ≥135/≥155 bpm, bom prognóstico isolado.
- **Mapeamento de tempo:** `DOUBILET_TIME_MAPPING`: 6+0/6+1 = 1º grupo; 6+3–7+0 = 2º grupo; **6+2 = zona indeterminada** — APP_POLICY.
- **Fisiologia 6+0–9+6:** Silva & Bailão, *RBGO* 2000;22(9), Tab. 2 — colunas −2DP/M/+2DP **publicadas**, por meia semana. Alocação dos dias nas meias semanas não definida no artigo — o app testa as duas alocações plausíveis (APP_POLICY) e só classifica quando concordam.
- **Fisiologia 10+0–13+6:** Pettersen & Faria, *RBGO* 2001;23:567 — p5/p50/p95 por semana completa (1.078 fetos).
- **14+0–19+6:** sem referência ultrassonográfica pontual validada — descritivo.
- **≥20+0:** 110–160 bpm como alerta, faixa basal de CTG (FIGO 2015; Pildner von Steinburg 2013).
- **Status:** CONFIRMADO (todas as camadas, PRIMARY_TABLE/PRIMARY_ABSTRACT conforme o trecho).

## A.4 Translucência nucal (TN)

- **Curva FMF:** Nicolaides KH, Snijders RJM, Cuckle HS, carta *Prenatal Diagnosis* 1998. Equação log10 TN = −0,3599+0,0127·CCN−0,000058·CCN²; MoM 0,62/1,57; CCN 45–84. 40 CCNs recalculados em Python fora do app, idênticos ao motor.
- **Curva Faria:** Pettersen & Faria, *RBUS* 2010 — reprodução autoral da tabela de Faria 2004. 119/119 células conferidas. Só <p5/p5–p95/>p95, sem zona limítrofe reconstruída.
- **Status:** CONFIRMADO (PRIMARY para a carta FMF; AUTHORIAL_REPRODUCTION para Faria).

## A.5 Dilatação do trato urinário (UTD)

- **Referência:** Nguyen HT et al. 2021 update on the urinary tract dilation (UTD) classification system. *Pediatr Radiol* 2022;52:740-751. DOI 10.1007/s00247-021-05263-w. Correção 2023;53:1217 (só o APRPD do P3 = 15mm).
- **Local:** Fig. 1, lida diretamente. Antenatal A2-3: cálices "*Any Dilation*"; ureter/parênquima/bexiga/oligoâmnio só contam "*with APRPD ≥4mm or calyceal dilation*". "Central/Peripheral Dilation" só no pós-natal.
- **Status:** Fig. 1 CONFIRMADA — PRIMARY_FIGURE. Texto integral (para o trecho sobre cálice central) permanece pendente de acesso institucional — não bloqueia a regra vigente, apoiada na figura.

## A.6 Outros módulos citados no motor, não reauditados neste ciclo

Ciobanu et al. 2019 (CPR/FMF), INTERGROWTH-21st (CA/PFE), Hadlock PFE (4/3 parâmetros), Hadlock 1991 (percentil de peso), Vintzileos 1984 (comprimento fetal, auxiliar), RPOC descritivo, placenta descritiva, DMSG +30 informativo — mantidos como estavam, sem alteração nesta rodada.

---
---

# PARTE B — As 10 adjudicações da R14 (com as correções da revisão externa)

## B.1 CC/CA — Campbell & Thoms 1977

- **Referência:** Campbell S, Thoms A. Ultrasound measurement of the fetal head to abdomen circumference ratio in the assessment of growth retardation. *Br J Obstet Gynaecol* 1977;84(3):165-174. DOI 10.1111/j.1471-0528.1977.tb12550.x · PMID 843490.
- **Nível:** PRIMARY_ABSTRACT (resumo) + SECONDARY_REPRODUCTION (tabela, vista em Joshi BR, *J Inst Med Nepal* 2017, Tab. 2 — rótulos de coluna invertidos nessa reprodução; o artigo original está em paywall).
- **Dado original:** n=568 gestações normais, 17–41 semanas. O próprio resumo mistura "95 per cent confidence limits" e "95th centile limit" para os mesmos limites — construção estatística **indeterminada**. Em 31 fetos pequenos para a idade, 22 (71%) ficaram acima do limite do percentil 95.
- **Domínio:** 17–41 semanas, em blocos de 2 semanas (17-18, 19-20, ..., 39-40; 41 isolada) — sem evidência de regressão contínua que sustente interpolação fracionária.
- **Decisão:** REBAIXADO PARA DESCRITIVO. `T_CCAC[Math.floor(g)]` lida por bloco real (pares 17-18/19-20/.../39-40; 41 isolada — corrigido na revisão: o rótulo do bloco antes usava `[floor(g), floor(g)+1]`, que ficava errado nas semanas pares; agora usa a lógica de pares corretos). Exibida como "referência de Campbell 1977 (bloco X–Y sem)", sem cor de normal/anormal, fora da lista "fora da faixa"/critério de RCF.
- **Status:** PARCIALMENTE CONFIRMADO (valores) / INDETERMINADO (estatística e legitimidade de interpolação fracionária).
- **Documentação sincronizada (correção pós-revisão):** o comentário de código de `T_CCAC` e a linha do overlay de Referências foram reescritos para não afirmarem mais "o artigo publica média com IC95%; os rótulos p5/p95 são aproximação" — agora registram a indeterminação estatística real e que a tabela vem de reprodução secundária, não do artigo original.

## B.2 CF/CC — Hadlock et al. 1984

- **Referência:** Hadlock FP, Harrist RB, Shah Y, Park SK. The femur length/head circumference relation in obstetric sonography. *J Ultrasound Med* 1984;3(10):439-442. DOI 10.7863/jum.1984.3.10.439 · PMID 6387166.
- **Nível:** PRIMARY_ABSTRACT (amostra e domínio); a tabela semanal de limites só foi localizada em manuais de equipamento (GE Voluson/LOGIQ) — EQUIPMENT_REPRODUCTION, nunca confirmada no artigo original nem em reprodução autorizada.
- **Dado original:** n=361 fetos normais, 15–42 semanas.
- **Decisão:** REMOVIDO o classificador. A faixa fixa "13,30–23,90% em toda a janela" do baseline anterior era, na prática, o menor limite inferior e o maior limite superior de linhas semanais diferentes de uma tabela nunca verificada — não uma faixa única legítima.
- **Status:** UNKNOWN_ORIGIN / APP_LEGACY para o classificador. CF/CC agora é só numérico, sem normal/anormal.
- **Não migrado para OMS/Kiserud:** a tabela corrigida (Kiserud et al., *PLOS Med* 2017, com duas erratas em 2017 e 2021) não foi extraída e conferida célula a célula nesta rodada — migrar sem essa conferência violaria a mesma regra que está sendo aplicada aqui. Pendente para ciclo futuro.

## B.3 CF/DBP — Hohler & Quetel 1981

- **Referência:** Hohler CW, Quetel TA. Comparison of ultrasound femur length and biparietal diameter in late pregnancy. *Am J Obstet Gynecol* 1981;141(7):759-762. DOI 10.1016/0002-9378(81)90700-6 · PMID 7315902.
- **Nível:** PRIMARY_ABSTRACT.
- **Dado original:** "linear relationship... after 22 weeks' gestation"; FL/BPD = 79 ± 8% (71–87%).
- **Estatística:** o resumo **não define** o que ±8 representa. O rótulo "90% CI" é de manuais de equipamento — **REFUTADO** como citação do autor.
- **Decisão:** MANTIDO 71–87% como **faixa publicada** (nunca "normal" — correção pós-revisão, ver B.9), com gate real em **≥23+0 semanas** (APP_POLICY). Abaixo do gate, o valor é só descritivo.
- **Status:** PARCIALMENTE CONFIRMADO (79±8% = 71-87%) / REFUTADO (rótulo "90% CI").

## B.4 CF/CA — Hadlock et al. 1983

- **Referência:** Hadlock FP, Deter RL, Harrist RB, Park SK. A date-independent predictor of intrauterine growth retardation: femur length/abdominal circumference ratio. *AJR* 1983;141(5):979-984. PMID 6605074.
- **Nível:** PRIMARY_ABSTRACT + fragmentos de PRIMARY_FULLTEXT.
- **Dado original:** n=361, 15–42 semanas; após 21 semanas a razão independe da idade gestacional; normal (mean ± 2SD) 22±2% = 20–24%; corte de rastreio 23,5% = **p90**, sensibilidade de 63% para RCIU (30 casos).
- **Decisão:** MANTIDO 20–24% como **faixa normal** (Hadlock publica explicitamente como "normal range" — por isso, diferente de CF/DBP, esta é a única das três razões onde a palavra "normal" é usada na UI). Gate real em **≥22+0 semanas** (APP_POLICY). Frase causal "típico de insuficiência placentária" REMOVIDA, substituída por linguagem descritiva citando a sensibilidade de 63%.
- **Status:** CONFIRMADO (amostra, domínio, 20–24%, corte de 23,5%=p90, sensibilidade 63%).

## B.5 Razão úmero/fêmur (U/F) 0,90–1,10

- **Busca dedicada:** Krakow D et al. Guidelines for the prenatal diagnosis of fetal skeletal dysplasias. *Genet Med* 2009;11(2):127-133. PMCID PMC2832320. SMFM/AJOG 2018. FEBRASGO nº 43 (2025).
- **Achado:** nenhuma fonte valida a razão U/F 0,90–1,10 nem "úmero curto"/"fêmur curto"/"rizomélico". O que está validado é o percentil/escore z **individual** de cada osso — e as duas sociedades usam limiares **diferentes entre si**: Krakow 2009 (avaliação especializada com medida ≤p5 ou >3 DP abaixo da média) e SMFM 2018 (<p5 ou >2 DP abaixo da média para "curto").
- **Decisão:** REMOVIDO. U/F é só valor numérico. **Correção pós-revisão:** o texto anterior citava incorretamente "abaixo do p3" (não corresponde a nenhuma das duas fontes, que usam p5, com DP diferente entre si) — reescrito para não misturar p3/p5/−2DP/−3DP numa única regra; cada sociedade citada separadamente, com o limiar que lhe pertence.
- **Status:** UNKNOWN_ORIGIN / APP_LEGACY.
- **Fora do escopo (deliberadamente não adicionado):** CF/pé, CF/CA<0,16, CT/CA, índices de letalidade.

## B.6 igBio() e heurísticas de divergência biométrica

- **Busca dedicada:** nenhuma fonte publicada valida a ponderação cerebelo×3/DBP×2/CC×2/FL×2, nem os cortes de 1/1,5/2/3 semanas usados para classificar a comparação.
- **Decisão original da R14:** removidos a classificação "compatível/aceitável/discordância importante" em `peso()`, o alerta agregado em `coer()` para ≥3 semanas, a cor clínica das IGs individuais em ≥1/≥2 semanas, e o alerta de dispersão ≥1,5 semana.
- **BLOQUEADOR encontrado na revisão externa e corrigido nesta rodada:** mesmo com a cor e o texto "compatível/discordância" neutralizados, o bloco `if(ad>=1){...}` dentro de `peso()` (ramo `!datando`, ou seja, quando a IG já está estabelecida e a biometria só é comparada) continuava usando `ad=|gbComp−g|` para **acionar decisões clínicas reais** no cartão `igbRes`: "Isto é crescimento, não data", "a discordância é alteração do crescimento", "mudar a data aqui apagaria a restrição", comparação com `limiarRedata()` sugerindo ou não redatação, e a recomendação "meça o cerebelo". Isso violava o próprio critério da R14 (zero decisão clínica automática sem proveniência) porque a heurística não validada continuava decidindo.
- **Correção:** neste ramo (`!datando`), o cartão `igbRes` agora é **sempre oculto** (`hide(eb)`), incondicionalmente — `gbComp` nunca mais aciona `limiarRedata()`, nunca mais declara crescimento alterado, nunca mais sugere (ou nega) redatação, nunca mais recomenda medir o cerebelo. `gbComp` continua calculado e exibido só como diferença numérica neutra no cartão `igRes` (texto acima do `igbRes`).
- **Preservado, sem alteração:** o cartão `igbRes` no ramo `datando===true` (quando a IG está sendo estabelecida por HC+FL/`igBioHCFL()`, validado, ISUOG grau B) — ali `gb=gbDat`, não `gbComp`, e o aviso de "gestação subotimamente datada" (ACOG, quando `gb>=22`) permanece intacto, porque não deriva da heurística não validada.
- **`limiarRedata()` e o fluxo de redatação por DUM/US/CCN:** continuam existindo, mas **não recebem mais `gbComp` como gatilho** em nenhum caminho — o gatilho de `ad>=1` que os acionava só existia dentro do bloco removido. Este mecanismo (por dias, ISUOG/ACOG) segue como um sistema válido e à parte, mas **a formulação anterior de que ele era "separado" da heurística não validada estava incompleta** enquanto seu gatilho ainda era `gbComp` — isso foi corrigido removendo o gatilho, não apenas reformulando o texto.
- **Também preservados:** as IGs equivalentes individuais por parâmetro (exibidas de forma descritiva, sem corte clínico) e o texto do laudo "Idade equivalente por parâmetro" (puramente informativo).
- **Status:** APP_HEURISTIC / NÃO VALIDADA — agora sem nenhuma via de acionar decisão clínica.

## B.7 Oligoâmnio — gravidade por MBV

- **Diagnóstico (inalterado):** FEBRASGO, Protocolo nº 43 (2025): MBV ≤2,0 cm.
- **Graduação removida:** "<1 acentuado / 1–2 moderado" sem sustentação em diretriz contemporânea. Chamberlain PF et al. *Am J Obstet Gynecol* 1984;150(3):245-249 usa "decreased"(<1cm)/"marginal"(1-2cm), não "acentuado"/"moderado". FEBRASGO nº 82 (2018, mais antiga) chama de "severo" o MBV ≤1cm — fronteira diferente do baseline antigo (<1).
- **Decisão:** diagnóstico binário mantido; grau automático REMOVIDO.
- **Status:** diagnóstico CONFIRMADO; graduação histórica REMOVIDA por não ser padrão contemporâneo.

## B.8 Polidrâmnio — operadores e gravidade por MBV

- **Diagnóstico (inalterado):** FEBRASGO nº 43 (2025) e ISUOG 2024: MBV >8 cm.
- **Divergência documentada:** SMFM Consult Series #46 (*AJOG* 2018;219(4):B2-B18, DOI 10.1016/j.ajog.2018.07.016, reafirmada 2024) define o diagnóstico geral como MBV **≥8 cm**. **Correção pós-revisão:** a formulação anterior descrevia isso como "1 décimo de mm abaixo da política do app" — **incorreta**: a divergência é uma diferença de **operador na igualdade exata de 8,00 cm** (≥ inclui 8,00; > exclui 8,00), não uma diferença de grandeza de 0,1mm. Texto corrigido em toda a documentação e na própria UI (nota exibida quando MBV=8,00 exatos, tanto no ramo "normal" quanto no ramo "polidrâmnio").
- **Graduação corrigida:** a atribuição anterior ("Manning") nunca foi auditada; a busca desta rodada não a confirmou. As mesmas fronteiras (8-11/12-15/≥16) estão em SMFM #46, Tabela 2. Atribuição trocada para SMFM #46; limites inferiores tornados **inclusivos** (8,01–11,99 leve; 12,00–15,99 moderado; ≥16,00 grave).
- **Status:** diagnóstico CONFIRMADO com discrepância de guideline documentada; graduação CORRIGIDA (fonte e fronteiras).

## B.9 CF/DBP não pode ser chamado de "normal" (correção de renderer)

- **Achado da revisão externa:** o renderer genérico das taxas escrevia "normal" na frente de toda faixa exibida, inclusive CF/DBP — mas Hohler & Quetel 1981 nunca usa essa palavra, e a estatística do ±8% é indeterminada (ver B.3).
- **Correção:** o array de taxas agora carrega um 6º campo com o rótulo que a própria fonte sustenta: "normal" para CF/CA (Hadlock 1983 publica "normal range" explicitamente) e "faixa publicada" para CF/DBP (sem essa palavra na fonte). O renderer usa esse rótulo em vez de escrever "normal" para todas.
- **Status:** implementação corrigida; nenhuma mudança de dado ou de classificação, só de rótulo.

## B.10 Sequência de deterioração Doppler

- **Referências:** ISUOG Practice Guidelines — diagnosis and management of SGA fetus and FGR. *Ultrasound Obstet Gynecol* 2020. DOI 10.1002/uog.22134. FIGO — best practice advice for FGR. *Int J Gynaecol Obstet* 2021. DOI 10.1002/ijgo.13522.
- **Achado:** as duas diretrizes descrevem **dois fenótipos com padrões diferentes**, não uma escada obrigatória. RCF tardia: "alterations in UA Doppler and venous districts are RARE...MCA-PI...the most important Doppler parameters in the surveillance of late FGR" (ISUOG 2020). RCF precoce: progressão "typically precedes a cascade", como tendência, não regra individual.
- **Decisão:** `sequencia()` reescrita. "Onde está na sequência" → "Territórios hemodinâmicos avaliados". Classe/semântica "pulou" REMOVIDA (achado de ACM/CPR alterado com AU normal é o padrão esperado na RCF tardia, não uma etapa saltada). Frases de precedência obrigatória em `dopplerIntegrado()` suavizadas.
- **Limpeza pós-revisão:** CSS morto da classe `.seq-e.pulou`/`.seq-e.pulou .seq-p` removido; comentário de cabeçalho do bloco CSS atualizado (antes dizia só "sequência de deterioração", sem contexto da renomeação).
- **Status:** CONFIRMADO que não há sequência universal obrigatória, com fonte primária (texto integral das duas diretrizes).

## B.11 Ureter fetal — cortes de 4 e 7 mm

- **Corte de 4 mm:** busca dedicada não encontrou fonte primária para diâmetro ureteral fetal >4mm como corte antenatal. UNKNOWN_ORIGIN.
- **Corte de 7 mm:** BAPU. Farrugia MK et al. Consensus statement on the management of primary obstructive megaureter. *J Pediatr Urol* 2014;10(1):26-33. DOI 10.1016/j.jpurol.2013.09.018. Define ureter >7mm como anormal, mas no **manejo pós-natal** — não transportável para rastreio antenatal.
- **Decisão:** classificação numérica automática REMOVIDA para os dois cortes. Medida em mm agora só descritiva. UTD qualitativo (`eUreUTD`) continua sendo a única classificação clínica formal — intocado.
- **Status:** 4mm UNKNOWN_ORIGIN (removido). 7mm PARCIALMENTE CONFIRMADO (pós-natal/pediátrico) — não transportável, também removido do classificador antenatal.

---
---

# PARTE C — APP_POLICY explícitas (resumo)

| Política | O quê | Por quê |
|---|---|---|
| Gate CF/CA ≥22+0 sem | Hadlock 1983 não define o primeiro dia de "after 21 weeks" | Operacionalização conservadora |
| Gate CF/DBP ≥23+0 sem | Hohler 1981 não define o primeiro dia de "after 22 weeks" | Idem |
| Diagnóstico de poli/oligo por FEBRASGO/ISUOG, não SMFM | App brasileiro, hierarquia FEBRASGO>ISUOG>Rumack>CBR/SBR | Referências do usuário |
| Zona 6+2 sem indeterminada (FCF) | Notação semana decimal vs semana+dia ambígua nesse ponto | Doubilet não define |
| Alocação dupla de meia-semana (Silva & Bailão) | Artigo não define arredondamento dos dias | Classifica só quando as duas alocações concordam |
| Bloco de Campbell por `Math.floor(g)`, sem interpolar | Tabela é em blocos de 2 semanas, sem regressão contínua publicada | Evita inventar continuidade |

---
---

# PARTE D — Limitações residuais (declaradas)

- PDFs originais de Campbell 1977, Hadlock 1984 (JUM), Hadlock 1983 (texto completo além dos fragmentos), Hohler 1981 (texto completo) e BAPU 2014 (Tabela 1) não foram obtidos — auditoria feita com resumos e fragmentos de busca.
- Tabela corrigida da OMS/Kiserud para CF/CC não extraída e conferida célula a célula — por isso CF/CC permanece descritivo em vez de migrado.
- Protocolo FEBRASGO específico de Doppler/RCF (se existir) não localizado — a posição do item B.10 apoia-se em ISUOG 2020 e FIGO 2021.
- Posição atual do ACOG sobre graduação de oligoâmnio e a diretriz ISUOG 2024 de esqueleto fetal não obtidas nesta rodada.
- Texto integral de Nguyen 2022 (UTD) sobre cálice central antenatal permanece pendente de acesso institucional (não bloqueia a regra vigente, apoiada na Fig. 1).

# PARTE E — Regras removidas ou rebaixadas nesta R14 (resumo para handoff)

| Regra anterior | Origem alegada | Status real | Ação |
|---|---|---|---|
| CC/CA normal/anormal via interpolação fracionária | "Campbell 1977" | Estatística indeterminada; interpolação não sustentada | Descritivo, por bloco |
| CF/CC faixa fixa 13,30–23,90% | "Hadlock 1984" | Tabela nunca vista fora de manual de equipamento | Removido |
| CF/DBP rotulado "normal" e "90% IC" | "Hohler 1981" | Fonte não usa "normal" nem define a estatística do ±8% | Rótulo corrigido, mantida a faixa |
| CF/CA "típico de insuficiência placentária" | "Hadlock 1983" | Linguagem causal não encontrada na fonte | Descritivo, com sensibilidade citada |
| U/F 0,90–1,10, "rizomélico" | Desconhecida | Sem fonte | Removido |
| igBio 1/2/3/1,5 semanas — cores e alertas clínicos | Desconhecida | Sem fonte; **ainda acionava `igbRes`/`limiarRedata()` até esta correção** | Removido, incluindo o gatilho residual |
| Oligo "acentuado"/"moderado" (MBV) | "convenção histórica" | Fronteiras e rótulos não batem com nenhuma fonte atual | Removido, diagnóstico binário mantido |
| Poli "Manning" 8-12/12-16/>16 | Atribuição nunca auditada | Números batem com SMFM #46, não confirmados em Manning | Atribuição e fronteiras corrigidas |
| Sequência Doppler obrigatória, classe "pulou" | Uso interno do app | ISUOG 2020/FIGO 2021 refutam sequência universal | Reescrita para territórios paralelos |
| Ureter >4mm / >7mm | Convenção auxiliar do app | Sem fonte antenatal (4mm); pós-natal/pediátrica (7mm) | Removidos; UTD qualitativo é a única autoridade |

Este arquivo é a base para o próximo handoff científico (Codex ou outro).

---

# PARTE F — Ciclo R14.1 a R14.11 (pós-freeze da R14)

Esta parte é autocontida: pode ser anexada a qualquer versão consolidada deste documento.
Nenhuma curva, tabela, fonte ou limiar das Partes A–E foi alterado neste ciclo. As mudanças
são de **semântica de saída** (o que pode ou não virar achado, conclusão ou laudo), de
**apresentação** e de **persistência**. Cada item abaixo foi verificado no código antes de
ser implementado, e várias alegações de auditorias externas foram refutadas por não
corresponderem ao arquivo vigente (registradas em F.4).

## F.1 Histórico de versões e integridade

| Versão | SHA-256 | Bytes | Conteúdo |
|---|---|---|---|
| R14 (freeze) | `4821d7fb828b5c5e0f987b0fb2f7115a36f230f142bc4b551f3f093109608cf6` | 448.306 | Baseline científica congelada |
| R14.1 | `c71d4e36c63eb4aafbaee0d03c22dfa8bd65349280af9bda61a51b5003f2af12` | 448.976 | Cartão neutro legível no modo escuro; foco no toque |
| R14.2 | `5c26641d194e86c7dfa24f3feef40f7d3d4eae223136a060e810a1ede75a5399` | 450.142 | Pendências clicáveis; foco do "Próximo pendente" |
| R14.3 | `52260c516e8a836fab0c6bee1b87d3eb1c83566319dc3141e86280dd9e8b04c5` | 451.482 | Mapa das abas; painéis ancestrais; confirmação de troca de referência; data/hora na recuperação |
| R14.4 | `52949077cf665d90b1acf29e801ac217e216dda02bbe2345b29f90298707400a` | 452.010 | Cabeçalho rola; faixa IG/peso/pendências fixa |
| R14.5 | `85dd6708a66e1d4ffdd2a250b1ebadf0121e1e6d906e3b05e777ac9f7dea377e` | 449.700 | Bloco de seguimento morto removido; "Positiva"; comprimento fora da tela clínica |
| R14.6 | `a0e7740c782b749afc51cdace8d7e39e00dae74efbe36aee98dba6124f7cc7a8` | 450.713 | Sem cor por diferença de IG (2º local); sem-referência fora dos achados |
| R14.7 | `ea5deb31815abd3105c8d1270b3a5cae4c9d5b5b835d490b0e3a5f4d203a245d` | 449.421 | Lista morta da leitura biométrica removida; U/F fora da interface |
| R14.8 | `d23aebe5c56312e3524dac8cc8f14d07880a948993f786f2254bc1ac66fabcff` | 450.981 | Doppler grave não mascarado por anemia; comprimento fora do laudo |
| R14.9 | `5c915f8fa21446b61d205450e64a7e4669ccb7db09070e379e97b6d6b3131c36` | 455.570 | Modo Paciente ampliado |
| R14.10 | `8a59841de44f88ef7b5d15c9b2e37e290cbea081bd7a9d4fa9864b9e735a3ba9` | 455.634 | Revisão final: concordância, CSS morto, tabela de referências |
| **R14.11 (vigente)** | `d1ba54b7b39ea87aec30eebc89cf453dcd582ae527dc6463f541002accc5bc85` | 457.627 | Exame salvo carimbado com a versão do motor |

`SCHEMA_VERSION` permaneceu **13** em todo o ciclo (ver F.2.7). Regressão ao fim do ciclo:
golden R14 80/80; suíte histórica sem regressão nova; DV1 200/200 cenários sem divergência;
estado clínico + laudo idênticos à versão anterior em 231 cenários a cada passo sem mudança
clínica intencional.

## F.2 Decisões semânticas e de política (valem para qualquer reimplementação)

### F.2.1 SEM_REFERÊNCIA ≠ achado (R14.6)
Medida existente porém não classificável pela referência ativa (ex.: artérias uterinas
medidas sem via informada, ou fora do domínio da curva) **nunca** entra na síntese de
achados ("achados associados") nem aumenta gravidade. Continua contando só para
**cobertura** ("Doppler foi tentado"). Mesmo princípio de "não avaliado ≠ normal", no
sentido inverso: não classificável ≠ alterado.

### F.2.2 Idade equivalente por parâmetro: nenhuma cor em lugar nenhum (R14.6)
A decisão B.6 (idade equivalente é descritiva, sem corte de 1/1,5/2/3 semanas) só tinha sido
aplicada a um dos dois renderizadores. O segundo, que exibe a idade ao lado de cada campo de
biometria, ainda coloria por limiares escalonados pela IG — removido. A seta ↑/↓ é só
direção. **Exceção legítima:** a linha da CA pode ter cor, mas só pelo percentil validado da
CA (INTERGROWTH-21st): abaixo do p3 → grave; abaixo do p10 ou acima do p97 → atenção. A CA
acima do p97 só aparecia colorida "de carona" na heurística removida; foi religada
explicitamente à fonte validada.

### F.2.3 Gravidade não depende da ordem de avaliação (R14.8)
Na síntese de feto com peso adequado, a anemia (PSV-ACM > 1,5 MoM) era avaliada antes de
diástole zero/reversa na umbilical e ducto venoso alterado, com retorno imediato: quando os
dois coexistiam, a conclusão citava só a anemia. Agora o achado hemodinâmico grave é
sempre avaliado primeiro, e a coexistência gera uma classe própria que **nomeia os dois**
na síntese e na conclusão do laudo. Os casos isolados permaneceram idênticos. A escalada
de gravidade máxima (frase "alta gravidade hemodinâmica") nunca foi afetada, porque lê os
achados brutos.

### F.2.4 Regra do laudo (R14.8)
**Nenhuma informação entra automaticamente no laudo se não estiver visível na interface
clínica.** Aplicação: o comprimento fetal estimado (Vintzileos et al. 1984, auxiliar) saiu
da tela clínica na R14.5 e continuava entrando sozinho no laudo — removido do laudo; segue
calculado apenas para o Modo Paciente.

### F.2.5 Modo Paciente (R14.9–R14.10)
Tela de comunicação. Nada dela entra no laudo ou na síntese.
- **Mostra:** tempo de gestação (meses + semanas e dias), FCF em bpm, peso, comprimento,
  "completa o mês em", data provável do parto com contagem regressiva, concepção.
- **Nunca mostra:** percentil, Doppler, líquido amniótico — números que exigem
  interpretação presencial.
- **Precisão:** peso arredondado a 50 g (erro do método ~10–15%), comprimento ao cm inteiro,
  sempre com "cerca de".
- **Concepção:** estimada como DUM + 14 dias (ciclo de 28 dias presumido); o ultrassom não
  determina a data. **Nunca o dia exato.** Início/meados/fim do mês quando a IG vem de CCN
  ou DUM; só o mês nas demais origens (biometria tardia, exame anterior de trimestre
  desconhecido, IG digitada).
- **Gemelares:** peso, comprimento e FCF por bebê (A/B), sempre na ordem A→B. No 1º
  trimestre a FCF não é registrada por feto → linha oculta em gestação gemelar.
- Linha sem dado fica oculta.

### F.2.6 Proteções de uso (R14.3)
- Troca de referência (curva de peso Hadlock↔INTERGROWTH, TN FMF↔Faria, uterinas
  Gómez↔Cavoretto) **pede confirmação somente se já houver resultado** calculado com a
  referência atual.
- Recuperação de exame com mais de 1 h mostra sempre data e hora explícitas — defesa contra
  confundir com o exame da paciente anterior.

### F.2.7 Versão do motor ≠ versão do formato (R14.11)
`SCHEMA_VERSION` protege o **formato** do exame salvo (incompatível → só descartar). Ele não
muda quando só as **regras** mudam — e as regras mudaram várias vezes com o schema em 13.
O exame salvo agora leva o carimbo da versão do app (`motorV`, fonte única `APP_VERSAO`,
que também alimenta o rodapé). Recuperação em versão diferente: aviso explícito ("salvo na
X · app atualizado para Y — resultados recalculados, revise antes de assinar"), recuperação
**permitida**. Campo opcional e retrocompatível: payload v13 sem carimbo = "versão
anterior"; por isso o schema continua 13.

## F.3 Removidos ou alterados na apresentação

| Item | Versão | Motivo | O que continua existindo |
|---|---|---|---|
| Bloco "seguimento sugerido" | R14.5 | Nunca renderizava (DOM/CSS mortos) | Estado interno, usado na frase de alta gravidade do laudo |
| "Positiva (normal)" na onda A do DV 1º tri | R14.5 | Onda A e IP são leituras independentes | "Positiva" |
| Comprimento fetal na tela clínica / no laudo | R14.5 / R14.8 | Não muda decisão; regra F.2.4 | Só no Modo Paciente |
| Lista de idade por parâmetro no cartão de biometria | R14.7 | Nunca ficava visível | Idade ao lado de cada campo; linha do laudo |
| Razão U/F na interface | R14.7 | Sem faixa auditada; só ocupava linha para dizer isso | Percentil/escore z individual de cada osso |

## F.4 Mantido por decisão explícita (não reabrir sem motivo novo)
- **Média ponderada `igBio`** (heurística interna): mantida por decisão do responsável —
  descritiva, rotulada como sem validação, sem cor e sem nenhuma decisão pendurada nela
  desde a R14. Uma auditoria externa recomendou removê-la; a decisão foi mantê-la.
- **Quadro de territórios hemodinâmicos** na aba Medidas: **não** duplica a leitura
  integrada do Doppler (fica em outra aba e responde a outra pergunta). Alegação de
  duplicação refutada duas vezes contra o código.
- **"Normal" no DV do 1º trimestre quando só a onda A foi avaliada (sem IP):** decisão
  explícita da C3b.2a; módulo DV1 congelado.
- Alegações de auditorias externas que não correspondiam ao código vigente (registro para
  não re-litigar): cor por diferença de IG "ainda ativa" no cartão de proporções (já
  removida na R14 — o problema real era o segundo renderizador, F.2.2); sem-referência
  "no radar" após a R14.6 (já corrigido); feedback háptico (inexistente no arquivo).

## F.5 Pendências operacionais
- `sw.js` não auditado (está só no repositório): se usar cache com nome fixo, o aparelho
  pode continuar servindo a versão antiga depois do deploy.
- Validação em iPhone real (os testes automatizados rodam em Chromium, não em WebKit).
- Uso em 30–50 exames reais.
