#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SUÍTE DE REGRESSÃO — Calculadora Doppler Obstétrico (linha R14; validada na R14.35)
===================================================================================
Um arquivo só com os testes que validaram as versões R14.24 a R14.35. Cada grupo protege
um defeito REAL que já existiu; nenhum grupo injeta classificação pronta em ST.

COMO USAR
    pip install playwright --break-system-packages
    playwright install chromium webkit
    python3 suite_regressao_doppler.py [index.html] [--webkit | --ambos]

Sem argumento, usa "index.html" no diretório atual. --webkit roda no motor do Safari;
--ambos roda Chromium e depois WebKit. A suíte sobe um servidor HTTP local próprio (porta
livre) só para servir esse arquivo. Saída silenciosa: placar por grupo e detalhe só das
falhas. Código de saída != 0 se algo falhar. Tempo: ~4 min por navegador.

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

NÃO COBRE (ver CONTEXTO.md e o pacote de testes de cada versão): tabelas-verdade de 104 casos,
Clinical Truth v3.1, varredura de 28.080 combinações, consumidores/razões/uterinas/TN das
R14.25–R14.26, worker (sw.js), iPhone/Safari físico, uso offline real, validação clínica.
"""
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
      return {ver:(typeof APP_VERSAO!=='undefined')?APP_VERSAO:null,dup:d.slice(0,5),fn:['run','cmpMedida','phiPreciso','pctPesoFromZ','discCat','discFmt','fetoOutro','seletiva','discordancia','rotP','rotPfeQ','setDataExameISO','dtHojeSync','casasPar','fxVal','fxCorte','momTxt','achadosTxt'].filter(function(k){return typeof window[k]!=='function'})};}""")
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
            crit=any('CA de um dos fetos' in t for t in o['criteria'])
            if o['other']!=below: f.append(('fetoOutro','%d+%d'%(w,d),inp))
            if crit!=below: f.append(('seletiva','%d+%d'%(w,d),inp))
    grupo('4 Gemelar — CA do outro feto e sFGR',n,f)

