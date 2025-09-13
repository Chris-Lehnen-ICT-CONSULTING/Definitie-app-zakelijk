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
  const toolbar = document.querySelector('.toolbar');
  // Create badge container once, placed just under toolbar
  const badgeContainer = document.createElement('div');
  badgeContainer.id = 'queryBadges';
  badgeContainer.className = 'search-badges';
  if(toolbar && toolbar.parentElement){
    toolbar.insertAdjacentElement('afterend', badgeContainer);
  }

  const docs = (data.documents||[]).slice();
  const idMap = {};
  docs.forEach(d=>{ if(d && d.id) idMap[String(d.id)] = d; });

  function viewerHref(path, title){
    const base = new URL('viewer.html', location.href);
    if(path){ base.searchParams.set('src', path); }
    if(title){ base.searchParams.set('title', title); }
    return base.toString();
  }

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
    const newHash = '#'+params.toString();
    if(location.hash !== newHash){
      location.hash = newHash;
    }
  }

  // --- US-095: Lightweight query parser ---
  // Parses key:value tokens with optional quoted values, supports multiple values per key.
  // Supported keys (MVP): id, owner, type, status, sprint, prio (alias: prioriteit, priority), title
  function normalizeKey(k){
    const key = String(k||'').toLowerCase();
    if(key === 'prio' || key === 'prioriteit' || key === 'priority') return 'prioriteit';
    if(key === 'id' || key === 'owner' || key === 'type' || key === 'status' || key === 'sprint' || key === 'title') return key;
    return null; // unknown keys ignored in MVP
  }

  function parseQuery(query){
    const result = {
      text: [],        // free text tokens
      filters: {       // key -> array of values
        id: [], owner: [], type: [], status: [], sprint: [], prioriteit: [], title: []
      },
      raw: String(query||'')
    };
    const q = String(query||'');
    if(!q.trim()) return result;

    // Match sequences of: key:("value with spaces"|'value'|value)
    const re = /(^|\s)([a-zA-Z_][a-zA-Z0-9_]*):(?:"([^"]*)"|'([^']*)'|([^\s]+))/g;
    let m;
    // Keep track of ranges to remove matched segments from leftover
    const spans = [];
    while((m = re.exec(q))){
      const raw = m[0];
      const key = normalizeKey(m[2]);
      const val = (m[3]!==undefined && m[3]!==null) ? m[3]
                : (m[4]!==undefined && m[4]!==null) ? m[4]
                : (m[5]!==undefined && m[5]!==null) ? m[5]
                : '';
      if(key && val){
        if(!Array.isArray(result.filters[key])) result.filters[key] = [];
        result.filters[key].push(val);
      }
      // Track the absolute index of the match to strip later
      const start = m.index + (m[1] ? m[1].length : 0);
      spans.push([start, start + raw.trimStart().length]);
    }

    // Build leftover by removing matched spans
    if(spans.length){
      // Merge overlapping spans for safety
      spans.sort((a,b)=>a[0]-b[0]);
      const merged = [];
      for(const s of spans){
        if(!merged.length || s[0] > merged[merged.length-1][1]) merged.push(s);
        else merged[merged.length-1][1] = Math.max(merged[merged.length-1][1], s[1]);
      }
      let last = 0; let leftover = '';
      for(const [a,b] of merged){
        leftover += q.slice(last, a);
        last = b;
      }
      leftover += q.slice(last);
      // Remaining words become free-text tokens
      leftover.trim().split(/\s+/).filter(Boolean).forEach(t=>result.text.push(t));
    } else {
      // No key:value tokens; split all as free text
      q.trim().split(/\s+/).filter(Boolean).forEach(t=>result.text.push(t));
    }

    return result;
  }

  function match(d, query){
    // Legacy free-text matcher (kept for now). Token-based filtering will be applied in pipeline.
    if(!query) return true;
    const s=(d.id+' '+(d.title||'')+' '+(d.status||'')+' '+(d.owner||'')).toLowerCase();
    return query.split(/\s+/).every(t=>s.includes(t));
  }

  function render(){
    const query=(q.value||'').trim();
    // Keep hash 'q' in sync for bookmarkable queries
    setHashParam('q', query);
    const parsed = parseQuery(query);
    const plainQuery = parsed.text.join(' ').toLowerCase();
    // Update badge UI
    updateBadgeUI(parsed);
    const t = tf.value;
    const s = sf.value;
    // Base filtering: free-text + dropdown type/status
    let filtered = docs.filter(d => match(d,plainQuery) && (!t||d.type===t) && (!s||String(d.status||'')===s));

    // Sprint dropdown (visible in planning, but apply if set)
    const sprintFilterVal = (sprintSel && sprintSel.value) ? String(sprintSel.value) : '';
    if(sprintFilterVal){
      const want = sprintFilterVal.toLowerCase();
      filtered = filtered.filter(d => String(d.sprint||'').toLowerCase() === want);
    }

    // Token-based filtering (AND across keys, OR within a key)
    const ci = (x)=>String(x||'').toLowerCase();
    const hasAny = (arr)=>Array.isArray(arr) && arr.length>0;
    if(hasAny(parsed.filters.id)){
      const wants = parsed.filters.id.map(ci);
      filtered = filtered.filter(d => wants.includes(ci(d.id)));
    }
    if(hasAny(parsed.filters.owner)){
      const wants = parsed.filters.owner.map(ci);
      filtered = filtered.filter(d => wants.includes(ci(d.owner)));
    }
    if(hasAny(parsed.filters.type)){
      const wants = parsed.filters.type.map(ci);
      filtered = filtered.filter(d => wants.includes(ci(d.type)));
    }
    if(hasAny(parsed.filters.status)){
      const wants = parsed.filters.status.map(ci);
      filtered = filtered.filter(d => wants.includes(ci(d.status)));
    }
    if(hasAny(parsed.filters.sprint)){
      const wants = parsed.filters.sprint.map(ci);
      filtered = filtered.filter(d => wants.includes(ci(d.sprint)));
    }
    if(hasAny(parsed.filters.prioriteit)){
      const wants = parsed.filters.prioriteit.map(ci);
      filtered = filtered.filter(d => wants.includes(ci(d.prioriteit)));
    }
    if(hasAny(parsed.filters.title)){
      const wants = parsed.filters.title.map(ci);
      filtered = filtered.filter(d => {
        const blob = ci((d.title||d.id||d.path));
        return wants.every(w => blob.includes(w));
      });
    }

    // view handling
    const view = getView();
    document.body.setAttribute('data-view', view);
    if(viewTabs){
      Array.from(viewTabs.querySelectorAll('a')).forEach(a=>{
        const isActive=(a.getAttribute('href')||'').includes('view='+view);
        a.classList.toggle('active', !!isActive);
        a.setAttribute('aria-selected', isActive ? 'true' : 'false');
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
      if(v.length === 0){
        const empty = document.createElement('div');
        empty.className = 'meta';
        empty.style.margin = '12px';
        empty.textContent = 'Geen items gevonden voor de huidige selectie. Pas je filters aan of kies een andere sprint.';
        list.appendChild(empty);
        return;
      }
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
        const td1=document.createElement('td'); const a=document.createElement('a'); a.textContent=e.id||'EPIC'; a.href=viewerHref(e.rendered_url||e.url||e.path, e.title||e.id||'EPIC'); attachAltClickFilter(a, e.id||''); td1.appendChild(a);
        const td2=document.createElement('td'); td2.textContent=e.title||'';
        const td3=document.createElement('td');
        reqIds.forEach(rid=>{
          const r = idMap[rid];
          const chip=document.createElement('span'); chip.className='chip';
          if(r && (r.rendered_url||r.url)){
            const link=document.createElement('a'); link.href=viewerHref(r.rendered_url||r.url, r.title||rid); link.textContent=rid; attachAltClickFilter(link, rid); chip.appendChild(link);
          } else { chip.textContent=rid; }
          // filter button
          chip.appendChild(makeFilterButton(rid));
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
        const link=document.createElement('a'); link.className='link'; link.href=viewerHref(d.rendered_url||d.url||d.path, d.title||d.id||d.path); link.textContent='open';
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
            const target=idMap[eid]; if(target && (target.rendered_url||target.url)) a.href=viewerHref(target.rendered_url||target.url, target.title||eid);
            attachAltClickFilter(a, eid);
            const wrap=document.createElement('span'); wrap.className='chip'; wrap.appendChild(a); wrap.appendChild(makeFilterButton(eid));
            rels.appendChild(wrap);
          });
        }
        // linked stories
        if(Array.isArray(d.linked_stories) && d.linked_stories.length){
          const lbl=document.createElement('span'); lbl.className='rels-label'; lbl.textContent='US:'; rels.appendChild(lbl);
          d.linked_stories.forEach(uid=>{
            const a=document.createElement('a'); a.className='badge link-badge'; a.textContent=uid;
            const target=idMap[uid]; if(target && (target.rendered_url||target.url)) a.href=viewerHref(target.rendered_url||target.url, target.title||uid);
            attachAltClickFilter(a, uid);
            const wrap=document.createElement('span'); wrap.className='chip'; wrap.appendChild(a); wrap.appendChild(makeFilterButton(uid));
            rels.appendChild(wrap);
          });
        }
        const link=document.createElement('a'); link.className='link'; link.href=viewerHref(d.rendered_url||d.url||d.path, d.title||d.id||d.path); link.textContent='open';
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
        const link=document.createElement('a'); link.className='link'; link.href=viewerHref(d.url||d.path, d.title||d.id||d.path); link.textContent='open';
        li.append(type,title,meta,link); list.appendChild(li);
      });
    }
    const c = data.aggregate && data.aggregate.counts || {};
    // counts shown reflect current view selection
    const shown = list.querySelectorAll('li.doc-item').length;
    stats.textContent=`Items: ${shown}  |  (REQ:${c.REQ||0} EPIC:${c.EPIC||0} US:${c.US||0} BUG:${c.BUG||0} ARCH:${c.ARCH||0} GUIDE:${c.GUIDE||0} TEST:${c.TEST||0} COMP:${c.COMP||0} DOC:${c.DOC||0})`;
  }

  // ---- Chip deeplink helpers (US-086) ----
  function applyIDFilter(id, append){
    const token = `id:${id}`;
    const cur = (q.value||'').trim();
    const next = append && cur ? `${cur} ${token}` : token;
    q.value = next;
    render();
  }
  function attachAltClickFilter(anchor, id){
    if(!anchor) return;
    anchor.addEventListener('click', (e)=>{
      if(e.altKey){ e.preventDefault(); applyIDFilter(id, e.shiftKey); }
    });
  }
  function makeFilterButton(id){
    const btn=document.createElement('button');
    btn.className='filter-btn';
    btn.type='button';
    btn.textContent='🔎';
    btn.title=`Filter op id:${id} (Shift: toevoegen)`;
    btn.setAttribute('aria-label', `Filter op id ${id}`);
    btn.addEventListener('click', (e)=>{ applyIDFilter(id, !!e.shiftKey); });
    return btn;
  }

  function updateBadgeUI(parsed){
    if(!badgeContainer) return;
    // Clear
    badgeContainer.textContent = '';
    const hasTokens = (parsed.text && parsed.text.length) || Object.values(parsed.filters||{}).some(a=>Array.isArray(a)&&a.length);
    // Also consider active sprint dropdown as a token-equivalent
    const activeSprintDropdown = (sprintSel && sprintSel.value) ? sprintSel.value : '';
    if(!hasTokens && !activeSprintDropdown){
      badgeContainer.style.display = 'none';
      return;
    }
    badgeContainer.style.display = '';
    const hint = document.createElement('span');
    hint.className = 'hint';
    hint.textContent = 'Filters:';
    badgeContainer.appendChild(hint);

    // Render filter badges
    const renderPair = (k,v)=>{
      const b = document.createElement('span');
      b.className = 'badge';
      b.textContent = `${k}:${v}`;
      badgeContainer.appendChild(b);
    };
    for(const [k,vals] of Object.entries(parsed.filters)){
      if(Array.isArray(vals)) vals.forEach(v=>renderPair(k,v));
    }
    // Free-text badges
    (parsed.text||[]).forEach(tk=>{
      const b=document.createElement('span'); b.className='badge'; b.textContent=tk; badgeContainer.appendChild(b);
    });

    // If sprint dropdown is active and not already present as a sprint: token, render a sprint badge
    if(activeSprintDropdown){
      const existing = (parsed.filters && parsed.filters.sprint) ? parsed.filters.sprint.map(v=>String(v).toLowerCase()) : [];
      if(!existing.includes(String(activeSprintDropdown).toLowerCase())){
        const sb = document.createElement('span'); sb.className='badge'; sb.textContent = `sprint:${activeSprintDropdown}`; badgeContainer.appendChild(sb);
      }
    }

    // Clear button (query)
    const clear = document.createElement('button');
    clear.className = 'clear-query';
    clear.type = 'button';
    clear.textContent = '× Wissen';
    clear.title = 'Zoekopdracht wissen';
    clear.setAttribute('aria-label','Wis zoekopdracht');
    clear.addEventListener('click', ()=>{ q.value=''; render(); });
    badgeContainer.appendChild(clear);

    // Reset all filters
    const reset = document.createElement('button');
    reset.className = 'reset-all';
    reset.type = 'button';
    reset.textContent = 'Reset alle filters';
    reset.title = 'Reset query, type/status/sprint en werk-filters';
    reset.setAttribute('aria-label','Reset alle filters');
    reset.addEventListener('click', ()=>{
      // Inputs
      if(q) q.value='';
      if(tf) tf.value='';
      if(sf) sf.value='';
      if(sprintSel) sprintSel.value='';
      if(ownerInput) ownerInput.value='';
      if(workStatus) workStatus.value='';
      if(workPriority) workPriority.value='';
      if(workOnlyUs) workOnlyUs.checked=false;
      // Hash params
      setHashParam('q',''); setHashParam('view', getView());
      setHashParam('owner',''); setHashParam('wstatus',''); setHashParam('wprio',''); setHashParam('wonlyus','');
      render();
    });
    badgeContainer.appendChild(reset);
  }

  function renderPlanningHierarchy(items, headerLabel){
    const h = document.createElement('h3'); h.className='group';
    // Compute type counts for header summary
    const typeCounts = items.reduce((acc,d)=>{ const t=String(d.type||'').toUpperCase(); acc[t]=(acc[t]||0)+1; return acc; }, {});
    const parts = [];
    if(typeCounts.EPIC) parts.push(`EPIC:${typeCounts.EPIC}`);
    if(typeCounts.US) parts.push(`US:${typeCounts.US}`);
    if(typeCounts.BUG) parts.push(`BUG:${typeCounts.BUG}`);
    const suffix = parts.length ? ` — ${parts.join(' • ')}` : '';
    h.textContent = `${headerLabel} (${items.length})${suffix}`;
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
    // Sort epics using planning comparator on their epic docs for consistent order
    Object.keys(epics).filter(Boolean).sort((a,b)=>{
      const A = epics[a].epic || {};
      const B = epics[b].epic || {};
      return cmpPlanning(A,B);
    }).forEach(eid=>{
      const e = epics[eid];
      const eHeader = document.createElement('div'); eHeader.className='planning-epic';
      const eBadge = document.createElement('span'); eBadge.className='badge type'; eBadge.textContent='EPIC';
      const eTitle = document.createElement('a'); eTitle.textContent=(e.epic&&(e.epic.title||e.epic.id))||eid; eTitle.href=viewerHref((e.epic&&(e.epic.rendered_url||e.epic.url))||'#', (e.epic&&e.epic.title)||eid); attachAltClickFilter(eTitle, (e.epic&&e.epic.id)||eid||'');
      // Counts per epic
      const usCount = Object.keys(e.us||{}).length;
      const bugCount = Object.values(e.us||{}).reduce((acc, u)=>acc + ((u.bugs&&u.bugs.length)||0), 0);
      const eMeta = document.createElement('span'); eMeta.className='meta'; eMeta.textContent = ` — US:${usCount} • BUG:${bugCount}`;
      eHeader.append(eBadge, eTitle, eMeta); list.appendChild(eHeader);
      const usKeys = Object.keys(e.us).sort((a,b)=>{ const A=e.us[a].us||{}; const B=e.us[b].us||{}; return cmpPlanning(A,B); });
      usKeys.forEach(uid=>{
        const u=e.us[uid];
        const li=document.createElement('div'); li.className='planning-us';
        const uBadge=document.createElement('span'); uBadge.className='badge type'; uBadge.textContent='US';
        const uLink=document.createElement('a'); uLink.textContent=u.us.title||u.us.id; uLink.href=viewerHref(u.us.rendered_url||u.us.url, u.us.title||u.us.id); attachAltClickFilter(uLink, u.us.id||'');
        const uMeta=document.createElement('span'); uMeta.className='meta';
        const statusTxt = String(u.us.status||'');
        const prioTxt = String(u.us.prioriteit||'');
        const pts=u.us.story_points?`SP:${u.us.story_points}`:null;
        const bugc = (u.bugs && u.bugs.length) ? `bugs:${u.bugs.length}` : null;
        const statusEl=document.createElement('span'); statusEl.className=`badge status-badge status-${statusTxt.toUpperCase()}`; statusEl.textContent=statusTxt||'';
        const prioEl=document.createElement('span'); prioEl.className=`badge prio-badge prio-${prioTxt.toUpperCase()}`; prioEl.textContent=prioTxt||'';
        const uFilter = makeFilterButton(u.us.id||'');
        li.append(uBadge,uLink,uFilter,document.createTextNode(' '),statusEl,document.createTextNode(' '),prioEl);
        const after=document.createElement('span'); after.className='meta'; after.textContent=['', pts, bugc].filter(Boolean).join(' · ');
        li.append(document.createTextNode(' '), after);
        if(u.bugs && u.bugs.length){
          const bugRow=document.createElement('div'); bugRow.className='planning-bugs';
          u.bugs.sort(cmpPlanning).forEach(b=>{ const chip=document.createElement('a'); chip.className='badge bug-chip'; chip.textContent=b.title||b.id||'BUG'; chip.href=viewerHref(b.rendered_url||b.url||b.path, b.title||b.id||'BUG'); attachAltClickFilter(chip, b.id||''); bugRow.appendChild(chip); const fb = makeFilterButton(b.id||''); bugRow.appendChild(fb); });
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
      const link=document.createElement('a'); link.className='link'; link.href=viewerHref(d.rendered_url||d.url||d.path, d.title||d.id||d.path); link.textContent='open';
      li.append(type,title,meta,link); list.appendChild(li);
    });
  }

  // Initialize search from hash (bookmarkable query)
  try {
    const initialQ = getHashParam('q');
    if(initialQ) q.value = initialQ;
  } catch(e){}

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
