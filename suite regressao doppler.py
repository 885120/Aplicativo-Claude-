#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SUÍTE DE REGRESSÃO — Calculadora Doppler Obstétrico (linhas R14–R15; validada na R15.2; sentinelas e portão em 15/10/2026)
===================================================================================
Um arquivo só com os testes que validaram as versões R14.24 a R15.2. Cada grupo protege
um defeito REAL que já existiu; nenhum grupo injeta classificação pronta em ST.

COMO USAR
    pip install playwright --break-system-packages
    playwright install chromium webkit
    python3 suite_regressao_doppler.py [index.html] [--webkit | --ambos] [--comparar no_ar.html [--n 300]]

Sem argumento, usa "index.html" no diretório atual. --webkit roda no motor do Safari;
--ambos roda Chromium e depois WebKit. A suíte sobe um servidor HTTP local próprio (porta
livre) só para servir esse arquivo. Saída silenciosa: placar por grupo e detalhe só das
falhas. Código de saída 1 se algo falhar. Tempo: ~6 min por navegador.

PORTÃO DE PUBLICAÇÃO (regra desde 15/10/2026 — nenhuma versão vai ao ar sem os três passos)
    1. python3 suite_regressao_doppler.py index.html --ambos --comparar index_no_ar.html
       → suíte inteira nos dois motores + diferencial de 300 exames (60 gemelares) contra a versão
         que está no ar hoje (baixe o index.html do site/GitHub antes de substituir). Código 2 =
         só diferenças: cada uma tem de ser mudança DECLARADA da versão nova; senão, é regressão.
         --so-comparar roda só o diferencial.
    2. Subir os arquivos (envie primeiro, apague depois).
    3. Checklist de 5 minutos no iPhone ANTES DO PRIMEIRO PACIENTE (README.md, "Antes de publicar");
       falhou, volta ao backup (Vercel → Instant Rollback).

ANTES DE "CONSERTAR" O APP POR CAUSA DE UMA FALHA AQUI
Confirme que a expectativa do teste não é que está desatualizada. Isso já aconteceu
várias vezes (ver CONTEXTO.md). As expectativas usam oráculos independentes do motor:
frações exatas, Decimal e erfc da biblioteca matemática do Python. Os grupos 10–12
conferem também textos de tela e de laudo: se a redação mudar de propósito, atualize
o teste na mesma versão.

GRUPOS
  1 Integridade            HTML carrega, sem erro de JS, IDs únicos, funções-chave presentes
  2 CA — fronteiras        p3/p10/p90/p97: 108 em semanas completas + todas as digitáveis por dia (R14.24)
  3 Ossos longos e DIO     p3 dos ossos; p10/p90 da DIO (R14.24)
  4 Gemelar — CA           fetoOutro() e critério sFGR na igualdade do p10 (R14.24)
  5 F01–F05 (R14.27)       gate de PFE do outro feto; Φ preciso no peso; IG ausente + AEDF/REDF;
                           escopo do outro feto; discordância (categoria e texto)
  6 Exibição da discordância (R14.28)  número exibido nunca cruza o corte; fallback <20%/<25%
  7 Φ preciso × erfc       phiPreciso() embarcado contra math.erfc
  8 Data do exame (R14.29–R14.31)  cartão visível nos dois contextos; dia/mês/ano; data
                           impossível, ano incompleto e futura; dd/mm/aaaa
  9 Rótulo de percentil (R14.32)  rotPfeQ() nunca mostra número do lado errado de p3/p10/
                           p90/p97; espaço fino depois de < e >; "< p10" visível no cartão e no laudo
 10 R14.33                 átrio 9–9,9 mm normal; colo por janela de IG; avisos da PSV ≥ 35 sem;
                           aviso de Hadlock (Roberts/Adu-Bredu); tela de referências
 11 R14.34                 osso nasal e tricúspide só de 11+0 a 13+6; osso nasal do 2º tri só
                           de 20+0 a 24+6; citações FEBRASGO
 12 R14.35                 valor × corte exibidos (PSV, CPR, AU, uterinas); colo como achado materno
 13 R14.36                 via das uterinas: transabdominal pré-selecionada em exame novo; aviso no
                           1º trimestre até o primeiro toque; compatibilidade curva × via × IG mantida
 14 R14.36                 barrinha de consulta sob cada artéria uterina: ao vivo, cor/rótulo pelo p95,
                           some sem via ou com curva incompatível, nunca entra em ST, laudo ou classificação
 15 R14.36                 incisura por quadradinho: marcado = presente; desmarcado com IP do lado = ausente;
                           sem IP = não avaliada; laudo cita só a presença; exames antigos
 16–35                     uma por versão (R14.37 a R15.2): ver o título de cada grupo na saída e o CONTEXTO.md

