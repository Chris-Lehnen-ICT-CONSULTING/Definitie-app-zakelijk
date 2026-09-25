"""Gerichte offline onderzoeksproeven; geen wijziging van applicatiecode."""
import sys, os, json, asyncio, ast, dataclasses, hashlib, platform, traceback
from pathlib import Path
from datetime import datetime, UTC
ROOT=Path.cwd()
OUT=Path(__file__).resolve().parent
sys.dont_write_bytecode=True
geblokkeerd=[]
def bewaker(event,args):
    pad=None
    if event=='open':
        p,mode,flags=args
        if isinstance(p,(str,bytes,os.PathLike)) and ((isinstance(mode,str) and any(x in mode for x in 'wax+')) or (isinstance(flags,int) and flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))): pad=p
    elif event in ('os.mkdir','os.remove','os.rmdir','os.rename'):pad=args[0]
    elif event in ('socket.connect','socket.getaddrinfo'):
        raise PermissionError('Netwerk uitgeschakeld voor offline onderzoek')
    if pad is not None and not Path(os.fsdecode(pad)).resolve().is_relative_to(OUT):
        geblokkeerd.append({'event':event,'pad':os.fsdecode(pad)})
        raise PermissionError('Schrijven buiten eigen bewijsmap geblokkeerd: '+os.fsdecode(pad))
sys.addaudithook(bewaker)
opzet=json.loads((OUT/'proefopzet-v1.json').read_text())
result={'starttijd_utc':datetime.now(UTC).isoformat(),'python':platform.python_version(),'head':'26f2374d302fc66fc0b12ed29dc34585f7c0a5c3','opzet_sha256':hashlib.sha256((OUT/'proefopzet-v1.json').read_bytes()).hexdigest(),'proeven':[]}
def proef(id,functie):
    try: result['proeven'].append({'id':id,'uitgevoerd':True,'uitkomst':functie()})
    except Exception as e: result['proeven'].append({'id':id,'uitgevoerd':False,'fout':repr(e),'traceback':traceback.format_exc()})
record=json.loads((ROOT/'src/toetsregels/regels/INT-02.json').read_text())
def p1():
    from services.validation.evaluators.judgment_review import JudgmentReviewEvaluator
    from services.validation.evaluators.base import EvaluationDeps
    from services.validation.types_internal import EvaluationContext
    from toetsregels.runtime_contract import build_rule_record
    r=build_rule_record('INT-02',record); e=JudgmentReviewEvaluator(); rows=[]
    for c in opzet['gevallen']:
        res=e.evaluate(r,EvaluationContext.from_params(c['text'],begrip=c['term'],metadata=c['context']),EvaluationDeps(None,frozenset()))
        rows.append({'id':c['id'],'uitkomst':dataclasses.asdict(res)})
        assert res.status=='review_required' and res.score is None
    return rows
proef('P1',p1)
def p2():
    from services.prompts.modules.json_based_rules_module import JSONBasedRulesModule
    m=JSONBasedRulesModule('INT','integrity_rules','INT regels','🔒','Integriteit Regels (INT)',70)
    rows=[]
    for examples in (True,False):
        m.initialize({'include_examples':examples})
        text='\n'.join(m._format_rule('INT-02',record))
        assert 'Vermijd voorwaardelijke formuleringen' in text and record['toetsvraag'] not in text
        rows.append({'voorbeelden':examples,'tekst':text})
    return rows
proef('P2',p2)
def p3():
    from services.validation.modular_validation_service import ModularValidationService
    from toetsregels.manager import get_toetsregel_manager
    async def uitvoeren():
        svc=ModularValidationService(get_toetsregel_manager(),None,None); rows=[]
        for c in (opzet['gevallen'][0],opzet['gevallen'][4]):
            r=await svc.validate_definition(begrip=c['term'],text=c['text'],ontologische_categorie=None,context=c['context'])
            rows.append({'id':c['id'],'runstatus':r.get('status'),'rule_status':r.get('rule_statuses',{}).get('INT-02'),'reviews':[x for x in r.get('review_required',[]) if x['rule_id']=='INT-02'],'violations':[x for x in r.get('violations',[]) if x.get('code')=='INT-02'],'overall_score':r.get('overall_score')})
        return rows
    return asyncio.run(uitvoeren())
proef('P3',p3)
def p4():
    from services.cleaning_service import CleaningService,CleaningConfig
    async def uitvoeren():
        svc=CleaningService(CleaningConfig(log_operations=False)); rows=[]
        cases=[('INT02-C100',opzet['gevallen'][0]['term'],'stelselmatige dader: '+opzet['gevallen'][0]['text']),('INT02-C03','aanvraag','Aanvraag die wordt afgewezen indien een bijlage ontbreekt.')]
        for id,term,text in cases:
            r=await svc.clean_text(text,term)
            rows.append({'id':id,'invoer':text,'resultaat':dataclasses.asdict(r)})
            assert 'indien' in r.cleaned_text
        return rows
    return asyncio.run(uitvoeren())
proef('P4',p4)
def bronfunctie(path,naam):
    tree=ast.parse((ROOT/path).read_text()); node=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name==naam)
    node.decorator_list=[]
    return compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),str(ROOT/path),'exec')
def p5():
    ns={'Any':object,'_rule_sort_key':str}
    exec(bronfunctie('src/ui/components/validation_view.py','_statuslijst_regels'),ns)
    res=ns['_statuslijst_regels']({'rule_statuses':{'INT-02':'review_required'},'review_required':[{'rule_id':'INT-02','reason':'TESTREDEN','signals':['indien']}]},uitgesloten=set())
    assert res==['🟠 Nog te beoordelen: INT-02']
    return {'bewijssoort':'uitvoering brongeëxtraheerde statushelper','regels':res}
proef('P5',p5)
def p6():
    from types import SimpleNamespace
    ns={'Any':object,'DefinitieRecord':object}
    exec(bronfunctie('src/services/definition_workflow_service.py','_evaluate_gate'),ns)
    policy=SimpleNamespace(hard_requirements={'min_one_context_required':True,'forbid_critical_issues':True},soft_requirements={'allow_hard_override':False,'missing_wettelijke_basis_soft':True},hard_min_score=.75,soft_min_score=.65)
    self=SimpleNamespace(_get_policy=lambda:policy,_gate_contextlijsten=lambda d:(['synthetisch'],[],['synthetische bron']),_con01_blokkades=lambda d:[],_con02_blokkades=lambda d:[])
    rows=[]
    for score,review in ((.9,[]),(.9,[{'rule_id':'INT-02','status':'review_required'}]),(None,[{'rule_id':'INT-02','status':'review_required'}])):
        d=SimpleNamespace(validation_score=score,get_validation_issues_list=lambda:[],review_required=review)
        rows.append({'score':score,'review_required':review,'gate':ns['_evaluate_gate'](self,d)})
    assert rows[0]['gate']==rows[1]['gate'] and rows[2]['gate']['status']=='blocked'
    return {'bewijssoort':'geïsoleerde gatefunctie; CON-01/02 en recordinterfaces gecontroleerd vervangen','gevallen':rows}
proef('P6',p6)
result['geblokkeerde_schrijfacties']=geblokkeerd
result['eindtijd_utc']=datetime.now(UTC).isoformat()
with (OUT/'proefuitkomsten-v1.json').open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2,default=str)
print(json.dumps(result,ensure_ascii=False,indent=2,default=str))
