# Calculadora Doppler Obstétrico

Aplicativo web (PWA, arquivo HTML único) de apoio à decisão em ultrassonografia obstétrica:
biometria e peso fetal, Doppler (umbilical, cerebral média, CPR, uterinas, ducto venoso),
crescimento, gemelar, 1º trimestre e laudo. Uso clínico pelo autor no SUS (Alagoas).
Ferramenta de consulta durante o exame — **não substitui o julgamento clínico**.

Autor e responsável clínico: Dr. Diogo S. Ribeiro (CRM 5789-AL).

## Versão atual

| Arquivo | Versão | SHA-256 |
|---|---|---|
| `index.html` | R14.35 | `47b3d14c74c611dd1fc44ee7b2e6a58700d856f6bc13cdb96edcd8d43879dbc4` |
| `sw.js` | R14.23-SW2 | `868972f473094deafe00372b44de52f1e35b2ff15a576d6222d5b39f70fcc840` |

Endereço: <https://calculadora-doppler.vercel.app> (Vercel, branch `main`).

## Arquivos

| Arquivo | Para que serve |
|---|---|
| `index.html` | O aplicativo inteiro (HTML + CSS + JavaScript, sem dependências externas). |
| `sw.js` | Service worker: guarda o app no aparelho para abrir **sem internet**. Não tem lógica clínica. |
| `CONTEXTO.md` | Leitura obrigatória antes de alterar qualquer coisa: decisões fechadas, armadilhas, pendências. |
| `suite_regressao_doppler.py` | Suíte de regressão da linha R14, R14.24 a R14.35 (12 grupos, 57.284 checagens). |
| `REFERENCIAS.md` | *(recomendado adicionar)* referências e adjudicações; versão atual: `REFERENCIAS_R14_28.md`. |

## Como publicar uma versão nova — sem repetir o erro de 02/10/2026

As versões são entregues com o número no nome (ex.: `Calculadora_Doppler_Obstetrico_R14_28.html`).
**A Vercel só abre a raiz do site se existir um arquivo chamado exatamente `index.html`.**
Em 02/10/2026 o site ficou fora do ar (404) porque o HTML estava como `Calculadora.html`.
Em 07/10/2026 o arquivo subiu como `index.html.html`: o iPhone esconde a extensão e mostra só
"index.html". Depois de enviar, abra o arquivo no GitHub e confira o nome completo.

1. **Antes de enviar**, renomeie o HTML novo para `index.html` (minúsculas, sem espaços).
2. No GitHub: **Add file → Upload files**, envie o `index.html` (ele **substitui** o antigo) e
   confirme em *Commit changes* direto na `main`. Não apague o `index.html` antigo antes.
3. Só reenvie o `sw.js` se houver versão nova dele — e sempre com o nome `sw.js`.
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
```

Saída silenciosa: placar por grupo e detalhes só das falhas. Antes de "consertar" o app por
causa de uma falha, confirme que a expectativa do teste não está desatualizada (ver `CONTEXTO.md`).

## Limites

Candidata técnica: não há declaração de aprovação científica global, validação em
iPhone/Safari físico nem validação clínica formal. Hierarquia de fontes do app:
**FEBRASGO → CBR → ISUOG** (demais fontes complementam lacunas, com atribuição explícita).