SENTINELAS (36–40) — não protegem um defeito específico: procuram CLASSES de erro, com sementes fixas.
Nasceram da auditoria de 15/10/2026 (o decimal perdido no gemelar passou anos porque os testes usavam
fill(), que não digita como o dedo). Regra: teste novo que envolva digitação usa keyboard.type.
 36 Digitação real         todo campo numérico visível, tecla a tecla, em 5 contextos; no WebKit, teclado
                           pt-BR com VÍRGULA (como o iPhone); o valor tem de ficar inteiro
 37 Coerência              150 exames aleatórios: sem NaN/undefined/null/[object/Infinity em tela, faixa e
                           laudo; laudo sem erro de formatação; PFE/percentil/IG/título/umbilical iguais
                           no cartão, na faixa, no laudo e na conclusão; gemelar: chips = laudo = conclusão
 38 Ida e volta            100 exames: salvar → Limpar → recuperar devolve laudo, avisos e estado idênticos
 39 Monotonicidade         18 campos varridos em passos finos: a gravidade só piora no sentido clínico certo
 40 Toques aleatórios      220 toques (botões, abas, listas, digitação) com 7 invariantes de interface

NÃO COBRE (ver CONTEXTO.md e o pacote de testes de cada versão): tabelas-verdade de 104 casos,
Clinical Truth v3.1, varredura de 28.080 combinações, consumidores/razões/uterinas/TN das
R14.25–R14.26, worker (sw.js), iPhone/Safari físico, uso offline real, validação clínica.
"""
import math
import sys, os, json, math, random, threading, socket, http.server, functools
from fractions import Fraction
from decimal import Decimal, ROUND_HALF_UP
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sys.exit("Falta o playwright. Rode:\n  pip install playwright --break-system-packages\n  playwright install chromium")

RES={}          # grupo -> {'checks':n,'falhas':[...]}
def grupo(nome,n,f): RES[nome]={'checks':n,'falhas':f}

# ------------------------------------------------------------------ servidor local
def servir(html_path):
    pasta=os.path.dirname(os.path.abspath(html_path)); nome=os.path.basename(html_path)
    class H(http.server.SimpleHTTPRequestHandler):
        def log_message(self,*a): pass
        def translate_path(self,p):
            p=p.split('?')[0]
            if p in ('/',''): p='/'+nome
            return os.path.join(pasta,p.lstrip('/'))
    s=socket.socket(); s.bind(('127.0.0.1',0)); porta=s.getsockname()[1]; s.close()
    srv=http.server.ThreadingHTTPServer(('127.0.0.1',porta),H); threading.Thread(target=srv.serve_forever,daemon=True).start()
    return srv,'http://127.0.0.1:%d/'%porta

# ------------------------------------------------------------------ utilidades
EPS=2.220446049250313e-16
def cmpm(a,b):
    e=16*EPS*max(1,abs(a),abs(b)); return 0 if abs(a-b)<=e else (-1 if a<b else 1)
def discat(v): return 2 if cmpm(v,25)>=0 else (1 if cmpm(v,20)>=0 else 0)
def tofixed(v,p): return str(Decimal(v).quantize(Decimal(1).scaleb(-p),rounding=ROUND_HALF_UP))   # = Number.prototype.toFixed
def disc_oraculo(v):
    c=discat(v)
    for p in (0,2,3,4):
        s=tofixed(v,p)
        if discat(float(s))==c: return (s if p==0 else s.replace('.',','))+'%'
    return '<20%' if c==0 else ('<25%' if c==1 else tofixed(v,0)+'%')
Phi=lambda z:0.5*math.erfc(-z/math.sqrt(2))
def cl(x): return Fraction(str(round(x,1)))      # tabelas transcritas com 1 casa de mm

def reset(pg):
    pg.evaluate("()=>document.getElementById('bRst').click()"); pg.wait_for_timeout(20)

# ------------------------------------------------------------------ 1 integridade
def g_integridade(pg,erros):
    f=[]; n=0
    o=pg.evaluate("""()=>{var ids=[].map.call(document.querySelectorAll('[id]'),function(e){return e.id});var s={},d=[];ids.forEach(function(i){if(s[i])d.push(i);s[i]=1;});
      return {ver:(typeof APP_VERSAO!=='undefined')?APP_VERSAO:null,dup:d.slice(0,5),fn:['run','cmpMedida','phiPreciso','pctPesoFromZ','discCat','discFmt','fetoOutro','seletiva','discordancia','rotP','rotPfeQ','setDataExameISO','dtHojeSync','casasPar','fxVal','fxCorte','momTxt','achadosTxt','viaUtAviso','utLadoBar','incSt','incValor','chkParte','chkLn','textoConclusao','ancFixa','nivelaDuo','compValido','compPacTxt','gemVisual','gemQuadro','plEstadoAtual','laudoPlacenta','abasTipo','tituloExame','temDoppler','temMorfo'].filter(function(k){return typeof window[k]!=='function'})};}""")
    n+=3
    if not o['ver']: f.append(('APP_VERSAO ausente',))
    if o['dup']: f.append(('IDs duplicados',o['dup']))
    if o['fn']: f.append(('funções ausentes',o['fn']))
    n+=1
    if erros: f.append(('erros de JavaScript ao carregar',erros[:3]))
    grupo('1 Integridade (%s)'%o['ver'],n,f)

# ------------------------------------------------------------------ 2 CA fronteiras
def g_ca(pg):
    T=pg.evaluate("()=>({t:T_CA,p10:T_CA_P10,p90:T_CA_P90})")
    def col(tag,w):
        if tag=='p3': return cl(T['t'][str(w)][0])
        if tag=='p97': return cl(T['t'][str(w)][2])
        return cl(T[tag][str(w)])
    def cut(tag,w,d):
        c=col(tag,w); return c if d==0 else c+(col(tag,w+1)-c)*Fraction(d,7)
    def run1(w,d,cm):
        reset(pg); pg.evaluate("([w,d,cm])=>{AUTO_BIO=false;$('sem').value=w;$('dias').value=d;$('bCA').value=cm;run();}",[w,d,cm])
        return pg.evaluate("()=>({f:ST.ca?ST.ca.flag:null,a:ST.ca?ST.ca.acima90:null,l:$('ldT').textContent})")
    def chk(tag,off,r):
        below=off<0; above=off>0; bad=[]
        if tag=='p3' and (r['f']=='baixo3')!=below: bad.append('flag baixo3')
        if tag=='p3' and (('feto com restrição de crescimento segundo critérios' in r['l'])!=below): bad.append('conclusão RCF por CA<p3')
        if tag=='p10' and (r['f'] in('baixo3','baixo10'))!=below: bad.append('flag <p10')
        if tag=='p10' and (('circunferência abdominal abaixo do percentil 10' in r['l'])!=below): bad.append('conclusão CA<p10')
        if tag=='p90' and bool(r['a'])!=above: bad.append('acima90')
        if tag=='p90' and (('grande para a idade gestacional' in r['l'])!=above): bad.append('conclusão grande')
        if tag=='p97' and (r['f']=='alto')!=above: bad.append('flag alto')
        return bad
    for nome,ages in (('2a CA — semanas completas',[(w,0) for w in range(14,41)]),('2b CA — fronteiras decimais (todos os dias)',[divmod(x,7) for x in range(98,281)])):
        f=[]; n=0; fr=0
        for w,d in ages:
            for tag in ('p3','p10','p90','p97'):
                c=cut(tag,w,d)
                if (c*10).denominator!=1: continue
                fr+=1; k=int(c*10)
                for off in (-1,0,1):
                    cm='%.2f'%((k+off)/100.0); bad=chk(tag,off,run1(w,d,cm)); n+=1
                    if bad: f.append(('%d+%d'%(w,d),tag,cm,bad))
        grupo('%s (%d fronteiras)'%(nome,fr),n,f)

# ------------------------------------------------------------------ 3 ossos e DIO
def g_ossos_dio(pg):
    FT={'eUme':'T_UME','eRad':'T_RAD','eUln':'T_ULN','eTib':'T_TIB','eFib':'T_FIB'}; f=[]; n=0
    tabs=pg.evaluate("(ns)=>{var o={};ns.forEach(function(k){o[k]=window[k]});return o;}",list(FT.values()))
    for fld,tn in FT.items():
        for w in range(14,41):
            row=tabs[tn].get(str(w))
            if not row: continue
            k=int(Fraction(str(round(row[0],1)))*10)
            for off in (-1,0,1):
                cm='%.2f'%((k+off)/100.0); reset(pg)
                pg.evaluate("([f,w,cm])=>{AUTO_BIO=false;$('sem').value=w;$('dias').value=0;$(f).value=cm;run();}",[fld,w,cm])
                r=pg.evaluate("(f)=>({f:ST.ossosQ&&ST.ossosQ[f]?ST.ossosQ[f].flag:null,l:$('ldT').textContent})",fld); n+=1; below=off<0
                if ((r['f']=='baixo')!=below) or (('Osso longo abaixo do percentil 3' in r['l'])!=below): f.append((fld,w,cm,r['f']))
    T=pg.evaluate("()=>T_DIO")
    for w in range(15,41):
        row=T.get(str(w))
        if not row: continue
        for idx,tag in ((0,'p10'),(2,'p90')):
            c=Fraction(str(row[idx]))
            if (c*10).denominator!=1: continue
            k=int(c*10)
            for off in (-1,0,1):
                cm='%.2f'%((k+off)/100.0); reset(pg)
                pg.evaluate("([w,cm])=>{AUTO_BIO=false;$('sem').value=w;$('dias').value=0;$('eDio').value=cm;run();}",[w,cm])
                fl=pg.evaluate("()=>ST.estr?ST.estr.dio:null"); n+=1
                esp=('baixo' if (tag=='p10' and off<0) else ('alto' if (tag=='p90' and off>0) else 'ok'))
                if fl!=esp: f.append(('DIO',w,tag,cm,fl,esp))
    grupo('3 Ossos longos (p3) e DIO (p10/p90)',n,f)

# ------------------------------------------------------------------ 4 gemelar CA
def g_gemelar_ca(pg):
    JS="""x=>{setModo('bio');$('sem').value=x.w;$('dias').value=x.d;$('bCA').value=x.inp;caPercentil();FETO='A';DADOS={A:null,B:{modo:'bio',campos:{bCA:x.inp},chk:{}}};const other=fetoOutro();const original=fetoOutro;window.fetoOutro=function(){return{w:2000,q:50,modo:'bio',caAvaliada:true,caAbaixo10:false,auAvaliada:true,auAlto:false}};ST.gemelar={};ST.pfe={w:1500,q:9};ST.disc={formalComparavel:true,v:0};ST.au=null;$('corion').value='mc';seletiva();const criteria=ST.sfgr.crit;window.fetoOutro=original;return{other:other.caAbaixo10,criteria:criteria}}"""
    pg.evaluate("()=>{AUTO_BIO=false;}"); T=pg.evaluate("()=>T_CA_P10"); f=[]; n=0
    for day in range(98,281):
        w,d=divmod(day,7); lo=cl(T[str(w)]); c=lo if not d else lo+(cl(T[str(w+1)])-lo)*Fraction(d,7)
        if (c*10).denominator!=1: continue
        k=int(c*10)
        for off in (-1,0,1):
            inp='%.2f'%((k+off)/100.0); o=pg.evaluate(JS,{'w':w,'d':d,'inp':inp}); n+=2; below=off<0
            crit=any(t.startswith('CA d') and 'abaixo do p10' in t for t in o['criteria'])   # R14.46: critério nomeia o feto
            if o['other']!=below: f.append(('fetoOutro','%d+%d'%(w,d),inp))
            if crit!=below: f.append(('seletiva','%d+%d'%(w,d),inp))
    grupo('4 Gemelar — CA do outro feto e sFGR',n,f)

# ------------------------------------------------------------------ helpers de interface (gemelar)
SNAP="()=>({feto:FETO,pfe:ST.pfe,sfgr:ST.sfgr,disc:ST.disc,o:(function(){var o=fetoOutro();return o?{w:o.w,q:o.q}:null})(),rep:$('ldT').textContent})"
def gem(pg,ig,dias,corion,curva,wA,wB):
    pg.locator('#bRst').click(); abaDat(pg); pg.locator('#sem').fill(str(ig)); pg.locator('#dias').fill(str(dias))
    pg.evaluate("c=>{CURVA=c;}",curva); abaMed(pg); pg.locator('#mDir').click(); pg.locator('#pDir').fill(str(wA)); gemOn(pg,corion)
    pg.locator('#fB').click(); pg.locator('#pDir').fill(str(wB)); pg.locator('#pDir').blur()
    sB=pg.evaluate(SNAP); pg.locator('#fA').click(); sA=pg.evaluate(SNAP); return sA,sB
def abaDat(pg):
    pg.evaluate("()=>{var t=document.querySelector('.tab[data-p=\"p0\"]'); if(t&&t.className.indexOf('on')<0) t.click();}")
def gemOn(pg,corion=None):   # R15.0: "Gestação múltipla" e a corionicidade ficam no cartão Gestação da Datação
    abaDat(pg); pg.locator('#gemelar').check()
    if corion is not None: pg.locator('#corion').select_option(corion)
    abaMed(pg)
def abaMed(pg):   # R14.57/R15.0: ir para Medidas é tocar na aba (o botão Direto só põe o cursor na IG)
    pg.evaluate("()=>{var t=[].find.call(document.querySelectorAll('.tab'),function(x){return x.dataset.p==='p1'&&!x.hidden}); if(t&&t.className.indexOf('on')<0) t.click();}")
def setdiast(pg,di):
    pg.evaluate("v=>{var e=document.getElementById('diast');e.value=v;e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));run();}",di)
def linhas(rep): return [x.strip() for x in rep.split('\n') if x.strip().startswith('Discordância de peso entre os fetos:')]

# ------------------------------------------------------------------ 5 F01–F05 (R14.27)
def g_r27(pg):
    # F01 — PFE inválido do outro feto não pode chegar ao classificador
    f=[]; n=0
    for corion in ('mc','dc',''):
        for curva in ('hadlock','ig21'):
            for ig in (22,30,36):
                for w in (1,49,50,7000,7001,9000):
                    wA=pg.evaluate("([c,ig])=>{CURVA=c;return Math.round(medAtivo(ig));}",[curva,ig])
                    sA,sB=gem(pg,ig,0,corion,curva,wA,w); n+=1; inval=(w<50 or w>7000)
                    if inval:
                        if sA['o']['w'] is not None: f.append(('outro inválido exposto',corion,curva,ig,w))
                        if sB['pfe'] is not None: f.append(('B aceitou PFE inválido',corion,curva,ig,w))
                        if sA['sfgr'] is not None or sB['sfgr'] is not None: f.append(('sFGR com PFE inválido',corion,curva,ig,w))
                        if sA['disc'] is not None: f.append(('discordância com PFE inválido',corion,curva,ig,w))
                    elif sA['o']['w']!=float(w): f.append(('PFE válido do outro feto não chegou',corion,curva,ig,w))
    for corion in ('mc','dc'):
        sA,sB=gem(pg,30,0,corion,'hadlock',600,49); n+=1
        for lado,s in (('A',sA),('B',sB)):
            if not (s['sfgr'] and s['sfgr'].get('cls')=='sfgr-solitario-pendente'): f.append(('<p3 válido + outro inválido deve ficar pendente',corion,lado))
    grupo('5a F01 gate de PFE do outro feto',n,f)
    # F02 — percentil de peso do lado certo do corte (Φ preciso), testemunhos e queda longitudinal
    f=[]; n=0
    r=pg.evaluate("""()=>{var cuts=[[Z_P3,3],[Z_P10,10],[Z_P90,90],[Z_P97,97]],bad=0,n=0;
      for(var c=0;c<cuts.length;c++){var Z=cuts[c][0],Q=cuts[c][1];for(var s=-1;s<=1;s+=2){for(var k=0;k<=300;k++){var off=s*Math.pow(10,-9+k*(3.5/300));
        var q=pctPesoFromZ(Z+off);n++;if(off<0? !(q<Q) : !(q>Q)) bad++;}}}return {n:n,bad:bad};}""")
    n+=r['n']
    if r['bad']: f.append(('vizinhanças dos 4 cortes: q do lado errado',r['bad']))
    for nome,w,d,dbp,cc,ca,fl,zk,cut in (('p3 30+3',30,3,'7.50','27.86','25.06','5.20','Z_P3',3),('p10 28+5',28,5,'8.00','27.76','22.69','5.17','Z_P10',10),('p90 36+0',36,0,'7.50','32.68','33.22','8.45','Z_P90',90)):
        pg.locator('#bRst').click(); abaDat(pg); pg.locator('#sem').fill(str(w)); pg.locator('#dias').fill(str(d)); abaMed(pg); pg.locator('#mBio').click()
        for i,v in (('bDBP',dbp),('bCC',cc),('bCA',ca),('bFL',fl)): pg.locator('#'+i).fill(v); pg.locator('#'+i).blur()
        o=pg.evaluate("(zk)=>{var g=getGA();return {q:ST.pfe.q,z:(Math.log(ST.pfe.w)-Math.log(medP(g)))/HADLOCK_SD_LN,zc:window[zk]}}",zk); n+=1
        if (o['q']>cut)!=(o['z']>o['zc']): f.append(('testemunho '+nome,o))
    L=pg.evaluate("()=>{var wn=hadlock4(9.00,28.45,29.94,6.55);return {wn:wn,dq:pctAtivo(wn,34)-pctAtivo(2000,31)};}")
    z=lambda w,g:(math.log(w)-(0.578+0.332*g-0.00354*g*g))/0.12
    dq=100*(Phi(z(L['wn'],34))-Phi(z(2000,31))); n+=1
    if abs(L['dq']-dq)>1e-9 or (L['dq']<-50)!=(dq<-50): f.append(('queda longitudinal',L['dq'],dq))
    grupo('5b F02 percentil de peso (Φ preciso)',n,f)
    # F03 — IG ausente/inválida + AEDF/REDF não presume forma tardia
    f=[]; n=0
    for sem in ('','3','50','46'):
        for di in ('zero','rev'):
            pg.locator('#bRst').click(); abaDat(pg); pg.locator('#sem').fill(sem); pg.locator('#dias').fill('0'); abaMed(pg); pg.locator('#mDir').click(); pg.locator('#pDir').fill('1800'); setdiast(pg,di)
            o=pg.evaluate("()=>({ga:getGA(),cls:ST.sint?ST.sint.cls:null,txt:document.body.innerText,card:$('sintRes').textContent.toLowerCase()})"); n+=1
            if o['ga'] is not None: continue
            if o['cls']!='aedf-ig-desconhecida' or 'informe a IG' not in o['txt'] or 'partir de 32' in o['card'] or 'forma precoce' in o['card']: f.append(('IG desconhecida',repr(sem),di,o['cls']))
            if ('Diástole '+('reversa' if di=='rev' else 'ausente')+' na umbilical') not in o['txt']: f.append(('achado de gravidade sumiu',repr(sem),di))
    for di in ('zero','rev'):
        pg.locator('#bRst').click(); abaDat(pg); pg.locator('#sem').fill('34'); pg.locator('#dias').fill('0'); abaMed(pg); pg.locator('#mDir').click(); setdiast(pg,di)
        o=pg.evaluate("()=>({cls:ST.sint?ST.sint.cls:null,txt:document.body.innerText})"); n+=1
        if o['cls']!='aedf-tardio' or 'A partir de 32 semanas este achado' not in o['txt']: f.append(('IG ≥32 válida mudou',di,o['cls']))
    grupo('5c F03 IG ausente/inválida + AEDF/REDF',n,f)
    # F04 — confirmação da AU do outro feto no escopo dele, em qualquer modo
    f=[]; n=0
    for mode in ('bio','dir'):
        for ac,bc in ((True,False),(False,True),(False,False),(True,True)):
            pg.evaluate("""x=>{$('bRst').click();AUTO_BIO=false;IGSRC='usant';$('sem').value=30;$('gemelar').checked=true;setModo('dir');$('pDir').value=1800;PLC={A:{auip:x.ac?[3.9]:[]},B:{auip:x.bc?[3.9]:[]}};DADOS.B={modo:x.mode,campos:{pDir:'1800',bDBP:'7',bCC:'26',bCA:'22',bFL:'5.2',auip:'3.9'},chk:{}};run();}""",{'mode':mode,'ac':ac,'bc':bc})
            a=pg.evaluate("()=>fetoOutro().auAvaliada"); pg.evaluate("()=>trocaFeto('B')"); b=pg.evaluate("()=>ST.au"); n+=1
            if a!=(b is not None): f.append(('escopo da AU',mode,ac,bc))
    grupo('5d F04 escopo do outro feto',n,f)

# ------------------------------------------------------------------ 6 exibição da discordância (R14.28)
def g_r28(pg):
    GET="()=>({v:ST.disc.v,card:$('discRes').textContent.replace(/\\s+/g,' '),rep:$('ldT').textContent})"
    f=[]; n=0; A=('7.80','28.50','26.00','5.80')
    for nome,B,show,catx,cc in (('B1',('7.00','26.00','22.62','5.96'),'19,997%','dentro do esperado',0),('B2',('7.00','26.00','22.00','5.81'),'24,998%','risco',1)):
        res={}
        for ori in ('A','B'):
            pg.locator('#bRst').click(); abaDat(pg); pg.locator('#sem').fill('30'); pg.locator('#dias').fill('0'); abaMed(pg); pg.locator('#mBio').click()
            for i,v in zip(('bDBP','bCC','bCA','bFL'),A): pg.locator('#'+i).fill(v); pg.locator('#'+i).blur()
            gemOn(pg,'dc'); pg.locator('#fB').click(); abaMed(pg); pg.locator('#mBio').click()
            for i,v in zip(('bDBP','bCC','bCA','bFL'),B): pg.locator('#'+i).fill(v); pg.locator('#'+i).blur()
            pg.locator('#f'+ori).click(); o=pg.evaluate(GET); res[ori]=o; n+=1
            if show not in o['card'] or catx not in o['card']: f.append(('cartão',nome,ori,o['card'][:80]))
            L=linhas(o['rep']); gx='Discordância de peso entre os fetos: '+show+'.'
            if (cc==0 and L!=[gx]) or (cc==1 and (gx not in L or len(L)!=2)): f.append(('corpo/guia',nome,ori,L))
        if res['A']['card']!=res['B']['card'] or linhas(res['A']['rep'])!=linhas(res['B']['rep']): f.append(('assimetria A/B',nome))
    for a,bw in ((2000,1601),(2000,1600),(2000,1599),(2000,1501),(2000,1500),(2000,1499),(1280,960),(2000,1700),(1000,801),(1000,800),(1000,751),(1000,750),(5000,'4000.0001'),(5000,'3750.0001')):
        pg.locator('#bRst').click(); abaDat(pg); pg.locator('#sem').fill('30'); pg.locator('#dias').fill('0'); abaMed(pg); pg.locator('#mDir').click(); pg.locator('#pDir').fill(str(a)); gemOn(pg,'dc')
        pg.locator('#fB').click(); pg.locator('#pDir').fill(str(bw)); pg.locator('#pDir').blur(); res={}
        for ori in ('A','B'):
            pg.locator('#f'+ori).click(); res[ori]=pg.evaluate(GET); n+=1
        v=(float(a)-float(bw))/float(a)*100; ex=disc_oraculo(v); o=res['A']; gx='Discordância de peso entre os fetos: '+ex+'.'; L=linhas(o['rep'])
        if ex not in o['card']: f.append(('cartão',a,bw,ex,o['card'][:70]))
        # R14.46: com a discordância já citada entre os critérios de restrição seletiva, a conclusão não a repete
        if discat(v)>=1 and gx not in L and ('discordância de peso de '+ex) not in o['rep']: f.append(('guia',a,bw,ex,L))
        if discat(v)==0 and L!=[gx]: f.append(('corpo',a,bw,ex,L))
        if res['A']['card']!=res['B']['card'] or linhas(res['A']['rep'])!=linhas(res['B']['rep']): f.append(('assimetria A/B',a,bw))
    vals=[]
    for c in (20.0,25.0):
        for e in (0.5,0.1,0.05,0.01,0.006,0.005,0.0049,0.003,0.001,5e-4,1e-4,5e-5,4e-5,1e-5,1e-6,1e-9,1e-12,1e-14,1e-15,0): vals+=[c-e,c+e]
    random.seed(28)
    for c in (20.0,25.0): vals+=[random.uniform(c-0.02,c+0.02) for _ in range(8000)]
    got=pg.evaluate("(vs)=>vs.map(function(v){return discFmt(v)})",vals); n+=len(vals)
    for v,g in zip(vals,got):
        if g!=disc_oraculo(v): f.append(('discFmt',repr(v),g,disc_oraculo(v)))
    grupo('6 Exibição da discordância (número nunca cruza o corte)',n,f)

# ------------------------------------------------------------------ 7 Φ preciso × erfc
def g_phi(pg):
    random.seed(7); zs=[i/500.0 for i in range(-4000,4001)]+[random.uniform(-6,6) for _ in range(20000)]
    v=pg.evaluate("(zs)=>zs.map(function(z){return phiPreciso(z)})",zs); ma=0.0; f=[]
    for z,x in zip(zs,v): ma=max(ma,abs(x-Phi(z)))
    if ma>=2e-15: f.append(('erro absoluto máximo',ma))
    grupo('7 Φ preciso × erfc (erro máx %.1e)'%ma,len(zs),f)

# ------------------------------------------------------------------ 8 data do exame (R14.29–R14.31)
def g_data(pg):
    F=[]; C=[0]
    def ok(c,m):
        C[0]+=1
        if not c: F.append(m)
    def digita(d,m,y):
        for i,v in (('dtHojeD',d),('dtHojeM',m),('dtHojeY',y)): pg.fill('#'+i,v)
        pg.wait_for_timeout(30)
        return pg.evaluate("()=>({iso:$('dtHoje').value, av:$('dtHojeAviso').style.display==='none'?'':$('dtHojeAviso').textContent})")
    for ctx in ('A','B'):
        v=pg.evaluate("(c)=>{setCtx(c);var e=$('dataExameCard');return !!(e&&e.offsetParent!==null);}",ctx)
        ok(v,('cartão da data do exame invisível no contexto',ctx))
    pg.evaluate("()=>setCtx('A')")
    ok(pg.evaluate("()=>$('dtHoje').type==='hidden' && $('dtHojeD').type==='number'"),('campos da data não são dia/mês/ano numéricos',))
    for d,m,y,iso,aviso in (('5','10','2026','2026-10-05',''),('29','2','2024','2024-02-29',''),('29','2','2026','','Data inválida'),
                            ('31','4','2026','','Data inválida'),('5','10','26','','4 dígitos'),('','10','2026','','Informe dia, mês e ano'),
                            ('5','10','2099','2099-10-05','futuro')):
        r=digita(d,m,y)
        ok(r['iso']==iso,('ISO da data do exame',d,m,y,r['iso']))
        ok((aviso in r['av']) if aviso else r['av']=='',('aviso da data',d,m,y,r['av'][:60]))
    r=pg.evaluate("()=>{setDataExameISO('2026-03-07');return [$('dtHojeD').value,$('dtHojeM').value,$('dtHojeY').value,dataExtenso('2026-03-07')];}")
    ok(r[:3]==['07','03','2026'],('setDataExameISO não preenche os três campos',r))
    ok(r[3]=='07/03/2026',('data exibida fora de dd/mm/aaaa',r[3]))
    grupo('8 Data do exame (R14.29–R14.31)',C[0],F)

# ------------------------------------------------------------------ 9 rótulo de percentil (R14.32)
def g_rotulo(pg):
    """Contrato: o rótulo exibido nunca contradiz a classe. Classe abaixo de um corte nunca
    mostra número >= corte; acima nunca mostra <= corte; '<'/'>' sempre seguidos de U+202F."""
    F=[]; C=[0]
    def ok(c,m):
        C[0]+=1
        if not c: F.append(m)
    qs=[c+k/1000.0 for c in (1,3,10,90,97,99) for k in range(-600,601,3)]+[0.2,0.5,50.0,99.6]
    R=pg.evaluate("(qs)=>qs.map(function(q){return rotPfeQ(q).p})",qs)
    for q,p in zip(qs,R):
        if p[0] in '<>':
            ok(p[1]==' ',('sem espaço fino depois de < ou >',q,p))
            c=float(p[2:].lstrip('p'))
            ok((q<c) if p[0]=='<' else (q>c),('lado exibido errado',q,p))
            continue
        x=float(p[1:].replace(',','.'))
        for c in (3,10,90,97):
            if q<c: ok(x<c,('número exibido cruza o corte por baixo',q,p,c))
            if q>c: ok(x>c,('número exibido cruza o corte por cima',q,p,c))
    # na tela: peso com q entre 9,95 e 10 aparece como "< p10" e o texto não some (innerHTML)
    import statistics
    mu=0.578+0.332*32-0.00354*32*32
    w=next(w for w in range(1000,3000) if 9.95<statistics.NormalDist().cdf((math.log(w)-mu)/0.12)*100<10)
    r=pg.evaluate("""(w)=>{$('bRst').click();$('sem').value=32;$('dias').value=0;IGSRC='mao';setModo('dir');$('pDir').value=String(w);run();
       return {q:ST.pfe?ST.pfe.q:null, tela:$('pRes').innerText, laudo:$('ldT').textContent};}""",w)
    ok(r['q'] is not None and r['q']<10,('peso de teste não ficou abaixo de p10',w,r['q']))
    ok('< p10' in r['tela'],('cartão do peso não mostra < p10',w,r['tela'][:120]))
    ok('(< p10)' in r['laudo'],('laudo não mostra (< p10)',w,r['laudo'][:200]))
    grupo('9 Rótulo de percentil nunca contradiz a classe (R14.32)',C[0],F)

# ------------------------------------------------------------------ 10 R14.33
JS_SET="""([g,d,fields])=>{$('bRst').click(); if(g===null){$('sem').value='';$('dias').value='';} else {$('sem').value=g;$('dias').value=d;} IGSRC='mao';
 for(var k in fields){$(k).value=fields[k];} run();
 return {E:JSON.parse(JSON.stringify(ST.estr||{})), psv:ST.psv?JSON.parse(JSON.stringify(ST.psv)):null,
  atr:($('eAtrRes')||{textContent:''}).textContent, colo:($('eColoRes')||{textContent:''}).textContent,
  psvR:($('psvRes')||{textContent:''}).textContent, chk:($('chk')||{textContent:''}).textContent,
  ld:($('ldT')||{textContent:''}).textContent, dif:document.body.innerText.indexOf('Comprimento cervical reduzido')>=0};}"""
def g_r33(pg):
    F=[]; C=[0]; nm=''
    def ok(c,m):
        C[0]+=1
        if not c: F.append(m)
    S=lambda g,d,f: pg.evaluate(JS_SET,[g,d,f])
    # --- átrio
    for cm,exp,sev in (('0.85','ok',None),('0.90','ok',None),('0.95','ok',None),('0.99','ok',None),('1.00','alt','leve'),('1.29','alt','leve'),('1.30','alt','moderada'),('1.50','alt','moderada'),('1.51','grave','grave')):
        r=S(22,0,{'eAtr':cm})
        ok(r['E'].get('atr')==exp,(nm,'atr estado',cm,r['E'].get('atr')))
        if sev: ok(r['E'].get('atrSev')==sev,(nm,'atr sev',cm,r['E'].get('atrSev')))
        ok('3–4 semanas' not in r['atr'] and 'limite superior' not in r['atr'],(nm,'atr texto antigo',cm))
        ok('limite superior' not in r['ld'],(nm,'atr laudo antigo',cm))
        if exp=='ok' and cm>='0.90': ok('próximo do limite' in r['atr'] and 'Normal' in r['atr'],(nm,'atr texto novo',cm,r['atr'][:80]))
        if exp!='ok': ok('ventriculomegalia' in r['ld'],(nm,'atr laudo vm',cm))
    # --- colo
    for g,d,cm,exp,lbl in ((20,0,'1.00','curto','Colo curto'),(20,0,'1.50','curto','Colo curto'),(20,0,'1.60','curto','Colo curto'),(20,0,'2.50','curto','Colo curto'),
                          (20,0,'2.60','lim','Limítrofe'),(20,0,'3.00','lim','Limítrofe'),(20,0,'3.10','ok','Adequado'),
                          (23,6,'2.00','curto','Colo curto'),(24,0,'2.00','red','Comprimento cervical reduzido'),(28,0,'1.00','red','Comprimento cervical reduzido'),
                          (28,0,'2.50','red','Comprimento cervical reduzido'),(28,0,'2.60','ok','Adequado'),(28,0,'3.00','ok','Adequado'),(None,None,'2.00','red','Comprimento cervical reduzido')):
        r=S(g,d,{'eColo':cm})
        ok(r['E'].get('colo')==exp,(nm,'colo estado',g,d,cm,r['E'].get('colo')))
        ok(lbl in r['colo'],(nm,'colo rótulo',g,d,cm,r['colo'][:90]))
        ok('muito curto' not in r['colo'].lower() and 'muito curto' not in r['ld'],(nm,'colo muito curto ainda aparece',g,cm))
        if exp=='red':
            if g is not None: ok('comprimento cervical reduzido' in r['ld'],(nm,'colo laudo red',g,cm))
            ok(('Sem IG' in r['colo'])==(g is None),(nm,'colo texto sem IG',g,cm))
            ok(('sinal do lama' in r['colo'])==(float(cm)<=1.5),(nm,'colo checar lama',g,cm))
        if exp=='curto': ok('colo curto' in r['ld'],(nm,'colo laudo curto',g,cm)); ok(('sinal do lama' in r['colo'])==(float(cm)<=1.5),(nm,'colo lama janela',cm))
    # --- PSV
    med=lambda g: pg.evaluate("(g)=>medPSV(g)",g)
    for g,mom,expflag,need,forbid in ((36,1.0,'ok',['não exclui anemia'],['transfusão']),(35,1.0,'ok',['não exclui anemia'],[]),(34,1.0,'ok',[],['não exclui anemia']),
                                     (36,1.6,'alto',['transfusão intrauterina'],['não exclui anemia']),(36,1.35,'lim',['transfusão intrauterina'],['não exclui anemia']),(30,1.6,'alto',[],['transfusão intrauterina','não exclui anemia'])):
        v=round(mom*med(g),1)
        r=S(g,0,{'psv':str(v)})
        ok(r['psv'] and r['psv'].get('flag')==expflag,(nm,'psv flag',g,mom,r['psv']))
        for s in need: ok(s in r['chk'],(nm,'psv aviso falta',g,mom,s))
        for s in forbid: ok(s not in r['chk'],(nm,'psv aviso indevido',g,mom,s))
        if expflag=='lim': ok('critério de atenção deste app' in r['psvR'],(nm,'psv lim nota'))
    r=S(41,0,{'psv':'60'})
    ok(r['psv'] and r['psv'].get('flag')=='fora-faixa' and 'validação diagnóstica do estudo original' in r['psvR'],(nm,'psv fora-faixa texto',r['psvR'][:120]))
    # --- aviso Hadlock (peso baixo)
    r=pg.evaluate("""()=>{$('bRst').click();$('sem').value=32;$('dias').value=0;IGSRC='mao';setModo('dir');$('pDir').value='1450';run();return {q:ST.pfe?ST.pfe.q:null,chk:$('chk').textContent};}""")
    ok(r['q'] is not None and r['q']<20,(nm,'hadlock q',r['q']))
    ok('Adu-Bredu' in r['chk'] and '5,1%' in r['chk'] and 'das pacientes' in r['chk'] and 'p16' not in r['chk'] and 'C0-A' in r['chk'],(nm,'hadlock aviso',r['chk'][:200]))
    # --- referências, versão, textos estáticos
    t=pg.evaluate("()=>({ref:$('refOv').innerText, ver:$('verFt').textContent, html:document.documentElement.outerHTML})")
    for s in ('Hadlock et al., AJOG 1985;151:333-337','Adu-Bredu','Table S1','NHS England','Salomon et al., UOG 2019;53:715-723','validação diagnóstica entre 15 e 36 semanas','Maisonneuve','10.61622/0100-7254536202507','Malinger','SMFM Consult Series #45','Colo uterino','Coutinho'):
        ok(s in t['ref'],(nm,'ref falta',s))
    ok('Protocolo nº 43' not in t['ref'],(nm,'ref nº43 ainda'))
    ok('apoiada na ISUOG' in t['html'],(nm,'21 dias ISUOG'))
    grupo('10 Átrio, colo, PSV, Hadlock, referências (R14.33)',C[0],F)

# ------------------------------------------------------------------ 11 R14.34
R1="""([s,d,on,tr,dur])=>{$('bRst').click();$('sem').value=s;$('dias').value=d;IGSRC='mao';run();
 $('rON').value=on; $('rTR').value=tr; $('rTRdur').value=dur; run();
 var L=($('ldT')||{textContent:''}).textContent;
 return {on:ST.on, tr:ST.tr, onR:$('rONRes').textContent, trR:$('rTRRes').textContent, ldON:/osso nasal ausente/i.test(L), ldTR:/regurgitação tricúspide presente/i.test(L), ldConc:/marcadores ultrassonográficos alterados/i.test(L)};}"""
R2="""([s,d,on,pfn])=>{$('bRst').click();$('sem').value=s;$('dias').value=d;IGSRC='mao';$('eON').value=on;$('ePFN').value=pfn;run();
 var L=($('ldT')||{textContent:''}).textContent;
 return {on:ST.estr.on, card:$('eONRes').textContent, ld:/osso nasal/i.test(L)};}"""
def g_r34(pg):
    F=[]; C=[0]; nm=''
    def ok(c,m):
        C[0]+=1
        if not c: F.append(m)
    # E1
    for s,d,dentro in ((8,0,False),(9,3,False),(10,0,False),(10,6,False),(11,0,True),(12,0,True),(13,6,True)):
        r=pg.evaluate(R1,[s,d,'aus','70','maior'])
        if dentro:
            ok(r['on'] and r['on']['flag']=='alt',(nm,'E1 on dentro',s,d,r['on']))
            ok(r['tr'] and r['tr']['flag']=='alt',(nm,'E1 tr dentro',s,d,r['tr']))
            ok(r['ldON'] and r['ldTR'] and r['ldConc'],(nm,'E1 laudo dentro',s,d))
        else:
            ok(r['on'] is None and r['tr'] is None,(nm,'E1 estado fora',s,d,r['on'],r['tr']))
            ok('Fora da janela' in r['onR'] and 'Fora da janela' in r['trR'],(nm,'E1 cartão fora',s,d))
            ok(not r['ldON'] and not r['ldTR'] and not r['ldConc'],(nm,'E1 laudo fora',s,d))
        r=pg.evaluate(R1,[s,d,'pres','40','menor'])
        if dentro: ok(r['on'] and r['on']['flag']=='ok' and r['tr'] and r['tr']['flag']=='ok',(nm,'E1 normais dentro',s,d))
        else: ok(r['on'] is None and r['tr'] is None,(nm,'E1 normais fora',s,d))
    # E2
    for s,d,on,pfn,exp in ((17,0,'0.38','',None),(19,6,'0.38','',None),(20,0,'0.38','','alt'),(22,0,'0.38','','alt'),(24,6,'0.38','','alt'),(25,0,'0.38','',None),(30,0,'0.38','',None),
                           (22,0,'0.50','','ok'),(22,0,'0.50','0.45','alt'),(17,0,'0.50','0.45',None),(20,0,'0.45','','ok')):
        r=pg.evaluate(R2,[s,d,on,pfn])
        ok(r['on']==exp,(nm,'E2 estado',s,d,on,pfn,r['on']))
        if exp is None: ok('Fora da janela' in r['card'] and not r['ld'],(nm,'E2 fora texto/laudo',s,d,r['card'][:60]))
        if exp=='alt': ok(r['ld'],(nm,'E2 laudo alt',s,d))
    # D1/D2
    t=pg.evaluate("()=>({ref:$('refOv').innerText, ver:$('verFt').textContent})")
    for s in ('O app não sugere intervalos de seguimento','o app não automatiza a vigilância','Ultrassonografia morfológica do segundo trimestre (Protocolo de Obstetrícia nº 43, 2025; antes nº 78, 2018)','classificados só entre 11+0 e 13+6'):
        ok(s in t['ref'],(nm,'ref',s))
    ok('Protocolo 78 (Femina, 2025)' not in t['ref'],(nm,'ref 78 ainda'))
    r=pg.evaluate("()=>{$('bRst').click();$('sem').value=30;$('dias').value=0;IGSRC='mao';$('mbv').value='5';$('ila').value='12';run();return document.body.textContent}")
    ok('Ultrassonografia obstétrica do 3º trimestre (2025), Tabela 1' in r,(nm,'líquido citação'))
    grupo('11 Janelas de IG dos marcadores (R14.34)',C[0],F)

# ------------------------------------------------------------------ 12 R14.35
num=lambda s: float(s.replace('<','').replace('\u202f','').replace(',','.').strip())
def g_r35(pg):
    F=[]; C=[0]; nm=''
    def ok(c,m):
        C[0]+=1
        if not c: F.append(m)
    # PSV: todos os valores de 0,1 cm/s cujo MoM fica a < 0,01 de 1,3 ou 1,5, em 4 IGs
    cases=pg.evaluate("""()=>{var o=[];[16,25,30,38].forEach(function(g){var md=medPSV(g);for(var v10=100;v10<=1300;v10++){var m=v10/10/md;
       if(Math.abs(m-1.5)<0.01||Math.abs(m-1.3)<0.01) o.push([g,v10/10]);}});return o;}""")
    for g,v in cases:
        r=pg.evaluate("""([g,v])=>{$('bRst').click();$('sem').value=g;$('dias').value=0;IGSRC='mao';$('psv').value=v.toFixed(1);run();
          var L=$('ldT').textContent, m=L.match(/PSV da ACM: [\\d,]+ cm\\/s \\(([\\d,]+) MoM\\)/);
          return {f:ST.psv.flag, mom:ST.psv.mom, out:$('psvV').textContent.replace(' MoM',''), ld:m?m[1]:null};}""",[g,v])
        x=num(r['out']); f=r['f']
        good=(f=='alto' and x>=1.5) or (f=='lim' and 1.3<=x<1.5) or (f=='ok' and x<1.3)
        ok(good,(nm,'PSV exibido x classe',g,v,r))
        if r['ld']: ok(r['ld']==r['out'],(nm,'PSV laudo≠cartão',g,v,r))
    ok(len(cases)>50,(nm,'PSV poucos casos',len(cases)))
    # CPR: colisões com p5 e com 1,0
    cc=pg.evaluate("""()=>{var o=[];for(var g=20;g<=40;g+=4){var pc=ciobanuCPRref(gaDiasCiobanu(g));
       for(var ai=50;ai<=300;ai+=1)for(var ui=50;ui<=300;ui+=1){var c=(ai/100)/(ui/100);
        if((n2(c)===n2(pc[0])&&c!==pc[0])||(n2(c)==='1,00'&&c<1)) {o.push([g,ai/100,ui/100]); if(o.length%7) {} }}} return o.filter(function(_,i){return i%25===0;}).slice(0,60);}""")
    for g,a,u in cc:
        r=pg.evaluate("""([g,a,u])=>{$('bRst').click();$('sem').value=g;$('dias').value=0;IGSRC='mao';$('acmip').value=a.toFixed(2);$('auip').value=u.toFixed(2);run();
          var t=$('cprRes').textContent, m=t.match(/p5 nesta IG \\(Ciobanu 2019\\/FMF\\) = ([\\d,]+)/);
          var L=$('ldT').textContent, l=L.match(/Relação cerebroplacentária: ([\\d,]+)/);
          if(!ST.cpr) return null;
          return {v:ST.cpr.v, below:ST.cpr.baixoP5, out:$('cprV').textContent, p5:m?m[1]:null, ld:l?l[1]:null};}""",[g,a,u])
        if r is None: continue
        x=num(r['out'])
        if r['p5']: ok((x<num(r['p5']))==r['below'] or (not r['below'] and x==num(r['p5'])),(nm,'CPR valor×p5',g,a,u,r))
        if r['v']<1: ok(x<1,(nm,'CPR <1 exibido como 1',g,a,u,r))
        if r['ld']: ok(r['ld']==r['out'],(nm,'CPR laudo≠cartão',g,a,u,r))
    ok(len(cc)>10,(nm,'CPR poucos casos',len(cc)))
    # AU: valor = p95 arredondado
    for g in range(20,41):
        r=pg.evaluate("""(g)=>{var pc=ciobanuAU(gaDiasCiobanu(g));var v=Math.round(pc[2]*100)/100;
          $('bRst').click();$('sem').value=g;$('dias').value=0;IGSRC='mao';$('auip').value=v.toFixed(2);run();
          var t=$('auRes').textContent, m=t.match(/p95 ([\\d,]+)/); return {v:v,raw:pc[2],f:ST.au?ST.au.flag:null,p95:m?m[1]:null};}""",g)
        if not r['p95']: continue
        s=num(r['p95'])
        if r['v']>r['raw']: ok(s<r['v'],(nm,'AU p95 exibido',g,r))
        elif r['v']<r['raw']: ok(s>r['v'],(nm,'AU p95 exibido <',g,r))
    # Uterinas: média de dois lados perto do p95 interpolado
    for g in (20.43,26.71,33.14):
        r=pg.evaluate("""(g)=>{var p=interp(T_UT,g); var out=[];
          for(var k=-3;k<=3;k++){var m=Math.round(p[2]*200)/200+k*0.005; var d=Math.round(m*100)/100, e=Math.round((2*m-d)*100)/100;
           $('bRst').click();$('sem').value=Math.floor(g);$('dias').value=Math.round((g-Math.floor(g))*7);IGSRC='mao';CURVA_UT='gomez';VIA_UT='ta';$('utD').value=d.toFixed(2);$('utE').value=e.toFixed(2);run();
           var t=$('utRes').textContent, mm=t.match(/p95 ([\\d,]+)/); out.push([ST.ut?ST.ut.v:null, ST.ut?ST.ut.flag:null, mm?mm[1]:null, $('utV').textContent]);}
          return out;}""",g)
        for v,f,p95,shown in r:
            if v is None or p95 is None: continue
            x=num(shown); c=num(p95)
            ok((f=='alto' and x>c) or (f=='ok' and x<=c),(nm,'UT exibido×p95',g,v,f,shown,p95))
    # Colo na conclusão
    r=pg.evaluate("""()=>{$('bRst').click();$('sem').value=22;$('dias').value=0;IGSRC='mao';setModo('bio');
      $('bDBP').value='5.40';$('bCC').value='19.80';$('bCA').value='17.40';$('bFL').value='3.90';$('eColo').value='2.00';run();
      var a=[$('ldT').textContent,document.body.textContent.indexOf('Peso adequado, achado materno')>=0];
      $('eAtr').value='1.10';run(); return a.concat([$('ldT').textContent]);}""")
    ok('com achado materno: colo curto' in r[0] and 'morfológico' not in r[0].split('CONCLUSÃO')[1],(nm,'colo conclusão só materno',r[0][-260:]))
    ok(r[1],(nm,'título síntese achado materno'))
    ok('com achado morfológico: ventriculomegalia e achado materno: colo curto' in r[2],(nm,'conclusão mista',r[2][-260:]))   # R14.48: singular
    grupo('12 Valor × corte exibidos; colo materno (R14.35)',C[0],F)

# ------------------------------------------------------------------ 13 via das uterinas (R14.36)
def g_via(pg):
    """Exame novo começa em transabdominal; no 1º trimestre, aviso até o primeiro toque na via.
    A compatibilidade curva × via × IG continua decidindo se classifica."""
    F=[]; C=[0]
    def ok(c,m):
        C[0]+=1
        if not c: F.append(m)
    S="""([g,curva,toque,d,e])=>{$('bRst').click();
      if(g===null){$('sem').value='';$('dias').value='';} else {$('sem').value=g;$('dias').value=0;} IGSRC='mao';
      if(curva&&CURVA_UT!==curva){CURVA_UT=curva;renderCurvaUt();}
      run();
      if(toque){document.querySelector('.viaUtBtn[data-via="'+toque+'"]').click();}
      if(g!==null && g<14){$('rUtD').value=d;$('rUtE').value=e;} else {$('utD').value=d;$('utE').value=e;}
      run();
      var av=[].map.call(document.querySelectorAll('.viaUtAviso'),function(a){return a.style.display==='none'?'':a.textContent;});
      var on=[].map.call(document.querySelectorAll('.viaUtBtn.on'),function(b){return b.dataset.via;});
      var o=(g!==null && g<14)?ST.rut:ST.ut;
      return {via:VIA_UT,padrao:VIA_UT_PADRAO,av:av,on:on,cls:o?o.flag:null,
              res:((g!==null&&g<14)?$('rUtRes'):$('utRes')).textContent,laudo:$('ldT').textContent};}"""
    # 1º trimestre, Gómez, sem toque: aviso visível, Gómez 1º tri é transvaginal → não classifica
    r=pg.evaluate(S,[12,'gomez',None,'1.60','1.80'])
    ok(r['via']=='ta' and r['padrao'] is True,('exame novo não começa em transabdominal pré-selecionada',r['via'],r['padrao']))
    ok(r['on']==['ta','ta'],('botão transabdominal não aparece marcado nos dois cartões',r['on']))
    ok(all('Confirme a via' in a for a in r['av']),('aviso de 1º trimestre ausente',r['av']))
    ok(all('Cavoretto' in a for a in r['av']),('aviso não indica a curva compatível com transabdominal',r['av']))
    ok(r['cls'] is None and 'incompatível' in r['res'],('Gómez + transabdominal no 1º tri classificou',r['cls'],r['res'][:80]))
    # toque em transvaginal: aviso some e Gómez classifica
    r=pg.evaluate(S,[12,'gomez','tv','1.60','1.80'])
    ok(r['padrao'] is False and all(a=='' for a in r['av']),('aviso não some depois do toque',r['av']))
    ok(r['cls'] in ('ok','alto'),('transvaginal confirmada no 1º tri não classificou',r['cls']))
    # toque em transabdominal também confirma
    r=pg.evaluate(S,[12,'gomez','ta','1.60','1.80'])
    ok(r['padrao'] is False and all(a=='' for a in r['av']),('toque em transabdominal não confirma',r['av']))
    # Cavoretto no 1º tri: aviso sem a frase de Gómez; classifica (curva transabdominal)
    r=pg.evaluate(S,[12,'cavoretto',None,'1.60','1.80'])
    ok(all('Confirme a via' in a and 'Gómez' not in a for a in r['av']),('aviso com Cavoretto errado',r['av']))
    ok(r['cls'] in ('ok','alto'),('Cavoretto + transabdominal no 1º tri não classificou',r['cls']))
    # reset volta ao padrão (não herda a via da paciente anterior)
    r=pg.evaluate("()=>{document.querySelector('.viaUtBtn[data-via=\"tv\"]').click();$('bRst').click();return [VIA_UT,VIA_UT_PADRAO];}")
    ok(r==['ta',True],('reset não volta para transabdominal pré-selecionada',r))
    # 2º/3º trimestre sem toque: sem aviso, classifica, laudo cita a via
    r=pg.evaluate(S,[30,'gomez',None,'0.65','0.81'])
    ok(all(a=='' for a in r['av']),('aviso aparece fora do 1º trimestre',r['av']))
    ok(r['cls']=='ok',('2º/3º tri não classificou com a via padrão',r['cls']))
    ok('Artérias uterinas (via transabdominal)' in r['laudo'],('laudo não cita a via',r['laudo'][-200:]))
    # sem IG: aviso segue o contexto (1º tri só no contexto B)
    r=pg.evaluate("()=>{$('bRst').click();$('sem').value='';$('dias').value='';escolheCtx('B');run();var a=[].map.call(document.querySelectorAll('.viaUtAviso'),function(x){return x.style.display==='none'?'':x.textContent;});escolheCtx('A');run();var b=[].map.call(document.querySelectorAll('.viaUtAviso'),function(x){return x.style.display==='none'?'':x.textContent;});return [a,b];}")
    ok(all('Confirme a via' in a for a in r[0]),('sem IG no contexto de 1º tri: aviso ausente',r[0]))
    ok(all(a=='' for a in r[1]),('sem IG no contexto de 2º/3º tri: aviso indevido',r[1]))
    # persistência: o estado salvo guarda a marca; payload sem o campo é tratado como via escolhida
    r=pg.evaluate("""()=>{$('bRst').click();$('sem').value=12;$('dias').value=0;IGSRC='mao';$('rUtD').value='1.6';run();
       var o=coletaEstado(); var tem=o&&('VIA_UT_PADRAO' in o)&&o.VIA_UT_PADRAO===true;
       var o2=JSON.parse(JSON.stringify(o)); delete o2.VIA_UT_PADRAO; aplicaEstado(o2);
       var a=VIA_UT_PADRAO; aplicaEstado(o); return [tem,a,VIA_UT_PADRAO];}""")
    ok(r[0],('estado salvo sem VIA_UT_PADRAO',r))
    ok(r[1] is False,('payload antigo sem o campo virou via pré-selecionada',r))
    ok(r[2] is True,('recuperação perdeu a marca de via pré-selecionada',r))
    grupo('13 Via das uterinas: transabdominal padrão + aviso no 1º tri (R14.36)',C[0],F)

# ------------------------------------------------------------------ 14 barrinha por lado (R14.36)
def g_lado(pg):
    """Barrinha de consulta sob cada artéria uterina: mesma curva/via/IG do IP médio, cor e
    rótulo no padrão do app, ao vivo, e NUNCA entra em ST, laudo ou classificação."""
    F=[]; C=[0]
    def ok(c,m):
        C[0]+=1
        if not c: F.append(m)
    pg.evaluate("()=>{$('bRst').click();$('sem').value=30;$('dias').value=5;IGSRC='mao';run();}")
    # ao vivo: digitar só a direita (evento de input real) já desenha a barrinha dela
    digita=lambda i,v: pg.evaluate("([i,v])=>{var e=$(i);e.value=v;e.dispatchEvent(new Event('input',{bubbles:true}));}",[i,v])
    digita('utD','0.65'); pg.wait_for_timeout(60)
    r=pg.evaluate("()=>({d:$('utDBar').className,e:$('utEBar').className,nota:$('utLadoNota').style.display,lbl:$('utDMk').textContent,ut:ST.ut})")
    ok('on' in r['d'] and 'on' not in r['e'],('barrinha não aparece ao vivo só no lado digitado',r))
    ok(r['nota'] in ('block','inline'),('legenda de consulta ausente',r['nota']))   # R14.37: trecho da legenda única
    ok(r['ut'] is None,('um lado só não pode gerar IP médio',r['ut']))
    digita('utE','0.81'); pg.wait_for_timeout(60)
    # contrato por valor, em volta do p95 de Gómez a 30s5d, e extremos
    vals=[round(0.30+0.01*k,2) for k in range(0,231)]
    R=pg.evaluate("""(vals)=>{var g=getGA(),p=interp(T_UT,g),o=[];
      vals.forEach(function(v){$('utD').value=v.toFixed(2);run();
        o.push({v:v,p95:p[2],cls:$('utDMk').className,lbl:$('utDMk').textContent,on:$('utDBar').className.indexOf('on')>=0,
                st:JSON.stringify(ST.utD),ut:ST.ut?ST.ut.v:null});});
      return o;}""",vals)
    for x in R:
        acima = x['v']>x['p95']+1e-9
        ok(x['on'],('barrinha sumiu',x['v']))
        ok(('alt' in x['cls'])==acima,('cor da barrinha não segue o p95',x['v'],x['p95'],x['cls']))
        l=x['lbl']
        if l[0] in '<>':
            ok(l[1]==' ',('sem espaço fino',x['v'],l))
            c=float(l[2:].lstrip('p'))
            if l[0]=='>': ok(acima or c<95,('rótulo > com valor não acima',x['v'],l))
            if l[0]=='<': ok(not acima,('rótulo < com valor acima do p95',x['v'],l))
        else:
            n=float(l[1:].replace(',','.'))
            ok((n>95)==acima or (n<95 and not acima),('número do rótulo cruza o p95',x['v'],l,x['p95']))
        ok(x['st']=='{"v":%s}'%(('%g'%x['v']) if x['v']!=int(x['v']) else int(x['v'])) or x['st'].startswith('{"v":'),('ST do lado ganhou classificação',x['st']))
        ok(abs(x['ut']-(x['v']+0.81)/2)<1e-9,('IP médio mudou de regra',x['v'],x['ut']))
    # não entra no laudo nem muda a classificação do IP médio
    r=pg.evaluate("""()=>{$('utD').value='1.80';$('utE').value='0.30';run();
       return {dAlt:$('utDMk').className, flag:ST.ut.flag, laudo:$('ldT').textContent};}""")
    ok('alt' in r['dAlt'] and r['flag']=='ok',('lado alto deveria pintar só a barrinha; IP médio normal',r['dAlt'],r['flag']))
    ok('direita' not in r['laudo'].lower().split('artérias uterinas')[-1][:120] if 'Artérias uterinas' in r['laudo'] else True,('laudo cita o lado',r['laudo'][-200:]))
    # sem via, ou curva incompatível: some
    r=pg.evaluate("()=>{VIA_UT=null;run();var a=[$('utDBar').className,$('utLadoNota').style.display];VIA_UT='ta';run();return a;}")
    ok('on' not in r[0] and r[1]=='none',('barrinha aparece sem via',r))
    r=pg.evaluate("()=>{VIA_UT='tv';run();var a=$('utDBar').className;VIA_UT='ta';run();return a;}")
    ok('on' not in r,('barrinha aparece com via incompatível (transvaginal a 30 sem)',r))
    # 1º trimestre: Gómez + transabdominal incompatível → sem barrinha; transvaginal → aparece
    r=pg.evaluate("""()=>{$('bRst').click();$('sem').value=12;$('dias').value=0;IGSRC='mao';$('rUtD').value='1.6';$('rUtE').value='2.9';run();
       var a=[$('rUtDBar').className,$('rUtEBar').className];
       document.querySelector('.viaUtBtn[data-via="tv"]').click();
       var b=[$('rUtDBar').className,$('rUtEBar').className,$('rUtEMk').className,$('rUtLadoNota').style.display,ST.rut?ST.rut.flag:null];
       return [a,b];}""")
    ok(all('on' not in x for x in r[0]),('1º tri Gómez + transabdominal: barrinha não devia aparecer',r[0]))
    ok('on' in r[1][0] and 'on' in r[1][1] and r[1][3]=='block',('1º tri transvaginal: barrinhas ausentes',r[1]))
    ok('alt' in r[1][2],('1º tri: lado acima do p95 sem cor',r[1]))
    # Cavoretto também alimenta a barrinha
    r=pg.evaluate("""()=>{$('bRst').click();CURVA_UT='cavoretto';renderCurvaUt();$('sem').value=30;$('dias').value=0;IGSRC='mao';$('utD').value='0.70';run();
       var a=$('utDBar').className; CURVA_UT='gomez';renderCurvaUt();run(); return a;}""")
    ok('on' in r,('Cavoretto: barrinha ausente',r))
    grupo('14 Barrinha de consulta por artéria uterina (R14.36)',C[0],F)

# ------------------------------------------------------------------ 15 incisura por quadradinho (R14.36)
def g_inc(pg):
    """Marcado = presente; desmarcado com o IP daquele lado medido = ausente; desmarcado sem IP =
    não avaliada. O laudo cita só a presença. Antes de 24 sem a presença é fisiológica."""
    F=[]; C=[0]
    def ok(c,m):
        C[0]+=1
        if not c: F.append(m)
    S="""([g,d,e,cd,ce])=>{$('bRst').click();$('sem').value=g;$('dias').value=0;IGSRC='mao';
      $('utD').value=d;$('utE').value=e;
      [['incDChk',cd],['incEChk',ce]].forEach(function(p){var c=$(p[0]);if(c.checked!==p[1]){c.checked=p[1];c.dispatchEvent(new Event('change',{bubbles:true}));}});
      run();
      return {v:incValor(),d:incSt('incD'),e:incSt('incE'),res:$('incRes').textContent,
              laudo:$('ldT').textContent,cd:$('incDChk').checked,ce:$('incEChk').checked,
              ut:ST.ut?ST.ut.flag:null};}"""
    casos=[  # g, D, E, chkD, chkE, incValor esperado, frase no laudo (None = nenhuma)
      (30,'0.65','0.81',False,False,'aus',None),
      (30,'0.65','0.81',True,False,'uni','incisura protodiastólica unilateral'),
      (30,'0.65','0.81',False,True,'uni','incisura protodiastólica unilateral'),
      (30,'0.65','0.81',True,True,'bil','incisura protodiastólica bilateral'),
      (30,'0.65','',False,False,'parc',None),
      (30,'','',False,False,'na',None),
      (30,'','',True,False,'parc','incisura protodiastólica à direita; esquerda não avaliada'),
      (30,'0.65','',False,True,'uni','incisura protodiastólica unilateral'),
      (20,'1.10','1.20',True,True,'bil','incisura protodiastólica bilateral'),
    ]
    for g,d,e,cd,ce,exp,frase in casos:
        r=pg.evaluate(S,[g,d,e,cd,ce])
        ok(r['v']==exp,('estado da incisura',g,d,e,cd,ce,r['v'],exp))
        ok(r['cd']==cd and r['ce']==ce,('quadradinho não reflete o estado',cd,ce,r['cd'],r['ce']))
        low=r['laudo'].lower()
        if frase: ok(frase in low,('laudo sem a presença',g,d,e,cd,ce,low[-200:]))
        ok('ausência de incisura' not in low and 'sem incisura' not in low,('laudo cita ausência',g,d,e,cd,ce))
        if exp=='na': ok(r['res'].strip()=='',('cartão de incisura com nada avaliado',r['res'][:60]))
        if exp=='aus': ok('Sem incisura' in r['res'],('cartão não mostra sem incisura',r['res'][:60]))
        if exp=='bil' and g<24: ok('Esperado nesta fase' in r['res'],('antes de 24 sem não diz fisiológica',r['res'][:80]))
        ok(r['ut'] in (None,'ok','alto'),('incisura alterou a classificação do IP médio',r['ut']))
    # a classificação do IP médio não depende da incisura
    a=pg.evaluate(S,[30,'0.65','0.81',False,False])['ut']; b=pg.evaluate(S,[30,'0.65','0.81',True,True])['ut']
    ok(a==b=='ok',('incisura mudou a classificação das uterinas',a,b))
    # persistência e exames antigos: 'aus' explícito salvo antes vira regra do IP; 'pres' volta marcado
    r=pg.evaluate("""()=>{$('bRst').click();$('sem').value=30;$('dias').value=0;IGSRC='mao';$('utD').value='0.65';$('utE').value='0.81';
       $('incDChk').checked=true;$('incDChk').dispatchEvent(new Event('change',{bubbles:true}));run();
       var o=coletaEstado(); var o2=JSON.parse(JSON.stringify(o)); o2.sel.incE='aus'; o2.campos.utE='';
       $('bRst').click(); aplicaEstado(o); run(); var a=[$('incDChk').checked,$('incEChk').checked,incValor()];
       $('bRst').click(); aplicaEstado(o2); run(); var b=[$('incDChk').checked,$('incEChk').checked,incValor(),incSt('incE')];
       return [a,b];}""")
    ok(r[0]==[True,False,'uni'],('recuperação perdeu a incisura',r[0]))
    ok(r[1][3]=='na' and r[1][2]=='parc',("'aus' antigo sem IP virou ausência",r[1]))
    # reset limpa os quadradinhos
    r=pg.evaluate("()=>{$('bRst').click();run();return [$('incDChk').checked,$('incEChk').checked,incValor()];}")
    ok(r==[False,False,'na'],('reset não limpa a incisura',r))
    grupo('15 Incisura por quadradinho (R14.36)',C[0],F)

# ------------------------------------------------------------------ 16 R14.37 ergonomia
def g_r37(pg):
    """Ergonomia aprovada em 10/10/2026: Medidas começa pela biometria; abas fixas no rodapé;
    avisos do Laudo dobrados sem perder texto; Copiar laudo | Copiar conclusão; simetria;
    campo em edição não é empurrado. Botões e fontes NÃO mudam (pedido explícito)."""
    F=[]; C=[0]
    def ok(c,m):
        C[0]+=1
        if not c: F.append(m)
    pg.set_viewport_size({'width':390,'height':664})
    FILL="""()=>{$('bRst').click();$('sem').value=32;$('dias').value=2;IGSRC='mao';setModo('bio');
      $('bDBP').value='8.10';$('bCC').value='29.50';$('bCA').value='26.40';$('bFL').value='6.10';$('mbv').value='4.2';
      $('auip').value='1.05';$('acmip').value='1.90';$('utD').value='0.70';$('utE').value='0.82';$('diast').value='pres';run();}"""
    TAB="(t)=>{var b=[].find.call(document.querySelectorAll('.tab'),function(x){return x.dataset.p===t});b.click();window.scrollTo(0,0);}"
    pg.evaluate(FILL)
    # 1. Medidas começa pela biometria; síntese no fim
    r=pg.evaluate("""()=>{var k=[].slice.call($('p1').children).filter(function(x){return x.tagName!=='SCRIPT'});
      var i=function(id){return k.indexOf($(id));}; var c=k.filter(function(x){return x.classList.contains('card')||x.tagName==='DETAILS'});
      return {primeiro:k[0].querySelector('h2')?k[0].querySelector('h2').textContent:k[0].id, s:i('sintRes'),q:i('seqBox'),g:i('guiaBox'),ultimoCard:k.indexOf(c[c.length-1])};}""")
    ok(r['primeiro']=='Peso fetal',('Medidas não começa pelo peso',r))
    ok(r['s']>r['ultimoCard'] and r['q']>r['s'] and r['g']>r['q'],('síntese/sequência/guia fora do fim',r))
    # 2. abas no rodapé; fontes e botões do cabeçalho como estavam
    pg.evaluate(TAB,'p1')
    r=pg.evaluate("""()=>{var t=document.querySelector('.tabs'),cs=getComputedStyle(t),tb=document.querySelector('.tab');
      return {pos:cs.position,bot:Math.round(t.getBoundingClientRect().bottom),ih:innerHeight,fs:getComputedStyle(tb).fontSize,
        sub:getComputedStyle(document.querySelector('.hd-r h1 i')).display,rst:Math.round($('bRst').getBoundingClientRect().height),
        ic:[].map.call(document.querySelectorAll('.hd-b .ic'),function(e){return Math.round(e.getBoundingClientRect().height)})};}""")
    r0=pg.evaluate("()=>({p:getComputedStyle($('topo')).position, dentro:!!$('topo').querySelector('.tabs')})")
    ok(r0['p']=='sticky' and r0['dentro'] and r['pos']=='static',('R15.0: abas presas em cima, com a faixa',r0,r))
    ok(r['fs']=='13px',('fonte da aba mudou',r['fs']))
    ok(r['sub']=='block',('subtítulo do cabeçalho sumiu',r['sub']))
    ok(r['rst']==28 and all(h==44 for h in r['ic']) ,('tamanho de botão do cabeçalho mudou',r))
    r=pg.evaluate("""()=>{$('bCA').focus();var a=getComputedStyle(document.querySelector('.tabs')).display;$('bCA').blur();return a;}""")
    pg.wait_for_timeout(150)
    r2=pg.evaluate("()=>getComputedStyle(document.querySelector('.tabs')).display")
    ok(r!='none' and r2!='none',('R15.0: abas em cima ficam durante a digitação (não empurram o campo)',r,r2))
    # 3. barra de cópia só no Laudo; conclusão = trecho do laudo
    r=pg.evaluate("()=>document.querySelector('.barCopy').getBoundingClientRect().height")
    ok(r==0,('barra de cópia fora do Laudo',r))
    pg.evaluate(TAB,'p3')
    r=pg.evaluate("""()=>{var t=$('ldT').textContent;return {d:getComputedStyle(document.querySelector('.barCopy')).display,
      c:textoConclusao(),fim:t.slice(t.indexOf('CONCLUSÃO')).trim(),a:$('bCpy').textContent,b:$('bCpyC').textContent,
      tabsTop:document.querySelector('.tabs').getBoundingClientRect().top,barBot:document.querySelector('.barCopy').getBoundingClientRect().bottom};}""")
    ok(r['d']=='flex' and r['a']=='Copiar laudo' and r['b']=='Copiar conclusão',('barra de cópia',r))
    ok(r['c'].startswith('CONCLUSÃO') and r['c']==r['fim'],('conclusão copiada difere do laudo',r['c'][:80]))
    ok(abs(pg.evaluate("()=>innerHeight")-r['barBot'])<=1,('R15.0: barra de cópia encosta no rodapé',r))
    r=pg.evaluate("()=>{laudoIndisponivel(['x'],false);var a=[$('bCpy').disabled,$('bCpyC').disabled];run();return a.concat([$('bCpyC').disabled]);}")
    ok(r==[True,True,False],('cópia de conclusão não acompanha laudo indisponível',r))
    # 4. avisos dobrados: nada se perde, nada corta tag, abreviação não é frase
    r=pg.evaluate("""()=>{var o=[];
      var T=['Percentil de peso <b>colado no p10</b> (p10,4). Com margem de ±10% do método, o valor cruza o limiar nos dois sentidos — não trate como corte rígido.',
             'Curto. Fim.','Texto com <b>negrito. Que</b> continua por muitas e muitas palavras para passar de cinquenta letras.',
             'Segundo Roberts AW et al. Isso continua por muitas e muitas palavras para passar de cinquenta letras aqui.'];
      T.forEach(function(m){var p=chkParte(m);o.push(p?[p[0],p[1]]:null);});
      var h={r:'R',d:'D'}; o.push(chkParte(h)); return o;}""")
    ok(r[0] and r[0][0].endswith('(p10,4).') and (r[0][0]+' '+r[0][1])==("Percentil de peso <b>colado no p10</b> (p10,4). Com margem de ±10% do método, o valor cruza o limiar nos dois sentidos — não trate como corte rígido."),('divisão perdeu texto',r[0]))
    ok(r[1] is None,('aviso curto foi dobrado',r[1]))
    ok(r[2] is None or '<b>' not in r[2][0] or '</b>' in r[2][0],('cortou dentro do negrito',r[2]))
    ok(r[3] is None or not r[3][0].endswith('al.'),('cortou em "et al."',r[3]))
    ok(r[4]==['R','D'],('aviso com resumo explícito',r[4]))
    r=pg.evaluate("""()=>{var ls=[].slice.call(document.querySelectorAll('#chk .chk-ln'));
      var had=ls.filter(function(l){return l.textContent.indexOf('Hadlock 1991')>=0})[0]; if(!had) return null;
      var vis0=getComputedStyle(had.querySelector('.pqD')).display; had.querySelector('.pqT').click();
      var vis1=getComputedStyle(had.querySelector('.pqD')).display;
      return {res:had.firstChild.textContent+had.childNodes[1].textContent, d:had.querySelector('.pqD').textContent, v0:vis0, v1:vis1, t:had.querySelector('.pqT').textContent};}""")
    # R14.51: perto do p10 a nota de Hadlock entra no "por quê" do aviso único do percentil
    ok(r and 'perto do p10' in r['res'] and 'Roberts AW' in r['d'] and '5,1%' in r['d'],('aviso de Hadlock sem resumo/detalhe completo',r))
    ok(r and r['v0']=='none' and r['v1']=='block' and r['t']=='menos ‹',('por quê não abre',r))
    # 5. simetria
    pg.evaluate(TAB,'p2')
    r=pg.evaluate("""()=>{var o={};
      o.bar=$('auBar').getBoundingClientRect().top-$('acmBar').getBoundingClientRect().top;
      o.inp=$('auip').getBoundingClientRect().top-$('acmip').getBoundingClientRect().top;
      var pil=[];document.querySelectorAll('.pane .ch').forEach(function(h){var tg=h.querySelector('.tg'),q=h.querySelector('.qbtn');if(!tg)return;
        var p=h.closest('.pane'); var was=p.className; p.className='pane on';
        var r=h.getBoundingClientRect(),a=tg.getBoundingClientRect(); var nx=tg.nextElementSibling;
        var lim=(nx?nx.getBoundingClientRect().left:r.right); pil.push(Math.round(lim-a.right)); p.className=was;});
      o.pil=pil; return o;}""")
    ok(abs(r['bar'])<=1 and abs(r['inp'])<=1,('Doppler fetal desalinhado entre umbilical e cerebral',r))
    ok(all(x<=14 for x in r['pil']),('pílula solta no cabeçalho',r['pil']))
    pg.evaluate(TAB,'p1')
    r=pg.evaluate("""()=>{var o=[];document.querySelectorAll('#p1 details').forEach(function(d){d.open=true});
      document.querySelectorAll('.unit').forEach(function(u){var p=u.closest('.pane'); if(!p) return; var w=p.className; p.className='pane on';
        var i=u.querySelector('input'),s=u.querySelector('.u'); if(i&&s&&i.offsetParent){var a=i.getBoundingClientRect(),b=s.getBoundingClientRect();
        var d=(b.top+b.height/2)-(a.top+a.height/2); if(Math.abs(d)>1.5) o.push(i.id+':'+d.toFixed(1));} p.className=w;});
      var f=$('eFib').getBoundingClientRect().width, t=$('eTib').getBoundingClientRect().width;
      return {u:o,fib:f,tib:t};}""")
    ok(not r['u'],('unidade fora do centro do campo',r['u'][:5]))
    ok(abs(r['fib']-r['tib'])<=1,('Fíbula fora da grade dos ossos',r))
    # 6. campo em edição não é empurrado (o que muda acima dele é compensado)
    pg.evaluate(FILL); pg.evaluate(TAB,'p1')
    def empurra(id,v,inject=False):
        return pg.evaluate("""([id,v,inj])=>{var e=$(id); window.scrollTo(0,0); window.scrollBy(0,e.getBoundingClientRect().top-300);
          var tmp=null; if(inj){tmp=function(){var d=document.createElement('div');d.className='tmpEmp';d.style.height='180px';
            var p=e.closest('.pane'); p.insertBefore(d,p.firstChild);}; e.addEventListener('input',tmp);}
          var y0=e.getBoundingClientRect().top; e.value=v; e.dispatchEvent(new Event('input',{bubbles:true}));
          var d=e.getBoundingClientRect().top-y0; if(tmp){e.removeEventListener('input',tmp);document.querySelectorAll('.tmpEmp').forEach(function(x){x.remove()});}
          return d;}""",[id,v,inject])
    for id,v in (('bDBP','0.3'),('bCC','0.3'),('bFL','0.3'),('bCA','40')):
        d=empurra(id,v); ok(abs(d)<=2,('campo empurrado',id,v,d))
    d=empurra('bCA','26.40',True); ok(abs(d)<=2,('bloco novo acima empurrou o campo',d))
    grupo('16 Ergonomia, simetria e campo parado (R14.37)',C[0],F)

# ------------------------------------------------------------------ 17 R14.38 correções da bateria
def g_r38(pg):
    """Bateria de 10/10/2026: "Próximo pendente" e aviso rápido acima das barras do rodapé;
    "por quê" abre pelo teclado; em 320 px os pares de campos ficam nivelados e nada vaza."""
    F=[]; C=[0]
    def ok(c,m):
        C[0]+=1
        if not c: F.append(m)
    TAB="(t)=>{var b=[].find.call(document.querySelectorAll('.tab'),function(x){return x.dataset.p===t});b.click();window.scrollTo(0,0);}"
    FILL="""()=>{$('bRst').click();$('sem').value=32;$('dias').value=2;IGSRC='mao';setModo('bio');
      $('bDBP').value='';$('bCC').value='29.50';$('bCA').value='26.40';$('bFL').value='6.10';$('mbv').value='4.2';
      $('auip').value='1.05';$('acmip').value='1.90';$('utD').value='0.70';$('utE').value='0.82';$('diast').value='pres';run();}"""
    pg.set_viewport_size({'width':390,'height':664}); pg.evaluate(FILL); pg.evaluate(TAB,'p3'); pg.wait_for_timeout(400)
    r=pg.evaluate("""()=>{var b=$('bProx'); if(b.hidden) return {vis:false}; var r=b.getBoundingClientRect();
      var e=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2); return {vis:r.height>0, topo:(e===b||b.contains(e)), quem:e&&(e.id||e.className)};}""")
    ok(r.get('vis') and r.get('topo'),('Próximo pendente coberto no Laudo',r))
    pg.evaluate("()=>toast('x')"); pg.wait_for_timeout(300)
    r=pg.evaluate("""()=>{var t=document.querySelector('.toast').getBoundingClientRect();
      return [document.querySelector('.tabs'),document.querySelector('.barCopy'),$('bProx')].map(function(x){var c=x.getBoundingClientRect();
        return c.height>0 && !(t.bottom<=c.top||t.top>=c.bottom||t.right<=c.left||t.left>=c.right);});}""")
    ok(not any(r),('aviso rápido em cima de barra/botão',r))
    pg.evaluate("()=>{$('bDBP').value='8.10';run();}"); pg.wait_for_timeout(80)
    pg.evaluate("()=>{var t=document.querySelector('#chk .pqT'); t.focus();}"); pg.keyboard.press('Enter'); pg.wait_for_timeout(80)
    ok(pg.evaluate("()=>!!document.querySelector('#chk .chk-ln.ab')"),('por quê não abre com Enter',))
    pg.keyboard.press(' '); pg.wait_for_timeout(80)
    ok(pg.evaluate("()=>!document.querySelector('#chk .chk-ln.ab')"),('por quê não fecha com espaço',))
    for w in (320,390):
        pg.set_viewport_size({'width':w,'height':700}); pg.wait_for_timeout(120)
        for t in ('p1','p6','p2','p5','p3','p0','p4'):
            pg.evaluate(TAB,t); pg.wait_for_timeout(80)
            pg.evaluate("(t)=>{document.querySelectorAll('#'+t+' details').forEach(function(d){d.open=true});}",t); pg.wait_for_timeout(80)
            r=pg.evaluate("""()=>{var o=[]; if(document.documentElement.scrollWidth>innerWidth+1) o.push('rolagem horizontal');
              var p=document.querySelector('.pane.on'); p.querySelectorAll('*').forEach(function(e){ if(!e.offsetParent) return; var r=e.getBoundingClientRect();
                if(r.width>0&&(r.right>innerWidth+1||r.left<-1)) o.push('vaza '+(e.id||e.className));});
              p.querySelectorAll('.duo').forEach(function(d){var c=[].filter.call(d.children,function(x){return x.offsetParent&&!x.getAttribute('aria-hidden')}); if(c.length!==2) return;
                var i=c.map(function(x){return x.querySelector('input,select.sel')}); if(i[0]&&i[1]&&Math.abs(i[0].getBoundingClientRect().top-i[1].getBoundingClientRect().top)>1.5) o.push('desnivelado '+i[0].id);});
              return o.slice(0,4);}""")
            ok(not r,(w,t,r))
    pg.set_viewport_size({'width':1024,'height':850})
    grupo('17 Correções da bateria: flutuantes, teclado, 320 px (R14.38)',C[0],F)

# ------------------------------------------------------------------ 18 R14.39 tamanho do bebê + Próximo pendente
def g_r39(pg):
    """Tamanho do bebê (Vintzileos 1984: 6,18 + 0,59 × fêmur em mm) só para a paciente: aparece
    na aba Medidas com fêmur 3,0–9,0 cm, número redondo e faixa ±6%; nunca no laudo, na conclusão
    ou na cópia (o Modo Paciente foi removido na R14.43). "Próximo pendente" visível em todas as abas."""
    F=[]; C=[0]
    def ok(c,m):
        C[0]+=1
        if not c: F.append(m)
    pg.set_viewport_size({'width':390,'height':664})
    S="""(fl)=>{$('bRst').click();$('sem').value=32;$('dias').value=2;IGSRC='mao';setModo('bio');
      $('bDBP').value='8.10';$('bCC').value='29.50';$('bCA').value='26.40';$('bFL').value=fl;run();
      var e=$('compPac'); return {on:e.className.indexOf('on')>=0, t:e.textContent, ld:$('ldT').textContent, conc:textoConclusao(),
        comp:ST.comp, fv:val('bFL'), semPac:!$('pacOv')&&!$('bPac')};}"""
    for k in range(0,1001):
        fl=round(1.0+k*0.01,2)                     # 1,00 a 11,00 cm
        r=pg.evaluate(S,'%.2f'%fl)
        dentro = 3-1e-9 <= fl <= 9+1e-9 and r['fv'] is not None   # fêmur barrado pela plausibilidade do app não mostra nada
        ok(r['on']==dentro,('linha do tamanho fora da faixa do fêmur',fl,r['on']))
        ok('Vintzileos' not in r['ld'] and 'tamanho do bebê' not in r['ld'].lower() and 'comprimento' not in r['ld'].lower(),('tamanho entrou no laudo',fl))
        ok('tamanho' not in r['conc'].lower(),('tamanho entrou na conclusão',fl))
        if dentro:
            c=6.18+0.59*fl*10
            ok(abs(r['comp']-c)<1e-9,('fórmula',fl,r['comp'],c))
            jr=lambda x: math.floor(x+0.5)          # = Math.round do JavaScript (meio arredonda para cima)
            cj=r['comp']
            ok(('≈ %d cm'%jr(cj)) in r['t'] and ('%d–%d cm'%(jr(cj*0.94),jr(cj*1.06))) in r['t'],('texto/faixa',fl,r['t']))
            ok(r['semPac'],('Modo Paciente voltou (removido na R14.43)',fl))
        else:
            ok(r['comp'] is None,('tamanho calculado fora da faixa do fêmur',fl,r['comp']))
    r=pg.evaluate("()=>{setModo('dir');$('pDir').value='1800';run();var a=$('compPac').className;setModo('bio');return a;}")
    ok('on' not in r,('tamanho aparece no peso informado direto',r))
    # Próximo pendente em todas as abas, por cima de tudo, e leva ao campo
    pg.evaluate("()=>{$('bRst').click();$('sem').value=32;$('dias').value=2;IGSRC='mao';$('bCC').value='29.5';$('bCA').value='26.4';$('bFL').value='6.1';run();}")
    for t in ('p0','p1','p2','p3'):
        pg.evaluate("(t)=>{var b=[].find.call(document.querySelectorAll('.tab'),function(x){return x.dataset.p===t});b.click();window.scrollTo(0,0);}",t)
        pg.wait_for_timeout(350)
        r=pg.evaluate("""()=>{var b=$('bProx'), r=b.getBoundingClientRect(); if(b.hidden||!r.height) return {vis:false};
          var e=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2); return {vis:true,topo:(e===b||b.contains(e)),pai:b.parentNode.tagName,quem:e&&(e.id||e.className),y:Math.round(r.top)};}""")
        ok(r.get('vis') and r.get('topo'),('Próximo pendente ausente/coberto',t,r))
        pg.evaluate("()=>toast('x')"); pg.wait_for_timeout(250)
        r=pg.evaluate("""()=>{var t=document.querySelector('.toast').getBoundingClientRect();
          return [document.querySelector('.tabs'),document.querySelector('.barCopy'),$('bProx')].map(function(x){var c=x.getBoundingClientRect();
            return c.height>0 && !(t.bottom<=c.top||t.top>=c.bottom||t.right<=c.left||t.left>=c.right);});}""")
        ok(not any(r),('aviso rápido em cima de barra/botão',t,r))
    pg.evaluate("()=>$('bProx').click()"); pg.wait_for_timeout(500)
    r=pg.evaluate("()=>[document.activeElement&&document.activeElement.id, document.querySelector('.pane.on').id]")
    ok(r==['bDBP','p1'],('Próximo pendente não leva ao campo que falta',r))
    pg.set_viewport_size({'width':1024,'height':850})
    grupo('18 Tamanho do bebê e Próximo pendente (R14.39)',C[0],F)

# ------------------------------------------------------------------ 19 R14.41 gemelar organizado
def g_r41(pg):
    """Gemelar: feto ativo sempre identificado (cor, etiqueta, faixa do topo), troca por toque em
    qualquer aba, quadro A × B coerente com o que cada feto mostra no próprio cartão; nada disso
    aparece sem gemelar nem entra no laudo."""
    import random
    F=[]; C=[0]
    def ok(c,m):
        C[0]+=1
        if not c: F.append(m)
    pg.set_viewport_size({'width':390,'height':700})
    vis="(id)=>{var e=$(id); return !!(e&&e.offsetParent&&e.getBoundingClientRect().height>0);}"
    # sem gemelar: nada novo aparece
    pg.evaluate("()=>{$('bRst').click();$('sem').value=30;$('dias').value=0;IGSRC='mao';$('bDBP').value='7.6';$('bCC').value='27.5';$('bCA').value='25.4';$('bFL').value='5.7';$('auip').value='1.0';$('acmip').value='1.8';run();}")
    for t,ids in (('p1',['gemCmp','fTagMed','discRes','sfgrRes']),('p2',['segFetoDop','fTagDop'])):
        pg.evaluate("(t)=>{[].find.call(document.querySelectorAll('.tab'),function(x){return x.dataset.p===t}).click()}",t); pg.wait_for_timeout(60)
        for i in ids: ok(not pg.evaluate(vis,i),('aparece sem gemelar',i))
    r=pg.evaluate("()=>[document.body.classList.contains('gemOn'),document.querySelectorAll('#estPfe .chipF').length,$('estPfe').textContent]")
    ok(r[0]==False and r[1]==0 and 'g' in r[2],('faixa/estado sem gemelar',r))
    # com gemelar: ordem do card e identidade
    pg.evaluate("()=>{var g=$('gemelar'); g.checked=true; g.dispatchEvent(new Event('change',{bubbles:true})); [].find.call(document.querySelectorAll('.tab'),function(x){return x.dataset.p==='p1'}).click();}")
    r=pg.evaluate("""()=>{var y=function(id){return $(id).getBoundingClientRect().top};
      return {ord:[y('fA'),y('fTagMed'),y('mBio'),y('bDBP')], tag:$('fTagMed').textContent, faixa:getComputedStyle($('bDBP').closest('.card')).boxShadow};}""")
    ok(r['ord']==sorted(r['ord']) and r['ord'][0]>0,('ordem do card do peso',r['ord']))
    r0=pg.evaluate("""()=>{document.querySelector('.tab[data-p="p0"]').click(); var y=function(id){return $(id).getBoundingClientRect().top};
      var o=[y('gemelar'),y('corion')]; document.querySelector('.tab[data-p="p1"]').click(); return o;}""")
    ok(r0[0]>0 and r0[1]>r0[0],('R15.0: gemelar e corionicidade no cartão Gestação',r0))
    ok(r['tag'].strip()=='Medidas do Feto A' and 'inset' in r['faixa'],('identidade do feto A',r))
    random.seed(19)
    LBL=r"""()=>{var t=function(id){var e=$(id); return e?e.textContent.trim():''}; var rows={};
      document.querySelectorAll('#gemCmp tr').forEach(function(tr){var c=tr.children; if(c.length===3) rows[c[0].textContent]=[c[1].textContent,c[2].textContent];});
      return {feto:FETO, rows:rows, pfe:ST.pfe?Math.round(ST.pfe.w)+' g':'—', pq:ST.pfe?rotPfe().p:'—', ca:(ST.ca&&MODO==='bio')?rotCA().p:'—',
        au:/\bon\b/.test($('auBar').className)?(n2(parseFloat($('auip').value))+' · '+t('auMk')):'—', acm:/\bon\b/.test($('acmBar').className)?(n2(parseFloat($('acmip').value))+' · '+t('acmMk')):'—',
        chips:[].map.call(document.querySelectorAll('#estPfe .chipF'),function(x){return x.textContent})};}"""
    for k in range(40):
        g=random.randint(22,37)
        A={'bDBP':'%.2f'%random.uniform(5.5,9.5),'bCC':'%.2f'%random.uniform(20,34),'bCA':'%.2f'%random.uniform(17,36),'bFL':'%.2f'%random.uniform(4,7.5),
           'auip':'%.2f'%random.uniform(0.6,1.9),'acmip':'%.2f'%random.uniform(0.9,2.5)}
        B={'bDBP':'%.2f'%random.uniform(5.5,9.5),'bCC':'%.2f'%random.uniform(20,34),'bCA':'%.2f'%random.uniform(17,36),'bFL':'%.2f'%random.uniform(4,7.5),
           'auip':'%.2f'%random.uniform(0.6,1.9),'acmip':'%.2f'%random.uniform(0.9,2.5)}
        if k%5==0: B['auip']=''; B['acmip']=''
        pg.evaluate("""([g,A,B])=>{$('bRst').click();$('sem').value=g;$('dias').value=3;IGSRC='mao';run();
          var c=$('gemelar'); c.checked=true; c.dispatchEvent(new Event('change',{bubbles:true}));
          [['A',A],['B',B]].forEach(function(p){trocaFeto(p[0]); Object.keys(p[1]).forEach(function(i){$(i).value=p[1][i];}); run();}); trocaFeto('A'); run();}""",[g,A,B])
        a=pg.evaluate(LBL)
        pg.evaluate("()=>document.querySelector('#estPfe .chipF.fB').click()"); pg.wait_for_timeout(20)
        b=pg.evaluate(LBL)
        ok(b['feto']=='B',('toque no chip não trocou',k))
        for cur,col in ((a,0),(b,1)):
            rw=cur['rows']
            ok(rw.get('Peso',['',''])[col]==cur['pfe'],('peso do quadro ≠ cartão',k,cur['feto'],rw.get('Peso'),cur['pfe']))
            ok(rw.get('Percentil',['',''])[col]==cur['pq'],('percentil ≠ cartão',k,cur['feto'],rw.get('Percentil'),cur['pq']))
            ok(rw.get('CA',['',''])[col]==cur['ca'],('CA ≠ cartão',k,cur['feto'],rw.get('CA'),cur['ca']))
            ok(rw.get('Umbilical IP',['',''])[col]==cur['au'],('umbilical ≠ cartão',k,cur['feto'],rw.get('Umbilical IP'),cur['au']))
            ok(rw.get('Cerebral IP',['',''])[col]==cur['acm'],('cerebral ≠ cartão',k,cur['feto'],rw.get('Cerebral IP'),cur['acm']))
        # o quadro mostra o mesmo para cada feto, esteja ele na tela ou guardado
        ok(a['rows']==b['rows'],('quadro muda conforme o feto na tela',k,a['rows'],b['rows']))
        ok(a['chips']==b['chips'],('faixa do topo muda conforme o feto na tela',k,a['chips'],b['chips']))
        ok('Quadro' not in pg.evaluate("()=>$('ldT').textContent"),('quadro no laudo',k))
    # seletor do Doppler troca o feto e a etiqueta acompanha
    pg.evaluate("()=>{[].find.call(document.querySelectorAll('.tab'),function(x){return x.dataset.p==='p2'}).click(); document.querySelector('#segFetoDop button[data-f=\"A\"]').click();}")
    r=pg.evaluate("()=>[FETO,$('fTagDop').textContent.trim(),document.querySelector('#segFetoDop button.on').getAttribute('data-f'),$('fA').className]")
    ok(r==['A','Doppler do Feto A','A','on'],('seletor do Doppler',r))
    # faixa do topo cabe numa linha em 320 px
    pg.set_viewport_size({'width':320,'height':640}); pg.wait_for_timeout(80); pg.evaluate("()=>run()")
    r=pg.evaluate("()=>{window.scrollTo(0,0); var e=$('estBar'),h=document.querySelector('.hd'); return [e.getBoundingClientRect().top, h.getBoundingClientRect().bottom, e.getBoundingClientRect().height];}")
    ok(r[0]>=r[1]-1 and r[2]<=44,('R15.0: faixa abaixo do título, numa linha',r))
    pg.set_viewport_size({'width':1024,'height':850})
    grupo('19 Gemelar organizado: identidade, troca e quadro A × B (R14.41)',C[0],F)

# ------------------------------------------------------------------ 20 R14.42 placenta
def g_r42(pg):
    """Placenta por exceção: vazio não muda nada; prévia = borda ≤ 2,0 cm ou recobrindo (FEBRASGO 2025);
    < 16 sem sem classificação; 16–27+6 suspeita + reavaliar com 32 sem; ≥ 28 placenta prévia;
    cesárea/acretismo só valem com prévia; vasa prévia; uma linha só no gemelar."""
    F=[]; C=[0]
    def ok(c,m):
        C[0]+=1
        if not c: F.append(m)
    S=r"""(a)=>{ $('bRst').click(); if(a.g!==null){$('sem').value=a.g[0];$('dias').value=a.g[1];IGSRC='mao';}
      $('bDBP').value='8.1';$('bCC').value='29.5';$('bCA').value='26.4';$('bFL').value='6.1';
      $('plOI').value=(a.d===null?'':a.d); $('plRec').checked=a.rec; $('plVia').value=a.via;
      $('plCes').checked=!!a.ces; $('plAcr').checked=!!a.acr; $('plForma').value=a.forma||''; $('plVel').checked=!!a.vel;
      if(a.gem){ var gg=$('gemelar'); gg.checked=true; gg.dispatchEvent(new Event('change',{bubbles:true})); }
      run();
      var t=$('ldT').textContent, P=ST.estr.plac;
      return {cls:P.cls, prev:P.prev, vazio:P.vazio, box:$('plPrev').style.display, res:$('plRes').textContent, resOn:/\bon\b/.test($('plRes').className),
        ld:t, conc:textoConclusao(), chk:$('chk').textContent, guia:$('guiaBox').textContent};}"""
    GAS=[None,(12,0),(15,6),(16,0),(20,3),(27,6),(28,0),(32,0),(38,2)]
    DS=[None,'0','1.0','2.0','2.01','3.0']
    n=0
    for g in GAS:
        for d in DS:
            for rec in (False,True):
                for via in ('ta','tv'):
                    if d is None and not rec and via=='tv': continue
                    r=pg.evaluate(S,{'g':g,'d':d,'rec':rec,'via':via,'ces':True,'acr':False})
                    n+=1
                    dmm=None if d is None else float(d)*10
                    prev = rec or (dmm is not None and dmm<=20+1e-9)
                    ga=None if g is None else g[0]+g[1]/7
                    exp = (None if not prev and dmm is None else ('longe' if not prev else
                          ('semIG' if ga is None else ('precoce' if ga<16 else ('susp' if ga<28 else 'pp')))))
                    tag=(g,d,rec,via)
                    ok(r['cls']==exp,('classe',tag,r['cls'],exp))
                    ok(r['prev']==prev,('prévia',tag,r['prev']))
                    ok((r['box']!='none')==prev,('campos de via/cesárea',tag,r['box']))
                    vazio = (dmm is None and not rec)
                    ok(r['vazio']==vazio and (r['resOn']==(not vazio)),('vazio',tag,r['vazio'],r['resOn']))
                    if g is not None and g[0]<14: continue   # 1º trimestre: laudo próprio, sem o cartão de placenta
                    if g is None:   # sem IG o app não monta laudo (comportamento anterior) — só a tela importa
                        ok(('Informe a IG' in r['res'])==prev,('sem IG: pede a IG',tag,r['res'][:80])); continue
                    ok(('Placenta:' in r['ld'])==(not vazio),('linha do corpo',tag))
                    ok(('Antecedente de cesárea' in r['ld'])==prev,('cesárea só com prévia',tag))
                    concl=r['conc']
                    if exp=='pp':
                        ok('Placenta prévia,' in concl and '32 semanas' not in concl,('conclusão ≥ 28',tag,concl[-160:]))
                    elif exp=='susp':
                        ok('Suspeita de placenta prévia' in concl and 'transvaginal com 32 semanas' in concl,('conclusão 16–27+6',tag,concl[-160:]))
                    else:
                        ok('placenta prévia' not in concl.lower(),('conclusão sem prévia',tag,concl[-160:]))
                    tam = prev and via=='ta' and exp in ('susp','pp')
                    ok(('avaliada por via transabdominal' in r['chk'])==tam,('confira: via transabdominal',tag))
                    ok((('Placenta prévia' in r['guia']) or ('Suspeita de placenta prévia' in r['guia']))==(exp in ('susp','pp')),('o que investigar',tag))
                    if exp in ('susp','pp'): ok('vasa prévia' in r['guia'],('vasa prévia no investigar',tag))
                    if d is not None and not rec and dmm<=20: ok(('sem recobri-lo' in r['ld']),('sem recobrir no laudo',tag))
                    if rec: ok('recobrindo o orifício interno' in r['ld'],('recobre no laudo',tag))
    # acretismo só com prévia; forma e velamentosa
    r=pg.evaluate(S,{'g':(33,0),'d':'1.2','rec':False,'via':'tv','ces':True,'acr':True})
    ok('Sinais ultrassonográficos sugestivos de acretismo' in r['ld'] and 'acretismo' in r['conc'],('acretismo com prévia',r['conc'][-200:]))
    r=pg.evaluate(S,{'g':(33,0),'d':'3.0','rec':False,'via':'tv','ces':True,'acr':True})
    ok('acretismo' not in r['ld'],('acretismo sem prévia entrou',))
    for forma,txt in (('bilob','Placenta bilobada.'),('acess','Lobo placentário acessório')):
        r=pg.evaluate(S,{'g':(30,0),'d':None,'rec':False,'via':'ta','forma':forma})
        ok(txt in r['ld'] and 'vasa prévia' in r['res'] and 'vasa prévia' in r['guia'],('forma',forma))
    r=pg.evaluate(S,{'g':(30,0),'d':None,'rec':False,'via':'ta','vel':True})
    ok('Inserção velamentosa do cordão umbilical.' in r['ld'] and 'Inserção velamentosa' in r['conc'],('velamentosa',r['conc'][-120:]))
    # gemelar: uma vez só
    r=pg.evaluate(S,{'g':(33,0),'d':'1.0','rec':False,'via':'tv','gem':True})
    ok(r['ld'].count('Placenta prévia,')==1 and r['ld'].count('Placenta: ')==1,('gemelar repetiu a placenta',r['ld'].count('Placenta prévia,'),r['ld'].count('Placenta: ')))
    ok('Gestação múltipla' in r['guia'] and 'vasa prévia' in r['guia'],('gemelar sem vasa prévia no investigar',))
    # sem nada preenchido: nada muda
    r=pg.evaluate(S,{'g':(33,0),'d':None,'rec':False,'via':'ta'})
    ok('Placenta' not in r['ld'] and not r['resOn'] and r['box']=='none',('vazio mexeu no laudo',))
    # distância negativa é implausível → ignorada
    r=pg.evaluate(S,{'g':(33,0),'d':'-1','rec':False,'via':'ta'})
    ok('Placenta' not in r['ld'],('distância negativa entrou no laudo',))
    # recuperação mantém a placenta; Limpar zera
    r=pg.evaluate("""()=>{$('bRst').click();$('sem').value=30;$('dias').value=0;IGSRC='mao';$('plOI').value='1.1';$('plRec').checked=false;
      document.querySelector('.plViaSeg button[data-via="tv"]').click(); $('plVel').checked=true; run();
      var o=coletaEstado(); $('bRst').click(); var limpo=[$('plOI').value,$('plVia').value,$('plVel').checked];
      aplicaEstado(o); return {limpo:limpo, depois:[$('plOI').value,$('plVia').value,$('plVel').checked,ST.estr.plac.cls]};}""")
    ok(r['limpo']==['','ta',False],('Limpar não zerou a placenta',r['limpo']))
    ok(r['depois']==['1.1','tv',True,'pp'],('recuperação perdeu a placenta',r['depois']))
    grupo('20 Placenta por exceção: prévia, janelas, acretismo, vasa prévia (R14.42)',C[0],F)

# ------------------------------------------------------------------ 21 R14.44 tipo de exame
def g_r44(pg):
    """R14.44 → R15.0: o seletor de tipo de exame saiu. Abas do 2º/3º tri sempre as 5; título vem dos dados (Doppler
    preenchido; praxe → morfológica); a frase do Doppler segue o antigo "Obstétrico": peso adequado sem Doppler não
    cita Doppler, feto pequeno sem Doppler cita "não avaliado"; preencher não apaga nada; 1º tri automático."""
    F=[]; C=[0]
    def ok(c,m):
        C[0]+=1
        if not c: F.append(m)
    ST_=r"""()=>({abas:[].filter.call(document.querySelectorAll('.tab'),function(t){return !t.hidden}).map(function(t){return t.dataset.p}),
      t1:$('ldT').textContent.split('\n')[0], conc:textoConclusao(), sint:$('sintRes').textContent, est:$('estBar').textContent.replace(/\s+/g,' ').trim(),
      jan:$('morfoJanela').style.display, seq:getComputedStyle($('seqBox')).display})"""
    BASE=r"""(a)=>{$('bRst').click();$('sem').value=a[0];$('dias').value=a[1];IGSRC='mao';setModo('bio');
      $('bDBP').value=a[2][0];$('bCC').value=a[2][1];$('bCA').value=a[2][2];$('bFL').value=a[2][3];$('mbv').value='4.2';run();}"""
    AIG22=['5.30','19.80','17.20','3.90']
    pg.evaluate(BASE,[22,2,AIG22]); r=pg.evaluate(ST_)
    ok(r['abas']==['p0','p1','p6','p2','p3'],('abas do 2º/3º tri',r['abas']))
    ok(r['t1'].startswith('Ultrassonografia obstétrica — '),('título obstétrico',r['t1']))
    ok('Doppler' not in r['conc'] and 'Sugere-se' not in r['conc'],('conclusão do obstétrico normal',r['conc']))
    ok('Doppler fetal não avaliado' not in r['sint'] and r['seq']=='none',('síntese/territórios sem Doppler',r['sint'][:80],r['seq']))
    pg.evaluate("()=>{$('eUme').value='3.40';run();}"); r=pg.evaluate(ST_)
    ok(r['t1'].startswith('Ultrassonografia morfológica do 2º trimestre — ') and r['jan']=='none',('morfológico pela praxe',r['t1'],r['jan']))
    pg.evaluate("()=>{$('sem').value=30;run();}"); r=pg.evaluate(ST_)
    ok(r['t1'].startswith('Ultrassonografia morfológica do 3º trimestre — ') and r['jan']=='none',('morfológico do 3º tri, sem aviso de janela',r['t1'],r['jan']))
    pg.evaluate(BASE,[22,2,AIG22]); pg.evaluate("()=>{$('utD').value='0.9';$('utE').value='1.0';$('eAtr').value='1.2';run();}")
    r=pg.evaluate(ST_)
    ok('com Dopplervelocimetria' in r['t1'] and r['t1'].startswith('Ultrassonografia obstétrica'),('uterinas medidas: com Doppler; átrio não faz morfológico',r['t1']))
    pg.evaluate("()=>{document.querySelector('.tab[data-p=\"p2\"]').click(); document.querySelector('.tab[data-p=\"p6\"]').click(); document.querySelector('.tab[data-p=\"p1\"]').click();}")
    r=pg.evaluate("()=>[$('utD').value,$('utE').value,$('eAtr').value]")
    ok(r==['0.9','1.0','1.2'],('trocar de aba apagou dado',r))
    pg.evaluate(BASE,[30,2,['7.40','27.00','22.00','5.40']]); r=pg.evaluate(ST_)
    ok('Doppler fetal não avaliado' in r['conc'],('feto pequeno perdeu a frase do Doppler',r['conc'][:200]))
    pg.evaluate("()=>{$('bRst').click();$('sem').value=12;$('dias').value=3;IGSRC='mao';run();}"); r=pg.evaluate(ST_)
    ok(r['abas']==['p0','p4','p5','p3'] and 'Obstétrico' not in r['est'],('1º trimestre',r))
    r=pg.evaluate("""()=>{$('bRst').click();$('sem').value=25;$('dias').value=0;IGSRC='mao';$('eDbo').value='5.0';run();
      var o=coletaEstado(); $('bRst').click(); aplicaEstado(o);
      return [$('ldT').textContent.split('\\n')[0],[].filter.call(document.querySelectorAll('.tab'),function(t){return !t.hidden}).map(function(t){return t.dataset.p})];}""")
    ok(r[0].startswith('Ultrassonografia morfológica do 2º trimestre') and r[1]==['p0','p1','p6','p2','p3'],('recuperação',r))
    grupo('21 Sem tipo de exame: abas, título pelos dados, frase do Doppler (R14.44 → R15.0)',C[0],F)

# ------------------------------------------------------------------ 22 R14.45 → R15.0 faixa do topo
def g_r45(pg):
    """A faixa nunca mostra tipo de exame. R15.0: presa às abas, sempre visível; sem IG diz "IG não definida"; com IG,
    "IG <s d> · origem · trimestre"; o 1º item nunca começa com "·"; peso só no 2º/3º tri."""
    F=[]; C=[0]
    def ok(c,m):
        C[0]+=1
        if not c: F.append(m)
    EST=r"""()=>{var b=$('estBar'), vis=[].filter.call(b.children,function(x){return getComputedStyle(x).display!=='none'});
      return {txt:b.textContent.replace(/\s+/g,' ').trim(), hidden:b.hidden, n:vis.length, ig:$('estIG').textContent,
        first:vis.length?getComputedStyle(vis[0],'::before').content:'none', hb:b.getBoundingClientRect().height};}"""
    ARM=r"""(a)=>{$('bRst').click(); if(a.ig){$('sem').value=a.ig[0];$('dias').value=a.ig[1];IGSRC='mao';}
      if(a.bio){setModo('bio');$('bDBP').value='5.30';$('bCC').value='19.80';$('bCA').value='17.20';$('bFL').value='3.90';}
      if(a.dop){$('auip').value='1.10';} if(a.morfo){$('eUme').value='3.40';}
      run();}"""
    for dop in (False,True):
        for morfo in (False,True):
            for ig in (None,[22,2],[32,0]):
                for bio in (False,True):
                    pg.evaluate(ARM,{'ig':ig,'bio':bio,'dop':dop,'morfo':morfo}); r=pg.evaluate(EST)
                    tag=(dop,morfo,ig,bio)
                    ok(not any(w in r['txt'] for w in ('Obstétrico','Doppler','Morfológ')),('tipo na faixa',tag,r['txt']))
                    ok(not r['hidden'] and r['n']>=1 and r['hb']>0,('faixa sempre visível',tag,r))
                    ok(r['first'] in ('none','normal'),('ponto solto no 1º item',tag,r))
                    ok(r['ig']==('IG não definida' if ig is None else 'IG %ds %dd · informada · 2º/3º tri'%(ig[0],ig[1])),('IG na faixa',tag,r['ig']))
    pg.evaluate("()=>{$('bRst').click();escolheCtx('B');run();}"); r=pg.evaluate(EST)
    ok(r['txt']=='IG não definida' and not r['hidden'],('1º tri sem IG',r))
    pg.evaluate("()=>{$('bRst').click();$('sem').value=25;$('dias').value=0;IGSRC='mao';$('eUme').value='3.4';run(); var o=coletaEstado(); $('bRst').click(); aplicaEstado(o); run();}")
    r=pg.evaluate(EST)
    ok(r['txt'].startswith('IG 25s 0d') and r['first'] in ('none','normal'),('recuperado',r))
    grupo('22 Faixa do topo: sempre visível, sem tipo de exame (R14.45 → R15.0)',C[0],F)

# ------------------------------------------------------------------ 23 R14.46 gemelar revisado
def g_r46(pg):
    """Gemelar revisado: transfusão feto-fetal (FEBRASGO <2/>8; limítrofe no corte; discordância ≥ 4 cm),
    TAPS (estágios 1/2/3; Delphi = limítrofe), conclusão de cada feto descritiva, início precoce/tardio pela
    corionicidade, Gratacós, falso "incompleto", fetos nomeados, amnionicidade, peso informado × informado,
    datação pelo maior feto, laudo sem frases do aplicativo, simetria A/B e faixa do topo."""
    F=[]; C=[0]
    def ok(c,m):
        C[0]+=1
        if not c: F.append(m)
    ARM=r"""(c)=>{ $('bRst').click(); $('sem').value=c.sem; $('dias').value=c.dias||0; IGSRC='mao'; run();
      var g=$('gemelar'); g.checked=true; g.dispatchEvent(new Event('change',{bubbles:true}));
      $('corion').value=c.cor; $('corion').dispatchEvent(new Event('change',{bubbles:true}));
      ['A','B'].forEach(function(f){ trocaFeto(f); var d=c[f]; if(d.pDir) setModo('dir'); else setModo('bio');
        if(d.diast==='int') diastIntOpt(true); Object.keys(d).forEach(function(k){$(k).value=d[k];}); run(); });
      trocaFeto(c.fim||'A'); run();
      var ld=$('ldT').textContent, i=ld.indexOf('CONCLUSÃO');
      return {T:ST.gemT, s:ST.sfgr, disc:ST.disc, ld:ld, conc:i>=0?ld.slice(i):'', sint:$('sintRes').innerText};}"""
    N4={'bDBP':'8.20','bCC':'29.50','bCA':'28.00','bFL':'6.20'}
    N22A={'bDBP':'5.30','bCC':'19.80','bCA':'17.20','bFL':'3.90'}; N22B={'bDBP':'5.40','bCC':'20.00','bCA':'17.80','bFL':'4.00'}
    N30={'bDBP':'7.70','bCC':'28.00','bCA':'26.00','bFL':'5.80'}
    def cas(sem,cor,A,B,fim='A'): return pg.evaluate(ARM,{'sem':sem,'cor':cor,'A':A,'B':B,'fim':fim})
    # 1. transfusão feto-fetal
    for (a,b,esp) in (('1.5','9.0','stff'),('1.9','8.1','stff'),('2.0','8.0','stff-lim'),('1.5','8.0','stff-lim'),
                      ('2.0','9.0','stff-lim'),('2.1','7.9','disc-la'),('2.5','6.5','disc-la'),('2.5','6.4',None),('3.0','6.9',None),('9.0','1.5','stff')):
        r=cas(22,'mc',dict(N22A,mbv=a),dict(N22B,mbv=b)); st=(r['T'] or {}).get('la',{}) or {}
        ok(st.get('st')==esp,('STFF',a,b,st,esp))
        if esp=='stff':
            ok('compatível com síndrome de transfusão feto-fetal' in r['conc'] and 'Achado de alta gravidade (critério de transfusão feto-fetal)' in r['conc'],('STFF laudo',a,b))
            ok(st.get('don')==('A' if float(a)<float(b) else 'B'),('doador',a,b,st))
    for cor in ('dc','mcma'):
        r=cas(22,cor,dict(N22A,mbv='1.5'),dict(N22B,mbv='9.0'))
        ok(not ((r['T'] or {}).get('la')),('STFF fora da MC diamniótica',cor,r['T']))
    r=cas(22,'mc',dict(N22A,mbv='1.5',diast='pres'),dict(N22B,mbv='10.5',dv='rev'))
    ok(r['T']['la']['q3']==['B'] and 'estágio III de Quintero' in r['conc'],('Quintero III',r['T']['la']))
    # 2. TAPS — PSV em cm/s escolhida para o MoM desejado em 30+0 (mediana Mari)
    med=pg.evaluate("()=>medPSV(30)")
    for (ma,mb,est,lim) in ((1.6,0.79,1,False),(1.8,0.7,2,False),(1.72,0.85,1,False),(1.45,0.40,0,True),(1.4,0.9,0,False)):
        r=cas(30,'mc',dict(N30,psv='%.4f'%(ma*med)),dict(N30,bCC='28.10',psv='%.4f'%(mb*med)))
        tp=(r['T'] or {}).get('taps')
        ok((tp or {}).get('est',0)==est and bool((tp or {}).get('lim'))==lim,('TAPS',ma,mb,tp))
    r=cas(30,'mc',dict(N30,psv='%.4f'%(1.8*med),auip='1.2',diast='zero'),dict(N30,bCC='28.10',psv='%.4f'%(0.7*med)))
    ok(r['T']['taps']['est3'] and 'estágio 3' in r['conc'],('TAPS 3',r['T']['taps']))
    r=cas(30,'dc',dict(N30,psv='%.4f'%(1.8*med)),dict(N30,bCC='28.10',psv='%.4f'%(0.7*med)))
    ok(r['T'] is None,('TAPS na dicoriônica',r['T']))
    # 3. conclusão de cada feto descritiva; 5. fetos nomeados; 7. sem frases do aplicativo; 8. amnionicidade
    B2={'bDBP':'7.70','bCC':'27.80','bCA':'24.20','bFL':'5.80','auip':'1.45','acmip':'1.50','diast':'pres'}
    r=cas(32,'dc',dict(N4,auip='0.95',acmip='1.90',diast='pres'),B2)
    ok('segundo critérios Delphi/ISUOG' not in r['ld'] and 'Feto B: PFE 1395 g' in r['conc'],('feto descritivo',r['conc'][:300]))
    ok(r['s']['cls']=='sfgr' and r['s']['feto']=='B' and all('um dos fetos' not in x for x in r['s']['crit']),('nomeado',r['s']))
    ok('de início tardio' in r['conc'] and 'dicoriônica e diamniótica' in r['ld'],('início/amnionicidade',r['conc'][:200]))
    ok(not any(w in r['ld'] for w in ('aplicativo','este módulo','transfusor')),('frase do app no laudo',))
    ok(r['conc'].count('discordância de peso')+r['conc'].count('Discordância de peso')==1,('discordância repetida',r['conc']))
    rB=cas(32,'dc',dict(N4,auip='0.95',acmip='1.90',diast='pres'),B2,fim='B')
    ok(rB['ld']==r['ld'],('simetria A/B do laudo',))
    r=cas(32,'mc',{'bDBP':'7.90','bCC':'28.30','bCA':'25.50','bFL':'5.90'},{'bDBP':'7.80','bCC':'28.00','bCA':'25.00','bFL':'5.85'})
    ok(r['s']['cls']=='both-sga-overlap' and 'restrição de crescimento segundo' not in r['ld'],('ambos PIG',r['s']['cls']))
    # 6 + 10. início pela corionicidade e Gratacós
    A26={'bDBP':'6.50','bCC':'24.00','bCA':'21.50','bFL':'4.80','auip':'1.10','diast':'pres'}
    for cor,d,ini,gr in (('mc','int','tardio','III'),('mc','zero','tardio','II'),('mc','pres','tardio','I'),('dc','zero','precoce',None)):
        r=cas(26,cor,A26,{'bDBP':'6.10','bCC':'22.50','bCA':'18.80','bFL':'4.40','auip':'1.90','diast':d})
        ok(r['s']['cls']=='sfgr' and ('início '+ini) in r['conc'],('início',cor,d,r['conc'][:250]))
        ok((('tipo '+gr+' de Gratacós') in r['conc']) if gr else ('Gratacós' not in r['conc']),('Gratacós',cor,d))
    # 4. "incompleto" só quando ainda poderia fechar
    r=cas(22,'mc',dict(N22A),dict(N22B))
    ok(r['s']['cls']=='sem-criterio' and 'incompleta' not in r['ld'],('só a umbilical faltando',r['s']))
    r=cas(30,'mc',dict(N30,auip='1.00',diast='pres'),dict(N30,auip='1.05',diast='pres'))
    ok(r['s']['cls']=='sem-criterio',('pesos iguais, umbilicais normais',r['s']))
    r=cas(30,'mc',{'pDir':'1500'},{'pDir':'1400'})
    ok(r['s']['cls']=='incompleto' and len(r['s']['falta'])==2,('dois em aberto = incompleto',r['s']))
    # 9. dois pesos informados = comparáveis
    ok(r['disc']['formalComparavel'] is True,('dir×dir',r['disc']))
    r=cas(30,'dc',{'pDir':'1500'},dict(N30))
    ok(r['disc']['formalComparavel'] is False,('bio×dir',r['disc']))
    # 11. datação pelo maior feto
    d=pg.evaluate(r"""()=>{ $('bRst').click(); var g=$('gemelar'); g.checked=true; g.dispatchEvent(new Event('change',{bubbles:true}));
      $('corion').value='dc'; run();
      function fill(v){ ['bDBP','bCC','bCA','bFL'].forEach(function(i,k){$(i).value=v[k];}); run(); }
      fill(['7.40','26.80','23.00','5.50']); $('bBioApply').click(); var ig1=sdT(getGA());
      trocaFeto('B'); fill(['8.20','29.50','28.00','6.20']);
      var aviso=$('igbRes').innerText, bt=$('bBioApply').textContent, vis=$('bBioApply').style.display!=='none';
      $('bBioApply').click(); return {ig1:ig1, aviso:aviso, bt:bt, vis:vis, ig2:sdT(getGA()), depois:$('igbRes').innerText};}""")
    ok(d['vis'] and 'feto menor' in d['aviso'] and d['bt']=='Datar pelo feto B (maior CC)' and d['ig2']!=d['ig1'] and d['depois']=='',('datação pelo maior',d))
    # 13. faixa do topo: gemelar sem IG sem "·" solto; faixa vazia some
    f=pg.evaluate(r"""()=>{ $('bRst').click(); var g=$('gemelar'); g.checked=true; g.dispatchEvent(new Event('change',{bubbles:true})); run();
      var b=$('estBar'), vis=[].filter.call(b.children,function(x){return getComputedStyle(x).display!=='none'});
      var r={txt:b.textContent.trim(), first:vis.length?getComputedStyle(vis[0],'::before').content:'none'};
      g.checked=false; g.dispatchEvent(new Event('change',{bubbles:true})); run();
      r.vazia=getComputedStyle(b).display; r.txt2=b.textContent.trim(); return r;}""")
    ok(f['txt']!='' and f['first'] in ('none','normal') and f['vazia']!='none' and f['txt2']=='IG não definida',('faixa (R15.0: sempre visível)',f))
    grupo('23 Gemelar revisado: transfusão feto-fetal, TAPS, conclusão por feto, Gratacós, datação (R14.46)',C[0],F)

# ------------------------------------------------------------------ 24 R14.47 auditoria geral
def g_r47(pg):
    """Auditoria geral: laudo do 1º tri com a IG do exame e CCN em mm; campo em branco fora do laudo (vai ao
    Confira); UTD por exceção; percentil da conclusão = rótulo do corpo; conclusão sem achados repetidos;
    contraste do tema claro; resumo nos cartões recolhidos; textos sem jargão."""
    F=[]; C=[0]
    def ok(c,m):
        C[0]+=1
        if not c: F.append(m)
    CHK="()=>[].map.call(document.querySelectorAll('#chk .chk-ln'),function(l){return l.textContent})"
    # 1º tri: IG do exame, origem, mm, sem instrução; aviso de redatação só acima do limiar ACOG
    for sem,dias,src,bcf,redata in ((13,2,'dum','',False),(13,6,'dum','pres',True),(12,4,'mao','pres',False),(10,0,'usant','',True)):
        r=pg.evaluate("""(a)=>{$('bRst').click();$('sem').value=a[0];$('dias').value=a[1];IGSRC=a[2];run();
          $('rCCN').value='6.10';$('rTN').value='0.16';$('semBcf').value=a[3];run();
          return {ld:$('ldT').textContent, ig:sdT(getGA())};}""",[sem,dias,src,bcf])
        chk=' '.join(pg.evaluate(CHK)); l0=r['ld'].split('\n')[0]
        ok(l0.startswith('Ultrassonografia de primeiro trimestre — %d semanas e %d %s'%(sem,dias,'dia' if dias==1 else 'dias')),('IG do exame no laudo',l0))   # R14.48: sem "dia(s)"
        ok(('datada pelo comprimento' not in l0) and (('última menstruação' in l0) if src=='dum' else True),('origem',src,l0))
        ok('preencha' not in r['ld'] and 'CCN de 61,0 mm' in r['ld'] and 'cm.' not in r['ld'].split('\n')[2],('texto do 1º tri',r['ld'][:300]))
        ok(('Atividade cardíaca' in chk)==(bcf==''),('aviso da atividade cardíaca',bcf,chk[:200]))
        ok(('redata-se pelo CCN' in chk)==redata,('aviso de redatação',sem,dias,chk[:300]))
    # UTD por exceção
    r=pg.evaluate("""()=>{$('bRst').click();$('sem').value=22;$('dias').value=3;IGSRC='mao';setModo('bio');
      $('bDBP').value='5.30';$('bCC').value='19.80';$('bCA').value='17.20';$('bFL').value='3.90';$('ePel').value='0.6';run();
      return $('ldT').textContent;}""")
    chk=' '.join(pg.evaluate(CHK))
    ok('classificada como UTD A1 (APRPD de 0,60 cm), sem outros achados' in r and 'faltam' not in r and 'incompleta' not in r,('UTD A1 por exceção',r[:400]))
    ok('considera sem alteração o que ficou em branco' in chk,('UTD no Confira',chk[:300]))
    r=pg.evaluate("()=>{$('ePel').value='0.8';run();return $('ldT').textContent;}")
    ok('UTD A2-3' in r,('A2-3 pela pelve continua',r[:300]))
    # percentil da conclusão = rótulo do corpo; achados uma vez só; diástole em branco fora do laudo
    r=pg.evaluate("""()=>{$('bRst').click();$('sem').value=32;$('dias').value=2;IGSRC='mao';setModo('bio');
      $('bDBP').value='8.10';$('bCC').value='29.50';$('bCA').value='26.40';$('bFL').value='6.10';$('mbv').value='4.2';
      $('auip').value='1.30';$('acmip').value='1.50';$('diast').value='pres';run(); return $('ldT').textContent;}""")
    conc=r[r.index('CONCLUSÃO'):]
    ok('(percentil 10,4)' in conc and 'PFE: 1730 g (p10,4)' in r,('percentil da conclusão',conc[:200]))
    ok(conc.count('Ciobanu 2019/FMF')==1 and 'associado a' not in conc and 'alteração placentária: ' in conc,('achados repetidos',conc[:400]))
    r=pg.evaluate("()=>{$('mbv').value='9.5';run();var l=$('ldT').textContent;return l.slice(l.indexOf('CONCLUSÃO'));}")
    ok('associado a polidrâmnio' in r,('polidrâmnio fica como associado',r[:400]))
    r=pg.evaluate("""()=>{$('bRst').click();$('sem').value=30;$('dias').value=0;IGSRC='mao';$('auip').value='1.00';$('diast').value='na';run();return $('ldT').textContent;}""")
    chk=' '.join(pg.evaluate(CHK))
    ok('Fluxo diastólico' not in r and 'fluxo diastólico não foi avaliado' in chk,('diástole em branco',r[-200:],chk[:200]))
    # gemelar: "falta avaliar" e "não avaliados" fora do laudo
    r=pg.evaluate("""()=>{$('bRst').click();$('sem').value=30;$('dias').value=0;IGSRC='mao';run();
      var g=$('gemelar'); g.checked=true; g.dispatchEvent(new Event('change',{bubbles:true})); $('corion').value='mc'; run();
      setModo('dir'); $('pDir').value='1500'; run(); trocaFeto('B'); setModo('dir'); $('pDir').value='1400'; run(); trocaFeto('A'); run();
      return $('ldT').textContent;}""")
    chk=' '.join(pg.evaluate(CHK))
    ok('falta avaliar' not in r and 'não avaliados' not in r and 'incompleta' not in r,('gemelar sem falta no laudo',r[-400:]))
    ok('Restrição seletiva — falta avaliar' in chk,('gemelar no Confira',chk[:300]))
    # tela: contraste, botão da TN, resumo dos cartões, textos
    t=pg.evaluate("""()=>{$('bRst').click();$('sem').value=32;$('dias').value=2;IGSRC='mao';$('mbv').value='1.5';run();
      var s=document.querySelector('#laBox > summary'); $('laBox').open=false; var r1=$('resLA').textContent, v1=getComputedStyle($('resLA')).display;
      $('laBox').open=true; var v2=getComputedStyle($('resLA')).display; $('laBox').open=false;
      return {ink3:getComputedStyle(document.documentElement).getPropertyValue('--ink3').trim(), tn:$('bCurvaTN').className,
        r1:r1, v1:v1, v2:v2, alt:$('resLA').className, txt:document.body.innerText};}""")
    ok(t['ink3'].lower() in ('#647079',) or t['ink3']=='',('cinza terciário',t['ink3']))
    ok('tgb' in t['tn'],('botão da TN',t['tn']))
    ok(t['r1']=='· MBV 1,5 cm · oligoâmnio' and t['v1']!='none' and t['v2']=='none' and 'alt' in t['alt'],('resumo do líquido',t['r1'],t['v1'],t['v2']))
    ok(not any(w in t['txt'] for w in ('política do app','estatística indeterminada','heurística interna','pulsatility index')),('jargão na tela',))
    d=pg.evaluate("""()=>{$('bRst').click();$('sem').value=22;$('dias').value=0;IGSRC='mao';setModo('bio');
      $('bDBP').value='5.30';$('bCC').value='19.80';$('bCA').value='17.20';$('bFL').value='3.90';run();
      var g=getGA(), gb=igBio(val('bDBP'),val('bCC'),val('bCA'),val('bFL')); var o=sd(gb); $('sem').value=o.s; $('dias').value=o.d; run();
      return $('igRes').innerText+' | '+(document.querySelector('#igRes .s')||{}).textContent;}""")
    ok('0s 0d' not in d,('diferença zero',d[:200]))
    grupo('24 Auditoria geral: 1º tri, campo em branco, UTD, conclusão, contraste, resumos (R14.47)',C[0],F)

# ------------------------------------------------------------------ 25 R14.48 avaliação em 8 etapas
def g_r48(pg):
    """FCF embrionária no laudo; FCF com a atividade em branco = presente; FCF com atividade ausente vai ao Confira;
    "2 dias" e singular/plural no laudo; "Ducto venoso"; CCN fora da faixa; leitura integrada com o termo do laudo;
    rótulos ligados aos campos; área de toque dos botões de curva; referências novas; pq() removida. E ramos raros
    que a suíte não exercitava: velocidade com queda, uterinas do 1º tri acima do p95, viabilidade transabdominal,
    saco pequeno para o embrião, FCF em 6s2d, gemelar com os dois fetos pequenos."""
    F=[]; C=[0]
    def ok(c,m):
        C[0]+=1
        if not c: F.append(m)
    CHK="()=>[].map.call(document.querySelectorAll('#chk .chk-ln'),function(l){return l.textContent}).join(' ')"
    V1="""(a)=>{$('bRst').click();$('sem').value=a[0];$('dias').value=a[1];IGSRC='mao';run();VIA_VIAB='tv';
      $('rCCN').value=a[2];$('semBcf').value=a[3];$('fcf1').value=a[4];if(a[5])$('rTN').value=a[5];run();
      return {ld:$('ldT').textContent, bcf:$('semBcf').value, badge:$('ldBadge').textContent};}"""
    # FCF com atividade presente
    r=pg.evaluate(V1,[7,0,'1.0','pres','140',''])
    ok('Embrião com CCN de 10,0 mm e atividade cardíaca presente, com frequência de 140 bpm.' in r['ld'],('FCF no laudo',r['ld']))
    ok(r['ld'].startswith('Ultrassonografia obstétrica — 7 semanas e 0 dias.'),('"0 dias"',r['ld'][:80]))
    bPres=r['badge']
    # FCF com a atividade em branco: vira "Presente"
    r=pg.evaluate(V1,[7,0,'1.0','','140','']); chk=pg.evaluate(CHK)
    ok(r['bcf']=='pres' and 'frequência de 140 bpm' in r['ld'] and 'Atividade cardíaca' not in chk,('FCF com atividade em branco',r['bcf'],r['ld'],chk[:200]))
    # FCF com atividade ausente: contradição no Confira, FCF fora do laudo, fora do contador
    r=pg.evaluate(V1,[7,0,'1.0','aus','140','']); chk=pg.evaluate(CHK)
    ok('marcada como ausente' in chk and 'frequência de' not in r['ld'] and r['bcf']=='aus',('FCF com atividade ausente',r['ld'],chk[:300]))
    ok(int(r['badge'] or 0)==int(bPres or 0)-1,('contador sem a FCF fora do laudo',bPres,r['badge']))
    # sem FCF: texto antigo, sem mudança
    r=pg.evaluate(V1,[7,0,'1.0','pres','',''])
    ok('Embrião com atividade cardíaca presente e CCN de 10,0 mm.' in r['ld'],('sem FCF',r['ld']))
    # rastreio 11-14 com FCF e TN
    r=pg.evaluate(V1,[12,4,'6.10','pres','158','0.16'])
    ok('Feto com CCN de 61,0 mm e atividade cardíaca presente, com frequência de 158 bpm.' in r['ld'] and 'Translucência nucal de 1,6 mm' in r['ld'],('FCF no rastreio',r['ld']))
    ok(r['ld'].startswith('Ultrassonografia de primeiro trimestre — 12 semanas e 4 dias'),('"4 dias"',r['ld'][:90]))
    # CCN fora da faixa de cálculo
    r=pg.evaluate(V1,[12,4,'61','','',''])
    ok(r['ld'].startswith('CCN de 61,00 cm fora da faixa de cálculo da referência (0,2 a 12,0 cm)') and 'Preencha' not in r['ld'],('CCN fora da faixa',r['ld']))
    # "1 dia" no laudo do 2º/3º tri; nenhum "dia(s)"
    r=pg.evaluate("""()=>{$('bRst').click();$('sem').value=30;$('dias').value=1;IGSRC='mao';setModo('bio');
      $('bDBP').value='7.70';$('bCC').value='28.00';$('bCA').value='25.50';$('bFL').value='5.70';run();return $('ldT').textContent;}""")
    ok(r.startswith('Ultrassonografia obstétrica — 30 semanas e 1 dia.') and 'dia(s)' not in r,('"1 dia"',r[:80]))
    # Ducto venoso com maiúscula; singular/plural dos parâmetros em atenção
    B="""$('bRst').click();$('sem').value=32;$('dias').value=2;IGSRC='mao';setModo('bio');
      $('bDBP').value='8.10';$('bCC').value='29.50';$('bCA').value='28.40';$('bFL').value='6.10';$('auip').value='0.95';$('acmip').value='1.90';$('diast').value='pres';"""
    r=pg.evaluate("()=>{"+B+"$('psv').value='68';$('dvip').value='0.55';run();var l=$('ldT').textContent;return l;}")
    ok('\nDucto venoso: IP 0,55' in r and '\nducto venoso' not in r,('Ducto venoso',r))
    ok('Há parâmetro Doppler fetal limítrofe ou de atenção, descrito acima.' in r,('singular',r[r.find('CONCLUS'):]))
    r=pg.evaluate("()=>{"+B+"$('auip').value='1.22';$('psv').value='68';run();var l=$('ldT').textContent;return l;}")
    ok('Há parâmetros Doppler fetais limítrofes ou de atenção, descritos acima.' in r and '(s)' not in r,('plural',r[r.find('CONCLUS'):]))
    # achados morfológicos: singular e plural
    r=pg.evaluate("""()=>{$('bRst').click();$('sem').value=22;$('dias').value=3;IGSRC='mao';setModo('bio');
      $('bDBP').value='5.30';$('bCC').value='19.80';$('bCA').value='17.20';$('bFL').value='3.90';$('eAtr').value='1.1';run();
      var a=$('ldT').textContent; $('eCT').value='10.0'; run(); return [a,$('ldT').textContent];}""")
    ok('com achado morfológico: ventriculomegalia.' in r[0],('singular morfológico',r[0][-200:]))
    ok('com achados morfológicos: ' in r[1] and '(s)' not in r[1],('plural morfológico',r[1][-260:]))
    # leitura integrada com o termo do laudo
    t=pg.evaluate("()=>{"+B.replace("'0.95'","'1.30'").replace("'1.90'","'1.50'")+"run();abasTipo();return $('dopBox').innerText;}")
    ok('Sinais de alteração placentária com redistribuição' in t and 'nsuficiência' not in t,('leitura integrada',t[:200]))
    # rótulos ligados; nome acessível; foco ao tocar no nome
    r=pg.evaluate("""()=>{ var sem=[]; ['sem','dias','bDBP','bCA','mbv','auip','acmip','utD','dvip','dv','corion','eColo','eAtr','rTN','rCCN','semBcf','fcf1','ePla','dtHojeM','dtDumY'].forEach(function(i){
        var e=$(i); if(!e||!((e.labels&&e.labels.length)||e.getAttribute('aria-label'))) sem.push(i); });
      var ov=[].find.call(document.querySelectorAll('label'),function(x){return /O que você está vendo/.test(x.textContent)});
      $('bRst').click(); $('sem').value=32; run(); abasTipo();
      [].find.call(document.querySelectorAll('.tab'),function(x){return x.dataset.p==='p2'&&!x.hidden}).click();
      document.querySelector('label[for=acmip]').click();
      return {sem:sem, ov:ov?ov.htmlFor:'?', foco:document.activeElement.id};}""")
    ok(not r['sem'] and r['ov']=='' and r['foco']=='acmip',('rótulos',r))
    # área de toque dos botões de curva (6 px acima e abaixo do botão ainda é o botão)
    r=pg.evaluate("""()=>{[].find.call(document.querySelectorAll('.tab'),function(x){return x.dataset.p==='p1'&&!x.hidden}).click();
      var b=$('bCurva'); b.scrollIntoView({block:'center'}); var q=b.getBoundingClientRect(), x=q.left+q.width/2;
      var e1=document.elementFromPoint(x,q.top-6), e2=document.elementFromPoint(x,q.bottom+6);
      return [!!(e1&&e1.closest('.tgb')===b), !!(e2&&e2.closest('.tgb')===b)];}""")
    ok(r==[True,True],('área de toque',r))
    # referências novas, pq() removida, versão
    r=pg.evaluate("()=>({ref:$('refOv').innerHTML, pq:typeof pq, v:APP_VERSAO})")
    for k in ('Committee Opinion 700','Papageorghiou','Gemelar — transfusão feto-fetal','Gemelar — TAPS','Gemelar — início e tipo','Placenta e orifício interno','<i>Pediatr Radiol</i> 2022;52:740-751'):
        ok(k in r['ref'],('referência',k))
    ok(r['pq']=='undefined',('pq removida',r['pq']))   # versão conferida no grupo da versão atual
    # ---- ramos raros
    r=pg.evaluate("""()=>{$('bRst').click();$('sem').value=32;$('dias').value=0;IGSRC='mao';setModo('bio');
      $('bDBP').value='7.60';$('bCC').value='28.00';$('bCA').value='25.00';$('bFL').value='5.80';run();
      $('dtHojeD').value='11';$('dtHojeM').value='10';$('dtHojeY').value='2026';
      $('vPeso').value='1500';$('vD').value='13';$('vM').value='09';$('vY').value='2026';
      ['dtHojeD','vPeso','vD','vM','vY'].forEach(function(i){$(i).dispatchEvent(new Event('input',{bubbles:true}));});run();
      return {dias:ST.vel&&ST.vel.dias, dq:ST.vel&&ST.vel.dq, ld:$('ldT').textContent};}""")
    ok(r['dias']==28 and r['dq']<-50 and 'queda do percentil de peso de p96 para' in r['ld'] and 'desaceleração do crescimento fetal' in r['ld'],('velocidade',r))
    r=pg.evaluate("""()=>{$('bRst').click();$('sem').value=12;$('dias').value=4;IGSRC='mao';run();VIA_UT='tv';
      $('rCCN').value='6.10';$('semBcf').value='pres';$('rUtD').value='2.6';$('rUtE').value='2.8';run();return {f:ST.rut&&ST.rut.flag, ld:$('ldT').textContent};}""")
    ok(r['f']=='alto' and 'acima do percentil 95 para a idade gestacional (Gómez 2008)' in r['ld'] and 'O achado isolado não determina risco individual' in r['ld'],('uterinas do 1º tri',r))
    r=pg.evaluate("""()=>{$('bRst').click();$('sem').value=7;$('dias').value=0;IGSRC='mao';run();VIA_VIAB='ta';$('rCCN').value='1.0';$('semBcf').value='aus';run();
      return {c:ST.tri1&&ST.tri1.cls, ld:$('ldT').textContent};}""")
    ok(r['c']=='suspeito' and 'abaixo do critério transabdominal (15 mm), não permitindo diagnóstico definitivo' in r['ld'],('viabilidade transabdominal',r))
    r=pg.evaluate("""()=>{$('bRst').click();$('sem').value=7;$('dias').value=0;IGSRC='mao';run();VIA_VIAB='tv';$('rCCN').value='1.0';$('semBcf').value='pres';
      setSacRelEnabled(true);$('dmsg').value='1.3';run();return {f:ST.rel&&ST.rel.flag, t:$('relRes').innerText};}""")
    ok(r['f']=='peq' and 'reavaliação em 7 a 10 dias' in r['t'],('saco pequeno',r))
    r=pg.evaluate("""()=>{$('bRst').click();$('sem').value=6;$('dias').value=2;IGSRC='mao';run();$('rCCN').value='0.5';$('semBcf').value='pres';$('fcf1').value='105';run();
      return {p:ST.fcf1&&ST.fcf1.prog, t:$('fcf1Res').innerText, ld:$('ldT').textContent};}""")
    ok(r['p'] is None and '6s2d: zona temporal indeterminada' in r['t'] and 'frequência de 105 bpm' in r['ld'],('FCF em 6s2d',r))
    r=pg.evaluate("""()=>{$('bRst').click();$('sem').value=30;$('dias').value=0;IGSRC='mao';run();
      var g=$('gemelar'); g.checked=true; g.dispatchEvent(new Event('change',{bubbles:true})); $('corion').value=''; run();
      setModo('dir'); $('pDir').value='1050'; run(); trocaFeto('B'); setModo('dir'); $('pDir').value='1000'; run(); trocaFeto('A'); run();
      return {c:ST.sfgr&&ST.sfgr.cls, ld:$('ldT').textContent};}""")
    ok(r['c']=='both-sga-overlap' and 'Ambos os fetos com PFE abaixo do percentil 10' in r['ld'] and 'a classificação final depende de revisão clínica' in r['ld'],('gemelar com os dois pequenos',r['c'],r['ld'][-400:]))
    grupo('25 Avaliação em 8 etapas: FCF no laudo, plural, rótulos, toque, referências + ramos raros (R14.48)',C[0],F)

# ------------------------------------------------------------------ 26 R14.49 auditoria externa
def g_r49(pg):
    """Queda longitudinal no percentil bruto (sem o corte de exibição p0,4–p99,4) e com "≥ 2 quartis" (FEBRASGO nº 90,
    2026), 21 dias mantidos; CPR sem o corte de 1,3 (só < p5 é atenção; < 1,0 acima do p5 é alerta só na tela; sem
    referência = não classificável); Hadlock acima de 40 semanas como extensão (Confira); referências de RCF."""
    F=[]; C=[0]
    def ok(c,m):
        C[0]+=1
        if not c: F.append(m)
    CHK="()=>[].map.call(document.querySelectorAll('#chk .chk-ln'),function(l){return l.textContent}).join(' ')"
    mu=lambda g:0.578+0.332*g-0.00354*g*g
    pr=lambda w,g:100*Phi((math.log(w)-mu(g))/0.12)
    VEL="""(a)=>{$('bRst').click();$('sem').value=a[0];$('dias').value=0;IGSRC='mao';setModo('dir');$('pDir').value=String(a[1]);
      if(a[4]){CURVA='ig21';}run();
      $('dtHojeD').value='11';$('dtHojeM').value='10';$('dtHojeY').value='2026';
      var d=new Date(2026,9,11-a[3]); $('vPeso').value=String(a[2]);$('vD').value=String(d.getDate());$('vM').value=String(d.getMonth()+1);$('vY').value=String(d.getFullYear());
      ['dtHojeD','vPeso','vD','vM','vY','pDir'].forEach(function(i){$(i).dispatchEvent(new Event('input',{bubbles:true}));});run();
      return {v:ST.vel, t:$('vRes').textContent, rawN:pctAtivoRaw(a[1],a[0]), rawP:pctAtivoRaw(a[2],a[0]-a[3]/7)};}"""
    # caso da auditoria: 32+0 2758 g (p99,80) → 36+0 2810 g (p49,59), 28 dias
    r=pg.evaluate(VEL,[36,2810,2758,28,False]); dq=pr(2810,36)-pr(2758,32)
    ok(abs(r['v']['dq']-dq)<1e-9 and r['v']['delphi'] is True and r['v']['qPrev']==99.4 and abs(r['v']['qPrevRaw']-pr(2758,32))<1e-9,('queda no bruto',dq,r['v']))
    # cauda inferior: o atual abaixo de p0,4 entra bruto na conta
    wPrev=round(math.exp(mu(32)+0.12*0.0),0); wNow=round(math.exp(mu(36)+0.12*(-2.9)),0)
    r=pg.evaluate(VEL,[36,int(wNow),int(wPrev),28,False]); dq=pr(wNow,36)-pr(wPrev,32)
    ok(r['v']['qNow']==0.4 and r['v']['qNowRaw']<0.4 and abs(r['v']['dq']-dq)<1e-9,('cauda inferior',dq,r['v']))
    # INTERGROWTH: mesma regra (bruto)
    r=pg.evaluate(VEL,[36,2810,2700,28,True])
    ok(r['v']['qPrevRaw']>99.4 and abs(r['v']['dq']-(r['rawN']-r['rawP']))<1e-12,('INTERGROWTH bruto',r['v']))
    # operador ≥ 50 e os 21 dias: fronteira exata (percentil bruto substituído só neste teste)
    B="""(a)=>{var o=window.pctAtivoRaw; window.pctAtivoRaw=function(w,g){return g>=a[1]-0.01?a[2]:a[3];};
      try{ $('bRst').click();$('sem').value=a[1];$('dias').value=0;IGSRC='mao';setModo('dir');$('pDir').value='2500';run();
      $('dtHojeD').value='11';$('dtHojeM').value='10';$('dtHojeY').value='2026';
      var d=new Date(2026,9,11-a[0]); $('vPeso').value='2400';$('vD').value=String(d.getDate());$('vM').value=String(d.getMonth()+1);$('vY').value=String(d.getFullYear());
      ['dtHojeD','vPeso','vD','vM','vY'].forEach(function(i){$(i).dispatchEvent(new Event('input',{bubbles:true}));});run();
      return {d:ST.vel.delphi, dq:ST.vel.dq, t:$('vRes').textContent}; } finally { window.pctAtivoRaw=o; run(); } }"""
    for dias,qn,qp,esp in ((21,25,75,True),(21,25.01,75,False),(20,10,75,False),(28,24.99,75,True)):
        r=pg.evaluate(B,[dias,36,qn,qp])
        ok(r['d']==esp,('operador/intervalo',dias,qn,qp,r))
        if esp: ok('Redução de 2 quartis ou mais' in r['t'] and 'Protocolo' in r['t'],('texto do critério',r['t'][:300]))
        if dias<21 and qp-qn>=50: ok('Intervalo insuficiente' in r['t'],('menos de 21 dias',r['t'][:200]))
    # CPR
    CP="""(a)=>{$('bRst').click();$('sem').value=a[0];$('dias').value=0;IGSRC='mao';setModo('dir');$('pDir').value=String(Math.round(medP(a[0])));
      $('auip').value=a[1];$('acmip').value=a[2];$('diast').value='pres';run();var l=$('ldT').textContent;var sd=statusDopplerFetal();
      return {f:ST.cpr.flag,ref:ST.cpr.temRef,au:ST.au&&ST.au.flag,acm:ST.acm&&ST.acm.flag,at:sd.atencao,n:sd.nAtencao,nc:sd.naoClassificaveis,cls:$('cprRes').className,card:$('cprRes').innerText,ld:l};}"""
    r=pg.evaluate(CP,[20,'1.25','1.50'])   # CPR 1,20 com p5 ≈ 0,846
    ok(r['f']=='ok' and not r['at'] and 'atenção' not in r['ld'] and 'sem alterações' in r['ld'] and 'p5 nesta IG' in r['card'],('CPR 1,20 em 20 sem',r))
    r=pg.evaluate(CP,[24,'1.25','1.55'])   # CPR 1,24 com p5 ≈ 1,094
    ok(r['f']=='ok' and not r['at'] and 'atenção' not in r['ld'],('CPR 1,24 em 24 sem',r['f'],r['ld'][-200:]))
    r=pg.evaluate(CP,[20,'1.40','1.26'])   # CPR 0,90: abaixo de 1,0, acima do p5
    ok(r['f']=='inv-abs' and 'wr' in r['cls'] and not r['at'] and 'atenção' not in r['ld'],('CPR < 1,0 acima do p5',r))
    r=pg.evaluate(CP,[30,'1.20','1.40'])   # CPR abaixo do p5
    ok(r['f']=='inv' and r['at'] and 'abaixo do p5' in r['ld'],('CPR < p5',r['f'],r['ld'][-250:]))
    r=pg.evaluate(CP,[18,'1.25','1.50'])   # sem referência (Ciobanu começa em 20+0)
    ok(r['f']=='semref' and not r['ref'] and 'CPR' in r['nc'] and 'Sem referência aplicável' in r['card'],('CPR sem referência',r))
    # Hadlock acima de 40 semanas: aviso de extensão no Confira
    H="""(a)=>{$('bRst').click();$('sem').value=a[0];$('dias').value=a[1];IGSRC='mao';setModo('dir');$('pDir').value='3500';if(a[2])CURVA='ig21';run();return 1;}"""
    for sem,dias,ig21,esp in ((40,3,False,'Hadlock 1991 (tabela original de 10 a 40 semanas'),(41,0,False,'Hadlock 1991'),(40,3,True,'INTERGROWTH-21st'),(40,0,False,None),(39,6,False,None)):
        pg.evaluate(H,[sem,dias,ig21]); chk=pg.evaluate(CHK)
        ok((esp is None and 'extensão' not in chk) or (esp is not None and 'extensão' in chk and esp in chk),('Hadlock > 40 sem',sem,dias,ig21,chk[:300]))
    # textos e referências
    r=pg.evaluate("""()=>{$('bRst').click();$('sem').value=34;$('dias').value=0;IGSRC='mao';setModo('bio');
      $('bDBP').value='8.40';$('bCC').value='30.50';$('bCA').value='28.00';$('bFL').value='6.40';$('auip').value='0.90';$('acmip').value='1.80';$('diast').value='pres';run();
      return {s:$('sintRes').innerText, ref:$('refOv').innerHTML, v:APP_VERSAO};}""")
    ok('Protocolo nº 90, 2026' in r['s'] and 'Tabela 2' in r['s'],('leitura FEBRASGO',r['s'][:400]))
    for k in ('Protocolo de Obstetrícia nº 90','Queda de 2 quartis','sem o corte de exibição','O antigo corte de 1,3 saiu','tabela original de 10 a 40 semanas','substitui o protocolo de RCF de 2018'):
        ok(k in r['ref'],('referência',k))
    ok('Martinelli' not in r['ref'],('referência antiga',))   # versão conferida no grupo da versão atual
    grupo('26 Auditoria externa: queda no bruto e ≥ 50, CPR sem 1,3, Hadlock > 40 sem, FEBRASGO nº 90 (R14.49)',C[0],F)

# ------------------------------------------------------------------ 27 R14.50 apresentação (plano UX/UI mobile)
def g_r50(pg):
    """Só apresentação: Confira com cor própria (não o vermelho de alterado); laudo em fonte proporcional; normal
    compacto sem fundo; letra mínima das etiquetas; barrinhas das uterinas mais finas que a da média; incisura em
    linha; cabeçalho mais baixo; todas as listas de opções com 16 px ou mais."""
    F=[]; C=[0]
    def ok(c,m):
        C[0]+=1
        if not c: F.append(m)
    pg.set_viewport_size({'width':390,'height':844})
    r=pg.evaluate("""()=>{$('bRst').click();$('sem').value=32;$('dias').value=2;IGSRC='dum';setModo('bio');
      $('bDBP').value='8.10';$('bCC').value='29.50';$('bCA').value='26.40';$('bFL').value='6.10';$('auip').value='0.95';$('acmip').value='1.90';
      $('utD').value='0.70';$('utE').value='0.82';VIA_UT='ta';$('incDChk').checked=true;$('diast').value='pres';run();abasTipo();
      var cs=function(e,ps){return getComputedStyle(e,ps||null)}, chk=document.querySelector('#chk .chk-i'), bad=cs(document.documentElement).getPropertyValue('--bad').trim();
      [].find.call(document.querySelectorAll('.tab'),function(x){return x.dataset.p==='p2'&&!x.hidden}).click();
      var mini=$('utDBar').querySelector('.bt').getBoundingClientRect().height, med=$('utBar').querySelector('.bt').getBoundingClientRect().height;
      var sels=[].filter.call(document.querySelectorAll('select.sel,select.selI'),function(e){return e.style.display!=='none';}).map(function(e){return [e.id,parseFloat(cs(e).fontSize)];});
      var tg=[].filter.call(document.querySelectorAll('.tg'),function(e){return e.offsetParent;}).map(function(e){return parseFloat(cs(e).fontSize);});
      var auOk=$('auRes'); 
      return {chkBorder:chk?cs(chk).borderLeftColor:null, badRgb:bad, chkGlyph:chk?cs(chk.querySelector('.chk-t'),'::before').content:null, miniCls:$('utDBar').className,
        ldFont:cs($('ldT')).fontFamily, mini:mini, med:med, sels:sels, tg:tg, gaLbl:parseFloat(cs(document.querySelector('.ga label')).fontSize),
        auCls:auOk.className, auBg:cs(auOk).backgroundColor, inc:cs($('incRes'),'::before').content, incBg:cs($('incRes')).backgroundColor,
        hd:Math.round(document.querySelector('.hd').getBoundingClientRect().height), v:APP_VERSAO};}""")
    def rgb(hx): hx=hx.lstrip('#'); return 'rgb(%d, %d, %d)'%tuple(int(hx[i:i+2],16) for i in (0,2,4))
    ok(r['chkBorder'] and r['chkBorder']!=rgb(r['badRgb']) and '?' in (r['chkGlyph'] or ''),('Confira com cor própria',r['chkBorder'],r['badRgb'],r['chkGlyph']))
    ok('mono' not in r['ldFont'].lower() and 'menlo' not in r['ldFont'].lower(),('laudo proporcional',r['ldFont']))
    ok(r['mini']<r['med'] and r['mini']<=4.5 and 'barMini' in r['miniCls'] and 'on' in r['miniCls'].split(),('barrinhas das uterinas',r['mini'],r['med'],r['miniCls']))
    ok(all(f>=16 for _,f in r['sels']) and len(r['sels'])>=15,('listas ≥ 16 px',[x for x in r['sels'] if x[1]<16],len(r['sels'])))
    ok(all(f>=10.5 for f in r['tg']) and r['gaLbl']>=10.5,('letra mínima',r['tg'],r['gaLbl']))
    ok('ok' in r['auCls'] and r['auBg'] in ('rgba(0, 0, 0, 0)','transparent'),('normal compacto',r['auCls'],r['auBg']))
    ok('Incisura' in (r['inc'] or '') and r['incBg'] in ('rgba(0, 0, 0, 0)','transparent'),('incisura em linha',r['inc'],r['incBg']))
    ok(r['hd']<=220,('cabeçalho mais baixo (era 241 px)',r['hd']))
    ok(r['v'] not in ('R14.47','R14.48','R14.49'),('versão anterior à R14.50',r['v']))   # versão exata conferida no grupo da versão atual
    # tema escuro: Confira continua distinto do vermelho
    r=pg.evaluate("""()=>{document.documentElement.setAttribute('data-tema','escuro'); var cs=getComputedStyle(document.documentElement);
      var o={conf:cs.getPropertyValue('--conf').trim(), bad:cs.getPropertyValue('--bad').trim()}; document.documentElement.removeAttribute('data-tema'); return o;}""")
    ok(r['conf'] and r['conf']!=r['bad'],('tema escuro',r))
    pg.set_viewport_size({'width':1024,'height':850})
    grupo('27 Apresentação: Confira, laudo, normal compacto, letra, uterinas, cabeçalho, listas (R14.50)',C[0],F)

# ------------------------------------------------------------------ 28 R14.51 avisos do peso e Confira tocável
def g_r51(pg):
    """Um problema, uma mensagem: perto do p10 um aviso só (margem, equação × tabela, < 1000 g no "por quê"); peso
    < 1000 g sem aviso solto no Confira (linha no cartão do peso); nota de Hadlock só com a curva de Hadlock; itens
    do Confira só texto (os atalhos da R14.51 saíram na R14.56)."""
    F=[]; C=[0]
    def ok(c,m):
        C[0]+=1
        if not c: F.append(m)
    pg.set_viewport_size({'width':390,'height':844})
    CHK="()=>[].map.call(document.querySelectorAll('#chk .chk-ln'),function(l){return {t:l.textContent,go:l.getAttribute('data-go')};})"
    B="$('bRst').click();$('sem').value=%d;$('dias').value=%d;IGSRC='mao';setModo('bio');$('bDBP').value='%s';$('bCC').value='%s';$('bCA').value='%s';$('bFL').value='%s';"
    def caso(js): pg.evaluate("()=>{"+js+"run();}"); return pg.evaluate(CHK)
    r=caso(B%(32,2,'8.10','29.50','26.40','6.10')+"$('auip').value='1.30';$('acmip').value='1.50';$('diast').value='pres';")
    pfe=[x for x in r if 'p10' in x['t'] or 'Hadlock' in x['t']]
    ok(len(pfe)==1 and 'perto do p10' in pfe[0]['t'] and 'Roberts AW' in pfe[0]['t'] and 'colado' not in pfe[0]['t'],('aviso único perto do p10',[x['t'][:80] for x in r]))
    r=caso(B%(24,0,'5.80','21.50','18.20','4.20'))
    pfe=[x for x in r if 'perto do p10' in x['t']]
    ok(len(pfe)==1 and '1000 g' in pfe[0]['t'] and not any(x['t'].startswith('Peso estimado abaixo de 1000') for x in r),('< 1000 g dentro do aviso perto do p10',[x['t'][:90] for x in r]))
    r=caso(B%(22,0,'5.30','19.80','17.20','3.90'))
    card=pg.evaluate("()=>$('pRes').textContent")
    ok(not any('1000 g' in x['t'] for x in r) and 'abaixo de 1000 g a fórmula perde precisão' in card,('< 1000 g só no cartão',[x['t'][:80] for x in r],card[-160:]))
    r=caso(B%(32,2,'8.10','29.50','26.40','6.10')+"CURVA='ig21';")
    ok(not any('Hadlock 1991' in x['t'] for x in r),('nota de Hadlock com INTERGROWTH',[x['t'][:80] for x in r]))
    # nota de Hadlock fora da janela do p10 continua sozinha (p < 6)
    r=caso("$('bRst').click();$('sem').value=32;$('dias').value=0;IGSRC='mao';setModo('dir');$('pDir').value=String(Math.round(Math.exp(hadlockMuLn(32)-0.12*2.0)));")
    ok(any(x['t'].startswith('Este app usa a equação de Hadlock 1991') for x in r),('nota de Hadlock abaixo do p6',[x['t'][:80] for x in r]))
    # R14.56: atalhos retirados — os avisos continuam (diástole, uterina de um lado), sem seta e sem navegar
    r=caso(B%(30,0,'7.70','28.00','25.50','5.70')+"$('auip').value='0.95';$('acmip').value='9.9';$('utD').value='0.8';")
    t=' '.join(x['t'] for x in r)
    ok('fluxo diastólico não foi avaliado' in t and 'Só um lado da uterina' in t and not any(x['go'] for x in r) and '›' not in t.replace('por quê ›',''),('Confira sem atalhos',[x['t'][:70] for x in r]))
    r=pg.evaluate("""()=>{[].find.call(document.querySelectorAll('.tab'),function(x){return x.dataset.p==='p3'&&!x.hidden}).click();
      var l=[].find.call(document.querySelectorAll('#chk .chk-ln'),function(x){return x.querySelector('.pqT')}); l.click(); var a0=document.querySelector('.pane.on').id;
      l.querySelector('.pqT').click(); return {aba:a0, ab:l.classList.contains('ab'), nav:typeof irParaAlvo};}""")
    ok(r['aba']=='p3' and r['ab'] and r['nav']=='undefined',('toque no item não navega; por quê abre',r))
    r=pg.evaluate("()=>APP_VERSAO"); ok(r not in ('R14.48','R14.49','R14.50'),('versão anterior à R14.51',r))
    pg.set_viewport_size({'width':1024,'height':850})
    grupo('28 Avisos do peso num item só, < 1000 g no cartão (R14.51; Confira sem atalhos desde a R14.56)',C[0],F)

# ------------------------------------------------------------------ 29 R14.52 auditoria setorial final
def g_r52(pg):
    """R14.52 tratava da seta do Confira para a umbilical. Desde a R14.56 o Confira não tem atalhos: o aviso "peso abaixo
    do p10 sem Doppler" continua em todo tipo de exame, sem seta e sem navegação."""
    F=[]; C=[0]
    def ok(c,m):
        C[0]+=1
        if not c: F.append(m)
    pg.set_viewport_size({'width':390,'height':844})
    for tipo in ('obst','morfo','dop'):
        r=pg.evaluate("""(t)=>{$('bRst').click();$('sem').value=30;$('dias').value=0;IGSRC='mao';setModo('dir');$('pDir').value='1100';run();abasTipo();
          var it=[].find.call(document.querySelectorAll('#chk .chk-ln'),function(l){return l.textContent.indexOf('sem Doppler')>=0});
          return {tem:!!it, go:!!(it&&(it.getAttribute('data-go')||it.querySelector('.chkSeta')||it.getAttribute('role')==='link'))};}""",tipo)
        ok(r['tem'] and not r['go'],('aviso sem Doppler, sem atalho',tipo,r))
    pg.set_viewport_size({'width':1024,'height':850})
    grupo('29 Aviso do peso < p10 sem Doppler em todo tipo de exame, sem atalho (R14.52 → R14.56)',C[0],F)

