# Calculadora Doppler Obstétrico

Aplicativo web (PWA, arquivo HTML único) de apoio à decisão em ultrassonografia obstétrica:
biometria e peso fetal, Doppler (umbilical, cerebral média, CPR, uterinas, ducto venoso),
crescimento, gemelar, 1º trimestre e laudo. Uso clínico pelo autor no SUS (Alagoas).
Ferramenta de consulta durante o exame — **não substitui o julgamento clínico**.

Autor e responsável clínico: Dr. Diogo S. Ribeiro (CRM 5789-AL).

## Versão atual

| Arquivo | Versão | SHA-256 |
|---|---|---|
| `index.html` | R15.2 | `6fc209264d36558b58f7601b2fc173fe9b978bab9745554b1796a6333611b63c` |
| `sw.js` | R14.23-SW2 | `868972f473094deafe00372b44de52f1e35b2ff15a576d6222d5b39f70fcc840` |

Endereço: <https://calculadora-doppler.vercel.app> (Vercel, branch `main`).

Versão anterior (backup, para voltar se preciso): R14.56 `969f8c93327b85cb5295d9bca633c7fb9eff90112879baf3b4f5bc33363f350a`.

**O que mudou na R15.0/R15.1 (14/10/2026):** abas em cima, presas ao rolar com a faixa da IG; o quadro da IG fica no cabeçalho, abaixo do título;
o tipo de exame saiu (o título do laudo vem do que foi preenchido e se corrige na aba Laudo); biometria completa na Morfologia,
na ordem do exame; velocidade de crescimento em Medidas; campo preenchido nunca some. Cálculos e laudo iguais à R14.56, exceto o título.
**R15.2 (15/10/2026):** no gemelar, o decimal digitado não se perde mais com o outro feto preenchido (defeito antigo); a tecla
apagar com o campo vazio volta ao campo anterior.

## Arquivos

| Arquivo | Para que serve |
|---|---|
| `index.html` | O aplicativo inteiro (HTML + CSS + JavaScript, sem dependências externas). |
| `sw.js` | Service worker: guarda o app no aparelho para abrir **sem internet**. Não tem lógica clínica. |
| `CONTEXTO.md` | Leitura obrigatória antes de alterar qualquer coisa: decisões fechadas, armadilhas, pendências. |
| `suite_regressao_doppler.py` | Suíte de regressão, R14.24 a R15.2: 35 grupos de versão + 5 sentinelas (165.036 checagens por motor) e o diferencial do portão de publicação (`--comparar`). |
| `REFERENCIAS.md` | De onde vem cada número do app: fontes, faixas, cortes e operadores, divergências, pendências e histórico. |

## Antes de publicar — portão (regra desde 15/10/2026)

Nenhuma versão vai ao ar sem os três passos.

1. **Suíte + diferencial (~15 min no computador).** Baixe do GitHub o `index.html` que está no ar, salve como
   `index_no_ar.html` ao lado do novo, e rode:
   ```bash
   python3 suite_regressao_doppler.py index.html --ambos --comparar index_no_ar.html
   ```
   Tem de terminar em **`PORTÃO DE PUBLICAÇÃO: suíte OK nos dois motores · diferencial IGUAL à versão no ar`**.
   Se o diferencial listar diferenças (código de saída 2), cada uma tem de ser mudança **declarada** da versão nova
   no `CONTEXTO.md` (ex.: título do laudo na R15.0). Diferença não declarada é regressão: **não publique**.
2. **iPhone, 5 minutos** — logo depois de subir e **antes do primeiro paciente**, com a internet ligada:
   - [ ] Rodapé mostra a versão que você subiu (se não, feche e reabra o app uma vez).
   - [ ] Role a Morfologia **com o teclado aberto**: abas e faixa da IG ficam presas no topo.
   - [ ] Gemelar com o feto A preenchido: no feto B, digite `7,4` no DBP → fica `7,4` (não `74`).
   - [ ] Campo vazio + tecla apagar → o cursor volta ao campo anterior.
   - [ ] Um exame simples até o fim: **Copiar laudo** e colar no sistema — texto completo, sem "NaN" ou "undefined".
   - [ ] Modo avião, feche e reabra o app: abre e calcula.

   Falhou algum item: volte à versão anterior (Vercel → *Deployments* → último deploy bom → **Instant Rollback**,
   ou reenvie o `index.html` do backup) e avise antes de usar.
3. **Só então** a versão está liberada para uso.

## Como publicar uma versão nova — sem repetir o erro de 02/10/2026

As versões são entregues com o número no nome (ex.: `Calculadora_Doppler_Obstetrico_R14_28.html`).
**A Vercel só abre a raiz do site se existir um arquivo chamado exatamente `index.html`.**
Em 02/10/2026 o site ficou fora do ar (404) porque o HTML estava como `Calculadora.html`.
Em 07/10/2026 o arquivo subiu como `index.html.html`: o iPhone esconde a extensão e mostra só
"index.html". Depois de enviar, abra o arquivo no GitHub e confira o nome completo.
Em 10/10/2026 os arquivos foram apagados e os novos não chegaram a subir (site em 404 por horas):
**envie primeiro, apague depois** — o upload de um arquivo com o mesmo nome já substitui o antigo.

1. **Antes de enviar**, renomeie o HTML novo para `index.html` (minúsculas, sem espaços).
2. No GitHub: **Add file → Upload files**, envie o `index.html` (ele **substitui** o antigo) e
   confirme em *Commit changes* direto na `main`. Não apague o `index.html` antigo antes.
3. Envie também `CONTEXTO.md`, `README.md`, `REFERENCIAS.md` e `suite_regressao_doppler.py` sempre que vierem na entrega —
   quem auditar o repositório precisa da documentação e da suíte da mesma versão do `index.html`.
   Só reenvie o `sw.js` se houver versão nova dele — e sempre com o nome `sw.js`.
4. A Vercel publica sozinha em segundos. Abra o endereço em **aba anônima** e confira a versão
   no app. Se der 404: Vercel → *Deployments* → último deploy bom → **Instant Rollback**.
5. No iPhone, abra uma vez com internet para o app atualizar o cache.

## Como testar

```bash
pip install playwright --break-system-packages
playwright install chromium          # opcional: playwright install webkit
python3 suite_regressao_doppler.py index.html            # Chromium
python3 suite_regressao_doppler.py index.html --webkit   # WebKit (não equivale a Safari/iPhone físico)
python3 suite_regressao_doppler.py index.html --ambos    # os dois, em sequência
python3 suite_regressao_doppler.py index.html --ambos --comparar index_no_ar.html   # portão de publicação
```

Grupos 36–40 são **sentinelas**: não protegem um defeito específico, procuram classes de erro (digitação tecla a
tecla com vírgula, texto proibido e coerência entre cartão, faixa, laudo e conclusão, salvar → recuperar,
gravidade clínica monotônica, toques aleatórios). Têm de passar em qualquer versão.

Saída silenciosa: placar por grupo e detalhes só das falhas. Antes de "consertar" o app por
causa de uma falha, confirme que a expectativa do teste não está desatualizada (ver `CONTEXTO.md`).

## Limites

Candidata técnica: não há declaração de aprovação científica global, validação em
iPhone/Safari físico nem validação clínica formal. Hierarquia de fontes do app:
**FEBRASGO → CBR → ISUOG** (demais fontes complementam lacunas, com atribuição explícita).
