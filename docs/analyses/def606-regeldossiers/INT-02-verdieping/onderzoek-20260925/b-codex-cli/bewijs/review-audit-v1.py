import json, hashlib, subprocess, re
from pathlib import Path
from datetime import datetime, timezone
root=Path(__file__).resolve().parent.parent
A=root.parent/'a-claude-cli'/'bewijs'
i=json.loads((A/'p1-invoer.json').read_text()); o=json.loads((A/'p1-uitkomsten.json').read_text()); rows=o['uitkomsten']
bind=json.loads((root/'bewijs/review-bronbinding-v1.json').read_text())
r={'tijd_utc':datetime.now(timezone.utc).isoformat(),'bewijssoort':'artefactcontrole; geen appaanroep','commit_actueel':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'commit_p1':o['commit'],'input_count':len(i),'output_count':len(rows),'input_output_exact':i==[{k:x[k] for k in ('id','begrip','tekst','context')} for x in rows],'int02_rr':sum(x['int02_status']=='review_required' for x in rows),'int02_pass':sum(x['int02_in_passed'] for x in rows),'int02_violation':sum(x['int02_violation'] for x in rows),'signaalgevallen':[x['id'] for x in rows if x['int02_signals']],'int10_fail':[x['id'] for x in rows if x['buur_statussen']['INT-10']=='fail'],'indien_gevallen':[x['id'] for x in rows if re.search(r'\bindien\b',x['tekst'],re.I)],'int01_fail':[x['id'] for x in rows if x['buur_statussen']['INT-01']=='fail'],'broncontrole':[{'path':b['path'],'ongewijzigd':hashlib.sha256((root/b['path']).read_bytes()).hexdigest()==b['sha256']} for b in bind['source_files']]}
c=json.loads((root.parent/'a-cowork/bewijs/proef-c1-uitkomsten.json').read_text());r['c1']={'commit':c['commit'],'samenvatting':c['samenvatting'],'rijen':[{'id':x['id'],**x['werkelijk'],'match':x['match'],'fout':x['fout']} for x in c['toetsing']]}
with (root/'bewijs/review-audituitkomsten-v1.json').open('x') as f:json.dump(r,f,ensure_ascii=False,indent=2)
print(json.dumps(r,ensure_ascii=False,indent=2))