# ------------------------------------------------------------------ 30 R14.53 auditoria independente da R14.52
def g_r53(pg):
    """Título da trajetória com 1 casa TRUNCADA: o número exibido nunca cruza os cortes 10/15/20/50 (antes, 49,97
    aparecia como "Queda de 50"); decisão no bruto, ≥ 50 e 21 dias sem mudança. Confira inteiro em violeta
    (divisórias e negrito). Cinza terciário do tema escuro ≥ 4,5:1 em todos os fundos. Comentário antigo superado."""
    F=[]; C=[0]
    def ok(c,m):
        C[0]+=1
        if not c: F.append(m)
    lbl=lambda dq:('%.1f'%(math.floor(abs(dq)*10)/10)).replace('.',',')
    # 1) formatador: vizinhança de cada corte em passos de 1 ulp, 1e-12…0,1 e 2 000 valores aleatórios
    r=pg.evaluate("""()=>{var f=new Float64Array(1), u=new BigInt64Array(f.buffer);
      function viz(x,k){f[0]=x;u[0]+=BigInt(k);return f[0];}
      var vals=[], cuts=[10,15,20,50];
      cuts.forEach(function(c){ for(var k=-60;k<=60;k++) vals.push(viz(c,k));
        [1e-12,1e-9,1e-6,1e-3,0.01,0.04,0.05,0.06,0.09,0.0999999,0.1].forEach(function(e){vals.push(c-e,c+e);}); });
      var s=12345; function rnd(){s=(s*16807)%2147483647; return s/2147483647;}
      for(var i=0;i<2000;i++) vals.push(rnd()*100);
      var bad=[], n=0;
      vals.forEach(function(x){ [x,-x].forEach(function(y){ var t=ptsTrunc(y), d=parseFloat(t.replace(',','.')), a=Math.abs(y);
        n++; if(!/^\\d+,\\d$/.test(t)) bad.push(['formato',y,t]);
        n++; if(d>a+1e-12 || a-d>=0.1+1e-9) bad.push(['truncagem',y,t]);
        cuts.forEach(function(c){ n++; if((d>=c)!==(a>=c)) bad.push(['cruza o corte',c,y,t]); }); }); });
      return {n:n,bad:bad.slice(0,5),nb:bad.length};}""")
    C[0]+=r['n']-1; ok(r['nb']==0,('formatador',r['nb'],r['bad']))
    # 2) casos da auditoria, pelo motor real (Hadlock, 32+0 → 36+0, 28 dias)
    mu=lambda g:0.578+0.332*g-0.00354*g*g
    pr=lambda w,g:100*Phi((math.log(w)-mu(g))/0.12)
    VEL="""(a)=>{$('bRst').click();$('sem').value=a[0];$('dias').value=0;IGSRC='mao';setModo('dir');$('pDir').value=String(a[1]);run();
      $('dtHojeD').value='11';$('dtHojeM').value='10';$('dtHojeY').value='2026';
      var d=new Date(2026,9,11-a[3]); $('vPeso').value=String(a[2]);$('vD').value=String(d.getDate());$('vM').value=String(d.getMonth()+1);$('vY').value=String(d.getFullYear());
      ['dtHojeD','vPeso','vD','vM','vY','pDir'].forEach(function(i){$(i).dispatchEvent(new Event('input',{bubbles:true}));});run();
      return {v:ST.vel, t:$('vRes').querySelector('.t').textContent, s:($('vRes').querySelector('.s')||{}).textContent||''};}"""
    for w,cls in ((2810,'2q'),(2812,'imp'),(2813,'imp'),(2814,'imp'),(2815,'imp')):
        r=pg.evaluate(VEL,[36,w,2758,28]); dq=pr(w,36)-pr(2758,32)
        ok(abs(r['v']['dq']-dq)<1e-9 and r['t']=='Queda de %s percentis'%lbl(r['v']['dq']),('título',w,dq,r['t']))
        ok(r['v']['delphi']==(cls=='2q') and (('Redução de 2 quartis ou mais' in r['s'])==(cls=='2q')) and (('Desaceleração importante' in r['s'])==(cls=='imp')),('classe',w,r['v']['delphi'],r['s']))
    ok(pg.evaluate(VEL,[36,2812,2758,28])['t']=='Queda de 49,9 percentis',('49,968 → 49,9',))
    ok(pg.evaluate(VEL,[36,2810,2758,28])['t']=='Queda de 50,2 percentis',('50,205 → 50,2',))
    # varredura: 2760–2950 g (acima do peso anterior); número do título ≥ corte ⇔ ramo do motor
    r=pg.evaluate("""()=>{var out=[];for(var w=2760;w<=2950;w++){$('pDir').value=String(w);$('pDir').dispatchEvent(new Event('input',{bubbles:true}));run();
      out.push([w,ST.vel.dq,ST.vel.delphi,ST.vel.flag,$('vRes').querySelector('.t').textContent]);} return out;}""")
    for w,dq,de,fl,t in r:
        m=t.replace('Queda de ','').replace('Subiu ','').replace(' percentis','')
        try: x=float(m.replace(',','.'))
        except ValueError: x=None
        ok((x is None and -10<dq<15) or (x is not None and (x>=50)==(dq<=-50) and (x>=20)==(dq<=-20) and (t==('Queda de ' if dq<0 else 'Subiu ')+lbl(dq)+' percentis')),('varredura',w,dq,t))
        ok(de==(dq<=-50),('delphi na varredura',w,dq,de))
    # 3) fronteiras exatas com o percentil bruto substituído só neste teste (20 e 21 dias)
    B="""(a)=>{var o=window.pctAtivoRaw; window.pctAtivoRaw=function(w,g){return g>=a[1]-0.01?a[2]:a[3];};
      try{ $('bRst').click();$('sem').value=a[1];$('dias').value=0;IGSRC='mao';setModo('dir');$('pDir').value='2500';run();
      $('dtHojeD').value='11';$('dtHojeM').value='10';$('dtHojeY').value='2026';
      var d=new Date(2026,9,11-a[0]); $('vPeso').value='2400';$('vD').value=String(d.getDate());$('vM').value=String(d.getMonth()+1);$('vY').value=String(d.getFullYear());
      ['dtHojeD','vPeso','vD','vM','vY'].forEach(function(i){$(i).dispatchEvent(new Event('input',{bubbles:true}));});run();
      return {d:ST.vel.delphi, dq:ST.vel.dq, f:ST.vel.flag, t:$('vRes').querySelector('.t').textContent, s:($('vRes').querySelector('.s')||{}).textContent||''}; } finally { window.pctAtivoRaw=o; run(); } }"""
    for qd in (49.49,49.50,49.96,49.99,50.00,50.01,50.2,19.99,20.0,20.01,9.99,10.0,10.01):
        for dias in (20,21):
            qp=75.0; qn=qp-qd; dq=qn-qp
            r=pg.evaluate(B,[dias,36,qn,qp])
            ok(abs(r['dq']-dq)<1e-12 and r['d']==(dq<=-50 and dias>=21),('decisão na fronteira',qd,dias,r))
            if dq<=-10: ok(r['t']=='Queda de %s percentis'%lbl(dq),('título na fronteira',qd,dias,r['t']))
            else: ok(r['t']=='Trajetória mantida',('abaixo de 10',qd,dias,r['t']))
            esp=('Redução de 2 quartis ou mais' if dias>=21 else 'Intervalo insuficiente') if dq<=-50 else ('Desaceleração importante' if dq<=-20 else ('Trajetória em desaceleração' if dq<=-10 else 'Crescimento proporcional'))
            ok(esp in r['s'],('subtítulo na fronteira',qd,dias,r['s']))
    for qd,esp in ((14.99,'Trajetória mantida'),(15.0,'Subiu 15,0 percentis'),(15.04,'Subiu 15,0 percentis')):
        r=pg.evaluate(B,[28,36,40+qd,40.0]); ok(r['t']==esp,('subida',qd,r['t']))
    # 4) Confira inteiro em violeta (claro e escuro); vermelho continua no cartão alterado
    CF="""(tema)=>{ if(tema) document.documentElement.setAttribute('data-tema',tema); else document.documentElement.removeAttribute('data-tema');
      $('bRst').click();$('sem').value=24;$('dias').value=0;IGSRC='mao';setModo('bio');
      $('bDBP').value='5.90';$('bCC').value='21.80';$('bCA').value='18.60';$('bFL').value='4.20';$('auip').value='1.10';$('utD').value='0.9';VIA_UT='ta';run();
      var pr=document.createElement('i'); pr.style.color='var(--conf)'; pr.style.borderTopColor='var(--confln)'; pr.style.borderTopStyle='solid'; document.body.appendChild(pr);
      var cs=getComputedStyle(pr), conf=cs.color, confln=cs.borderTopColor; pr.remove();
      var ln=[].slice.call(document.querySelectorAll('#chk .chk-ln')), bs=[].slice.call(document.querySelectorAll('#chk .chk-ln b'));
      var r={n:ln.length, nb:bs.length, conf:conf, confln:confln,
        bord:ln.slice(1).map(function(e){return getComputedStyle(e).borderTopColor}), cor:bs.map(function(e){return getComputedStyle(e).color})};
      document.documentElement.removeAttribute('data-tema'); return r;}"""
    for tema in (None,'escuro'):
        r=pg.evaluate(CF,tema)
        ok(r['n']>=2 and r['nb']>=1,('cenário do Confira sem itens suficientes',tema,r['n'],r['nb']))
        ok(all(x==r['confln'] for x in r['bord']),('divisória do Confira',tema,r['bord'],r['confln']))
        ok(all(x==r['conf'] for x in r['cor']),('negrito do Confira',tema,r['cor'],r['conf']))
    # 5) cinza terciário do tema escuro (tema forçado e tema do sistema) ≥ 4,5:1 nos fundos de texto
    def lum(h):
        h=h.lstrip('#'); c=[int(h[i:i+2],16)/255 for i in (0,2,4)]
        c=[x/12.92 if x<=0.03928 else ((x+0.055)/1.055)**2.4 for x in c]; return 0.2126*c[0]+0.7152*c[1]+0.0722*c[2]
    def cr(a,b): x,y=sorted([lum(a),lum(b)],reverse=True); return (x+0.05)/(y+0.05)
    TK="""()=>{var cs=getComputedStyle(document.documentElement),o={};['--ink3','--ink2','--card','--bg','--fld','--ntbg','--okbg','--wrbg','--badbg','--confbg'].forEach(function(k){o[k]=cs.getPropertyValue(k).trim()});return o;}"""
    pg.evaluate("()=>document.documentElement.setAttribute('data-tema','escuro')"); t1=pg.evaluate(TK)
    pg.evaluate("()=>document.documentElement.removeAttribute('data-tema')"); pg.emulate_media(color_scheme='dark'); t2=pg.evaluate(TK); pg.emulate_media(color_scheme='light')
    for t in (t1,t2):
        ok(t['--ink3'].lower()=='#7f8e98',('cinza terciário escuro',t['--ink3']))
        for k in ('--card','--bg','--fld','--ntbg','--okbg','--wrbg','--badbg','--confbg'):
            ok(cr(t['--ink3'],t[k])>=4.5,('contraste --ink3',k,t[k],round(cr(t['--ink3'],t[k]),2)))
        ok(lum(t['--ink3'])<lum(t['--ink2']),('hierarquia ink3 < ink2',t['--ink3'],t['--ink2']))
    # 6) comentário antigo marcado como superado; versão
    src=pg.evaluate("()=>fetch(location.href).then(function(r){return r.text()})")
    ok('Mantida a decisao do proprietario' not in src and 'HISTÓRICO SUPERADO' in src and 'toFixed(0)+\' percentis\'' not in src,('comentários/rótulo antigo',))
    r=pg.evaluate("()=>APP_VERSAO"); ok(r not in ('R14.48','R14.49','R14.50','R14.51','R14.52'),('versão anterior à R14.53',r))
    grupo('30 Título da trajetória nunca cruza o corte; Confira violeta; cinza escuro (R14.53)',C[0],F)

