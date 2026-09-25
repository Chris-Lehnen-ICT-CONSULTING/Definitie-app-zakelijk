"""Offline INT-02-onderzoek; geen applicatiewijziging."""
import asyncio,sys,os,json,hashlib,subprocess,ast,datetime
from pathlib import Path
OUT=Path(__file__).resolve().parent
ROOT=Path('/Users/chrislehnen/Projecten/Definitie-app')
sys.dont_write_bytecode=True
# Extra begrenzing naast sandbox: geen netwerk of schrijfacties buiten bewijs/.
def guard(event,args):
    if event in ('socket.connect','socket.connect_ex','socket.getaddrinfo'):
        raise PermissionError('Onderzoeksproef staat geen netwerk toe')
    if event=='open':
        p,mode,flags=args
        writing=(isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and bool(flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)))
        if writing and isinstance(p,(str,bytes)) and not Path(os.fsdecode(p)).resolve().is_relative_to(OUT):
            raise PermissionError('Schrijven buiten onderzoeksbewijs niet toegestaan: '+os.fsdecode(p))
sys.addaudithook(guard)
from services.validation.modular_validation_service import ModularValidationService
from toetsregels.manager import get_toetsregel_manager
from services.prompts.modules.json_based_rules_module import JSONBasedRulesModule
from services.cleaning_service import CleaningService,CleaningConfig
cases=[
 ('INT02-C50','stelselmatige dader','Persoon die als stelselmatige dader geldt indien hij in de vijf jaar voorafgaand aan het laatste feit drie maal wegens een misdrijf onherroepelijk is veroordeeld.',{'organisatorische_context':['Synthetisch ASTRA-model']},[r'\bindien\b']),
 ('INT02-C51','weigering','De bevoegde autoriteit weigert het document, tenzij hij van oordeel is dat de aanvrager onevenredig wordt benadeeld.',{'organisatorische_context':['Synthetisch ASTRA-model']},[r'\btenzij\b']),
 ('INT02-C52','aanvraag','Aanvraag die de behandelaar moet afwijzen bij een ontbrekende bijlage.',{'organisatorische_context':['Synthetisch loket']},[]),
 ('INT02-C53','vernietiging','Rechtshandeling waardoor de rechtsgevolgen van een eerdere rechtshandeling vervallen.',{'organisatorische_context':['Synthetisch begrippenmodel']},[]),
 ('INT02-C54','stemgerechtigd lid','Lid dat stemgerechtigd is alleen als het vóór 1 januari is ingeschreven.',{'organisatorische_context':['Fictieve vereniging']},[r'\balleen als\b']),
 ('INT02-C55','beschadigd voorwerp','Voorwerp met een waarneembare onderbreking van het oppervlak.',{'organisatorische_context':['Fictieve inspectie']},[]),
 ('INT02-C56','stelselmatige dader','Persoon die als stelselmatige dader geldt indien hij in de vijf jaar voorafgaand aan het laatste feit drie maal wegens een misdrijf onherroepelijk is veroordeeld.',{},[r'\bindien\b'])]
async def main():
    result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'python':sys.version,'offline':True,'stubs':[],'proof_type':'offline service/formatter/cleaning + source binding','cases':[]}
    svc=ModularValidationService(get_toetsregel_manager(),None,None)
    for cid,term,txt,ctx,sigs in cases:
        r=await svc.validate_definition(begrip=term,text=txt,ontologische_categorie=None,context=ctx)
        item=next((x for x in r.get('review_required',[]) if x['rule_id']=='INT-02'),None)
        rr={'id':cid,'input':{'term':term,'text':txt,'context':ctx},'expected':{'status':'review_required','signals':sigs},'actual':{'status':r.get('rule_statuses',{}).get('INT-02'),'review':item,'passed':'INT-02' in r.get('passed_rules',[]),'violations':[v for v in r.get('violations',[]) if v.get('code')=='INT-02'],'rule_result':r.get('rule_results',{}).get('INT-02'),'run_status':r.get('validation_status')}}
        rr['expectation_met']=rr['actual']['status']=='review_required' and item is not None and item['signals']==sigs and not rr['actual']['passed'] and not rr['actual']['violations']
        result['cases'].append(rr)
    record=json.loads((ROOT/'src/toetsregels/regels/INT-02.json').read_text())
    module=JSONBasedRulesModule('INT','integrity_rules','Integrity Validation Rules (INT)','🔒','Integriteit Regels (INT)',70)
    result['prompt']={}
    for examples in (True,False):
        module.initialize({'include_examples':examples})
        result['prompt'][str(examples)]='\n'.join(module._format_rule('INT-02',record))
    cleaning=CleaningService(CleaningConfig(log_operations=False))
    result['cleaning']=[]
    for index in (0,2):
        cid,term,txt,_,_=cases[index]
        raw='Ontologische categorie: type\n'+term+': '+txt.rstrip('.')
        r=await cleaning.clean_text(raw,term)
        result['cleaning'].append({'id':cid,'raw':raw,'cleaned':r.cleaned_text,'applied_rules':r.applied_rules,'metadata':r.metadata,'expected_content':txt,'expectation_met':r.cleaned_text==txt})
    old='d68a98a909630e15db6e1cb9c9c8171f957bff9d'
    path='src/services/validation/evaluators/judgment_review.py'
    previous=subprocess.check_output(['git','show',old+':'+path],cwd=ROOT,text=True)
    current=(ROOT/path).read_text()
    def node(s,name): return ast.dump(next(n for n in ast.walk(ast.parse(s)) if isinstance(n,ast.FunctionDef) and n.name==name),include_attributes=False)
    hist=json.loads((ROOT/'docs/analyses/def606-regeldossiers/INT-02-bewijs-v1/uitkomsten.json').read_text())
    raw=(ROOT/'src/toetsregels/regels/INT-02.json').read_bytes()
    oldraw=subprocess.check_output(['git','show',old+':src/toetsregels/regels/INT-02.json'],cwd=ROOT)
    result['historical_binding']={'old_commit':old,'record_equal_to_git':raw==oldraw,'record_equal_to_evidence':record==hist['record'],'sha256':hashlib.sha256(raw).hexdigest(),'historical_sha256':hist['source_sha256'],'signals_ast_unchanged':node(previous,'_signalen')==node(current,'_signalen'),'evaluate_ast_unchanged':node(previous,'evaluate')==node(current,'evaluate'),'restriction':'evaluate bevat alleen toegevoegde branches voor ESS-01/02/04; INT-02-codepad gelijk; overige keten niet gelijk verondersteld'}
    diff=subprocess.check_output(['git','diff',old,'HEAD','--','src/toetsregels/regels/INT-02.json',path],cwd=ROOT,text=True)
    with (OUT/'historische-diff-v1.txt').open('x') as f:f.write(diff)
    with (OUT/'proefuitkomsten-v1.json').open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps({'service_cases':len(cases),'service_expectations':all(r['expectation_met'] for r in result['cases']),'cleaning_expectations':[r['expectation_met'] for r in result['cleaning']],'historical_binding':result['historical_binding']},ensure_ascii=False))
asyncio.run(main())
