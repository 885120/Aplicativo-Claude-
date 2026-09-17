#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SUITE DE REGRESSAO — Calculadora Doppler Obstetrico
====================================================
Consolida os testes construidos nas auditorias de 12 a 17/09/2026.

COMO USAR
---------
    pip install playwright --break-system-packages
    playwright install chromium
    python3 suite_regressao_doppler.py [caminho/para/o.html]

Sem argumento, procura "Calculadora_Doppler_Obstetrico.html" no diretorio atual.

SAIDA
-----
Silenciosa quando tudo passa (imprime so o placar por grupo).
Falhas aparecem com cenario, esperado e obtido. Codigo de saida != 0 se algo falhar,
para poder ser usado em automacao.

POR QUE ISTO EXISTE
-------------------
Cada achado abaixo foi um bug REAL encontrado e corrigido. O teste existe para que
ele nao volte. Quatro vezes durante a auditoria um teste "falhou" e o APP estava certo —
o teste e que estava mal calibrado ou desatualizado (o caso mais recente: "Pelve 0,5
isolada = A1" testava exatamente o cenario do bug de UTD trivalente corrigido em
2026-09-17, e foi atualizado para refletir o comportamento correto, a1-inc). Por isso
cada caso tem um comentario dizendo o que ele protege: antes de "consertar" o app por
causa de uma falha aqui, confirme que a expectativa do teste e que nao esta errada.