# ------------------------------------------------------------------ 31 R14.54 Valores da IG (consulta inversa)
def g_r54(pg):
    """"Valores da IG": cada corte exibido, digitado no campo de verdade, cai do lado certo no motor (peso nas duas
    curvas, CA, umbilical, cerebral média, uterinas, ducto venoso, PSV), de 10+0 a 41+6; só leitura (estado e laudo
    iguais com o painel aberto); botão só com IG, sem aumentar o cabeçalho de 360 a 430 px."""
    F=[]; C=[0]
    def ok(c,m):
        C[0]+=1
        if not c: F.append(m)
    r=pg.evaluate("""()=>{$('bRst').click(); var semIG=$('bVIG').hidden;
      $('sem').value=30;$('dias').value=0;IGSRC='mao';run(); return {semIG:semIG, comIG:!$('bVIG').hidden};}""")
    ok(r['semIG'] and r['comIG'],('botão só com IG',r))
    # fronteiras pelo motor real
    r=pg.evaluate("""()=>{var F=[],n=0; function ck(c,m){n++; if(!c) F.push(m);}
      function fx(k,d){return (k/d).toFixed(d===100?2:(d===10?1:3));}
      for(var gd=70; gd<=293; gd+=3){ var s=Math.floor(gd/7), d=gd%7;
        $('bRst').click(); $('sem').value=s; $('dias').value=d; IGSRC='mao'; run(); var g=getGA();
        ['hadlock','ig21'].forEach(function(cv){ CURVA=cv; var L=vigLimites(g); if(!L.peso) return; setModo('dir');
          var P=[['p3',function(q){return q<3},'baixo'],['p10',function(q){return q<10},'baixo'],['p90',function(q){return q>90},'alto'],['p97',function(q){return q>97},'alto']];
          P.forEach(function(x){ var w=L.peso[x[0]];
            if(w===null){ $('pDir').value='50'; run(); var a50=ST.pfe&&x[1](ST.pfe.q);   // "—": corte fora de 50–7000 g
              ck(x[2]==='baixo'?a50===false:a50===true,['peso nulo sem motivo',cv,gd,x[0]]); return; }
            $('pDir').value=String(w); run(); var a=ST.pfe&&x[1](ST.pfe.q);
            $('pDir').value=String(x[2]==='baixo'?w+1:w-1); run(); var b=ST.pfe&&x[1](ST.pfe.q);
            ck(a===true && b===false,['peso',cv,gd,x[0],w]); }); });
        CURVA='hadlock'; $('pDir').value=''; var L=vigLimites(g);
        if(L.ca){ setModo('bio');
          [['p3',['baixo3'],'baixo'],['p10',['baixo3','baixo10'],'baixo'],['p90',null,'alto'],['p97',['alto'],'alto']].forEach(function(x){
            var k=L.ca[x[0]]; if(k===null){ck(false,['ca nulo',gd,x[0]]);return;}
            var test=function(kk){ $('bCA').value=fx(kk,100); run(); if(!ST.ca) return null;
              return x[0]==='p90' ? ST.ca.acima90 : x[1].indexOf(ST.ca.flag)>=0; };
            ck(test(k)===true && test(x[2]==='baixo'?k+1:k-1)===false,['CA',gd,x[0],k]); });
          $('bCA').value=''; setModo('dir'); }
        if(L.au){ var t=function(k){$('auip').value=fx(k,100);run();return ST.au&&ST.au.flag==='alto';};
          ck(t(L.au.p95)===true && t(L.au.p95-1)===false,['AU',gd,L.au.p95]); $('auip').value='';
          t=function(k){$('acmip').value=fx(k,100);run();return ST.acm&&ST.acm.flag==='baixo';};
          ck(t(L.acm.p5)===true && t(L.acm.p5+1)===false,['ACM',gd,L.acm.p5]); $('acmip').value='';
          ck(Math.abs(L.cpr.p5-ciobanuCPRref(gaDiasCiobanu(g))[0])<1e-15,['CPR',gd]); }
        else ck(gd<140||gd>293,['Ciobanu ausente',gd]);
        if(L.ut){ VIA_UT=L.ut.via; var tu=function(k){var a=Math.floor(k/2); $('utD').value=(a/100).toFixed(2); $('utE').value=((k-a)/100).toFixed(2); run();
            return ST.ut?ST.ut.flag:null;};
          ck(tu(L.ut.p95)==='alto' && tu(L.ut.p95-1)==='ok',['uterinas',gd,L.ut.via,L.ut.p95,tu(L.ut.p95),tu(L.ut.p95-1)]);
          $('utD').value='';$('utE').value=''; VIA_UT=null; }
        if(L.dv){ var tv=function(k){$('dvip').value=fx(k,100);run();return ST.dvip&&ST.dvip.flag==='alto';};
          ck(tv(L.dv.p95)===true && tv(L.dv.p95-1)===false,['DV',gd,L.dv.p95]); $('dvip').value=''; }
        if(L.psv){ var tp=function(k){$('psv').value=fx(k,10);run();return ST.psv&&ST.psv.flag;};
          ck(tp(L.psv.m15)==='alto' && tp(L.psv.m15-1)==='lim' && tp(L.psv.m13)==='lim' && tp(L.psv.m13-1)==='ok',['PSV',gd,L.psv.m15,L.psv.m13]); $('psv').value=''; }
      }
      return {n:n,F:F.slice(0,6),nf:F.length};}""")
    C[0]+=r['n']-1; ok(r['nf']==0,('fronteiras',r['nf'],r['F']))
    # painel: só leitura, textos e fechamento
    r=pg.evaluate("""()=>{$('bRst').click();$('sem').value=32;$('dias').value=3;IGSRC='mao';setModo('dir');$('pDir').value='1800';
      $('auip').value='1.10';$('acmip').value='1.60';$('diast').value='pres';run();
      var st=JSON.stringify(ST), ld=$('ldT').textContent; $('bVIG').click(); var on=$('vigOv').className.indexOf('on')>=0, h=$('vigBd').innerText;
      run(); var st2=JSON.stringify(ST), ld2=$('ldT').textContent; $('bVigX').click();
      return {on:on, fechou:$('vigOv').className.indexOf('on')<0, igual:st===st2&&ld===ld2, h:h, L:vigLimites(getGA())};}""")
    ok(r['on'] and r['fechou'] and r['igual'],('abre/fecha/só leitura',r['on'],r['fechou'],r['igual']))
    L=r['L']; h=r['h']
    for k in ('IG usada: 32s 3d','Hadlock 1991','INTERGROWTH-21st','Ciobanu 2019/FMF','Gómez 2008','Tongprasert 2012','Mari 2000','nada aqui entra no laudo',
              'até %d g'%L['peso']['p10'],'a partir de %d g'%L['peso']['p90'],'até '+('%.2f'%(L['ca']['p10']/100)).replace('.',','),
              'a partir de '+('%.2f'%(L['au']['p95']/100)).replace('.',','),'até '+('%.2f'%(L['acm']['p5']/100)).replace('.',','),
              'a partir de '+('%.3f'%(L['ut']['p95']/200)).replace('.',',')):
        ok(k in h,('texto do painel',k))
    # 1º trimestre: sem CA/Ciobanu/DV/PSV, com uterinas por via transvaginal (Gómez)
    r=pg.evaluate("""()=>{$('bRst').click();$('sem').value=12;$('dias').value=2;IGSRC='mao';run();$('bVIG').click();var h=$('vigBd').innerText;$('bVigX').click();return h;}""")
    ok('via transvaginal' in r and 'Sem referência nesta IG' in r and 'CA (14 a 40 semanas)' in r and 'ARTÉRIA UMBILICAL' not in r.upper().replace('ARTÉRIAS','') ,('1º trimestre',r[:300]))
    # cabeçalho: botão na linha da origem, sem aumentar a altura de 360 a 430 px
    for w in (360,375,390,430):
        pg.set_viewport_size({'width':w,'height':844})
        r=pg.evaluate("""()=>{$('bRst').click();var h0=Math.round(document.querySelector('.hd').getBoundingClientRect().height);
          $('sem').value=32;$('dias').value=3;IGSRC='mao';run();
          var b=$('bVIG').getBoundingClientRect(), t=$('origAtual').getBoundingClientRect();
          return {mesma:!$('bVIG').hidden && Math.abs(b.top-t.top)<12, hd:Math.round(document.querySelector('.hd').getBoundingClientRect().height), sw:document.documentElement.scrollWidth};}""")
        ok(r['mesma'] and r['hd']<=217 and r['sw']<=w,('cabeçalho',w,r))
    pg.set_viewport_size({'width':1024,'height':850})
    r=pg.evaluate("()=>APP_VERSAO"); ok(r not in ('R14.48','R14.49','R14.50','R14.51','R14.52','R14.53'),('versão anterior à R14.54',r))
    grupo('31 Valores da IG: cada corte cai do lado certo no motor; só leitura (R14.54)',C[0],F)