# ------------------------------------------------------------------ helpers de interface (gemelar)
SNAP="()=>({feto:FETO,pfe:ST.pfe,sfgr:ST.sfgr,disc:ST.disc,o:(function(){var o=fetoOutro();return o?{w:o.w,q:o.q}:null})(),rep:$('ldT').textContent})"
def gem(pg,ig,dias,corion,curva,wA,wB):
    pg.locator('#bRst').click(); pg.locator('#origDireto').click(); pg.locator('#sem').fill(str(ig)); pg.locator('#dias').fill(str(dias))
    pg.evaluate("c=>{CURVA=c;}",curva); pg.locator('#mDir').click(); pg.locator('#pDir').fill(str(wA)); pg.locator('#gemelar').check()
    pg.locator('#corion').select_option(corion); pg.locator('#fB').click(); pg.locator('#pDir').fill(str(wB)); pg.locator('#pDir').blur()
    sB=pg.evaluate(SNAP); pg.locator('#fA').click(); sA=pg.evaluate(SNAP); return sA,sB
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
        pg.locator('#bRst').click(); pg.locator('#origDireto').click(); pg.locator('#sem').fill(str(w)); pg.locator('#dias').fill(str(d)); pg.locator('#mBio').click()
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
            pg.locator('#bRst').click(); pg.locator('#origDireto').click(); pg.locator('#sem').fill(sem); pg.locator('#dias').fill('0'); pg.locator('#mDir').click(); pg.locator('#pDir').fill('1800'); setdiast(pg,di)
            o=pg.evaluate("()=>({ga:getGA(),cls:ST.sint?ST.sint.cls:null,txt:document.body.innerText,card:$('sintRes').textContent.toLowerCase()})"); n+=1
            if o['ga'] is not None: continue
            if o['cls']!='aedf-ig-desconhecida' or 'informe a IG' not in o['txt'] or 'partir de 32' in o['card'] or 'forma precoce' in o['card']: f.append(('IG desconhecida',repr(sem),di,o['cls']))
            if ('Diástole '+('reversa' if di=='rev' else 'ausente')+' na umbilical') not in o['txt']: f.append(('achado de gravidade sumiu',repr(sem),di))
    for di in ('zero','rev'):
        pg.locator('#bRst').click(); pg.locator('#origDireto').click(); pg.locator('#sem').fill('34'); pg.locator('#dias').fill('0'); pg.locator('#mDir').click(); setdiast(pg,di)
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
            pg.locator('#bRst').click(); pg.locator('#origDireto').click(); pg.locator('#sem').fill('30'); pg.locator('#dias').fill('0'); pg.locator('#mBio').click()
            for i,v in zip(('bDBP','bCC','bCA','bFL'),A): pg.locator('#'+i).fill(v); pg.locator('#'+i).blur()
            pg.locator('#gemelar').check(); pg.locator('#corion').select_option('dc'); pg.locator('#fB').click(); pg.locator('#mBio').click()
            for i,v in zip(('bDBP','bCC','bCA','bFL'),B): pg.locator('#'+i).fill(v); pg.locator('#'+i).blur()
            pg.locator('#f'+ori).click(); o=pg.evaluate(GET); res[ori]=o; n+=1
            if show not in o['card'] or catx not in o['card']: f.append(('cartão',nome,ori,o['card'][:80]))
            L=linhas(o['rep']); gx='Discordância de peso entre os fetos: '+show+'.'
            if (cc==0 and L!=[gx]) or (cc==1 and (gx not in L or len(L)!=2)): f.append(('corpo/guia',nome,ori,L))
        if res['A']['card']!=res['B']['card'] or linhas(res['A']['rep'])!=linhas(res['B']['rep']): f.append(('assimetria A/B',nome))
    for a,bw in ((2000,1601),(2000,1600),(2000,1599),(2000,1501),(2000,1500),(2000,1499),(1280,960),(2000,1700),(1000,801),(1000,800),(1000,751),(1000,750),(5000,'4000.0001'),(5000,'3750.0001')):
        pg.locator('#bRst').click(); pg.locator('#origDireto').click(); pg.locator('#sem').fill('30'); pg.locator('#dias').fill('0'); pg.locator('#mDir').click(); pg.locator('#pDir').fill(str(a)); pg.locator('#gemelar').check(); pg.locator('#corion').select_option('dc')
        pg.locator('#fB').click(); pg.locator('#pDir').fill(str(bw)); pg.locator('#pDir').blur(); res={}
        for ori in ('A','B'):
            pg.locator('#f'+ori).click(); res[ori]=pg.evaluate(GET); n+=1
        v=(float(a)-float(bw))/float(a)*100; ex=disc_oraculo(v); o=res['A']; gx='Discordância de peso entre os fetos: '+ex+'.'; L=linhas(o['rep'])
        if ex not in o['card']: f.append(('cartão',a,bw,ex,o['card'][:70]))
        if discat(v)>=1 and gx not in L: f.append(('guia',a,bw,ex,L))
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
    ok('com achado(s) morfológico(s): ventriculomegalia e achado materno: colo curto' in r[2],(nm,'conclusão mista',r[2][-260:]))
    grupo('12 Valor × corte exibidos; colo materno (R14.35)',C[0],F)

# ------------------------------------------------------------------ principal
def roda(alvo,webkit):
    RES.clear(); srv,url=servir(alvo)
    print('\nSuíte de regressão — %s  [%s]\n'%(os.path.basename(alvo),'WebKit' if webkit else 'Chromium'))
    with sync_playwright() as p:
        b=(p.webkit if webkit else p.chromium).launch()
        for g in (g_integridade,g_ca,g_ossos_dio,g_gemelar_ca,g_r27,g_r28,g_phi,g_data,g_rotulo,g_r33,g_r34,g_r35):
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
    args=[a for a in sys.argv[1:] if not a.startswith('--')]
    alvo=args[0] if args else 'index.html'
    if not os.path.exists(alvo): sys.exit('Arquivo não encontrado: '+alvo)
    motores=[False,True] if '--ambos' in sys.argv else ([True] if '--webkit' in sys.argv else [False])
    falhas=sum(roda(alvo,w) for w in motores)
    if falhas: print('\n  ATENÇÃO: antes de alterar o app, confirme se a expectativa do teste não é que está errada (CONTEXTO.md).')
    sys.exit(1 if falhas else 0)

if __name__=='__main__': main()
