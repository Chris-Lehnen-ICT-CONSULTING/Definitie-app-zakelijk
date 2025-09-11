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

  const docs = (data.documents||[]).slice();

  function getView(){
    const h=(location.hash||'').toLowerCase();
    const m=h.match(/view=([a-z0-9_-]+)/);
    return (m && m[1]) || 'all';
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
      if(sprintSel.childElementCount<=1){
        sprints.forEach(sp=>{
          const opt=document.createElement('option'); opt.value=sp; opt.textContent=sp; sprintSel.appendChild(opt);
        });
      }
      sprintSel.parentElement.style.display = (view==='planning') ? 'flex' : 'none';
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
      // apply optional sprint filter
      const sfv = sprintSel ? sprintSel.value : '';
      if(sfv) v = v.filter(d=>String(d.sprint||'')===sfv);
      v.sort(cmpPlanning);
      // group by sprint label
      const groups = {};
      v.forEach(d=>{
        const key = d.sprint || 'backlog';
        (groups[key] ||= []).push(d);
      });
      Object.keys(groups).sort((a,b)=>{
        const na=(d=>{const m=String(d).match(/(\d+)/);return m?parseInt(m[1],10):9999})(a);
        const nb=(d=>{const m=String(d).match(/(\d+)/);return m?parseInt(m[1],10):9999})(b);
        return na-nb || String(a).localeCompare(String(b));
      }).forEach(groupKey=>{
        const h = document.createElement('h3'); h.className='group'; h.textContent = `Sprint: ${groupKey}`;
        list.appendChild(h);
        groups[groupKey].forEach(d=>{
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
        const link=document.createElement('a'); link.className='link'; link.href=d.url||d.path; link.textContent='open'; link.target='_blank';
        li.append(type,title,meta,link); list.appendChild(li);
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

  q.addEventListener('input',render); tf.addEventListener('change',render); sf.addEventListener('change',render);
  if(sortSel) sortSel.addEventListener('change',render);
  if(sprintSel) sprintSel.addEventListener('change',render);
  window.addEventListener('hashchange', render);
  render();
})();