# ------------------------------------------------------------------ 32 R14.55 chave cm | mm
def g_r55(pg):
    """Chave cm | mm: abre em cm; troca ao vivo deslocando a vírgula no texto; o número que entra no motor é idêntico
    ao digitado em cm (exames aleatórios digitados em cm e em mm → estado e laudo iguais); exame salvo e feto guardado em
    cm; recuperação na unidade da tela; trava do mínimo de digitação no modo mm (TN conferida contra o CCN); cabeçalho
    da mesma altura de 360 a 430 px."""
    F=[]; C=[0]
    def ok(c,m):
        C[0]+=1
        if not c: F.append(m)
    r=pg.evaluate("""()=>({u:UNIDADE, on:$('unCm').classList.contains('on')&&!$('unMm').classList.contains('on'),
      us:Object.keys(UN_CAMPO).filter(function(i){var e=$(i);return !e||!e.parentNode.querySelector('.u')||e.parentNode.querySelector('.u').textContent!=='cm'}),
      n:Object.keys(UN_CAMPO).length})""")
    ok(r['u']=='cm' and r['on'] and r['n']==30 and not r['us'],('abre em cm',r))
    # 1) deslocamento da vírgula: o mm digitado vira exatamente o mesmo número do cm digitado
    r=pg.evaluate("""()=>{var bad=[],n=0;
      for(var k=1;k<=60000;k++){ var cm=(k/100).toFixed(2), mm=(k/10).toFixed(1); n++;   // 0,01 a 600 cm: uma checagem por valor
        if(parseFloat(desloca(mm,-1))!==parseFloat(cm)) bad.push(['mm→cm',mm,cm,desloca(mm,-1)]);
        if(parseFloat(desloca(cm,+1))!==parseFloat(mm)) bad.push(['cm→mm',cm,mm,desloca(cm,+1)]);
        if(parseFloat(desloca(desloca(cm,+1),-1))!==parseFloat(cm)) bad.push(['ida e volta',cm]); }
      [['0.35','3.5'],['28','280'],['5','50'],['.5','5'],['8.4','84'],['0.05','0.5'],['10','100'],['284.5','2845'],['0','0']].forEach(function(x){ n++;
        if(desloca(x[0],+1)!==x[1]) bad.push(['caso',x,desloca(x[0],+1)]); });
      return {n:n,bad:bad.slice(0,5),nb:bad.length};}""")
    C[0]+=r['n']-1; ok(r['nb']==0,('deslocamento',r['bad']))
    # 2) exames aleatórios digitados em cm e em mm → estado, laudo, conclusão e avisos idênticos
    r=pg.evaluate("""()=>{var s=4242; function rnd(){s=(s*16807)%2147483647; return s/2147483647;}
      function U(a,b,c){var x=a+rnd()*(b-a); return x.toFixed(c===undefined?2:c);}
      var bad=[],n=0;
      function caso(){ var g=20+Math.floor(rnd()*20), c={sem:g,dias:Math.floor(rnd()*7)};
        c.bDBP=U(5,10); c.bCC=U(18,36); c.bCA=U(15,40); c.bFL=U(3,8); c.mbv=U(1,12,1); c.ila=U(5,25,1);
        if(rnd()<.7){ c.eCer=U(1.8,5.5); c.eAtr=U(0.3,1.4); c.eCis=U(0.2,1.2); c.ePrg=U(0.2,0.8); c.eDbo=U(3,6); c.eDio=U(1,2); c.eON=U(0.5,1.2); c.ePFN=U(0.2,0.7); }
        if(rnd()<.5){ c.ePel=U(0.3,1.5); c.eBex=U(1.1,4); c.ePar=U(0.1,0.5); c.eUre=U(0.2,0.9); c.eCT=U(12,30); }   // acima dos mínimos da trava
        if(rnd()<.5){ c.eUme=U(2,6.5); c.eRad=U(1.8,5.5); c.eUln=U(2,6); c.eTib=U(2,6.5); c.eFib=U(2,6.2); }
        if(rnd()<.5){ c.eColo=U(1,5); c.ePla=U(1.5,4.5); c.plOI=U(0.5,6); }
        c.auip=U(0.6,1.6); c.acmip=U(1,2.4); return c; }
      function digita(c,u){ $('bRst').click(); setUnidade(u); $('sem').value=c.sem; $('dias').value=c.dias; IGSRC='mao'; setModo('bio');
        Object.keys(c).forEach(function(k){ if(k==='sem'||k==='dias') return; $(k).value = (u==='mm'&&UN_CAMPO[k]) ? desloca(c[k],+1) : c[k]; });
        $('diast').value='pres'; run();
        return {st:JSON.stringify(ST), ld:$('ldT').textContent, conc:$('ldConc').textContent, chk:[].map.call(document.querySelectorAll('#chk .chk-ln'),function(l){return l.textContent}).join('|')}; }
      for(var i=0;i<120;i++){ var c=caso(), a=digita(c,'cm'), b=digita(c,'mm'); n+=4;
        if(a.st!==b.st) bad.push([i,'estado']); if(a.ld!==b.ld) bad.push([i,'laudo']); if(a.conc!==b.conc) bad.push([i,'conclusão']);
        if(a.chk!==b.chk) bad.push([i,'avisos',a.chk.slice(0,120),b.chk.slice(0,120)]); }
      setUnidade('cm'); return {n:n,bad:bad.slice(0,4),nb:bad.length};}""")
    C[0]+=r['n']-1; ok(r['nb']==0,('cm × mm',r['nb'],r['bad']))
    # 3) troca ao vivo: tela convertida, motor igual, volta igual
    r=pg.evaluate("""()=>{$('bRst').click();setUnidade('cm');$('sem').value=32;$('dias').value=3;IGSRC='mao';setModo('bio');
      $('bDBP').value='8.10';$('bCC').value='29.50';$('bCA').value='28.45';$('bFL').value='6.1';$('mbv').value='4.5';$('eAtr').value='0.65';run();
      var st=JSON.stringify(ST), ld=$('ldT').textContent; $('unMm').click();
      var o={tela:[$('bCA').value,$('bFL').value,$('mbv').value,$('eAtr').value], u:$('bCA').parentNode.querySelector('.u').textContent,
        igual:JSON.stringify(ST)===st&&$('ldT').textContent===ld, corpo:document.body.classList.contains('unMm'), on:$('unMm').classList.contains('on')};
      $('unCm').click(); o.volta=[$('bCA').value,$('bFL').value,$('mbv').value,$('eAtr').value]; o.igual2=JSON.stringify(ST)===st; return o;}""")
    ok(r['tela']==['284.5','61','45','6.5'] and r['u']=='mm' and r['igual'] and r['corpo'] and r['on'],('troca ao vivo',r))
    ok(r['volta']==['28.45','6.1','4.5','0.65'] and r['igual2'],('volta ao cm',r))
    # 4) trava do modo mm: abaixo do mínimo pede confirmação; laudo indisponível até confirmar; cm não tem trava
    MIN={'ePrg':0.15,'ePFN':0.15,'eUre':0.20,'ePar':0.06,'eCis':0.20,'eAtr':0.30,'ePel':0.30,'eBex':0.72,'eDio':0.40,'ePla':0.60}   # bexiga: (24+12)/50
    for k,m in MIN.items():
        r=pg.evaluate("""(a)=>{$('bRst').click();setUnidade('mm');$('sem').value=24;$('dias').value=0;IGSRC='mao';setModo('dir');$('pDir').value='650';
          var mm=desloca(String(a[1]),+1), abaixo=desloca(String(Math.round(a[1]*100-1)/100),+1);
          if(a[0]==='ePar') $('eBex').value='50';   // parede vesical só aparece com megabexiga
          $(a[0]).value=abaixo; run(); var o={b:[val(a[0]),$('unAv_'+a[0]).className,LAUDO_INDISP]};
          $(a[0]).value=mm; run(); o.m=[val(a[0]),$('unAv_'+a[0]).className];
          $(a[0]).value=abaixo; run(); $('unAv_'+a[0]).querySelector('[data-unc]').click(); o.c=[val(a[0]),$('unAv_'+a[0]).className];
          $('bRst').click(); setUnidade('cm'); if(a[0]==='ePar') $('eBex').value='5'; $(a[0]).value=desloca(abaixo,-1); $('sem').value=24;$('dias').value=0;IGSRC='mao';run(); o.cm=val(a[0]); return o;}""",[k,m])
        ok(r['b'][0] is None and 'on' in r['b'][1] and r['b'][2] is True,('trava abaixo do mínimo',k,r))
        ok(r['m'][0] is not None and abs(r['m'][0]-m)<1e-12 and 'on' not in r['m'][1],('no mínimo passa',k,r))
        ok(r['c'][0] is not None and 'on' not in r['c'][1] and r['cm'] is not None,('confirmação e modo cm',k,r))
    # TN contra o CCN (1º trimestre): mínimo = metade da mediana da TN para o CCN (abaixo do p5); sem CCN, 0,6 mm
    r=pg.evaluate("""()=>{var o=[]; [45,60,84].forEach(function(ccn){ $('bRst').click(); setCtx('B'); setUnidade('mm'); $('sem').value=12;$('dias').value=3;IGSRC='mao';
        $('rCCN').value=String(ccn); run(); var t=interp(tabTN(),ccn), med=t[1], lim=0.5*med;
        $('rTN').value='0.18'; run(); var a=[val('rTN'),LAUDO_INDISP,$('unAv_rTN').className];
        $('rTN').value=(Math.ceil(lim*100)/100).toFixed(2); run(); var b=val('rTN');
        $('rTN').value='1.8'; run(); var c=val('rTN');
        o.push({ccn:ccn,lim:lim,a:a,b:b,c:c,p5:lim<t[0]}); }); setCtx('A'); setUnidade('cm'); return o;}""")
    for x in r:
        ok(x['a'][0] is None and x['a'][1] is True and 'on' in x['a'][2] and x['b'] is not None and abs(x['c']-0.18)<1e-12 and x['p5'],('TN × CCN',x))
    # 5) exame salvo sempre em cm; recuperação na unidade da tela
    r=pg.evaluate("""()=>{$('bRst').click();setUnidade('mm');$('sem').value=30;$('dias').value=0;IGSRC='mao';setModo('bio');
      $('bDBP').value='77.5';$('bCC').value='280';$('bCA').value='262.4';$('bFL').value='58';run();
      var o=coletaEstado(); return [o.campos.bDBP,o.campos.bCC,o.campos.bCA,o.campos.bFL,o.campos.sem];}""")
    ok(r==['7.75','28','26.24','5.8','30'],('salvo em cm',r))
    r=pg.evaluate("""()=>{var o=coletaEstado(); $('bRst').click(); setUnidade('cm'); aplicaEstado(o); var a=[$('bCA').value,UNIDADE];
      $('bRst').click(); setUnidade('mm'); aplicaEstado(o); var b=[$('bCA').value,UNIDADE]; run(); var w=ST.pfe&&ST.pfe.w;
      $('bRst').click(); setUnidade('cm'); aplicaEstado(o); run(); var w2=ST.pfe&&ST.pfe.w; setUnidade('cm'); return {a:a,b:b,w:w,w2:w2};}""")
    ok(r['a']==['26.24','cm'] and r['b']==['262.4','mm'] and r['w'] is not None and r['w']==r['w2'],('recuperação',r))
    # 6) gemelar: o feto guardado fica em cm; trocar de feto no modo mm preserva os valores
    r=pg.evaluate("""()=>{$('bRst').click();setUnidade('mm');$('sem').value=30;$('dias').value=0;IGSRC='mao';$('gemelar').checked=true;
      $('gemelar').dispatchEvent(new Event('change',{bubbles:true}));setModo('bio');
      $('bDBP').value='77.5';$('bCC').value='280';$('bCA').value='262.4';$('bFL').value='58';$('eAtr').value='1.9';run();
      trocaFeto('B'); var guardado=DADOS.A.campos.bCA, conf=$('ldT').textContent;   // bloqueio vai para o texto do laudo
      trocaFeto('A'); var volta=[$('bCA').value,$('eAtr').value];
      $('gemelar').checked=false; $('gemelar').dispatchEvent(new Event('change',{bubbles:true})); setUnidade('cm');
      return {g:guardado, v:volta, conf:conf};}""")
    ok(r['g']=='26.24' and r['v']==['262.4','1.9'],('gemelar',r['g'],r['v']))
    ok('Feto A' in r['conf'] and 'mínimo esperado em milímetros' in r['conf'],('trava do outro feto no laudo indisponível',r['conf'][:300]))
    # 7) mensagem de plausibilidade na unidade da chave; Valores da IG em mm; Limpar mantém a unidade
    r=pg.evaluate("""()=>{$('bRst').click();setUnidade('mm');$('sem').value=30;$('dias').value=0;IGSRC='mao';setModo('bio');$('bCA').value='26.24';run();
      var t=$('pRes')?$('pRes').innerText:''; var c=[].map.call(document.querySelectorAll('#chk .chk-ln'),function(l){return l.textContent}).join('|');
      $('bVIG').click(); var h=$('vigBd').innerText; $('bVigX').click(); $('bRst').click(); var u=UNIDADE; setUnidade('cm');
      return {t:t+' '+c, h:h, u:u};}""")
    ok('26,24 mm' in r['t'] and 'unidade' in r['t'],('aviso de plausibilidade em mm',r['t'][:300]))
    ok(' mm' in r['h'].split('CIRCUNFERÊNCIA')[1][:200] if 'CIRCUNFERÊNCIA' in r['h'] else False,('Valores da IG em mm',r['h'][:200]))
    ok(r['u']=='mm',('Limpar mantém a unidade',r['u']))
    # 8) cabeçalho da mesma altura e sem rolagem lateral, com a chave
    for w in (360,375,390,430):
        pg.set_viewport_size({'width':w,'height':844})
        r=pg.evaluate("""()=>{$('bRst').click();$('sem').value=32;$('dias').value=3;IGSRC='mao';run();
          var c=$('unMm').getBoundingClientRect();
          return {hd:Math.round(document.querySelector('.hd').getBoundingClientRect().height), sw:document.documentElement.scrollWidth, alvo:Math.round(c.height)};}""")
        ok(r['hd']<=217 and r['sw']<=w and r['alvo']>=32,('cabeçalho com a chave',w,r))
    pg.set_viewport_size({'width':1024,'height':850})
    # 9) sempre abre em cm (mesmo saindo em mm)
    pg.evaluate("()=>{setUnidade('mm');}"); pg.reload(); pg.wait_for_timeout(400)
    ok(pg.evaluate("()=>UNIDADE")=='cm',('reabre em cm',))
    r=pg.evaluate("()=>APP_VERSAO"); ok(r not in ('R14.48','R14.49','R14.50','R14.51','R14.52','R14.53','R14.54'),('versão anterior à R14.55',r))
    grupo('32 Chave cm | mm: motor idêntico, salvo em cm, trava do modo mm (R14.55)',C[0],F)

