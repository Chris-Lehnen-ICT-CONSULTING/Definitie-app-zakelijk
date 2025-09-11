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

  const docs = (data.documents||[]).slice().sort((a,b)=>{
    const at=(a.title||a.id||'').toLowerCase();
    const bt=(b.title||b.id||'').toLowerCase();
    return at.localeCompare(bt);
  });

  function match(d, query){
    if(!query) return true;
    const s=(d.id+' '+(d.title||'')+' '+(d.status||'')+' '+(d.owner||'')).toLowerCase();
    return query.split(/\s+/).every(t=>s.includes(t));
  }

  function render(){
    const query=(q.value||'').trim().toLowerCase();
    const t = tf.value;
    const s = sf.value;
    const filtered = docs.filter(d => match(d,query) && (!t||d.type===t) && (!s||String(d.status||'')===s));

    list.innerHTML='';
    filtered.forEach(d => {
      const li=document.createElement('li'); li.className='doc-item';
      const type=document.createElement('span'); type.className='badge type'; type.textContent=d.type||'DOC';
      const title=document.createElement('div'); title.className='title'; title.textContent=(d.title||d.id||d.path);
      const meta=document.createElement('div'); meta.className='meta'; meta.textContent=[d.status,d.owner,d.prioriteit,d.canonical?'canonical':null].filter(Boolean).join(' • ');
      const link=document.createElement('a'); link.className='link'; link.href=d.url||d.path; link.textContent='open';
      link.target='_blank';
      li.append(type,title,meta,link); list.appendChild(li);
    });
    const c = data.aggregate && data.aggregate.counts || {};
    stats.textContent=`Items: ${filtered.length}  |  (REQ:${c.REQ||0} EPIC:${c.EPIC||0} US:${c.US||0} BUG:${c.BUG||0} ARCH:${c.ARCH||0} GUIDE:${c.GUIDE||0} TEST:${c.TEST||0} COMP:${c.COMP||0} DOC:${c.DOC||0})`;
  }

  q.addEventListener('input',render); tf.addEventListener('change',render); sf.addEventListener('change',render);
  render();
})();

