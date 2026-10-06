(() => {
  const isSpanish = () => document.documentElement.lang === 'es';
  const ttl = 60 * 60 * 1000;
  let started = Date.now(), operations = [], pending = false, generation = 0;
  const pages = new Set(['dashboard','movements','reports','budgets','accounts','contacts','categories','payment-methods']);
  function remaining() { return Math.max(0, Math.ceil((ttl - (Date.now()-started))/60000)); }
  function updateClock() {
    const label = document.querySelector('[data-demo-clock]');
    if(label) label.textContent = isSpanish() ? `Reinicio en ${remaining()} min` : `Resets in ${remaining()} min`;
    if(remaining()===0) reset();
  }
  function bind() {
    initializeDialogs(); initializeMovementEditor(); initializePaymentMethodEditor(); initializeAccountEditor(); initializeContactEditor();
    document.querySelectorAll('form[method="get"] select').forEach(select => {
      select.removeAttribute('onchange');
      select.addEventListener('change', () => {
        const url = new URL(select.form.action);
        url.search = new URLSearchParams(new FormData(select.form)); navigate(url);
      });
    });
    document.querySelectorAll('form[onsubmit]').forEach(form=>form.removeAttribute('onsubmit'));
    document.querySelectorAll('[data-open-dialog]').forEach(button=>button.addEventListener('click',()=>{
      const form=document.getElementById(button.dataset.openDialog)?.querySelector('form');
      const month=form?.querySelector('[name="month_id"]')?.value;
      const date=form?.querySelector('[type="date"]');
      if(date && month) date.value=month+'-15';
    }));
    updateClock();
  }
  async function navigate(target, proposed=operations, replace=false) {
    if(pending) return;
    const url = new URL(target,location.href);
    url.searchParams.set('lang', url.searchParams.get('lang') || document.documentElement.lang || 'en');
    const page=url.pathname.slice(1)||'dashboard';
    if(!pages.has(page)) return;
    if(Date.now()-started>=ttl) { proposed=[]; started=Date.now(); }
    pending=true;
    const ticket=generation;
    const status=document.querySelector('[data-demo-status]');
    try {
      const res=await fetch('/demo/render',{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({page,lang:url.searchParams.get('lang'),month_id:url.searchParams.get('month_id'),operations:proposed})});
      if(!res.ok) {
        const error=await res.json().catch(()=>({detail:isSpanish()?'No se pudo aplicar el cambio. Reiniciá la demo e intentá de nuevo.':'Unable to apply the change. Reset the demo and try again.'}));
        throw new Error(typeof error.detail==='string'?error.detail:(isSpanish()?'Revisá los campos del formulario.':'Please check the form fields.'));
      }
      const text=await res.text();
      if(ticket!==generation)return;
      const doc=new DOMParser().parseFromString(text,'text/html');
      document.documentElement.lang = doc.documentElement.lang;
      document.querySelector('.app-shell').replaceWith(doc.querySelector('.app-shell'));
      document.querySelectorAll('body > dialog').forEach(d=>d.remove());
      doc.querySelectorAll('body > dialog').forEach(d=>document.body.append(d));
      operations=proposed;
      history[replace?'replaceState':'pushState']({},'',url.pathname+url.search);
      bind(); window.scrollTo(0,0);
    } catch(error) {
      if(status) { status.textContent=error.message; status.setAttribute('role','alert'); }
      alert(error.message);
    } finally {if(ticket===generation)pending=false;}
  }
  function reset(){generation++;pending=false;operations=[];started=Date.now();navigate(location.href,[],true);}
  document.addEventListener('click',event=>{
    const languageButton=event.target.closest('[data-demo-language]');
    if(languageButton){event.preventDefault(); const url=new URL(location.href); url.searchParams.set('lang',languageButton.dataset.demoLanguage); navigate(url); return;}
    if(event.target.closest('[data-demo-reset]')){event.preventDefault();reset();return;}
    const link=event.target.closest('a');
    if(!link||event.metaKey||event.ctrlKey||event.shiftKey||event.button!==0) return;
    const url=new URL(link.href);
    if(url.origin===location.origin && pages.has(url.pathname.slice(1))){event.preventDefault();navigate(url);}
  });
  document.addEventListener('submit',event=>{
    const form=event.target;
    if(form.method.toLowerCase()!=='post')return;
    event.preventDefault();
    const path=new URL(form.action).pathname;
    const data=Object.fromEntries(new FormData(form));
    let op;
    if(path==='/budgets')op={action:'budget',data};
    else if(path==='/movements')op={action:'create',data};
    else if(path.startsWith('/movements/')){
      const id=path.split('/')[2], remove=path.endsWith('/delete');
      if(remove&&!confirm(isSpanish()?'¿Eliminar este movimiento de tu demo?':'Delete this transaction from your demo?'))return;
      op={action:remove?'delete':'edit',id,data};
    } else return;
    const proposed=[...operations,op];
    const route=data.return_to||((path==='/budgets')?'/budgets':'/movements');
    navigate(route+'?month_id='+encodeURIComponent(data.month_id),proposed);
  });
  window.addEventListener('popstate',()=>navigate(location.href,operations,true));
  window.addEventListener('pageshow',event=>{if(event.persisted)reset();});
  window.addEventListener('pagehide',()=>{operations=[];started=Date.now();});
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)updateClock();});
  document.addEventListener('DOMContentLoaded',bind);
  setInterval(updateClock,15000);
})();