# ------------------------------------------------------------------ 33 R14.56 Confira sem atalhos
def g_r56(pg):
    """Atalhos do Confira retirados a pedido do médico: em exames aleatórios dos dois contextos, nenhum item tem seta,
    papel de link ou destino; o "por quê" continua; nenhum código de navegação sobrou."""
    F=[]; C=[0]
    def ok(c,m):
        C[0]+=1
        if not c: F.append(m)
    r=pg.evaluate("""()=>{var s=777; function rnd(){s=(s*16807)%2147483647; return s/2147483647;}
      function U(a,b){return (a+rnd()*(b-a)).toFixed(2);}
      var n=0,bad=[],pq=0,itens=0;
      for(var i=0;i<80;i++){ $('bRst').click(); var b=i%4===0; if(b){ setCtx('B'); $('sem').value=8+Math.floor(rnd()*5); $('dias').value=0; IGSRC='mao'; run();
          $('rCCN').value=U(0.4,6); if(rnd()<.5){$('fcf1').value='150';} if(rnd()<.5) $('rTN').value=U(0.1,0.4); }
        else { setCtx('A'); $('sem').value=20+Math.floor(rnd()*20); $('dias').value=Math.floor(rnd()*7); IGSRC='mao'; setModo('bio');
          $('bDBP').value=U(4,10);$('bCC').value=U(15,36);$('bCA').value=U(12,40);$('bFL').value=U(2,8);
          if(rnd()<.6){$('auip').value=U(0.5,1.8);} if(rnd()<.4){$('acmip').value=U(0.8,2.5);} if(rnd()<.4){$('utD').value=U(0.4,2);} }
        run();
        [].forEach.call(document.querySelectorAll('#chk .chk-ln'),function(l){ itens++; n++;
          if(l.getAttribute('data-go')||l.classList.contains('chk-go')||l.getAttribute('role')==='link'||l.querySelector('.chkSeta')) bad.push([i,l.textContent.slice(0,60)]);
          if(l.querySelector('.pqT')) pq++; }); }
      setCtx('A');
      return {n:n,itens:itens,pq:pq,bad:bad.slice(0,4),nb:bad.length,
        restos:['chkAlvo','irParaAlvo'].filter(function(k){return typeof window[k]!=='undefined'}),
        css:[].some.call(document.styleSheets,function(sh){try{return [].some.call(sh.cssRules,function(r){return (r.selectorText||'').indexOf('chk-go')>=0})}catch(e){return false}})};}""")
    C[0]+=max(r['n'],1)-1
    ok(r['nb']==0 and r['itens']>20 and r['pq']>0,('itens do Confira sem atalho',r['nb'],r['itens'],r['pq'],r['bad']))
    ok(not r['restos'] and not r['css'],('código de navegação sobrando',r['restos'],r['css']))
    r=pg.evaluate("()=>APP_VERSAO"); ok(r not in ('R14.48','R14.49','R14.50','R14.51','R14.52','R14.53','R14.54','R14.55'),('versão anterior à R14.56',r))
    grupo('33 Confira sem atalhos: só texto, "por quê" mantido (R14.56)',C[0],F)

