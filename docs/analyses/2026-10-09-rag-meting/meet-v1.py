"""RAG-meting 9 oktober 2026 (Cowork) — bewijs bij docs/plans/2026-10-09-RAG-kwaliteit-werkplan-v1.md.

Alleen-lezen op een KOPIE van data/bronnen.db (pad DB hieronder). Gebruikt de echte
RAGService._zoek_hybride (via retrieve_context_multi, alle collecties, top_k onbeperkt)
en rapporteert per begrip: kandidaten na de poort, rang van de begripsbepaling van
precies dit begrip, kernartikelen in de top 5, en per top-5-fragment wet, artikel,
type, rechtsgebied, cosine-score, lengte en positie van het begrip.
De shims bovenaan (stub-packages, datetime.UTC) waren nodig omdat de meting op
Python 3.10 draaide; onder de projectomgeving (3.13) zijn ze overbodig.
Resultaat: resultaat-v1.json (19 unieke zoekvragen; enkele staan dubbel in de lijst).
"""
import sys, json, os, sqlite3
REPO=os.path.expanduser("~/mnt/Definitie-app")
sys.path.insert(0, REPO+"/src")
import types, datetime as _dt
if not hasattr(_dt,'UTC'): _dt.UTC=_dt.timezone.utc
for naam, pad in [("services","/src/services"),("services.rag","/src/services/rag"),("utils","/src/utils"),("domain","/src/domain")]:
    m=types.ModuleType(naam); m.__path__=[REPO+pad]; sys.modules[naam]=m
from dotenv import dotenv_values
key=dotenv_values(REPO+"/.env")["OPENAI_API_KEY"]
from services.rag.embedding_service import EmbeddingService
from services.rag.embedding_store import EmbeddingStore
from services.rag.rag_service import RAGService
from utils.term_match import zoekpatronen, normaliseer_zoektekst
DB=os.path.expanduser("~/ragcheck/bronnen_kopie.db")
svc=RAGService(None, EmbeddingService(key), EmbeddingStore(DB), DB)
cids=[r[0] for r in sqlite3.connect(DB).execute("select distinct collection_id from rag_chunks")]
d=json.load(open(REPO+"/tests/fixtures/rag_meting/fase3_begrippen.json"))
cases=[(x["begrip"], x.get("rechtsgebied", d["rechtsgebied"]), x.get("kernartikelen",[])) for x in d["positief"]]
cases+= [("verdachte","strafrecht",[]),("beschikking","bestuursrecht",[]),("besluit","bestuursrecht",[]),
         ("persoonsgegevens","bestuursrecht",[]),("bestuursorgaan","bestuursrecht",[]),("inbeslagneming","strafrecht",[]),
         ("voorlopige hechtenis","strafrecht",[]),("ingezetene","bestuursrecht",[])]
out=[]
for begrip, rg, kern in cases:
    ctx=svc.retrieve_context_multi(begrip, collection_ids=cids, top_k=10**6, rechtsgebied=rg, zoektermen=[begrip])
    alle=ctx.chunks
    def is_def(c):
        if (c["metadata"] or {}).get("structuur_type")!="definitie": return False
        body=c["chunk_text"].split("\n",1)[-1]
        term=body.split(":",1)[0]
        return normaliseer_zoektekst(term).startswith(normaliseer_zoektekst(begrip))
    defranks=[i+1 for i,c in enumerate(alle) if is_def(c)]
    pats=[p for p in zoekpatronen(begrip) if not p.pattern.startswith(r"\A")]
    top=[]
    for c in alle[:5]:
        n=normaliseer_zoektekst(c["chunk_text"])
        pos=min([m.start() for p in pats for m in [p.search(n)] if m] or [-1])
        top.append({"wet":(c["wet_regeling"] or "")[:45],"art":c["artikel_lid"],"type":(c["metadata"] or {}).get("structuur_type"),
                    "rg":c["rechtsgebied"],"score":round(c["score"],3),"len":len(c["chunk_text"]),"begrip_pos":pos,
                    "door_drempel":c["score"]>=0.3})
    kernhit=[k for k in kern if any((c["wet_regeling"] or "").startswith(k.split("|")[0]) and str(c["artikel_lid"])==k.split("|")[1] for c in alle[:5])]
    out.append({"begrip":begrip,"rg_filter":rg,"kandidaten":ctx.kandidaten,"definitie_rangen":defranks[:5],
                "kern":kern,"kern_in_top5":kernhit,"top5":top})
    print(begrip, rg, "kand",ctx.kandidaten, "defrang",defranks[:5], "kern_in_top5",kernhit)
    for t in top: print("   ",t)
json.dump(out,open(os.path.expanduser("~/ragcheck/resultaat.json"),"w"),ensure_ascii=False,indent=1)
