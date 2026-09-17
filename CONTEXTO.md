# CONTEXTO — Calculadora Doppler Obstétrico

**Leia este arquivo inteiro antes de alterar qualquer coisa.**

Software clínico de apoio à decisão em ultrassonografia obstétrica. Arquivo HTML único,
hospedado no Vercel. Autor e único responsável clínico: Dr. Diogo S. Ribeiro
(obstetra/medicina fetal, CRM 5789-AL).

Última auditoria: 15–17/09/2026 · versão interna `v2026-09-15-audit1`
SHA-256 publicado nessa data: `2d942921aa068ce014060335e159bd28ed6a3d1426a4fb0be8a836549c8c8b2f`

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
   deste app já chegaram descrevendo bugs que não existiam mais, ou que nunca existiram.

---

## 1. Decisões fechadas — NÃO reabrir

Já foram adjudicadas pelo autor. Reabrir custa tempo e gera retrabalho.

| Tema | Decisão |
|---|---|
| IP da artéria umbilical | **Acharya 2005**, domínio 19–40 sem. Não migrar para Ciobanu. |
| IP da ACM (isolado) | **Arduini & Rizzo 1990**. Migração para Ciobanu discutida e adiada. |
| CPR | **Ciobanu 2019/FMF**, p5 por IG. Corte absoluto <1,0 permanece só como radar. |
| Queda longitudinal | Estritamente **>50** pontos percentuais **e** intervalo ≥21 dias. Uma auditoria externa propôs ≥50 sem o gate de 21 dias — foi **recusado**. |
| TN | Padrão **Faria 2004** (mm a mm, CCN 45–84), alternável para Snijders/FMF ao vivo, volta a Faria a cada exame. |
| Fórmula de peso | Hadlock 4 parâmetros. Percentil por motor híbrido calibrado por tabela (`DP_HADLOCK=0,1329`) — **não** é a equação pura de Hadlock 1991. Não trocar sem decisão. |
| Líquido amniótico | Perfil **FEBRASGO nº 82 (2018)**: oligoâmnio `< 2` cm (estrito). ISUOG 2024 usa `≤ 2` — é escolha de perfil, não bug. |
| Terminologia | "Restrição do crescimento fetal" (FEBRASGO). **Não** usar "CIUR". |

**Hierarquia de fontes:** FEBRASGO → ISUOG → Rumack → CBR/SBR. `fetalmed.net` é a
referência secundária canônica do projeto. Fonte fora dessas quatro: avisar e não
implementar sem autorização.

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
(<32 sem). Na tardia, C3 é apenas `CPR<p5 OU IP-AU>p95`. Não é esquecimento — é o
critério Delphi/ISUOG.

**Placenta e o "limite" da semana 30.** Ver acima. E o módulo de placenta é
deliberadamente **informativo**: não emite "placenta espessa/fina" como diagnóstico,
porque a fonte é de 1972, publica média e variação (não percentis), e nenhum guideline
adota corte diagnóstico. Não "melhore" isso voltando a cravar o termo.

**AVISO GERAL:** durante a auditoria, **três vezes** um teste falhou e o aplicativo estava
certo — o cenário do teste é que estava mal calibrado (ex.: uma ACM baixa que, sem eu
perceber, também derrubava a CPR abaixo do p5 e legitimamente fechava um componente).
Antes de alterar o app por causa de uma falha na suíte, verifique a expectativa do teste.

---

## 3. Bugs corrigidos que não podem voltar

Estão todos cobertos pela suíte. Listados porque entender a causa evita recriá-los.

- **Diástole descartada.** `diastValor()` retornava `'na'` quando o campo do IP estava
  vazio. Com diástole reversa selecionada e IP em branco, o app concluía "Doppler não
  avaliado" num feto p8. Era o pior bug da série. A guarda original fazia sentido quando
  o default do seletor era "presente"; depois que o default virou "não avaliada", ela
  passou a destruir dado real.
- **AEDF/REDF não fechava C3 na forma tardia.** Diástole ausente implica IP>p95 por
  definição. Agora entra no componente, sem contagem dupla.
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

---

## 4. Pendências abertas

| Item | Estado |
|---|---|
| **Ducto venoso tardio** | Tabela (Tongprasert 2012) verificada; **lógica de classificação nunca auditada**. Próximo alvo. |
| **PSV-ACM / anemia** | Fórmula de Mari 2000 confirmada; **módulo nunca auditado**. O corte de 1,5 MoM decide cordocentese. |
| `AUTO_BIO` | Média ponderada própria (cerebelo×3, DBP/CC/CF×2) **sem artigo que a valide**, podendo estabelecer IG formal. Sinalizado, não corrigido. |
| p10 da CA | Tabela INTERGROWTH embarcada tem só p3/p50/p97. O corte de p10 usa aproximação contínua. Importar a coluna oficial. |
| `coer()` | Regras além das já tocadas não foram varridas. Já produziu duas contradições de tela. |
| Modo paciente, `guia()`, barras de percentil, recuperação da persistência | Nunca auditados. Erram para o cosmético. |
| Cadência de seguimento da RCF | App sugere 3–4 sem; FEBRASGO nº 35/2018 diz **14 dias**. O app avisa da divergência, mas os números não foram alinhados — decisão clínica pendente. |

---

## 5. Escopo — o que este repositório é e não é

Este HTML é o aplicativo **em produção**, usado pelo autor no SUS em Alagoas.

Existe em paralelo um projeto Flutter, mantido por outra equipe/IA. Os dois são
**independentes**. Correções feitas aqui **não** são importadas automaticamente para lá,
e auditorias vindas de lá descrevem um código diferente deste — já chegaram apontando
bugs desta base que não existiam mais. Sempre confirme no código presente.

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