# ------------------------------------------------------------------ 34 R15.0–R15.1 reorganização (abas em cima, IG no cabeçalho, título deduzido)
def g_r15(pg):
    """Reorganização liberada em 14/10/2026: faixa + abas presas no topo; IG/origem na Datação; seletor de trimestre e
    tipo de exame fora; Biometria pergunta o trimestre sem IG; título deduzido (praxe/IG<28) com correção no Laudo;
    biometria completa na Morfologia (mesmos campos); velocidade em Medidas; Gestação na Datação; campo preenchido
    nunca some (prega fora da janela, aviso do outro trimestre); campos com janela somem vazios fora dela."""
    F=[]; C=[0]
    def ok(c,m):
        C[0]+=1
        if not c: F.append(m)
    pg.set_viewport_size({'width':390,'height':844})
    ABAS="()=>[].filter.call(document.querySelectorAll('.tab'),function(t){return !t.hidden}).map(function(t){return t.dataset.p+':'+t.textContent.replace(/\\d+$/,'').trim()})"
    ATIVA="()=>document.querySelector('.tab.on').dataset.p"
    TAB="(t)=>{document.querySelector('.tab[data-p=\"'+t+'\"]').click();}"
    T1="()=>$('ldT').textContent.split('\\n')[0]"
    # ---------- 1. estrutura
    r=pg.evaluate("""()=>{$('bRst').click(); return {ctx:!!document.querySelector('.ctx,#tipoEx,#cA,#cB,#tipoEx button'), tipo:typeof TIPO_EX,
      topo:getComputedStyle($('topo')).position, tabsIn:!!$('topo').querySelector('.tabs'), estIn:$('estBar').parentNode.id,
      estHid:$('estBar').hidden, est:$('estBar').textContent.trim(), semIG:$('estIG').className,
      sem:($('sem').closest('.hd')?'hd':'?'), orig:$('origemBox').closest('.hd')!==null, antes:$('origemBox').compareDocumentPosition($('topo'))&Node.DOCUMENT_POSITION_FOLLOWING,
      p0:[].map.call($('p0').children,function(x){return x.id}).join(','),
      vel:$('velBox').closest('.pane').id, velPrev:($('velBox').previousElementSibling||{}).querySelector?!!$('velBox').previousElementSibling.querySelector('#bDBP,#pCalc,#boxBio'):false,
      gem:$('gemelar').closest('.pane').id, cor:$('corion').closest('#gestCard')!==null, fs:$('segFeto').closest('.pane').id,
      corBox:$('corionBox').style.display, prax:$('praxeCard').querySelector('h2').textContent, dtVis:$('dtBox').style.display};}""")
    ok(not r['ctx'] and r['tipo']=='undefined',('seletor de trimestre/tipo de exame sobrando',r))
    ok(r['topo']=='sticky' and r['tabsIn'] and r['estIn']=='topo',('faixa+abas presas',r))
    ok(not r['estHid'] and r['est']=='IG não definida' and r['semIG']=='semIG',('faixa sem IG',r))
    ok(r['sem']=='hd' and r['orig'] and r['antes'],('R15.1: quadro da IG no cabeçalho, acima da faixa e das abas',r))
    ok(r['p0']=='outroTri,gestCard,dataExameCard,dtBox,viabCard,segAntBox,datasCard',('ordem da Datação',r['p0']))
    ok(r['vel']=='p1' and r['velPrev'],('velocidade logo abaixo do peso',r))
    ok(r['gem']=='p0' and r['cor'] and r['fs']=='p1' and r['corBox']=='none',('gemelar na Datação; troca de feto em Medidas',r))
    ok(r['prax']=='Biometria' and r['dtVis']=='none',('título do cartão / cartão DUM oculto',r))
    ok(pg.evaluate(ABAS)==['p0:Datação','p1:Medidas','p6:Morfologia','p2:Doppler','p3:Laudo'],('abas 2º/3º',pg.evaluate(ABAS)))
    pg.evaluate("()=>{$('bRst').click();$('sem').value=12;$('dias').value=3;IGSRC='mao';run();}")
    ok(pg.evaluate(ABAS)==['p0:Datação','p4:Medidas','p5:Doppler','p3:Laudo'],('abas 1º tri',pg.evaluate(ABAS)))
    r=pg.evaluate("()=>({g:$('gestCard').style.display, t:$('titCard').style.display, est:$('estIG').textContent})")
    ok(r['g']=='none' and r['t']=='none' and r['est']=='IG 12s 3d · informada · 1º tri',('1º tri: sem Gestação/título; faixa',r))
    # presas ao rolar; sem rolagem lateral em 4 larguras e 5 abas
    pg.evaluate("""()=>{$('bRst').click();$('sem').value=32;$('dias').value=2;IGSRC='mao';setModo('bio');
      $('bDBP').value='8.10';$('bCC').value='29.50';$('bCA').value='26.40';$('bFL').value='6.10';$('mbv').value='4.2';$('auip').value='1.05';$('acmip').value='1.90';run();}""")
    pg.evaluate(TAB,'p1'); pg.evaluate("()=>window.scrollTo(0,1400)"); pg.wait_for_timeout(250)
    r=pg.evaluate("()=>{var t=$('topo').getBoundingClientRect(), h=document.querySelector('.hd').getBoundingClientRect(); return {top:Math.round(t.top), hb:Math.round(h.bottom), y:scrollY, tab:document.elementFromPoint(195,Math.round(t.bottom)-15).closest('.tab')!==null};}")
    ok(r['top']==0 and r['hb']<=0 and r['y']>0 and r['tab'],('abas presas ao rolar',r))
    for w in (320,375,390,430):
        pg.set_viewport_size({'width':w,'height':760})
        for t in ('p0','p1','p6','p2','p3'):
            pg.evaluate(TAB,t); pg.wait_for_timeout(60)
            sw=pg.evaluate("()=>document.documentElement.scrollWidth")
            ok(sw<=w,('rolagem lateral',w,t,sw))
        r=pg.evaluate("""()=>{var q=[].filter.call(document.querySelectorAll('.tab'),function(t){return !t.hidden}).map(function(t){return t.getBoundingClientRect()});
          var e=$('estBar').getBoundingClientRect(); return {lin:q.every(function(c){return Math.abs(c.top-q[0].top)<2}), dentro:q.every(function(c){return c.left>=0&&c.right<=innerWidth+0.5}), est:Math.round(e.height)};}""")
        ok(r['lin'] and r['dentro'] and r['est']<=44,('abas numa linha',w,r))
    pg.set_viewport_size({'width':390,'height':844})
    pg.evaluate(TAB,'p3'); pg.wait_for_timeout(150)
    r=pg.evaluate("""()=>{var b=document.querySelector('.barCopy').getBoundingClientRect(), t=$('topo').getBoundingClientRect();
      return {vis:getComputedStyle(document.querySelector('.barCopy')).display!=='none', fundo:Math.round(innerHeight-b.bottom), cruza:!(b.top>=t.bottom)};}""")
    ok(r['vis'] and r['fundo']==0 and not r['cruza'],('barra de cópia no rodapé, só no Laudo',r))
    # ---------- 2. origem da IG
    def foco(): return pg.evaluate("()=>document.activeElement&&document.activeElement.id")
    pg.evaluate("()=>{$('bRst').click();window.scrollTo(0,0);}"); pg.evaluate(TAB,'p0'); pg.locator('#origBio').click(); pg.wait_for_timeout(120)
    r=pg.evaluate("()=>({pk:$('origPick').hidden, pend:ORIG_PEND, ctx:CTX})")
    ok(not r['pk'] and r['pend']=='bio' and r['ctx']=='A',('Biometria sem IG pergunta o trimestre',r))
    pg.locator('#pickCCN').click(); pg.wait_for_timeout(300)
    r=pg.evaluate("()=>({ctx:CTX, man:CTXMAN, pk:$('origPick').hidden, aba:document.querySelector('.tab.on').dataset.p, f:document.activeElement.id, viab:$('viabCard').style.display})")
    ok(r['ctx']=='B' and r['man']=='B' and r['pk'] and r['aba']=='p0' and r['f']=='rCCN' and r['viab']!='none',('CCN → 1º tri, foco no CCN',r))
    pg.evaluate("()=>{$('rCCN').value='6.10';run();}"); pg.locator('#bCCNApply').click(); pg.wait_for_timeout(150)
    r=pg.evaluate("()=>({src:IGSRC, pend:ORIG_PEND, bio:$('origBio').className, est:$('estIG').textContent})")
    ok(r['src']=='ccn' and r['pend'] is None and r['est'].endswith('· CCN · 1º tri'),('CCN aplicado resolve a pendência',r))
    pg.evaluate("()=>{$('bRst').click();}"); pg.evaluate(TAB,'p0')
    r=pg.evaluate("()=>({ctx:CTX, man:CTXMAN, pk:$('origPick').hidden, t:TITULO_MAN})")
    ok(r['ctx']=='A' and r['man'] is None and r['pk'] and r['t'] is None,('Limpar volta ao padrão',r))
    pg.locator('#origBio').click(); pg.locator('#pickBio').click(); pg.wait_for_timeout(300)
    r=pg.evaluate("()=>({ctx:CTX, aba:document.querySelector('.tab.on').dataset.p, f:document.activeElement.id, auto:AUTO_BIO})")
    ok(r['ctx']=='A' and r['aba']=='p1' and r['f']=='bDBP' and r['auto'],('DBP·CC·CA·F → Medidas, foco no DBP',r))
    pg.evaluate("()=>{$('bRst').click();$('sem').value=30;$('dias').value=0;IGSRC='mao';run();}"); pg.evaluate(TAB,'p0')
    pg.locator('#bOrig').click(); pg.locator('#origBio').click(); pg.wait_for_timeout(250)
    r=pg.evaluate("()=>({pk:$('origPick').hidden, aba:document.querySelector('.tab.on').dataset.p, f:document.activeElement.id})")
    ok(r['pk'] and r['aba']=='p1' and r['f']=='bDBP',('Biometria com IG vai direto',r))
    pg.evaluate("()=>{$('bRst').click();$('sem').value=12;$('dias').value=0;IGSRC='mao';run();}"); pg.evaluate(TAB,'p0')
    pg.locator('#bOrig').click(); pg.locator('#origBio').click(); pg.wait_for_timeout(250)
    r=pg.evaluate("()=>({aba:document.querySelector('.tab.on').dataset.p, f:document.activeElement.id})")
    ok(r['aba']=='p0' and r['f']=='rCCN',('1º tri com IG: Biometria leva ao CCN (Datação)',r))
    pg.evaluate("()=>{$('bRst').click();window.scrollTo(0,0);}"); pg.evaluate(TAB,'p0'); pg.locator('#origDireto').click(); pg.wait_for_timeout(150)
    ok(pg.evaluate(ATIVA)=='p0' and foco()=='sem',('Direto: cursor na IG, mesma aba',pg.evaluate(ATIVA),foco()))
    pg.locator('#origDum').click(); pg.wait_for_timeout(200)
    r=pg.evaluate("()=>({d:$('dtBox').style.display, o:$('dtBox').open, m:$('dtModo').value, s:$('dtSum').textContent, dum:$('dtDUM').style.display, us:$('dtUS').style.display, row:$('dtModoRow').style.display, f:document.activeElement.id})")
    ok(r=={'d':'','o':True,'m':'dum','s':'IG pela DUM','dum':'','us':'none','row':'none','f':'dtDumD'},('DUM: só o campo da DUM',r))
    pg.locator('#origDireto').click(); pg.wait_for_timeout(100)
    ok(pg.evaluate("()=>$('dtBox').style.display")=='none',('Direto depois de DUM vazio: cartão some',))
    pg.locator('#origUs').click(); pg.wait_for_timeout(200)
    r=pg.evaluate("()=>({d:$('dtBox').style.display, s:$('dtSum').textContent, us:$('dtUS').style.display, dum:$('dtDUM').style.display, f:document.activeElement.id})")
    ok(r=={'d':'','s':'IG pelo exame anterior','us':'','dum':'none','f':'dtDataD'},('Exame anterior: só data e IG',r))
    r=pg.evaluate("""()=>{$('dtHojeD').value='14';$('dtHojeM').value='10';$('dtHojeY').value='2026';$('dtDataD').value='01';$('dtDataM').value='09';$('dtDataY').value='2026';$('dtSem').value='20';$('dtDias').value='0';
      ['dtHojeD','dtDataD','dtSem'].forEach(function(i){$(i).dispatchEvent(new Event('input',{bubbles:true}));}); run(); $('bApply').click(); run();
      return {src:IGSRC, ig:sdT(getGA()), d:$('dtBox').style.display, est:$('estIG').textContent};}""")
    ok(r['src']=='usant' and r['ig']=='26s 1d' and r['d']=='' and r['est']=='IG 26s 1d · US anterior · 2º/3º tri',('IG pelo exame anterior',r))
    pg.evaluate("()=>{$('bRst').click();}"); ok(pg.evaluate("()=>$('dtBox').style.display")=='none',('Limpar esconde o cartão',))
    # ---------- 3. título deduzido
    B="$('bRst').click();$('sem').value=%d;$('dias').value=%d;IGSRC='mao';setModo('bio');$('bDBP').value='5.40';$('bCC').value='20.00';$('bCA').value='17.50';$('bFL').value='3.90';"
    pg.evaluate("()=>{"+B%(22,3)+"run();}")
    ok(pg.evaluate(T1).startswith('Ultrassonografia obstétrica — 22 semanas'),('obstétrica',pg.evaluate(T1)))
    pg.evaluate("()=>{$('eCer').value='2.30';run();}")
    ok(pg.evaluate(T1).startswith('Ultrassonografia obstétrica —'),('cerebelo sozinho não faz morfológico',pg.evaluate(T1)))
    for idc in ('eDbo','eUme','eRad','eUln','eTib','eFib'):
        pg.evaluate("(i)=>{"+B%(22,3)+"$(i).value='3.50';run();}",idc)
        ok(pg.evaluate(T1).startswith('Ultrassonografia morfológica do 2º trimestre — 22 semanas'),('praxe',idc,pg.evaluate(T1)))
    for (s,d,tri) in ((27,6,'2º'),(28,0,'3º'),(36,2,'3º'),(14,0,'2º')):
        pg.evaluate("()=>{"+B%(s,d)+"$('eUme').value='3.50';run();}")
        ok(pg.evaluate(T1).startswith('Ultrassonografia morfológica do %s trimestre — %d semanas'%(tri,s)),('trimestre do título',s,d,pg.evaluate(T1)))
    pg.evaluate("()=>{$('auip').value='1.05';run();}")
    ok(pg.evaluate(T1).startswith('Ultrassonografia morfológica do 2º trimestre com Dopplervelocimetria —'),('morfo + Doppler',pg.evaluate(T1)))
    pg.evaluate(TAB,'p3'); pg.locator('#segTit button[data-t="obst"]').click(); pg.wait_for_timeout(80)
    r=pg.evaluate("()=>({t:$('ldT').textContent.split('\\n')[0], m:TITULO_MAN, on:document.querySelector('#segTit .on').dataset.t, a:!!$('titAuto')})")
    ok(r['t'].startswith('Ultrassonografia obstétrica com Dopplervelocimetria') and r['m']=='obst' and r['on']=='obst' and r['a'],('correção no Laudo',r))
    r=pg.evaluate("()=>{var o=coletaEstado(); $('bRst').click(); var l=TITULO_MAN; aplicaEstado(o); return [l,TITULO_MAN,$('ldT').textContent.split('\\n')[0]];}")
    ok(r[0] is None and r[1]=='obst' and r[2].startswith('Ultrassonografia obstétrica com'),('escolha salva e recuperada',r))
    pg.evaluate(TAB,'p3'); pg.locator('#titAuto').click(); pg.wait_for_timeout(80)
    ok(pg.evaluate("()=>TITULO_MAN") is None and pg.evaluate(T1).startswith('Ultrassonografia morfológica'),('voltar ao automático',pg.evaluate(T1)))
    pg.evaluate("()=>{"+B%(30,0)+"run();}"); pg.evaluate(TAB,'p3'); pg.locator('#segTit button[data-t="morfo"]').click()
    ok(pg.evaluate(T1).startswith('Ultrassonografia morfológica do 3º trimestre — 30 semanas'),('morfológica escolhida à mão',pg.evaluate(T1)))
    r=pg.evaluate("()=>{"+B%(30,0)+"run(); var o=coletaEstado(); o.TIPO_EX='morfo'; $('bRst').click(); aplicaEstado(o); return [$('ldT').textContent.split('\\n')[0], typeof TIPO_EX];}")
    ok(r[0].startswith('Ultrassonografia obstétrica —') and r[1]=='undefined',('exame salvo com tipo antigo: tipo ignorado',r))
    # Doppler fora do exame: sem Doppler preenchido, peso adequado não cita Doppler; peso < p10 continua citando
    pg.evaluate("()=>{"+B%(30,0)+"$('bDBP').value='7.60';$('bCC').value='27.80';$('bCA').value='26.00';$('bFL').value='5.80';run();}")
    r=pg.evaluate("()=>[textoConclusao(), ST.sint&&ST.sint.cls]")
    ok('Doppler' not in r[0] and r[1] in ('aig','aig-la'),('AIG sem Doppler: conclusão sem Doppler',r))
    pg.evaluate("()=>{"+B%(32,0)+"$('bDBP').value='7.40';$('bCC').value='26.80';$('bCA').value='24.00';$('bFL').value='5.60';run();}")
    r=pg.evaluate("()=>[textoConclusao(), ST.sint&&ST.sint.cls]")
    ok('Doppler fetal não avaliado' in r[0] or 'não avaliad' in r[0],('peso < p10 sem Doppler: cita que não foi avaliado',r))
    # gemelar: praxe só no feto B ainda faz morfológico olhando o feto A
    r=pg.evaluate("""()=>{"""+B%(24,0)+"""$('gemelar').checked=true; run(); trocaFeto('B'); $('eUme').value='4.20'; run(); trocaFeto('A'); run();
      return [FETO, $('eUme').value, $('ldT').textContent.split('\\n')[0]];}""")
    ok(r[0]=='A' and r[1]=='' and 'morfológica do 2º trimestre' in r[2],('gemelar: praxe do outro feto conta',r))
    # ---------- 4. biometria completa na Morfologia (mesmos campos)
    pg.evaluate("()=>{"+B%(22,3)+"$('eCer').value='2.30';run();}")
    pg.evaluate(TAB,'p6'); pg.wait_for_timeout(120)
    r=pg.evaluate("""()=>({ord:[].map.call($('praxeCard').querySelectorAll('input.num'),function(i){return i.id}).join(','),
      calc:$('pCalc').closest('#praxeCard')!==null, ultimo:$('praxeCard').lastElementChild.id||$('praxeCard').lastElementChild.className,
      v:$('bDBP').value, pv:$('pV').textContent, bm:BIO_MORFO})""")
    ok(r['ord']=='bDBP,bCC,eCer,eDbo,bCA,bFL,eUme,eRad,eUln,eTib,eFib' and r['calc'] and r['v']=='5.40' and r['bm'],('ordem na Morfologia',r))
    pv0=r['pv']; pg.locator('#bCA').fill('18.20'); pg.wait_for_timeout(80)
    r=pg.evaluate("()=>({pv:$('pV').textContent, st:ST.pfe&&Math.round(ST.pfe.w)})")
    ok(r['pv']!=pv0 and str(r['st']) in r['pv'].replace('.',''),('digitar na Morfologia recalcula o peso',r,pv0))
    pg.evaluate(TAB,'p1'); pg.wait_for_timeout(120)
    r=pg.evaluate("""()=>({ord:[].map.call($('boxBio').querySelectorAll('input'),function(i){return i.id}).join(','), duo:[].filter.call($('boxBio').children,function(x){return x.classList.contains('duo')}).length,
      calc:$('pCalc').nextElementSibling.id, ca:$('bCA').value, bm:BIO_MORFO, mv:$('mvA').children.length+$('mvB').children.length+$('mvC').children.length+$('mvT').children.length})""")
    ok(r=={'ord':'bDBP,bCC,bCA,bFL','duo':2,'calc':'pBar','ca':'18.20','bm':False,'mv':0},('volta para Medidas no lugar',r))
    for _ in range(3):   # ida e volta repetida não duplica nada
        pg.evaluate(TAB,'p6'); pg.evaluate(TAB,'p2'); pg.evaluate(TAB,'p6'); pg.evaluate(TAB,'p1')
    ok(pg.evaluate("()=>document.querySelectorAll('#bDBP').length+$('boxBio').querySelectorAll('.duo').length+document.querySelectorAll('#pCalc').length")==4,('idas e voltas',))
    pg.evaluate(TAB,'p6'); pg.evaluate("()=>{$('bCC').focus();}")
    pg.locator('#bCC').fill(''); pg.locator('#bCC').type('20.00'); pg.wait_for_timeout(80)
    ok(foco()=='eCer',('Morfologia: CC → cerebelo',foco()))
    pg.locator('#eDbo').fill(''); pg.locator('#eDbo').type('3.50'); pg.wait_for_timeout(80)
    ok(foco()=='bCA',('Morfologia: DBO → CA',foco()))
    pg.locator('#bFL').fill(''); pg.locator('#bFL').type('3.90'); pg.wait_for_timeout(80)
    ok(foco()=='eUme',('Morfologia: fêmur → úmero',foco()))
    pg.evaluate("()=>{$('bCC').focus();}"); pg.keyboard.press('Enter'); pg.wait_for_timeout(60)
    ok(foco()=='eCer',('Enter segue a ordem da Morfologia',foco()))
    pg.evaluate(TAB,'p1'); pg.locator('#bCC').fill(''); pg.locator('#bCC').type('20.00'); pg.wait_for_timeout(80)
    ok(foco()=='bCA',('Medidas: CC → CA',foco()))
    pg.evaluate("()=>{setModo('dir');}"); pg.evaluate(TAB,'p6')
    r=pg.evaluate("()=>({a:getComputedStyle($('mvA')).display, b:getComputedStyle($('mvB')).display, c:$('pCalc').closest('#praxeCard')!==null})")
    ok(r['a']=='none' and r['b']=='none' and r['c'],('peso informado: as 4 medidas somem da Morfologia',r))
    pg.evaluate("()=>{setModo('bio');}")
    ok(pg.evaluate("()=>getComputedStyle($('mvA')).display")!='none',('volta à biometria',))
    pg.evaluate("()=>{$('sem').value=12;run();}")   # muda de contexto com a biometria na Morfologia
    ok(pg.evaluate("()=>[BIO_MORFO,$('bDBP').closest('.pane').id]")==[False,'p1'],('troca de trimestre devolve a biometria',))
    # ---------- 5. aviso do outro trimestre + faixa sem peso no 1º tri
    pg.evaluate("()=>{"+B%(32,2)+"$('mbv').value='4.2';$('auip').value='1.05';run();$('sem').value=12;$('dias').value=3;run();}")
    r=pg.evaluate("()=>({v:$('outroTri').style.display, t:$('outroTri').textContent, pfe:$('estPfe').textContent, ctx:CTX, ld:$('ldT').textContent})")
    ok(r['v']=='' and '2º/3º trimestre' in r['t'] and 'biometria' in r['t'] and 'Doppler' in r['t'] and 'líquido' in r['t'] and r['pfe']=='' and r['ctx']=='B',('outro trimestre: aviso; faixa sem peso',r))
    ok('PFE' not in r['ld'] and 'Líquido' not in r['ld'],('dado do outro trimestre fora do laudo',r['ld'][:200]))
    pg.locator('#outroTri .apaga').click(); pg.wait_for_timeout(80)
    r=pg.evaluate("()=>({v:$('outroTri').style.display, b:$('bDBP').value+$('mbv').value+$('auip').value, ig:getGA()!==null})")
    ok(r=={'v':'none','b':'','ig':True},('apagar os dados do outro trimestre',r))
    pg.evaluate("()=>{$('bRst').click();$('sem').value=12;$('dias').value=3;IGSRC='mao';run();$('rCCN').value='6.10';$('rTN').value='0.15';run();$('sem').value=30;$('dias').value=0;run();}")
    r=pg.evaluate("()=>({v:$('outroTri').style.display, t:$('outroTri').textContent})")
    ok(r['v']=='' and '1º trimestre' in r['t'] and 'CCN' in r['t'] and 'TN' in r['t'],('dados do 1º tri no 2º/3º',r))
    pg.evaluate("()=>{$('bRst').click();$('sem').value=30;$('dias').value=0;IGSRC='mao';run();}")
    ok(pg.evaluate("()=>$('outroTri').style.display")=='none',('sem dado de outro trimestre, sem aviso',))
    # ---------- 6. campo preenchido nunca some; janelas de IG
    pg.evaluate("()=>{$('bRst').click();$('sem').value=22;$('dias').value=0;IGSRC='mao';run();$('ePrg').value='0.70';run();}")
    r=pg.evaluate("()=>({cls:$('ePrgRes').className, ld:/Prega nucal/.test($('ldT').textContent), vis:$('prgWrap').style.visibility})")
    ok('bad' in r['cls'] and r['ld'] and r['vis']=='visible',('prega 22 sem',r))
    pg.evaluate("()=>{$('sem').value=26;run();}")
    r=pg.evaluate("()=>({v:$('ePrg').value, cls:$('ePrgRes').className, t:$('ePrgRes').textContent, ld:/Prega nucal/.test($('ldT').textContent), vis:$('prgWrap').style.visibility, st:ST.estr.prg})")
    ok(r['v']=='0.70' and 'nt' in r['cls'] and 'não entra no laudo' in r['t'] and not r['ld'] and r['vis']=='visible' and r['st'] is None,('prega fora da janela: fica, fora do laudo',r))
    pg.evaluate("()=>{$('sem').value=22;run();}")
    ok(pg.evaluate("()=>/Prega nucal/.test($('ldT').textContent)"),('volta à janela: volta ao laudo',))
    pg.evaluate("()=>{$('sem').value=26;run();}"); pg.evaluate(TAB,'p6'); pg.evaluate("()=>{$('estrBox').open=true;}")
    pg.locator('#ePrgRes .apaga').click(); pg.wait_for_timeout(80)
    ok(pg.evaluate("()=>[$('ePrg').value,$('prgWrap').style.visibility]")==['','hidden'],('apagar a prega; vazia some fora da janela',))
    for (s,vis) in ((19,'none'),(20,''),(24,''),(25,'none'),(30,'none')):
        pg.evaluate("(s)=>{$('bRst').click();$('sem').value=s;$('dias').value=(s===24?6:0);IGSRC='mao';run();}",s)
        ok(pg.evaluate("()=>$('onDuo').style.display")==vis,('osso nasal vazio, janela 20+0–24+6',s,vis))
    pg.evaluate("()=>{$('bRst').click();$('sem').value=30;$('dias').value=0;IGSRC='mao';run();$('eON').value='0.80';run();}")
    ok(pg.evaluate("()=>$('onDuo').style.display")=='' and 'janela' in pg.evaluate("()=>$('eONRes').textContent"),('osso nasal preenchido fora da janela fica',))
    for (s,vis) in ((9,'none'),(11,''),(13,'')):
        pg.evaluate("(s)=>{$('bRst').click();$('sem').value=s;$('dias').value=(s===13?6:0);IGSRC='mao';run();}",s)
        ok(pg.evaluate("()=>[CTX,$('tnCard').style.display]")==['B',vis],('TN vazia, janela 11+0–13+6',s,vis))
    pg.evaluate("()=>{$('bRst').click();$('sem').value=9;$('dias').value=0;IGSRC='mao';run();$('rTN').value='0.12';run();}")
    ok(pg.evaluate("()=>$('tnCard').style.display")=='',('TN preenchida fora da janela fica',))
    # ---------- 7. gemelar
    pg.evaluate("()=>{$('bRst').click();$('sem').value=30;$('dias').value=0;IGSRC='mao';run();}"); pg.evaluate(TAB,'p0')
    pg.locator('#gemelar').check(); pg.wait_for_timeout(80)
    r=pg.evaluate("()=>({cb:$('corionBox').style.display, fs:$('fetoSel').style.display, chips:$('estPfe').querySelectorAll('.chipF').length, gr:$('gemRes').className})")
    ok(r['cb']=='' and r['fs']=='' and r['chips']==2 and 'on' in r['gr'],('gemelar na Datação',r))
    for w in (320,375,390,430):
        pg.set_viewport_size({'width':w,'height':760}); pg.evaluate("()=>run()")
        r=pg.evaluate("()=>[Math.round($('estBar').getBoundingClientRect().height), getComputedStyle($('estIG').querySelector('.estX')).display]")
        ok(r[0]<=44 and r[1]=='none',('gemelar: faixa numa linha (sem origem/trimestre)',w,r))
    pg.set_viewport_size({'width':390,'height':844})
    pg.evaluate(TAB,'p6'); ok(pg.evaluate("()=>$('fTagMed').closest('#praxeCard')!==null"),('etiqueta do feto na Morfologia',))
    pg.evaluate(TAB,'p1'); ok(pg.evaluate("()=>$('fTagMed').closest('.pane').id")=='p1',('etiqueta volta',))
    pg.evaluate("()=>{$('bRst').click();}")
    ok(pg.evaluate("()=>[$('corionBox').style.display,$('gemelar').checked]")==['none',False],('Limpar desfaz o gemelar',))
    # ---------- 8. faixa: origem e trimestre
    for (src,txt) in (('dum','DUM'),('usant','US anterior'),('bio','biometria'),('ccn','CCN'),('mao','informada')):
        pg.evaluate("(s)=>{$('bRst').click();$('sem').value=25;$('dias').value=4;IGSRC=s;run();}",src)
        ok(pg.evaluate("()=>$('estIG').textContent")=='IG 25s 4d · %s · 2º/3º tri'%txt,('faixa',src,pg.evaluate("()=>$('estIG').textContent")))
    # R15.1: o quadro da IG rola com o título; faixa (com a IG) e abas ficam
    pg.evaluate("()=>{$('bRst').click();$('sem').value=30;$('dias').value=0;IGSRC='mao';run();}"); pg.evaluate(TAB,'p1'); pg.evaluate("()=>window.scrollTo(0,1200)"); pg.wait_for_timeout(200)
    r=pg.evaluate("()=>({sem:Math.round($('sem').getBoundingClientRect().bottom), topo:Math.round($('topo').getBoundingClientRect().top), est:$('estIG').textContent})")
    ok(r['sem']<=0 and r['topo']==0 and r['est']=='IG 30s 0d · informada · 2º/3º tri',('ao rolar: IG na faixa presa',r))
    pg.set_viewport_size({'width':1024,'height':850})
    ok(pg.evaluate("()=>APP_VERSAO") not in ('R15.0',),('versão anterior à R15.1',))
    grupo('34 Reorganização: abas em cima, IG no cabeçalho, título deduzido, biometria na Morfologia (R15.0–R15.1)',C[0],F)

# ------------------------------------------------------------------ 35 R15.2 gemelar digitando + apagar volta
def g_r152(pg):
    """Auditoria de 15/10/2026: (1) no gemelar, com o outro feto preenchido, digitar decimal tecla a tecla perdia o
    separador (4,2 → 42) em 29 de 33 campos — agora nenhum perde, e a conclusão do outro feto é refeita ao sair do
    campo (igual à calculada do zero); (2) tecla apagar com o campo vazio volta ao campo anterior da sequência do
    avanço automático, cursor no fim; tecla segurada não atravessa; campo com texto não salta; (3) texto do título."""
    F=[]; C=[0]
    def ok(c,m):
        C[0]+=1
        if not c: F.append(m)
    pg.set_viewport_size({'width':390,'height':844})
    def foco(): return pg.evaluate("()=>document.activeElement&&document.activeElement.id")
    TAB="(t)=>{document.querySelector('.tab[data-p=\"'+t+'\"]').click();}"
    GEM="""()=>{$('bRst').click();$('sem').value=30;$('dias').value=0;IGSRC='mao';$('gemelar').checked=true;$('corion').value='dc';run();
      $('bDBP').value='7.60';$('bCC').value='27.50';$('bCA').value='25.40';$('bFL').value='5.70';$('mbv').value='4.0';$('auip').value='1.00';run();
      trocaFeto('B');$('bDBP').value='7.40';$('bCC').value='27.00';$('bCA').value='23.50';$('bFL').value='5.50';$('mbv').value='3.8';$('auip').value='1.05';run();
      trocaFeto('A');run();}"""
    INT=set(['sem','dias','dtHojeD','dtHojeM','dtHojeY','dtDataD','dtDataM','dtDataY','dtSem','dtDias','dtDumD','dtDumM','dtDumY','vD','vM','vY','vPeso','pDir','fcf1','fcf2','segDias','eEix'])
    # (1) todo campo numérico visível, decimal digitado tecla a tecla, nos dois fetos
    for feto in ('A','B'):
        for a in ('p1','p6','p2'):
            pg.evaluate(GEM); pg.evaluate("(f)=>{trocaFeto(f);}",feto); pg.evaluate(TAB,a); pg.wait_for_timeout(60)
            pg.evaluate("()=>{document.querySelectorAll('.pane.on details').forEach(function(d){d.open=true}); var l=$('lnkPsv'); if(l&&l.offsetParent) l.click();}")
            ids=pg.evaluate("()=>[].filter.call(document.querySelectorAll('.pane.on input.num'),function(e){return e.id&&e.offsetParent&&getComputedStyle(e).visibility!=='hidden'}).map(function(e){return e.id})")
            for i in ids:
                if i in INT: continue
                pg.evaluate("(i)=>{$(i).value='';$(i).dispatchEvent(new Event('input',{bubbles:true}));}",i)
                pg.locator('#'+i).click(); pg.keyboard.type('1.25',delay=10)
                v=pg.evaluate("(i)=>$(i).value",i)
                ok(v=='1.25',('gemelar: separador perdido',feto,a,i,v))
                pg.evaluate("(i)=>{$(i).value='';$(i).dispatchEvent(new Event('input',{bubbles:true}));}",i)
    # conclusão do outro feto: parada durante a digitação, refeita ao sair do campo — igual ao cálculo do zero
    pg.evaluate(GEM); pg.evaluate(TAB,'p1'); pg.locator('#bCA').fill(''); pg.locator('#bCA').click(); pg.keyboard.type('21.1',delay=15)
    durante=pg.evaluate("()=>[GEM_PEND, document.activeElement.id, $('bCA').value]")
    pg.keyboard.type('0',delay=15)
    pg.evaluate(TAB,'p3'); pg.wait_for_timeout(120)
    depois=pg.evaluate("()=>({pend:GEM_PEND, ld:$('ldT').textContent, conc:textoConclusao()})")
    ref=pg.evaluate("()=>{document.activeElement&&document.activeElement.blur(); GEM_ULT=null; run(); return {ld:$('ldT').textContent, conc:textoConclusao()};}")
    ok(durante==[True,'bCA','21.1'],('durante a digitação o outro feto espera (campo intacto)',durante))
    ok(depois['pend'] is False and depois['ld']==ref['ld'] and depois['conc']==ref['conc'],('ao sair do campo, o laudo é o do cálculo do zero',depois['pend']))
    ok('Feto B' in ref['ld'],('laudo gemelar',ref['ld'][:120]))
    # sem gemelar e com gemelar sem o outro feto: nada muda (cálculo normal a cada tecla)
    pg.evaluate("()=>{$('bRst').click();$('sem').value=30;$('dias').value=0;IGSRC='mao';run();}"); pg.evaluate(TAB,'p1')
    pg.locator('#bCA').click(); pg.keyboard.type('25.40',delay=10)
    ok(pg.evaluate("()=>[GEM_PEND,$('bCA').value]")==[False,'25.40'],('feto único',))
    # (2) apagar volta
    pg.evaluate("()=>{$('bRst').click();$('sem').value=30;$('dias').value=0;IGSRC='mao';run();}"); pg.evaluate(TAB,'p1')
    pg.locator('#bDBP').click(); pg.keyboard.type('8.10',delay=10)
    ok(foco()=='bCC',('avanço DBP → CC',foco()))
    pg.keyboard.press('Backspace'); pg.wait_for_timeout(40)
    ok(foco()=='bDBP' and pg.evaluate("()=>$('bDBP').value")=='8.10',('apagar no CC vazio volta ao DBP, sem apagar nada',foco()))
    pg.keyboard.press('Backspace'); pg.wait_for_timeout(40)
    ok(pg.evaluate("()=>$('bDBP').value")=='8.1' and foco()=='bDBP',('o toque seguinte apaga o último dígito do DBP',pg.evaluate("()=>$('bDBP').value")))
    pg.keyboard.press('Backspace'); pg.keyboard.press('Backspace'); pg.keyboard.press('Backspace'); pg.wait_for_timeout(40)
    ok(pg.evaluate("()=>$('bDBP').value")=='' and foco()=='bDBP',('DBP vazio é o primeiro: não volta mais',foco()))
    # campo com texto: apagar só apaga
    pg.locator('#bCC').click(); pg.keyboard.type('29.5',delay=10); pg.keyboard.press('Backspace'); pg.wait_for_timeout(40)
    ok(foco()=='bCC' and pg.evaluate("()=>$('bCC').value").startswith('29'),('campo com texto não salta',foco(),pg.evaluate("()=>$('bCC').value")))
    # tecla segurada (repeat) não atravessa
    pg.evaluate("()=>{$('bCA').value='';$('bCC').value='';run();}"); pg.locator('#bCA').click()
    pg.evaluate("()=>{var e=$('bCA'); e.dispatchEvent(new KeyboardEvent('keydown',{key:'Backspace',repeat:true,bubbles:true,cancelable:true}));}")
    ok(foco()=='bCA',('tecla segurada não volta',foco()))
    # Medidas: CA → CC; fêmur → CA
    for de,para in (('bCA','bCC'),('bFL','bCA')):
        pg.locator('#'+de).click(); pg.evaluate("(i)=>{$(i).value='';}",de); pg.keyboard.press('Backspace'); pg.wait_for_timeout(30)
        ok(foco()==para,('Medidas: volta',de,para,foco()))
    # Morfologia: a ordem do exame
    pg.evaluate(TAB,'p6'); pg.wait_for_timeout(80)
    for de,para in (('bCC','bDBP'),('eCer','bCC'),('eDbo','eCer'),('bCA','eDbo'),('bFL','bCA'),('eUme','bFL'),('eRad','eUme'),('eUln','eRad'),('eTib','eUln'),('eFib','eTib')):
        pg.evaluate("(i)=>{$(i).value='';}",de); pg.locator('#'+de).click(); pg.keyboard.press('Backspace'); pg.wait_for_timeout(30)
        ok(foco()==para,('Morfologia: volta',de,para,foco()))
    # achados: prega nucal escondida fora da janela é pulada (IG 30: DIO volta ao átrio; IG 22: DIO volta à prega)
    pg.evaluate("()=>{$('estrBox').open=true;$('sSNC').open=true;$('sURI').open=true;}")
    for de,para in (('eAtr','eCis'),('eDio','eAtr'),('eBex','ePel')):
        pg.evaluate("(i)=>{$(i).value='';}",de); pg.locator('#'+de).click(); pg.keyboard.press('Backspace'); pg.wait_for_timeout(30)
        ok(foco()==para,('achados (30 sem): volta',de,para,foco()))
    pg.evaluate("()=>{$('sem').value=22;run();}"); pg.evaluate("()=>{$('eDio').value='';}"); pg.locator('#eDio').click(); pg.keyboard.press('Backspace'); pg.wait_for_timeout(30)
    ok(foco()=='ePrg',('achados (22 sem): DIO volta à prega',foco()))
    pg.evaluate(TAB,'p0'); pg.evaluate("()=>window.scrollTo(0,0)")
    for de,para in (('dtHojeM','dtHojeD'),('dtHojeY','dtHojeM')):
        pg.evaluate("(i)=>{$(i).value='';}",de); pg.locator('#'+de).click(); pg.keyboard.press('Backspace'); pg.wait_for_timeout(30)
        ok(foco()==para,('data do exame: volta',de,para,foco()))
    pg.evaluate("()=>{$('dias').value='';}"); pg.locator('#dias').click(); pg.keyboard.press('Backspace'); pg.wait_for_timeout(30)
    ok(foco()=='sem',('IG: dias → semanas',foco()))
    # FCF (Medidas) e umbilical (Doppler) não se ligam pelo apagar
    ok(pg.evaluate("()=>VOLTA.auip===undefined"),('sem volta entre abas',))
    # (3) texto do título
    pg.evaluate("()=>{$('bRst').click();$('sem').value=22;$('dias').value=0;IGSRC='mao';run();}")
    t=pg.evaluate("()=>$('titInfo').textContent")
    ok(t=='O app marcou Obstétrica: DBO e ossos além do fêmur não foram medidos. Um toque corrige.',('texto do título',t))
    pg.evaluate("()=>{$('eFib').value='3.4';run();}")
    t=pg.evaluate("()=>$('titInfo').textContent")
    ok(t=='O app marcou Morfológica porque DBO ou ossos além do fêmur foram medidos. Um toque corrige.',('texto do título',t))
    pg.set_viewport_size({'width':1024,'height':850})
    ok(pg.evaluate("()=>APP_VERSAO")=='R15.2',('versão',))
    grupo('35 Gemelar digitando decimal; apagar volta ao campo anterior (R15.2)',C[0],F)

# ================================================================== SENTINELAS (15/10/2026)
# Grupos 36–40: pegam CLASSES de erro, não um defeito específico. Nasceram da auditoria de 15/10/2026: o erro do
# gemelar (vírgula perdida) passou anos porque os testes preenchiam o campo de uma vez (fill). Regra: teste de
# interface que envolva digitação usa TECLA A TECLA (keyboard.type), nunca só fill().
import re as _re

def _eng(pg):
    try: return pg.context.browser.browser_type.name
    except Exception: return 'chromium'

def _gera(seed,N):
    """exames aleatórios reprodutíveis: 60% feto único 2º/3º tri, 20% gemelar, 20% 1º tri"""
    rnd=random.Random(seed)
    def U(a,b,c=2): return round(rnd.uniform(a,b),c)
    def bio(g):
        f=rnd.uniform(0.80,1.18)
        return dict(bDBP=round((0.30*g-0.9)*f,2), bCC=round((1.10*g-3.4)*f,2), bCA=round((1.05*g-3.6)*f,2), bFL=round((0.235*g-1.1)*f,2))
    out=[]
    for _ in range(N):
        t=rnd.random()
        if t<0.6:
            g=rnd.randint(15,40); c=dict(tipo='u',sem=g,dias=rnd.randint(0,6),**bio(g))
            if rnd.random()<.7: c.update(auip=U(0.5,2.0),acmip=U(0.8,2.6))
            if rnd.random()<.5: c.update(mbv=U(1,11,1))
            if rnd.random()<.3: c.update(utD=U(0.4,2.2),utE=U(0.4,2.2))
            if rnd.random()<.3: c.update(eUme=U(1,6.5),eDbo=U(2,6))
            if rnd.random()<.2: c.update(eAtr=U(0.4,1.6),eCer=U(1.2,5))
        elif t<0.8:
            g=rnd.randint(20,37); c=dict(tipo='g',sem=g,dias=rnd.randint(0,6),cor=rnd.choice(['dc','mc','']),A=bio(g),B=bio(g))
            if rnd.random()<.6: c['A'].update(auip=U(0.6,1.8)); c['B'].update(auip=U(0.6,1.8))
        else:
            g=rnd.randint(6,13); c=dict(tipo='t',sem=g,dias=rnd.randint(0,6),rCCN=U(0.3,8.4))
            if g>=11 and rnd.random()<.7: c.update(rTN=U(0.08,0.5))
        out.append(c)
    return out
