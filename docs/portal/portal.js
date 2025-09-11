(function(){
  function getData(){
    const el=document.getElementById('portal-data');
    if(!el) return {documents:[],aggregate:{}};
    try { return JSON.parse(el.textContent||'{}'); } catch(e){ return {documents:[],aggregate:{}}; }
  }

  const data = getData();
  const list = document.getElementById('list');
  const q = document.getElementById('q');
  const tf = document.getElementById('typeFilter');
  const sf = document.getElementById('statusFilter');
  const stats = document.getElementById('stats');
  const sortSel = document.getElementById('sortSelect');
  const sprintSel = document.getElementById('sprintFilter');
  const viewTabs = document.getElementById('viewTabs');
  const ownerInput = document.getElementById('ownerInput');
  const workStatus = document.getElementById('workStatus');
  const workPriority = document.getElementById('workPriority');
  const workOnlyUs = document.getElementById('workOnlyUs');

  const docs = (data.documents||[]).slice();
  const idMap = {};
  docs.forEach(d=>{ if(d && d.id) idMap[String(d.id)] = d; });

  function getView(){
    const h=(location.hash||'').toLowerCase();
    const m=h.match(/view=([a-z0-9_-]+)/);
    return (m && m[1]) || 'all';
  }
  function getHashParam(key){
    const h=(location.hash||'');
    const re=new RegExp(key+"=([^&]+)", 'i');
    const m=h.match(re); return m?decodeURIComponent(m[1]):'';
  }
  function setHashParam(key, val){
    const params = new URLSearchParams((location.hash||'').replace(/^#/,''));
    if(val) params.set(key,val); else params.delete(key);
    location.hash = '#'+params.toString();
  }

  function match(d, query){
    if(!query) return true;
    const s=(d.id+' '+(d.title||'')+' '+(d.status||'')+' '+(d.owner||'')).toLowerCase();
    return query.split(/\s+/).every(t=>s.includes(t));
  }

  function render(){
    const query=(q.value||'').trim().toLowerCase();
    const t = tf.value;
    const s = sf.value;
    let filtered = docs.filter(d => match(d,query) && (!t||d.type===t) && (!s||String(d.status||'')===s));

    // view handling
    const view = getView();
    document.body.setAttribute('data-view', view);
    if(viewTabs){
      Array.from(viewTabs.querySelectorAll('a')).forEach(a=>{
        const isActive=(a.getAttribute('href')||'').includes('view='+view);
        a.classList.toggle('active', !!isActive);
      });
    }

    // sprint filter options (planning view)
    if(sprintSel){
      const sprints = Array.from(new Set(docs.map(d=>d.sprint).filter(Boolean))).sort((a,b)=>{
        const na=(d=>{const m=String(d).match(/(\d+)/);return m?parseInt(m[1],10):9999})(a);
        const nb=(d=>{const m=String(d).match(/(\d+)/);return m?parseInt(m[1],10):9999})(b);
        return na-nb || String(a).localeCompare(String(b));
      });
      if(sprintSel.childElementCount<=1 && sprints.length){
        sprints.forEach(sp=>{
          const opt=document.createElement('option'); opt.value=sp; opt.textContent=sp; sprintSel.appendChild(opt);
        });
      }
      // Only show sprint filter if we actually have sprints
      const showSprint = (view==='planning') && sprints.length>0;
      sprintSel.parentElement.style.display = showSprint ? 'flex' : 'none';
    }
    // work controls
    if(ownerInput){
      const showWork = (view==='work');
      const wrap = ownerInput.parentElement; if(wrap) wrap.style.display = showWork ? 'flex' : 'none';
      if(showWork && !ownerInput.value){
        ownerInput.value = getHashParam('owner') || localStorage.getItem('portalOwner') || 'developer';
      }
      // hydrate selects from hash for deeplinks
      if(showWork){
        const hs = getHashParam('wstatus'); if(workStatus && typeof hs==='string') workStatus.value = hs;
        const hp = getHashParam('wprio'); if(workPriority && typeof hp==='string') workPriority.value = hp;
        const ho = getHashParam('wonlyus'); if(workOnlyUs) workOnlyUs.checked = (ho==='1');
      }
    }

    // sorteren
    const mode = (sortSel && sortSel.value) || 'title';
    const prRank = { KRITIEK:1, HOOG:2, GEMIDDELD:3, LAAG:4 };
    const cmpPlanning=(a,b)=>{
      const asn = (a.planning&&a.planning.sprint_number)||9999;
      const bsn = (b.planning&&b.planning.sprint_number)||9999;
      if(asn!==bsn) return asn-bsn;
      const ap = (a.planning&&a.planning.priority_rank)||9;
      const bp = (b.planning&&b.planning.priority_rank)||9;
      if(ap!==bp) return ap-bp;
      const at = (a.planning&&a.planning.type_rank)||9;
      const bt = (b.planning&&b.planning.type_rank)||9;
      if(at!==bt) return at-bt;
      return String(a.title||a.id||'').localeCompare(String(b.title||b.id||''));
    };
    filtered.sort((a,b)=>{
      if(mode==='priority'){
        const ap = prRank[String(a.prioriteit||'').toUpperCase()]||9;
        const bp = prRank[String(b.prioriteit||'').toUpperCase()]||9;
        if(ap!==bp) return ap-bp;
        const as = a.sprint||''; const bs = b.sprint||'';
        return String(a.title||a.id||'').localeCompare(String(b.title||b.id||''));
      }
      if(mode==='planning'){
        return cmpPlanning(a,b);
      }
      // default: title
      return String(a.title||a.id||'').localeCompare(String(b.title||b.id||''));
    });

    list.innerHTML='';

    if(view==='planning'){
      const allowed = new Set(['EPIC','US','BUG']);
      let v = filtered.filter(d=>allowed.has(String(d.type).toUpperCase()));
      const hasSprints = v.some(d=>!!d.sprint);
      // apply optional sprint filter only if sprints exist
      if(hasSprints){
        const sfv = sprintSel ? sprintSel.value : '';
        if(sfv) v = v.filter(d=>String(d.sprint||'')===sfv);
        // group by sprint label
        const groups = {};
        v.forEach(d=>{ const key = d.sprint || 'backlog'; (groups[key] ||= []).push(d); });
        const sprintKeys = Object.keys(groups).sort((a,b)=>{
          const na=(d=>{const m=String(d).match(/(\d+)/);return m?parseInt(m[1],10):9999})(a);
          const nb=(d=>{const m=String(d).match(/(\d+)/);return m?parseInt(m[1],10):9999})(b);
          return na-nb || String(a).localeCompare(String(b));
        });
        sprintKeys.forEach(groupKey=>{
          renderPlanningHierarchy(groups[groupKey].slice().sort(cmpPlanning), `Sprint: ${groupKey}`);
        });
      } else {
        // No sprints: render a single EPIC→US→BUG hierarchy
        renderPlanningHierarchy(v.slice().sort(cmpPlanning), 'Planning');
      }
    } else if (view==='req-matrix'){
      // Simple REQ ↔ EPIC matrix (EPIC rows with REQ chips)
      const epics = docs.filter(d=>String(d.type).toUpperCase()==='EPIC');
      const table=document.createElement('table'); table.className='matrix';
      const thead=document.createElement('thead'); const trh=document.createElement('tr');
      ['EPIC','Titel','REQs (count)'].forEach(h=>{ const th=document.createElement('th'); th.textContent=h; trh.appendChild(th); });
      thead.appendChild(trh); table.appendChild(thead);
      const tbody=document.createElement('tbody');
      epics.sort((a,b)=>String(a.id||a.title).localeCompare(String(b.id||b.title))).forEach(e=>{
        const reqIds = Array.isArray(e.linked_reqs)? e.linked_reqs : [];
        if(!reqIds.length) return; // show only epics with reqs
        const tr=document.createElement('tr');
        const td1=document.createElement('td'); const a=document.createElement('a'); a.textContent=e.id||'EPIC'; a.href=e.url||e.path; a.target='_blank'; td1.appendChild(a);
        const td2=document.createElement('td'); td2.textContent=e.title||'';
        const td3=document.createElement('td');
        reqIds.forEach(rid=>{
          const r = idMap[rid];
          const chip=document.createElement('span'); chip.className='chip';
          if(r && r.url){ const link=document.createElement('a'); link.href=r.url; link.target='_blank'; link.textContent=rid; chip.appendChild(link); }
          else { chip.textContent=rid; }
          td3.appendChild(chip);
        });
        const count=document.createElement('span'); count.className='meta'; count.textContent=`  (${reqIds.length})`;
        td3.appendChild(count);
        tr.append(td1,td2,td3); tbody.appendChild(tr);
      });
      list.appendChild(table);
    } else if (view==='work'){
      const owner = (ownerInput && ownerInput.value.trim()) || getHashParam('owner') || localStorage.getItem('portalOwner') || '';
      if(owner){ localStorage.setItem('portalOwner', owner); setHashParam('owner', owner); }
      const wanted = owner.toLowerCase();
      const wantStatus = (workStatus && workStatus.value) || getHashParam('wstatus') || '';
      const wantPrio = (workPriority && workPriority.value) || getHashParam('wprio') || '';
      const onlyUS = workOnlyUs ? !!workOnlyUs.checked : (getHashParam('wonlyus')==='1');
      if(workStatus){ setHashParam('wstatus', wantStatus); }
      if(workPriority){ setHashParam('wprio', wantPrio); }
      setHashParam('wonlyus', onlyUS ? '1' : '');
      const v = docs.filter(d=>{
        const t=String(d.type).toUpperCase();
        if(!(t==='US' || t==='BUG')) return false;
        if(onlyUS && t!=='US') return false;
        const st=String(d.status||'').toUpperCase();
        if(['GEREED','VOLTOOID','RESOLVED'].includes(st)) return false;
        if(wantStatus && st !== String(wantStatus).toUpperCase()) return false;
        const ow=String(d.owner||'').toLowerCase();
        if(wanted && !ow.includes(wanted)) return false;
        const pr = String(d.prioriteit||'').toUpperCase();
        if(wantPrio && pr !== String(wantPrio).toUpperCase()) return false;
        return true;
      }).sort(cmpPlanning);
      const h = document.createElement('h3'); h.className='group'; h.textContent=`Mijn Werk (${owner||'alle owners'}) – ${v.length} items`;
      list.appendChild(h);
      v.forEach(d=>{
        const li=document.createElement('li'); li.className='doc-item';
        const type=document.createElement('span'); type.className='badge type'; type.textContent=d.type||'DOC';
        const title=document.createElement('div'); title.className='title'; title.textContent=(d.title||d.id||d.path);
        const meta=document.createElement('div'); meta.className='meta';
        const sp = d.sprint?`sprint:${d.sprint}`:null;
        const pts = d.story_points?`SP:${d.story_points}`:null;
        meta.textContent=[d.status,d.owner,d.prioriteit,sp,pts].filter(Boolean).join(' • ');
        const link=document.createElement('a'); link.className='link'; link.href=d.url||d.path; link.textContent='open'; link.target='_blank';
        li.append(type,title,meta,link); list.appendChild(li);
      });
    } else if(view==='requirements'){
      const v = filtered.filter(d=>String(d.type).toUpperCase()==='REQ');
      v.forEach(d => {
        const li=document.createElement('li'); li.className='doc-item';
        const type=document.createElement('span'); type.className='badge type'; type.textContent=d.type||'REQ';
        const title=document.createElement('div'); title.className='title'; title.textContent=(d.title||d.id||d.path);
        const meta=document.createElement('div'); meta.className='meta';
        const rel = d.target_release?`rel:${d.target_release}`:null;
        meta.textContent=[d.status,d.owner,d.prioriteit,rel,d.canonical?'canonical':null].filter(Boolean).join(' • ');
        const rels=document.createElement('div'); rels.className='rels';
        // linked epics
        if(Array.isArray(d.linked_epics) && d.linked_epics.length){
          const lbl=document.createElement('span'); lbl.className='rels-label'; lbl.textContent='EPIC:'; rels.appendChild(lbl);
          d.linked_epics.forEach(eid=>{
            const a=document.createElement('a'); a.className='badge link-badge'; a.textContent=eid;
            const target=idMap[eid]; if(target && target.url) a.href=target.url; a.target='_blank';
            rels.appendChild(a);
          });
        }
        // linked stories
        if(Array.isArray(d.linked_stories) && d.linked_stories.length){
          const lbl=document.createElement('span'); lbl.className='rels-label'; lbl.textContent='US:'; rels.appendChild(lbl);
          d.linked_stories.forEach(uid=>{
            const a=document.createElement('a'); a.className='badge link-badge'; a.textContent=uid;
            const target=idMap[uid]; if(target && target.url) a.href=target.url; a.target='_blank';
            rels.appendChild(a);
          });
        }
        const link=document.createElement('a'); link.className='link'; link.href=d.url||d.path; link.textContent='open'; link.target='_blank';
        li.append(type,title,meta,rels,link); list.appendChild(li);
      });
    } else {
      // default: all documents flat list
      filtered.forEach(d => {
        const li=document.createElement('li'); li.className='doc-item';
        const type=document.createElement('span'); type.className='badge type'; type.textContent=d.type||'DOC';
        const title=document.createElement('div'); title.className='title'; title.textContent=(d.title||d.id||d.path);
        const meta=document.createElement('div'); meta.className='meta';
        const sp = d.sprint?`sprint:${d.sprint}`:null;
        const pts = d.story_points?`SP:${d.story_points}`:null;
        const rel = d.target_release?`rel:${d.target_release}`:null;
        meta.textContent=[d.status,d.owner,d.prioriteit,sp,pts,rel,d.canonical?'canonical':null].filter(Boolean).join(' • ');
        const link=document.createElement('a'); link.className='link'; link.href=d.url||d.path; link.textContent='open';
        link.target='_blank';
        li.append(type,title,meta,link); list.appendChild(li);
      });
    }
    const c = data.aggregate && data.aggregate.counts || {};
    // counts shown reflect current view selection
    const shown = list.querySelectorAll('li.doc-item').length;
    stats.textContent=`Items: ${shown}  |  (REQ:${c.REQ||0} EPIC:${c.EPIC||0} US:${c.US||0} BUG:${c.BUG||0} ARCH:${c.ARCH||0} GUIDE:${c.GUIDE||0} TEST:${c.TEST||0} COMP:${c.COMP||0} DOC:${c.DOC||0})`;
  }

  function renderPlanningHierarchy(items, headerLabel){
    const h = document.createElement('h3'); h.className='group';
    h.textContent = `${headerLabel} (${items.length})`;
    list.appendChild(h);
    const epics = {}; const orphans=[];
    items.forEach(d=>{
      const t=String(d.type).toUpperCase();
      if(t==='EPIC') epics[d.id||d.parent_epic||''] ||= { epic:d, us:{}};
      else if(t==='US'){
        const pe = d.parent_epic||''; epics[pe] ||= { epic: idMap[pe], us:{} };
        epics[pe].us[d.id||''] ||= { us:d, bugs:[] };
      } else if(t==='BUG'){
        const pu=d.parent_us||''; const usDoc=idMap[pu]; const pe=(usDoc&&usDoc.parent_epic)||d.parent_epic||'';
        if(!pe || !pu){ orphans.push(d); return; }
        epics[pe] ||= { epic: idMap[pe], us:{} };
        epics[pe].us[pu] ||= { us: idMap[pu], bugs:[] };
        epics[pe].us[pu].bugs.push(d);
      }
    });
    Object.keys(epics).filter(Boolean).forEach(eid=>{
      const e = epics[eid];
      const eHeader = document.createElement('div'); eHeader.className='planning-epic';
      const eBadge = document.createElement('span'); eBadge.className='badge type'; eBadge.textContent='EPIC';
      const eTitle = document.createElement('a'); eTitle.textContent=(e.epic&&(e.epic.title||e.epic.id))||eid; eTitle.href=(e.epic&&e.epic.url)||'#'; eTitle.target='_blank';
      eHeader.append(eBadge, eTitle); list.appendChild(eHeader);
      const usKeys = Object.keys(e.us).sort((a,b)=>{ const A=e.us[a].us||{}; const B=e.us[b].us||{}; return cmpPlanning(A,B); });
      usKeys.forEach(uid=>{
        const u=e.us[uid];
        const li=document.createElement('div'); li.className='planning-us';
        const uBadge=document.createElement('span'); uBadge.className='badge type'; uBadge.textContent='US';
        const uLink=document.createElement('a'); uLink.textContent=u.us.title||u.us.id; uLink.href=u.us.url; uLink.target='_blank';
        const uMeta=document.createElement('span'); uMeta.className='meta'; const pts=u.us.story_points?`SP:${u.us.story_points}`:null;
        uMeta.textContent=['status:'+(u.us.status||''), u.us.prioriteit, pts].filter(Boolean).join(' · ');
        li.append(uBadge,uLink,document.createTextNode(' '),uMeta);
        if(u.bugs && u.bugs.length){
          const bugRow=document.createElement('div'); bugRow.className='planning-bugs';
          u.bugs.sort(cmpPlanning).forEach(b=>{ const chip=document.createElement('a'); chip.className='badge bug-chip'; chip.textContent=b.title||b.id||'BUG'; chip.href=b.url||b.path; chip.target='_blank'; bugRow.appendChild(chip); });
          li.appendChild(bugRow);
        }
        list.appendChild(li);
      });
    });
    orphans.sort(cmpPlanning).forEach(d=>{
      const li=document.createElement('li'); li.className='doc-item';
      const type=document.createElement('span'); type.className='badge type'; type.textContent=d.type||'DOC';
      const title=document.createElement('div'); title.className='title'; title.textContent=(d.title||d.id||d.path);
      const meta=document.createElement('div'); meta.className='meta';
      const pts = d.story_points?`SP:${d.story_points}`:null;
      const rel = d.target_release?`rel:${d.target_release}`:null;
      meta.textContent=[d.status,d.owner,d.prioriteit,pts,rel,d.canonical?'canonical':null].filter(Boolean).join(' • ');
      const link=document.createElement('a'); link.className='link'; link.href=d.url||d.path; link.textContent='open'; link.target='_blank';
      li.append(type,title,meta,link); list.appendChild(li);
    });
  }

  q.addEventListener('input',render); tf.addEventListener('change',render); sf.addEventListener('change',render);
  if(sortSel) sortSel.addEventListener('change',render);
  if(sprintSel) sprintSel.addEventListener('change',render);
  if(ownerInput) ownerInput.addEventListener('change', render);
  if(workStatus) workStatus.addEventListener('change', render);
  if(workPriority) workPriority.addEventListener('change', render);
  if(workOnlyUs) workOnlyUs.addEventListener('change', render);
  window.addEventListener('hashchange', render);
  render();
})();