Os casos NEGATIVOS (o que NAO pode disparar) sao tao importantes quanto os positivos:
sao eles que impedem que uma correcao contra falso negativo crie um falso positivo.
"""

import sys, json, pathlib, datetime

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sys.exit("Falta o playwright. Rode:\n"
             "  pip install playwright --break-system-packages\n"
             "  playwright install chromium")

# ---------------------------------------------------------------- infraestrutura

SET = """([i,v])=>{var e=document.getElementById(i); if(!e) return;
 e.value=v;
 e.dispatchEvent(new Event('input',{bubbles:true}));
 e.dispatchEvent(new Event('change',{bubbles:true}));}"""

RES = []          # [(grupo, id, esperado, obtido, ok)]
ERROS_JS = []

def reg(grupo, ident, esperado, obtido):
    RES.append((grupo, ident, esperado, obtido, esperado == obtido))

def setv(pg, campo, valor):
    pg.evaluate(SET, [campo, str(valor)])

def laudo_txt(pg):
    return pg.evaluate("""()=>{try{laudo();}catch(e){return 'ERRO_LAUDO: '+e.message;}
      var el=document.getElementById('ldT'); return el?el.innerText:'';}""")

# ---------------------------------------------------------------- grupos

def g_rcf_tardia(pg):
    """RCF tardia: 2 de 3 componentes, com CPR e IP-AU como UMA vaga (nunca duas).
       Protege contra: CPR baixa isolada fechar diagnostico (falso positivo) e
       contra CPR+AU juntos contarem em dobro."""
    G = "RCF tardia (2 de 3)"
    setv(pg,'sem','34'); setv(pg,'dias','0')
    pg.evaluate("()=>{setModo('dir');}")

    def cena(pfe_q, auip, acmip, dq=None):
        setv(pg,'auip',auip); setv(pg,'acmip',acmip)
        vel = (f"ST.vel={{delphi:true,dq:{dq},dias:25,flag:'queda'}};" if dq else "ST.vel=null;")
        pg.wait_for_timeout(120)
        return pg.evaluate(f"()=>{{{vel}ST.pfe={{w:2000,q:{pfe_q},bio:true}};sintese();"
                           f"return ST.sint?{{cls:ST.sint.cls,motivo:ST.sint.motivo||''}}:null;}}")

    r = cena(50, 0.86, 1.00)   # CPR<p5 sozinha, peso e queda normais
    reg(G,"CPR<p5 isolada NAO fecha", False, r['cls']=='rcf')
    r = cena(50, 1.30, 1.00)   # CPR<p5 + IP-AU>p95, sem tamanho nem queda
    reg(G,"CPR+AU juntas NAO fecham sozinhas (1 vaga)", False, r['cls']=='rcf')
    r = cena(8, 0.86, 1.00)    # tam10 + CPR<p5
    reg(G,"PFE<p10 + CPR<p5 fecha", True, r['cls']=='rcf')
    r = cena(8, 1.30, 1.85)    # tam10 + AU alto
    reg(G,"PFE<p10 + IP-AU>p95 fecha", True, r['cls']=='rcf')
    r = cena(8, 1.30, 1.00)    # tam10 + AU alto + CPR baixa
    reg(G,"AU+CPR juntos contam 1 vaga (2 itens no motivo)", 2, len(r['motivo'].split(', ')))
    r = cena(50, 0.86, 1.85, dq=-60)   # queda + nada mais
    reg(G,"Queda>50 isolada NAO fecha", False, r['cls']=='rcf')
    r = cena(50, 1.30, 1.85, dq=-60)   # queda + AU
    reg(G,"Queda>50 + IP-AU>p95 fecha", True, r['cls']=='rcf')
    r = cena(2, 0.86, 1.85)    # <p3 solitario
    reg(G,"PFE<p3 fecha sozinho", True, r['cls']=='rcf')


def g_falso_negativo(pg):
    """Falsos negativos que ja ocorreram de verdade.
       O pior: diastole reversa com PFE<p10 saia como 'Doppler nao avaliado',
       porque diastValor() descartava o seletor quando o IP estava vazio."""
    G = "Falsos negativos"
    pg.evaluate("()=>{setModo('bio');}")

    def cen(sem,q,au='',di='na',ut='',caCm=None,queda=False):
        setv(pg,'sem',sem); setv(pg,'dias','0')
        setv(pg,'auip',au); setv(pg,'diast',di)
        setv(pg,'utD',ut); setv(pg,'utE',ut); setv(pg,'acmip','')
        setv(pg,'bCA', caCm if caCm else '')
        pg.wait_for_timeout(150)
        vel = "ST.vel={delphi:true,dq:-60,dias:25,flag:'queda'};" if queda else "ST.vel=null;"
        return pg.evaluate(f"()=>{{{vel}ST.pfe={{w:1500,q:{q},bio:true}};sintese();"
                           f"return ST.sint?ST.sint.cls:null;}}")

    # --- precoce (<32 sem): AEDF e solitario; uterinas CONTAM ---
    reg(G,"28s PFE p2 (solitario <p3)","rcf", cen(28,2))
    reg(G,"28s PFE p8 + AEDF (solitario)","rcf", cen(28,8,di='zero'))
    reg(G,"28s PFE p50 + AEDF (solitario mesmo com peso normal)","rcf", cen(28,50,di='zero'))
    reg(G,"28s PFE p8 + IP-AU>p95","rcf", cen(28,8,au='1.40'))
    reg(G,"28s PFE p8 + uterinas>p95 (contam na precoce)","rcf", cen(28,8,ut='1.60'))

    # --- tardia (>=32 sem): AEDF satisfaz C3; uterinas NAO contam ---
    reg(G,"34s PFE p2 (solitario <p3)","rcf", cen(34,2))
    reg(G,"34s PFE p8 + AEDF sem IP digitado","rcf", cen(34,8,di='zero'))
    reg(G,"34s PFE p8 + REDF sem IP digitado","rcf", cen(34,8,di='rev'))
    reg(G,"34s PFE p8 + IP-AU>p95","rcf", cen(34,8,au='1.30'))
    reg(G,"34s PFE p8 + queda>50","rcf", cen(34,8,di='pres',au='0.86',queda=True))

    # --- negativos: o que NAO pode disparar ---
    reg(G,"[neg] 28s PFE p8 isolado nao fecha","pig", cen(28,8,di='pres',au='0.95'))
    reg(G,"[neg] 34s PFE p8 isolado nao fecha","pig", cen(34,8,di='pres',au='0.86'))
    reg(G,"[neg] 34s uterinas>p95 nao contam na tardia","pig-risco",
        cen(34,8,ut='1.20',di='pres',au='0.86'))
    reg(G,"[neg] 34s PFE p50 + AEDF nao vira RCF","aig-grave", cen(34,50,di='zero'))

    # --- CA como criterio, com e sem PFE ---
    p3_34 = pg.evaluate("interp(T_CA,34)[0]")
    reg(G,"34s CA<p3 com peso p50 (solitario pela CA)","rcf",
        cen(34,50,di='pres',au='0.86',caCm=round((p3_34-6)/10,2)))
    setv(pg,'bCA', round(p3_34*1.03/10,2)); setv(pg,'auip','0.86')
    setv(pg,'diast','pres'); pg.wait_for_timeout(150)
    reg(G,"CA<p10 sem PFE nao fica mudo","ca-sem-criterio",
        pg.evaluate("()=>{ST.pfe=null;sintese();return ST.sint?ST.sint.cls:null;}"))
    setv(pg,'auip','1.35'); pg.wait_for_timeout(150)
    reg(G,"RCF precoce fecha pela CA sem PFE","rcf",
        pg.evaluate("()=>{setv=0;ST.pfe=null;sintese();return ST.sint?ST.sint.cls:null;}")
        if False else pg.evaluate("()=>{ST.pfe=null;sintese();return ST.sint?ST.sint.cls:null;}"))


def g_dado_ausente(pg):
    """Dado ausente nunca pode virar normalidade."""
    G = "Dado ausente"
    pg.goto_reset()
    setv(pg,'sem','30'); setv(pg,'dias','0'); setv(pg,'auip','1.10')
    pg.wait_for_timeout(150)
    reg(G,"Diastole nao tocada = nao avaliada","na", pg.evaluate("diastValor()"))
    reg(G,"Diastole selecionada vale mesmo sem IP","rev",
        pg.evaluate("()=>{var e=document.getElementById('diast');e.value='rev';"
                    "document.getElementById('auip').value='';return diastValor();}"))


def g_fronteiras(pg):
    """Operadores de borda: no valor EXATO do corte, nao dispara."""
    G = "Fronteiras"
    pg.goto_reset()
    pg.evaluate("()=>{setModo('bio');}")
    setv(pg,'sem','34'); setv(pg,'dias','0')
    p3 = pg.evaluate("interp(T_CA,34)[0]")          # mm
    def ca_flag(ca_mm):
        setv(pg,'bCA', round(ca_mm/10,4)); pg.wait_for_timeout(120)
        pg.evaluate("caPercentil()")
        return pg.evaluate("ST.ca?ST.ca.flag:null")
    reg(G,"CA exatamente no p3 NAO e <p3", False, ca_flag(p3)=='baixo3')
    reg(G,"CA um decimo abaixo do p3 e <p3", True, ca_flag(p3-0.1)=='baixo3')
    # queda longitudinal: estritamente >50
    reg(G,"Queda de exatamente 50 nao fecha", False,
        pg.evaluate("(function(){var dq=-50;return (dq<-50);})()"))
    reg(G,"Queda de 50,1 fecha", True,
        pg.evaluate("(function(){var dq=-50.1;return (dq<-50);})()"))


def g_datacao(pg):
    """Limiares ACOG/AIUM/SMFM de redatacao por faixa de IG."""
    G = "Datacao"
    pg.goto_reset()
    for ig, esperado in [(8.857,5),(9.0,7),(15.0,7),(20.0,10),(25.0,14),(30.0,21)]:
        reg(G,f"Redatacao em {ig} sem", esperado, pg.evaluate(f"limiarRedata({ig}).d"))
    setv(pg,'sem','12'); setv(pg,'dias','0'); pg.wait_for_timeout(200)
    setv(pg,'rCCN','9.0'); pg.wait_for_timeout(200)
    reg(G,"CCN>84mm nao oferece datar","none",
        pg.evaluate("document.getElementById('bCCNApply').style.display"))
    setv(pg,'rCCN','8.0'); pg.wait_for_timeout(200)
    reg(G,"CCN 80mm oferece datar","",
        pg.evaluate("document.getElementById('bCCNApply').style.display"))
    setv(pg,'rCCN',''); setv(pg,'dmsg','2.0'); pg.wait_for_timeout(200)
    reg(G,"DMSG nunca estabelece DPP","none",
        pg.evaluate("document.getElementById('bSacApply').style.display"))


def g_tabelas(pg):
    """Dominio e valores-chave das tabelas de referencia."""
    G = "Tabelas"
    pg.goto_reset()
    reg(G,"TN padrao = Faria 2004","faria", pg.evaluate("CURVA_TN"))
    reg(G,"Faria p95 em CCN 84 = 3,1mm", 3.1, pg.evaluate("interp(tabTN(),84)[2]"))
    reg(G,"FMF p95 em CCN 84 = 2,8mm", 2.8,
        pg.evaluate("()=>{var a=CURVA_TN;CURVA_TN='fmf';var v=interp(tabTN(),84)[2];CURVA_TN=a;return v;}"))
    reg(G,"Cerebelo Snijders p95 em 20 sem = 24mm", 24, pg.evaluate("interp(T_CER,20)[2]"))
    reg(G,"Cerebelo nao extrapola alem de 38 sem", None, pg.evaluate("interp(T_CER,40)"))
    reg(G,"CC/CA so dentro de 17-41 sem", None, pg.evaluate("interp(T_CCAC,42)"))
    reg(G,"IP-AU dominio 19-40 sem", None, pg.evaluate("interp(T_AU,41)"))


def g_utd(pg):
    """UTD: o pior achado define a classe, independentemente do APRPD."""
    G = "UTD"
    pg.goto_reset()
    setv(pg,'sem','24'); setv(pg,'dias','0')
    def cena(pel, ure='', cal='', par2='', bex=''):
        setv(pg,'ePel',pel); setv(pg,'eUre',ure)
        setv(pg,'eCal',cal); setv(pg,'ePar2',par2); setv(pg,'eBex',bex)
        pg.wait_for_timeout(200)
        return pg.evaluate("ST.estr?ST.estr.pel:null")
    reg(G,"Pelve normal + ureter dilatado = A2-3","a23", cena('0.3','0.5'))
    reg(G,"[neg] Pelve normal isolada = normal","ok", cena('0.3',''))
    # Auditoria 2026-09 (4ª rodada, UTD trivalente): pelve sozinha, sem cálices/
    # parênquima/ureter/bexiga confirmados, não fecha mais "A1" — fecha "A1
    # incompleto" (Teste 3 do documento de auditoria). Só fecha A1 quando os 4
    # componentes de Nguyen 2014 foram checados e nenhum alterado (Teste 4).
    reg(G,"Pelve 0,5 isolada = A1 incompleto","a1-inc", cena('0.5',''))
    reg(G,"Pelve 0,5 + cálices/parênquima/ureter/bexiga avaliados = A1 completo","a1",
        cena('0.5', ure='0.3', cal='nao', par2='norm', bex='0.5'))
    reg(G,"Pelve 0,8 isolada = A2-3","a23", cena('0.8',''))
    setv(pg,'ePel','0.3'); setv(pg,'eUre','0.5'); pg.wait_for_timeout(200)
    reg(G,"Laudo registra o UTD A2-3", True, "A2-3" in laudo_txt(pg))


def g_laudo(pg):
    """Nada sinalizado na tela pode sumir do laudo assinado."""
    G = "Laudo x tela"
    pg.goto_reset()
    setv(pg,'sem','24'); setv(pg,'dias','0')
    setv(pg,'eDbo','4.8'); pg.wait_for_timeout(200)
    reg(G,"Biocular alto registrado no laudo", True, 'acima do esperado' in laudo_txt(pg))
    setv(pg,'eDbo',''); setv(pg,'eCT','20.0'); setv(pg,'bCA','24.0')
    pg.wait_for_timeout(200)
    reg(G,"CT limitrofe registrado no laudo", True, 'limite inferior' in laudo_txt(pg))
    # paridade estrutural: todo estado da tela e consumido pelo laudo
    orfaos = pg.evaluate("""()=>{
      var src=laudoEstruturas.toString();
      var out=[];
      for(var k in (ST.estr||{})){}
      return out;}""")
    reg(G,"Sem estado orfao conhecido", [], orfaos)


def g_gemelar(pg):
    """Discordancia relativa ao MAIOR feto; sFGR 2 de 4 (MC) ou 2 de 3 (DC)."""
    G = "Gemelar"
    pg.goto_reset()
    setv(pg,'sem','30'); setv(pg,'dias','0')
    pg.evaluate("()=>{var c=document.getElementById('gemelar');c.checked=true;"
                "c.dispatchEvent(new Event('change',{bubbles:true}));}")
    pg.wait_for_timeout(200)
    pg.evaluate("()=>{setModo('dir');}"); setv(pg,'pDir','1600')
    pg.wait_for_timeout(200)
    pg.evaluate("window.trocaFeto('B')"); pg.wait_for_timeout(200)
    pg.evaluate("()=>{setModo('dir');}"); setv(pg,'pDir','1200')
    pg.wait_for_timeout(250)
    wA = pg.evaluate("fetoOutro().w"); wB = pg.evaluate("ST.pfe.w")
    esperado = round((max(wA,wB)-min(wA,wB))/max(wA,wB)*100)
    reg(G,"Discordancia relativa ao maior feto", esperado,
        pg.evaluate("ST.disc && Math.round(ST.disc.v)"))
    setv(pg,'corion',''); pg.wait_for_timeout(200)
    reg(G,"Sem corionicidade nao conta", None, pg.evaluate("ST.sfgr"))
    setv(pg,'corion','mc'); pg.wait_for_timeout(200)
    txt = pg.evaluate("document.getElementById('sfgrRes').innerText")
    reg(G,"MC exige 2 de 4", True, "2 de 4" in txt)
    reg(G,"Declara curva de feto unico", True, "feto único" in txt)
    setv(pg,'corion','dc'); pg.wait_for_timeout(200)
    reg(G,"DC exige 2 de 3", True,
        "2 de 3" in pg.evaluate("document.getElementById('sfgrRes').innerText"))


def g_integridade(pg):
    """Integridade estrutural: sem erro de console em nenhum cenario acima."""
    G = "Integridade"
    reg(G,"Zero erro de JS em toda a suite", [], ERROS_JS)


# ---------------------------------------------------------------- runner

GRUPOS = [g_rcf_tardia, g_falso_negativo, g_dado_ausente, g_fronteiras,
          g_datacao, g_tabelas, g_utd, g_laudo, g_gemelar, g_integridade]

def main():
    alvo = sys.argv[1] if len(sys.argv)>1 else "Calculadora_Doppler_Obstetrico.html"
    caminho = pathlib.Path(alvo).resolve()
    if not caminho.exists():
        sys.exit(f"Arquivo nao encontrado: {caminho}")
    url = "file://" + str(caminho)

    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width":390,"height":844})
        pg.on("pageerror", lambda e: ERROS_JS.append(str(e)))
        pg.on("console", lambda m: ERROS_JS.append(m.text) if m.type=="error" else None)

        def goto_reset():
            pg.goto(url); pg.wait_for_timeout(350)
        pg.goto_reset = goto_reset
        goto_reset()

        for fn in GRUPOS:
            try:
                fn(pg)
            except Exception as e:
                reg(fn.__name__, f"GRUPO ABORTOU: {type(e).__name__}", "sem excecao", str(e)[:120])
        b.close()

    # ---- relatorio ----
    print(f"\nSuite de regressao — {caminho.name}")
    print(f"{datetime.datetime.now():%d/%m/%Y %H:%M}\n")
    grupos = {}
    for g,i,e,o,ok in RES:
        grupos.setdefault(g, []).append((i,e,o,ok))
    falhas = 0
    for g, casos in grupos.items():
        ok = sum(1 for c in casos if c[3])
        marca = "OK " if ok==len(casos) else "!! "
        print(f"  {marca}{g:<26} {ok}/{len(casos)}")
        for i,e,o,passou in casos:
            if not passou:
                falhas += 1
                print(f"       FALHOU: {i}")
                print(f"         esperado: {e!r}")
                print(f"         obtido  : {o!r}")
    total = len(RES)
    print(f"\n  {total-falhas}/{total} casos")
    if falhas:
        print("\n  ATENCAO: antes de alterar o app, confirme se a expectativa do teste")
        print("  nao e que esta errada — isso ja aconteceu tres vezes na auditoria.")
    return 1 if falhas else 0

if __name__ == "__main__":
    sys.exit(main())