_ARMA=r"""(c)=>{ $('bRst').click(); var set=function(k,v){var e=$(k); if(e&&v!==undefined) e.value=v;};
  $('sem').value=c.sem; $('dias').value=c.dias; IGSRC='mao'; setModo('bio');
  if(c.tipo==='g'){ $('gemelar').checked=true; $('corion').value=c.cor; run();
     Object.keys(c.A).forEach(function(k){set(k,c.A[k]);}); run(); trocaFeto('B'); Object.keys(c.B).forEach(function(k){set(k,c.B[k]);}); run(); trocaFeto('A'); }
  else { Object.keys(c).forEach(function(k){ if(['tipo','sem','dias','cor','A','B'].indexOf(k)<0) set(k,c[k]); }); }
  run(); }"""

# ------------------------------------------------------------------ 36 digitação real
def g_digita(pg):
    """Todo campo numérico visível, digitado TECLA A TECLA, em 5 contextos (feto único 2º/3º tri e 1º tri, feto A e
    feto B do gemelar com o outro preenchido, modo mm). No WebKit o teclado é pt-BR e digita com VÍRGULA (como o
    iPhone); no Chromium, com ponto (o Chromium descarta a vírgula em campo numérico). O valor tem de ficar inteiro."""
    F=[]; C=[0]
    def ok(c,m):
        C[0]+=1
        if not c: F.append(m)
    eng=_eng(pg); sep=',' if eng=='webkit' else '.'
    ctx=pg.context.browser.new_context(locale='pt-BR' if eng=='webkit' else 'en-US',viewport={'width':390,'height':844})
    q=ctx.new_page(); q.on('dialog',lambda d:d.accept()); er=[]; q.on('pageerror',lambda e:er.append(str(e)[:120]))
    q.goto(pg.url); q.wait_for_timeout(500)
    CTXS={
     'único 30s':"()=>{$('bRst').click();setUnidade('cm');$('sem').value=30;$('dias').value=0;IGSRC='mao';run();}",
     'único 12s':"()=>{$('bRst').click();setUnidade('cm');$('sem').value=12;$('dias').value=3;IGSRC='mao';run();}",
     'gemelar A':"""()=>{$('bRst').click();setUnidade('cm');$('sem').value=30;$('dias').value=0;IGSRC='mao';$('gemelar').checked=true;run();
        trocaFeto('B');$('bDBP').value='7.40';$('bCC').value='27.00';$('bCA').value='23.50';$('bFL').value='5.50';$('mbv').value='3.8';$('auip').value='1.05';$('eCer').value='3.6';run();trocaFeto('A');run();}""",
     'gemelar B':"""()=>{$('bRst').click();setUnidade('cm');$('sem').value=30;$('dias').value=0;IGSRC='mao';$('gemelar').checked=true;run();
        $('bDBP').value='7.60';$('bCC').value='27.50';$('bCA').value='25.40';$('bFL').value='5.70';$('mbv').value='4.0';$('auip').value='1.00';$('eCer').value='3.7';run();trocaFeto('B');run();}""",
     'modo mm 30s':"()=>{$('bRst').click();setUnidade('mm');$('sem').value=30;$('dias').value=0;IGSRC='mao';run();}"}
    def esperado(i):
        if i.endswith('Y'): return '2026'
        if i in ('vPeso','pDir'): return '1234'
        if i in ('fcf1','fcf2'): return '145'
        if i=='dtSem': return '20'
        if i=='dtDias': return '3'
        if i.startswith(('dt','v')) and i.endswith('D'): return '12'
        if i.startswith(('dt','v')) and i.endswith('M'): return '09'
        if i=='eEix': return '45'
        return None
    for cen,prep in CTXS.items():
        for a in (['p0','p4','p5'] if '12s' in cen else ['p0','p1','p6','p2']):
            q.evaluate(prep); q.locator('.tab[data-p="%s"]'%a).click(); q.wait_for_timeout(60)
            q.evaluate("()=>{document.querySelectorAll('.pane.on details').forEach(function(d){d.open=true}); ['lnkPsv','lnkFcf2','lnkFcf1'].forEach(function(i){var l=$(i); if(l&&l.offsetParent) l.click();}); ORIG_PEND='usant'; $('dtModo').value='us'; run(); var d=$('dtBox'); if(d){d.open=true;}}")
            ids=q.evaluate("()=>[].filter.call(document.querySelectorAll('.pane.on input.num'),function(e){return e.id&&e.offsetParent&&getComputedStyle(e).visibility!=='hidden'&&!e.disabled}).map(function(e){return e.id})")
            for i in ids:
                exp=esperado(i); txt=exp if exp else '1'+sep+'25'
                q.evaluate("(i)=>{$(i).value='';$(i).dispatchEvent(new Event('input',{bubbles:true}));}",i)
                try:
                    q.locator('#'+i).click(timeout=2000); q.keyboard.type(txt,delay=8)
                except Exception as e:
                    ok(False,('campo não clicável',cen,a,i)); continue
                v=q.evaluate("(i)=>$(i).value",i)
                ok(v==(exp if exp else '1.25'),('digitação perdeu caractere',eng,cen,a,i,txt,v))
                q.evaluate("(i)=>{$(i).value='';$(i).dispatchEvent(new Event('input',{bubbles:true}));}",i)
    ok(C[0]>=195,('menos campos numéricos que os 204 da R15.2 — campo sumiu? se foi de propósito, ajuste aqui',C[0]))
    ok(not er,('erros de JS',er[:2]))
    ctx.close()
    grupo('36 Sentinela: digitação tecla a tecla em todo campo (%s)'%('vírgula pt-BR' if sep==',' else 'ponto'),C[0],F)

# ------------------------------------------------------------------ 37 texto proibido + coerência
def g_coerencia(pg):
    """150 exames aleatórios: nenhum NaN/undefined/null/[object/Infinity em tela, faixa ou laudo; laudo e conclusão
    sem espaço duplo, espaço antes de pontuação, ponto/vírgula dupla, parêntese vazio ou palavra repetida; PFE e
    percentil iguais no cartão, na faixa, no laudo e na conclusão; IG da faixa = IG do laudo; título × seletor do
    Laudo × praxe preenchida; umbilical do cartão = laudo; gemelar: chips da faixa = laudo = conclusão."""
    F=[]; C=[0]
    def ok(c,m):
        C[0]+=1
        if not c: F.append(m)
    pg.set_viewport_size({'width':390,'height':844})
    LE=r"""()=>({ld:$('ldT').textContent, conc:$('ldConc').textContent, chk:[].map.call(document.querySelectorAll('#chk .chk-ln'),function(l){return l.textContent}).join(' | '),
      est:$('estBar').innerText, estT:$('estBar').textContent, panes:[].map.call(document.querySelectorAll('.pane'),function(p){return p.textContent}).join(' '),
      pv:$('pV').textContent, au:($('auRes').textContent||''), ga:getGA()===null?null:sdT(getGA()),
      tit:(document.querySelector('#segTit .on')?document.querySelector('#segTit .on').dataset.t:null), indisp:LAUDO_INDISP})"""
    PROIB=_re.compile(r'NaN|undefined|\bnull\b|\[object|Infinity')
    FMT=[(_re.compile(r'[^\n ]  +[^\n ]'),'espaço duplo'),(_re.compile(r' [,.;:](?!\d)'),'espaço antes de pontuação'),(_re.compile(r'(?<!\.)\.\.(?!\.)'),'ponto duplo'),
         (_re.compile(r'\( |\s\)'),'espaço no parêntese'),(_re.compile(r'\(\)'),'parêntese vazio'),(_re.compile(r',,'),'vírgula dupla'),(_re.compile(r'\b([A-Za-zÀ-ú]{3,}) \1\b',_re.I),'palavra repetida')]
    def igext(ga):
        s,d=ga.split('s '); s=int(s); d=int(d.rstrip('d'))
        return '%d semana%s e %d dia%s'%(s,'' if s==1 else 's',d,'' if d==1 else 's')
    for i,c in enumerate(_gera(37,150)):
        pg.evaluate(_ARMA,c); r=pg.evaluate(LE)
        for nome in ('ld','conc','chk','estT','panes'):
            m=PROIB.search(r[nome]); ok(not m,('texto proibido',nome,i,r[nome][max(0,m.start()-50):m.end()+30] if m else ''))
        for rx,nm in FMT:
            for nome in ('ld','conc'):
                m=rx.search(r[nome]); ok(not m,(nm,nome,i,r[nome][max(0,m.start()-40):m.end()+20] if m else ''))
        if r['indisp']: continue
        ld=r['ld']
        if r['ga'] and c['tipo']!='t': ok(igext(r['ga']) in ld.split('\n')[0],('IG do laudo ≠ faixa',i,r['ga'],ld.split('\n')[0]))
        if r['ga']: ok(('IG '+r['ga']) in r['estT'],('IG da faixa',i,r['ga'],r['estT'][:60]))
        if c['tipo']!='t':
            mf=ld.startswith('Ultrassonografia morfológica')
            ok((r['tit']=='morfo')==mf,('título × seletor do Laudo',i,r['tit'],ld[:60]))
            ok(any(k in c for k in ('eDbo','eUme'))==mf,('título × praxe',i,ld[:60]))
        if c['tipo']=='u':
            m=_re.search(r'PFE: (\d+) g \(([^)]*)\)',ld)
            if m:
                g_,lab=m.group(1),m.group(2)
                ok(r['pv'].startswith(g_+' g'),('PFE cartão × laudo',i,r['pv'],g_))
                ok((g_+' g · '+lab) in r['estT'],('PFE faixa × laudo',i,r['estT'][:80],g_,lab))
                nums=_re.findall(r'percentil (\d+(?:,\d+)?|superior a 99|inferior a 1)',r['conc'])
                if nums and lab.startswith('p') and '<' not in lab and '>' not in lab and _re.search(r'(peso|PFE)',r['conc']):
                    ok(lab[1:] in nums,('percentil laudo × conclusão',i,lab,nums))
            ma=_re.search(r'Artéria umbilical: IP ([\d,]+) \(([^)]*)\)',ld)
            if ma: ok(r['au'].startswith(ma.group(2)),('umbilical cartão × laudo',i,r['au'][:30],ma.group(2)))
        if c['tipo']=='g':
            for f in ('A','B'):
                m=_re.search(r'— Feto %s —\nPFE: (\d+) g \(([^)]*)\)'%f,ld)
                if m:
                    chip=_re.search(r'%s\s*(\d+) g'%f,r['est'].replace('\n',' '))
                    ok(bool(chip) and chip.group(1)==m.group(1),('gemelar: chip × laudo',i,f))
                    mc=_re.search(r'Feto %s: PFE (\d+) g'%f,r['conc'])
                    if mc: ok(mc.group(1)==m.group(1),('gemelar: conclusão × laudo',i,f))
    pg.set_viewport_size({'width':1024,'height':850})
    grupo('37 Sentinela: texto proibido e coerência cartão × faixa × laudo (150 exames)',C[0],F)

# ------------------------------------------------------------------ 38 ida e volta do estado
def g_idavolta(pg):
    """100 exames aleatórios (com cm/mm, título escolhido à mão, gemelar com o feto B na tela): salvar → Limpar →
    recuperar devolve laudo, conclusão, avisos, faixa, título e estado (ST) idênticos."""
    F=[]; C=[0]
    def ok(c,m):
        C[0]+=1
        if not c: F.append(m)
    SNAP=r"""()=>{var st={}; Object.keys(ST).forEach(function(k){ try{ st[k]=JSON.stringify(ST[k],function(kk,vv){return kk==='plac'?undefined:vv;}); }catch(_){ st[k]='?'; } });
      return {ld:$('ldT').textContent, conc:$('ldConc').textContent, chk:[].map.call(document.querySelectorAll('#chk .chk-ln'),function(l){return l.textContent}).join('|'),
        st:st, est:$('estBar').textContent, tit:TITULO_MAN, ctx:CTX};}"""
    rnd=random.Random(38)
    for i,c in enumerate(_gera(38,100)):
        un=rnd.choice(['cm','cm','mm']); pg.evaluate("(u)=>{setUnidade(u);}",un); pg.evaluate(_ARMA,c)
        if c['tipo']!='t' and rnd.random()<.3: pg.evaluate("(t)=>{TITULO_MAN=t;run();}",rnd.choice(['obst','morfo']))
        if c['tipo']=='g' and rnd.random()<.5: pg.evaluate("()=>{trocaFeto('B');}")
        a=pg.evaluate(SNAP)
        pg.evaluate("()=>{var o=coletaEstado(); $('bRst').click(); if(o) aplicaEstado(o); run();}")
        z=pg.evaluate(SNAP)
        for k in ('ld','conc','chk','est','tit','ctx'): ok(a[k]==z[k],('ida e volta',i,c['tipo'],un,k,str(a[k])[:80],str(z[k])[:80]))
        ok(a['st']==z['st'],('ida e volta: estado',i,c['tipo'],un,[k for k in set(a['st'])|set(z['st']) if a['st'].get(k)!=z['st'].get(k)][:3]))
    pg.evaluate("()=>{setUnidade('cm');}")
    grupo('38 Sentinela: salvar → Limpar → recuperar = mesmo laudo (100 exames)',C[0],F)

# ------------------------------------------------------------------ 39 lógica clínica monotônica
def g_monot(pg):
    """Varre 18 campos em passos finos, em várias IGs: a gravidade do cartão (ok < limítrofe < alterado) só piora no
    sentido clínico certo — 'sobe' (valor maior nunca melhora), 'desce' (menor nunca melhora), 'vale' (os dois
    extremos pioram). Abaixo da faixa de plausibilidade o cartão mostra a trava de conferência, não classificação:
    o início da varredura de AU e ACM fica acima dela."""
    F=[]; C=[0]
    def ok(c,m):
        C[0]+=1
        if not c: F.append(m)
    CAMPOS=[('auip','auRes',(0.35,3.0,0.01),'sobe',(22,30,38),'A'),('acmip','acmRes',(0.55,3.5,0.01),'vale',(22,30,38),'A'),
     ('psv','psvRes',(10,100,0.5),'vale',(20,28,36),'A'),('dvip','dvipRes',(0.20,1.6,0.01),'sobe',(22,30),'A'),
     ('mbv','mbvRes',(0.3,14,0.05),'vale',(24,38),'A'),('ila','ilaRes',(1,40,0.1),'vale',(24,38),'A'),
     ('eAtr','eAtrRes',(0.3,2.2,0.01),'sobe',(20,34),'A'),('eCis','eCisRes',(0.1,1.6,0.01),'vale',(20,26),'A'),
     ('ePrg','ePrgRes',(0.2,1.0,0.01),'sobe',(18,22),'A'),('eColo','eColoRes',(0.5,5.5,0.01),'desce',(18,23),'A'),
     ('bCA','bCARes',(8,40,0.05),'vale',(22,36),'A'),('eCer','eCerRes',(1.0,6.0,0.02),'vale',(20,34),'A'),
     ('eDio','eDioRes',(0.6,2.6,0.01),'vale',(22,30),'A'),('eDbo','eDboRes',(2,7,0.02),'vale',(22,30),'A'),
     ('ePel','ePelRes',(0.1,2.0,0.01),'sobe',(20,30),'A'),('ePla','ePlaRes',(1,7,0.02),'vale',(24,32),'A'),
     ('fcf2','fcf2Res',(80,200,1),'vale',(24,32),'A'),('rTN','rTNRes',(0.05,0.8,0.005),'sobe',(12,13),'B')]
    SEV={'ok':0,'wr':1,'bad':2}
    for campo,res,(lo,hi,st),forma,igs,ctx in CAMPOS:
        for ig in igs:
            vals=[round(lo+k*st,4) for k in range(int(round((hi-lo)/st))+1)]
            r=pg.evaluate("""([campo,res,ig,vals,ctx])=>{ $('bRst').click(); $('sem').value=ig; $('dias').value=(ctx==='B'?2:0); IGSRC='mao';
                 if(ctx==='B'){ $('rCCN').value='6.20'; } else { setModo('bio'); }
                 if(campo==='psv'){ $('lnkPsv').click(); } if(campo==='fcf2'){ var l=$('lnkFcf2'); if(l.offsetParent) l.click(); }
                 run(); var out=[];
                 vals.forEach(function(v){ $(campo).value=String(v); run(); var e=$(res); var c=e?e.className:''; var m=c.match(/\\b(ok|wr|bad|nt)\\b/);
                   out.push([v, m?m[1]:'']); });
                 return out;}""",[campo,res,ig,vals,ctx])
            seq=[(v,SEV[c]) for v,c in r if c in SEV]
            ok(len(seq)>0,(campo,ig,'nenhum valor classificado'))
            if not seq: continue
            s=[x[1] for x in seq]; ruim=None
            if forma=='sobe': ruim=next(((seq[k-1],seq[k]) for k in range(1,len(s)) if s[k]<s[k-1]),None)
            elif forma=='desce': ruim=next(((seq[k-1],seq[k]) for k in range(1,len(s)) if s[k]>s[k-1]),None)
            else:
                m=min(s); i0=s.index(m); i1=len(s)-1-s[::-1].index(m)
                ruim=next((('lado baixo',seq[k-1],seq[k]) for k in range(1,i0+1) if s[k]>s[k-1]),None) or \
                     next((('lado alto',seq[k-1],seq[k]) for k in range(i1+1,len(s)) if s[k]<s[k-1]),None) or \
                     (('piora no meio',) if any(x!=m for x in s[i0:i1+1]) else None)
            ok(ruim is None,('monotonicidade',campo,'IG',ig,forma,ruim))
    grupo('39 Sentinela: gravidade só piora no sentido clínico certo (18 campos)',C[0],F)

# ------------------------------------------------------------------ 40 toques aleatórios com invariantes
def g_toques(pg):
    """220 toques aleatórios (botões, abas, painéis, quadradinhos, listas, campos) em largura sorteada, com trocas de
    IG no meio. A cada 7: biometria na Morfologia ⇔ aba Morfologia aberta; sem elemento duplicado; laudo sem "Erro de
    cálculo"; abas coerentes com o trimestre; sem rolagem lateral; sem texto proibido; IG da faixa = IG digitada."""
    F=[]; C=[0]
    def ok(c,m):
        C[0]+=1
        if not c: F.append(m)
    rnd=random.Random(40 if _eng(pg)=='chromium' else 41)
    pg.set_viewport_size({'width':rnd.choice([320,375,390,430]),'height':800})
    INV=r"""()=>{var on=document.querySelector('.tab.on'); var p=on?on.dataset.p:null; var g=getGA();
      var t=[].map.call(document.querySelectorAll('.pane'),function(x){return x.textContent}).join(' ')+$('estBar').textContent; var m=t.match(/NaN|undefined|\[object|Infinity/);
      return {p:p, bm:!!BIO_MORFO, pane:$('bDBP').closest('.pane').id, n:document.querySelectorAll('#bDBP').length+document.querySelectorAll('#pCalc').length,
        err:/Erro de cálculo/.test($('ldT').textContent), ctx:CTX, sw:document.documentElement.scrollWidth, w:innerWidth,
        vis:[].filter.call(document.querySelectorAll('.tab'),function(t){return !t.hidden}).map(function(t){return t.dataset.p}).join(','),
        proib:m?t.slice(Math.max(0,m.index-50),m.index+20):null,
        ig:(g===null ? $('estIG').textContent==='IG não definida' : $('estIG').textContent.indexOf('IG '+sdT(g))===0)};}"""
    ALVOS="""()=>{var r=[]; document.querySelectorAll('button, summary, .tab, label.chk-l, select, input.num, .chipF, .viaUtBtn, .viaViabBtn').forEach(function(e,i){
       if(!e.offsetParent && getComputedStyle(e).position!=='fixed') return; var c=e.getBoundingClientRect(); if(c.width<2||c.height<2) return;
       if(e.id==='bCpy'||e.id==='bCpyC') return; e.setAttribute('data-mk',i); r.push({i:i, tag:e.tagName}); }); return r;}"""
    for k in range(220):
        al=pg.evaluate(ALVOS)
        if al:
            a=rnd.choice(al); sel='[data-mk="%d"]'%a['i']
            try:
                if a['tag']=='SELECT':
                    opts=pg.evaluate("(s)=>[].map.call(document.querySelector(s).options,function(o){return o.value})",sel)
                    pg.locator(sel).select_option(rnd.choice(opts),timeout=600)
                elif a['tag']=='INPUT':
                    pg.locator(sel).click(timeout=600)
                    pg.keyboard.type(rnd.choice(['8.1','29.5','26.40','6','0.95','1.9','12','4.2','0.3','45','2.10','5.6','30']),delay=5)
                    pg.keyboard.press(rnd.choice(['Tab','Enter','Backspace']))
                else: pg.locator(sel).click(timeout=600)
            except Exception: pass
        if k%60==59: pg.evaluate("(s)=>{$('sem').value=s;$('dias').value=0;$('sem').dispatchEvent(new Event('input',{bubbles:true}));}",rnd.choice([9,12,14,22,28,33,38,'']))
        if k%7==0 or k==219:
            pg.evaluate("()=>{[].forEach.call(document.querySelectorAll('.teo'),function(o){var x=o.querySelector('.teo-x'); if(getComputedStyle(o).display!=='none'&&x) x.click();});}")
            r=pg.evaluate(INV)
            ok(r['bm']==(r['p']=='p6') and r['pane']==('p6' if r['p']=='p6' else 'p1'),('biometria fora do lugar',k,r))
            ok(r['n']==2,('elemento duplicado',k,r['n']))
            ok(not r['err'],('erro de cálculo no laudo',k))
            ok(r['vis']==('p0,p1,p6,p2,p3' if r['ctx']=='A' else 'p0,p4,p5,p3'),('abas incoerentes',k,r['vis'],r['ctx']))
            ok(r['sw']<=r['w'],('rolagem lateral',k,r['sw'],r['w']))
            ok(not r['proib'],('texto proibido',k,r['proib']))
            ok(r['ig'],('IG da faixa',k))
    pg.set_viewport_size({'width':1024,'height':850})
    grupo('40 Sentinela: 220 toques aleatórios com invariantes',C[0],F)

# ================================================================== PORTÃO DE PUBLICAÇÃO: comparar com a versão no ar
def _gera_cmp(seed,N):
    """exames para o diferencial: feto único com todos os blocos do laudo (biometria, líquido, Doppler fetal e
    materno, incisura, via, PSV, neuro, praxe, colo, 1º tri, ducto, velocidade de crescimento) + 20% gemelar"""
    rnd=random.Random(seed); out=[]
    def U(a,b,c=2): return round(rnd.uniform(a,b),c)
    gem=[x for x in _gera(seed+1,8*N+20) if x['tipo']=='g']
    for _ in range(N):
        if rnd.random()<0.2:
            out.append(gem.pop()); continue
        c={'tipo':'u','sem':rnd.randint(11,41),'dias':rnd.randint(0,6)}; g=c['sem']
        if g>=14:
            c.update(bDBP=U(2,10.5),bCC=U(8,37),bCA=U(7,42),bFL=U(1,8.2))
            if rnd.random()<.3: c.update(bDBP='')
        if rnd.random()<.8: c['mbv']=U(0.5,12,1)
        if rnd.random()<.4: c['ila']=U(2,30,1)
        if g>=14 and rnd.random()<.85: c.update(auip=U(0.4,2.2),acmip=U(0.7,2.8))
        c['diast']=rnd.choice(['na','pres','pres','pres','zero','rev'])
        if rnd.random()<.7: c.update(utD=U(0.3,2.6),utE=U(0.3,2.6))
        c['incD']=rnd.choice(['na','pres']); c['incE']=rnd.choice(['na','pres']); c['via']=rnd.choice(['ta','ta','tv',None])
        if rnd.random()<.3: c['psv']=U(15,95,1)
        if rnd.random()<.3: c.update(eCer=U(1,6),eAtr=U(0.3,1.5))
        if g>=14 and rnd.random()<.3: c['eUme']=U(1,7)
        if rnd.random()<.25: c['eColo']=U(0.8,5)
        if g<14 or rnd.random()<.15: c.update(rCCN=U(3,8.5),rTN=U(0.08,0.6))
        if rnd.random()<.2: c['dvip']=U(0.3,1.6)
        if g>=24 and rnd.random()<.5: c.update(vPeso=rnd.randint(300,3800),vDiasAtras=rnd.choice([14,20,21,28,35]))
        out.append(c)
    return out
_JS_CMP=r"""(c)=>{ $('bRst').click(); var set=function(i,v){var e=$(i); if(e&&v!==undefined&&v!==null) e.value=v;};
  $('sem').value=c.sem; $('dias').value=c.dias; IGSRC='mao'; try{setModo('bio');}catch(_){}
  if(c.tipo==='g'){ $('gemelar').checked=true; $('corion').value=c.cor; run();
     Object.keys(c.A).forEach(function(k){set(k,c.A[k]);}); run(); trocaFeto('B'); Object.keys(c.B).forEach(function(k){set(k,c.B[k]);}); run(); trocaFeto('A'); }
  else {
    if(c.psv!==undefined){ $('lnkPsv').click(); }
    ['bDBP','bCC','bCA','bFL','mbv','ila','auip','acmip','diast','utD','utE','incD','incE','psv','eCer','eAtr','eUme','eColo','rCCN','rTN','dvip'].forEach(function(k){set(k,c[k]);});
    VIA_UT=c.via; if(c.via) VIA_UT_PADRAO=false; try{renderViaUt();}catch(_){}
    try{pintaInc();}catch(_){}
    if(c.vPeso){ $('dtHojeD').value='11';$('dtHojeM').value='10';$('dtHojeY').value='2026'; var d=new Date(2026,9,11-c.vDiasAtras);
      $('vPeso').value=String(c.vPeso);$('vD').value=String(d.getDate());$('vM').value=String(d.getMonth()+1);$('vY').value=String(d.getFullYear());
      ['dtHojeD','vPeso','vD','vM','vY'].forEach(function(i){$(i).dispatchEvent(new Event('input',{bubbles:true}));}); }
  }
  run();
  var st={}; try{ Object.keys(ST).forEach(function(k){ try{ st[k]=JSON.stringify(ST[k],function(kk,vv){return kk==='plac'?undefined:vv;}); }catch(_){ st[k]='?'; } }); }catch(_){}
  var chk=[].map.call(document.querySelectorAll('#chk .chk-ln'),function(l){
     var d=l.querySelector('.pqD'); if(!d) return l.textContent;
     var r=''; for(var n=l.firstChild;n&&!(n.classList&&n.classList.contains('pqT'));n=n.nextSibling) r+=n.textContent; return r+' ¶ '+d.textContent;}).join(' | ');
  return {ld:$('ldT').textContent, conc:$('ldConc').textContent, chk:chk, st:st, est:$('estBar')?$('estBar').innerText:''};}"""
def compara(alvo,ref,webkit,N):
    """Diferencial de publicação: os mesmos N exames aleatórios na versão NO AR (ref) e na NOVA (alvo); compara laudo,
    conclusão, avisos do Confira, faixa do topo e estado interno (ST). Diferença não é necessariamente erro — mas
    TODA diferença precisa ser uma mudança DECLARADA da versão nova. As diferenças saem agrupadas por item."""
    casos=_gera_cmp(2026,N); R=[]; ER=[]
    for arq in (ref,alvo):
        srv,url=servir(arq); out=[]; er=[]
        with sync_playwright() as p:
            b=(p.webkit if webkit else p.chromium).launch(); pg=b.new_page(viewport={'width':390,'height':844})
            pg.on('dialog',lambda d:d.accept()); pg.on('pageerror',lambda e:er.append(str(e)[:120]))
            pg.goto(url); pg.wait_for_timeout(600)
            for c in casos: out.append(pg.evaluate(_JS_CMP,c))
            b.close()
        srv.shutdown(); R.append(out); ER.append(er)
    nv=lambda t:' '.join(str(t).replace('›','').split())
    G={}
    for i,(a,z) in enumerate(zip(*R)):
        if a['ld']!=z['ld'] and a['ld'].split('\n',1)[1:]==z['ld'].split('\n',1)[1:]:   # só a 1ª linha (título e IG)
            G.setdefault('laudo: só o título (1ª linha)',[]).append((i,casos[i]['tipo'],a['ld'].split('\n')[0][:90],z['ld'].split('\n')[0][:90])); a=dict(a,ld=z['ld'])
        for k,nome in (('ld','laudo (além do título)'),('conc','conclusão'),('chk','avisos do Confira'),('est','faixa do topo')):
            if nv(a[k])!=nv(z[k]):
                la,lz=nv(a[k]),nv(z[k]); j=next((x for x in range(min(len(la),len(lz))) if la[x]!=lz[x]),min(len(la),len(lz)))
                G.setdefault(nome,[]).append((i,casos[i]['tipo'],la[max(0,j-40):j+70],lz[max(0,j-40):j+70]))
        for k in sorted(set(a['st'])|set(z['st'])):
            if a['st'].get(k)!=z['st'].get(k): G.setdefault('estado ST.'+k,[]).append((i,casos[i]['tipo']))
    if ER[1]: G['erros de JavaScript na versão nova']=[tuple(ER[1][:3])]
    nd=sum(len(v) for v in G.values())
    print('\nComparação com a versão no ar (%s) [%s]: %d exames (%d gemelares) → %s'%(os.path.basename(ref),'WebKit' if webkit else 'Chromium',N,
          sum(1 for c in casos if c['tipo']=='g'),'IGUAIS' if not nd else '%d diferença(s)'%nd))
    for nome,v in G.items():
        print('  ≠ %-36s %d exame(s)'%(nome,len(v)))
        for x in v[:2]: print('       ex.:',json.dumps(x,ensure_ascii=False)[:260])
    if nd: print('  Cada item acima precisa ser uma mudança DECLARADA da versão nova (CONTEXTO.md). Se não for, é regressão: não publique.')
    return nd

# ------------------------------------------------------------------ principal
def roda(alvo,webkit):
    RES.clear(); srv,url=servir(alvo)
    print('\nSuíte de regressão — %s  [%s]\n'%(os.path.basename(alvo),'WebKit' if webkit else 'Chromium'))
    with sync_playwright() as p:
        b=(p.webkit if webkit else p.chromium).launch()
        for g in (g_integridade,g_ca,g_ossos_dio,g_gemelar_ca,g_r27,g_r28,g_phi,g_data,g_rotulo,g_r33,g_r34,g_r35,g_via,g_lado,g_inc,g_r37,g_r38,g_r39,g_r41,g_r42,g_r44,g_r45,g_r46,g_r47,g_r48,g_r49,g_r50,g_r51,g_r52,g_r53,g_r54,g_r55,g_r56,g_r15,g_r152,g_digita,g_coerencia,g_idavolta,g_monot,g_toques):
            pg=b.new_page(viewport={'width':1024,'height':850}); erros=[]
            pg.on('dialog',lambda d:d.accept()); pg.on('pageerror',lambda e:erros.append(str(e)[:120]))
            pg.goto(url); pg.wait_for_timeout(500)
            try:
                g(pg,erros) if g is g_integridade else g(pg)
            except Exception as e:
                grupo('%s — ABORTOU'%g.__name__,1,[('exceção',str(e).splitlines()[0][:200])])
            if erros and g is not g_integridade: RES.setdefault('erros de JavaScript',{'checks':0,'falhas':[]})['falhas'].append((g.__name__,erros[:2]))
            pg.close()
        b.close()
    srv.shutdown(); tot=0; falhas=0
    for nome,r in RES.items():
        ok=not r['falhas']; tot+=r['checks']; falhas+=len(r['falhas'])
        print('  %s %-62s %d checagens%s'%('OK' if ok else '!!',nome,r['checks'],'' if ok else '  →  %d falha(s)'%len(r['falhas'])))
        for x in r['falhas'][:6]: print('       FALHOU:',json.dumps(x,ensure_ascii=False)[:220])
    print('\n  %d checagens · %d falha(s)'%(tot,falhas))
    return falhas

def main():
    av=sys.argv[1:]; ref=None; N=300
    if '--comparar' in av:
        i=av.index('--comparar')
        if i+1>=len(av): sys.exit('Use: --comparar <index.html da versão no ar>')
        ref=av[i+1]; del av[i:i+2]
        if not os.path.exists(ref): sys.exit('Arquivo de referência não encontrado: '+ref)
    if '--n' in av:
        i=av.index('--n'); N=int(av[i+1]); del av[i:i+2]
    args=[a for a in av if not a.startswith('--')]
    alvo=args[0] if args else 'index.html'
    if not os.path.exists(alvo): sys.exit('Arquivo não encontrado: '+alvo)
    motores=[False,True] if '--ambos' in av else ([True] if '--webkit' in av else [False])
    falhas=0 if '--so-comparar' in av else sum(roda(alvo,w) for w in motores)
    if falhas: print('\n  ATENÇÃO: antes de alterar o app, confirme se a expectativa do teste não é que está errada (CONTEXTO.md).')
    difs=sum(compara(alvo,ref,w,N) for w in motores) if ref else 0
    if ref or '--ambos' in av:
        ok=not falhas and not difs; so='--so-comparar' in av
        if ok and so: print('\n  PORTÃO DE PUBLICAÇÃO: diferencial IGUAL à versão no ar · a suíte NÃO foi rodada (tire --so-comparar)')
        elif ok and '--ambos' not in av: print('\n  PORTÃO DE PUBLICAÇÃO: incompleto — rode com --ambos (Chromium e WebKit)')
        else: print('\n  PORTÃO DE PUBLICAÇÃO: %s'%('suíte OK nos dois motores%s'%(' · diferencial IGUAL à versão no ar' if ref else ' · diferencial não rodado (use --comparar)') if ok
              else ('%d falha(s) na suíte'%falhas if falhas else '')+(' · ' if falhas and difs else '')+('%d diferença(s) a conferir no diferencial'%difs if difs else '')))
        if ok and ref and not so and '--ambos' in av: print('  Pode subir. Depois, antes do primeiro paciente: checklist de 5 minutos no iPhone (README.md, "Antes de publicar").')
    sys.exit(1 if falhas else (2 if difs else 0))

if __name__=='__main__': main()
