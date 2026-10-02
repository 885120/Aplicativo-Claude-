#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SUÍTE DE REGRESSÃO — Calculadora Doppler Obstétrico (linha R14; validada na R14.28)
===================================================================================
Consolida, num arquivo só, os testes que validaram as versões R14.24 a R14.28. Cada grupo
protege um defeito REAL que já existiu; nenhum grupo injeta classificação pronta em ST.

COMO USAR
    pip install playwright --break-system-packages
    playwright install chromium            (opcional: playwright install webkit)
    python3 suite_regressao_doppler.py [index.html] [--webkit]

Sem argumento, usa "index.html" no diretório atual. A suíte sobe um servidor HTTP local
próprio (porta livre) só para servir esse arquivo. Saída silenciosa: imprime o placar por
grupo e detalha só as falhas. Código de saída != 0 se algo falhar.

ANTES DE "CONSERTAR" O APP POR CAUSA DE UMA FALHA AQUI
Confirme que a expectativa do teste não é que está desatualizada. Isso já aconteceu
várias vezes (ver CONTEXTO.md). As expectativas usam oráculos independentes do motor:
frações exatas, Decimal e erfc da biblioteca matemática do Python.

GRUPOS
  1 Integridade            HTML carrega, sem erro de JS, IDs únicos, funções-chave presentes
  2 CA — fronteiras        p3/p10/p90/p97: 108 em semanas completas + todas as digitáveis por dia (R14.24)
  3 Ossos longos e DIO     p3 dos ossos; p10/p90 da DIO (R14.24)
  4 Gemelar — CA           fetoOutro() e critério sFGR na igualdade do p10 (R14.24)
  5 F01–F05 (R14.27)       gate de PFE do outro feto; Φ preciso no peso; IG ausente + AEDF/REDF;
                           escopo do outro feto; discordância (categoria e texto)
  6 Exibição da discordância (R14.28)  número exibido nunca cruza o corte; fallback <20%/<25%
  7 Φ preciso × erfc       phiPreciso() embarcado contra math.erfc

NÃO COBRE (ver CONTEXTO.md e o pacote de testes de cada versão): tabelas-verdade de 104 casos,
Clinical Truth v3.1, varredura de 28.080 combinações, consumidores/razões/uterinas/TN das
R14.25–R14.26, worker em navegador real, iPhone/Safari físico, validação clínica.
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
      return {ver:(typeof APP_VERSAO!=='undefined')?APP_VERSAO:null,dup:d.slice(0,5),fn:['run','cmpMedida','phiPreciso','pctPesoFromZ','discCat','discFmt','fetoOutro','seletiva','discordancia'].filter(function(k){return typeof window[k]!=='function'})};}""")
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

# ------------------------------------------------------------------ principal
def main():
    args=[a for a in sys.argv[1:] if not a.startswith('--')]; webkit='--webkit' in sys.argv
    alvo=args[0] if args else 'index.html'
    if not os.path.exists(alvo): sys.exit('Arquivo não encontrado: '+alvo)
    srv,url=servir(alvo)
    print('\nSuíte de regressão — %s  [%s]\n'%(os.path.basename(alvo),'WebKit' if webkit else 'Chromium'))
    with sync_playwright() as p:
        b=(p.webkit if webkit else p.chromium).launch()
        for g in (g_integridade,g_ca,g_ossos_dio,g_gemelar_ca,g_r27,g_r28,g_phi):
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
    if falhas: print('\n  ATENÇÃO: antes de alterar o app, confirme se a expectativa do teste não é que está errada (CONTEXTO.md).')
    sys.exit(1 if falhas else 0)

if __name__=='__main__': main()
